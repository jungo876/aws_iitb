"""One-command deploy of KagazCheck to AWS.

  pip install boto3
  python infra/deploy.py                       # region ap-south-1 (Mumbai)
  python infra/deploy.py --model apac.amazon.nova-pro-v1:0

Steps: package Lambda -> upload to an artifacts bucket -> pick a Bedrock model
that works in this account -> create/update the CloudFormation stack ->
upload the static site -> invalidate CloudFront -> print the live URL.
"""
import argparse
import hashlib
import io
import json
import mimetypes
import os
import sys
import time
import zipfile

import boto3
from botocore.exceptions import ClientError

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
p = argparse.ArgumentParser()
p.add_argument("--region", default="ap-south-1")
p.add_argument("--stack", default="kagazcheck")
p.add_argument("--model", help="Bedrock model / inference profile id to force")
p.add_argument("--site-only", action="store_true", help="only re-upload the frontend")
args = p.parse_args()

session = boto3.Session(region_name=args.region)
account = session.client("sts").get_caller_identity()["Account"]
cfn = session.client("cloudformation")
s3 = session.client("s3")
print(f"Account {account}  region {args.region}  stack {args.stack}")


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ------------------------------------------------------------------ helpers
def ensure_bucket(name):
    try:
        s3.head_bucket(Bucket=name)
    except ClientError:
        log(f"creating artifacts bucket {name}")
        kw = {} if args.region == "us-east-1" else {"CreateBucketConfiguration": {"LocationConstraint": args.region}}
        s3.create_bucket(Bucket=name, **kw)
        s3.put_public_access_block(Bucket=name, PublicAccessBlockConfiguration={
            "BlockPublicAcls": True, "IgnorePublicAcls": True, "BlockPublicPolicy": True, "RestrictPublicBuckets": True})


def package_lambda():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(os.path.join(ROOT, "backend"))):
            if f.endswith(".py"):
                info = zipfile.ZipInfo(f, date_time=(2026, 1, 1, 0, 0, 0))
                info.external_attr = 0o644 << 16
                with open(os.path.join(ROOT, "backend", f), "rb") as fh:
                    z.writestr(info, fh.read(), zipfile.ZIP_DEFLATED)
    data = buf.getvalue()
    return data, hashlib.sha256(data).hexdigest()[:16]


def probe_bedrock():
    candidates = [
        (args.region, args.model),
        (args.region, "apac.amazon.nova-lite-v1:0"),
        (args.region, "global.amazon.nova-2-lite-v1:0"),
        (args.region, "amazon.nova-lite-v1:0"),
        ("us-east-1", "us.amazon.nova-lite-v1:0"),
    ] if args.model else [
        (args.region, "apac.amazon.nova-lite-v1:0"),
        (args.region, "global.amazon.nova-2-lite-v1:0"),
        (args.region, "amazon.nova-lite-v1:0"),
        ("us-east-1", "us.amazon.nova-lite-v1:0"),
    ]
    for region, model in candidates:
        if not model:
            continue
        try:
            br = session.client("bedrock-runtime", region_name=region)
            br.converse(modelId=model, messages=[{"role": "user", "content": [{"text": "Reply with OK"}]}],
                        inferenceConfig={"maxTokens": 5})
            log(f"Bedrock OK: {model} in {region}")
            return model, region
        except ClientError as e:
            log(f"Bedrock {model} in {region}: {e.response['Error']['Code']} - {e.response['Error']['Message'][:120]}")
    log("WARNING: no Bedrock model usable; app will fall back to Amazon Textract.")
    return "apac.amazon.nova-lite-v1:0", args.region


def stack_outputs():
    st = cfn.describe_stacks(StackName=args.stack)["Stacks"][0]
    return {o["OutputKey"]: o["OutputValue"] for o in st.get("Outputs", [])}


def deploy_stack(params):
    with open(os.path.join(ROOT, "infra", "template.yaml"), encoding="utf-8") as fh:
        body = fh.read()
    kw = dict(StackName=args.stack, TemplateBody=body, Capabilities=["CAPABILITY_IAM"],
              Parameters=[{"ParameterKey": k, "ParameterValue": v} for k, v in params.items()],
              Tags=[{"Key": "project", "Value": "kagazcheck"}])
    try:
        cfn.describe_stacks(StackName=args.stack)
        exists = True
    except ClientError:
        exists = False
    try:
        if exists:
            log("updating stack…")
            cfn.update_stack(**kw)
            waiter = cfn.get_waiter("stack_update_complete")
        else:
            log("creating stack (CloudFront takes ~5 minutes)…")
            cfn.create_stack(**kw, OnFailure="DELETE")
            waiter = cfn.get_waiter("stack_create_complete")
        waiter.wait(StackName=args.stack, WaiterConfig={"Delay": 15, "MaxAttempts": 120})
    except ClientError as e:
        if "No updates are to be performed" in str(e):
            log("stack already up to date")
        else:
            raise
    except Exception:
        events = cfn.describe_stack_events(StackName=args.stack)["StackEvents"][:15]
        for ev in events:
            if "FAILED" in ev["ResourceStatus"]:
                print("  ", ev["LogicalResourceId"], ev["ResourceStatus"], ev.get("ResourceStatusReason", ""))
        raise
    log("stack ready")


CACHE = {".html": "no-cache", ".js": "public, max-age=300", ".css": "public, max-age=300"}


def upload_site(bucket):
    site = os.path.join(ROOT, "frontend")
    n = 0
    for dirpath, _, files in os.walk(site):
        for f in files:
            full = os.path.join(dirpath, f)
            key = os.path.relpath(full, site).replace(os.sep, "/")
            ext = os.path.splitext(f)[1].lower()
            ctype = mimetypes.guess_type(f)[0] or "application/octet-stream"
            if ext in (".html", ".js", ".css"):
                ctype += "; charset=utf-8"
            s3.upload_file(full, bucket, key, ExtraArgs={
                "ContentType": ctype, "CacheControl": CACHE.get(ext, "public, max-age=86400")})
            n += 1
    log(f"uploaded {n} site files")


# ------------------------------------------------------------------ main
if not args.site_only:
    artifacts = f"kagazcheck-artifacts-{account}-{args.region}"
    ensure_bucket(artifacts)
    zip_bytes, digest = package_lambda()
    key = f"lambda/api-{digest}.zip"
    s3.put_object(Bucket=artifacts, Key=key, Body=zip_bytes)
    log(f"uploaded lambda package s3://{artifacts}/{key} ({len(zip_bytes) // 1024} KB)")
    model, model_region = probe_bedrock()
    deploy_stack({"CodeBucket": artifacts, "CodeKey": key, "BedrockModelId": model, "BedrockRegion": model_region})

out = stack_outputs()
upload_site(out["SiteBucketName"])
cf = session.client("cloudfront")
cf.create_invalidation(DistributionId=out["DistributionId"], InvalidationBatch={
    "Paths": {"Quantity": 1, "Items": ["/*"]}, "CallerReference": str(time.time())})
log("CloudFront invalidation requested")
with open(os.path.join(ROOT, "infra", "deploy_output.json"), "w") as fh:
    json.dump(out, fh, indent=2)
print("\nLIVE URL:", out["Url"])
