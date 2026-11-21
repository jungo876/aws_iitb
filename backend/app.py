"""KagazCheck API - single AWS Lambda behind an API Gateway HTTP API.

Routes
  GET  /api/health
  GET  /api/schemes
  POST /api/extract    {doc_type, image(base64 / data URL)}  -> fields
  POST /api/check      {scheme, docs, income_limit?}          -> report (en + hi)
  POST /api/translate  {texts[], target}                       -> texts[]
  POST /api/speak      {text, lang}                            -> mp3 (base64)
  GET  /api/stats                                              -> anonymous aggregates
"""
from __future__ import annotations

import base64
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone

import content
import extract as extractor
import rules

log = logging.getLogger()
log.setLevel(logging.INFO)

MOCK = os.environ.get("MOCK_AWS") == "1"
STATS_TABLE = os.environ.get("STATS_TABLE", "")
MAX_IMAGE_BYTES = 4_500_000
IST = timezone(timedelta(hours=5, minutes=30))

TRANSLATE_LANGS = {"mr", "ta", "te", "bn", "gu", "kn", "ml", "pa", "ur", "or"}
_translate_cache: dict = {}


def today_ist() -> date:
    return datetime.now(IST).date()


# ------------------------------------------------------------- helpers ---

def response(status: int, body: dict, headers: dict | None = None):
    h = {"content-type": "application/json; charset=utf-8", "cache-control": "no-store"}
    h.update(headers or {})
    return {"statusCode": status, "headers": h, "body": json.dumps(body, ensure_ascii=False)}


class BadRequest(Exception):
    pass


def parse_body(event) -> dict:
    raw = event.get("body") or ""
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise BadRequest("Body must be JSON") from e
    if not isinstance(data, dict):
        raise BadRequest("Body must be a JSON object")
    return data


def decode_image(value: str) -> tuple[bytes, str]:
    if not value or not isinstance(value, str):
        raise BadRequest("image is required")
    if value.startswith("data:"):
        value = value.split(",", 1)[-1]
    try:
        data = base64.b64decode(value, validate=False)
    except Exception as e:  # noqa: BLE001
        raise BadRequest("image must be base64") from e
    if len(data) > MAX_IMAGE_BYTES:
        raise BadRequest("Image too large. Please use a photo under 4 MB.")
    if data[:3] == b"\xff\xd8\xff":
        return data, "jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return data, "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return data, "webp"
    raise BadRequest("Unsupported image. Please upload a JPG or PNG photo.")


def _aws(name):
    return extractor._client(name)


# --------------------------------------------------------------- routes ---

def route_schemes(_body):
    return {"schemes": [
        {"id": k, "name": v["name"], "name_hi": v["name_hi"], "income_limit": v["income_limit"],
         "required": v["required"]}
        for k, v in rules.SCHEMES.items()
    ]}


def route_extract(body):
    doc_type = body.get("doc_type")
    if doc_type not in extractor.DOC_TYPES:
        raise BadRequest("doc_type must be one of " + ", ".join(extractor.DOC_TYPES))
    image, fmt = decode_image(body.get("image"))
    t0 = time.time()
    result = extractor.extract(doc_type, image, fmt)
    result["ms"] = int((time.time() - t0) * 1000)
    result["doc_type"] = doc_type
    result["type_mismatch"] = bool(result.get("detected_type")) and result["detected_type"] not in (doc_type,)
    log.info(json.dumps({"route": "extract", "doc": doc_type, "engine": result["engine"],
                         "ms": result["ms"], "detected": result.get("detected_type"),
                         "fallback": result.get("fallback_reason")}))
    return result


def _clean_docs(docs) -> dict:
    if not isinstance(docs, dict):
        raise BadRequest("docs must be an object")
    out = {}
    for k, v in docs.items():
        if k in extractor.DOC_TYPES and isinstance(v, dict):
            out[k] = {fk: (str(fv)[:200] if fv is not None else None) for fk, fv in v.items()
                      if fk in extractor.FIELDS[k]}
    return out


def route_check(body):
    scheme = body.get("scheme") or "other"
    docs = _clean_docs(body.get("docs") or {})
    if not docs:
        raise BadRequest("Add at least one document")
    limit = body.get("income_limit")
    limit = rules.parse_amount(limit) if limit not in (None, "") else None
    report = rules.run_checks(scheme, docs, today=today_ist(), income_limit_override=limit)
    for issue in report["issues"]:
        issue["text"] = {"en": content.render_issue(issue, "en"), "hi": content.render_issue(issue, "hi")}
    report["generated_on"] = today_ist().isoformat()
    record_stats(report)
    return report


def route_translate(body):
    target = body.get("target")
    texts = body.get("texts")
    if target not in TRANSLATE_LANGS:
        raise BadRequest("Unsupported language")
    if not isinstance(texts, list) or len(texts) > 80:
        raise BadRequest("texts must be a list (max 80)")
    texts = [str(t)[:2000] for t in texts]
    if sum(len(t) for t in texts) > 20000:
        raise BadRequest("Too much text")

    def one(t):
        if not t.strip():
            return t
        key = (t, target)
        if key not in _translate_cache:
            if MOCK:
                _translate_cache[key] = f"[{target}] {t}"
            else:
                r = _aws("translate").translate_text(Text=t, SourceLanguageCode="en", TargetLanguageCode=target)
                _translate_cache[key] = r["TranslatedText"]
        return _translate_cache[key]

    with ThreadPoolExecutor(max_workers=8) as pool:
        out = list(pool.map(one, texts))
    return {"texts": out, "target": target}


def route_speak(body):
    text = str(body.get("text") or "").strip()[:2800]
    lang = body.get("lang") if body.get("lang") in ("hi", "en") else "hi"
    if not text:
        raise BadRequest("text is required")
    if MOCK:
        return {"audio": "", "voice": "mock"}
    polly = _aws("polly")
    code = "hi-IN" if lang == "hi" else "en-IN"
    attempts = [("Kajal", "neural"), ("Aditi" if lang == "hi" else "Raveena", "standard")]
    last = None
    for voice, engine in attempts:
        try:
            r = polly.synthesize_speech(Text=text, OutputFormat="mp3", VoiceId=voice,
                                        Engine=engine, LanguageCode=code)
            audio = r["AudioStream"].read()
            return {"audio": base64.b64encode(audio).decode(), "voice": f"{voice}/{engine}"}
        except Exception as e:  # noqa: BLE001
            last = e
    raise RuntimeError(f"speech failed: {type(last).__name__}")


# --------------------------------------------------------------- stats ---

def record_stats(report: dict):
    """Store only anonymous counters - never names, numbers or images."""
    if MOCK or not STATS_TABLE:
        return
    keys = ["total", f"verdict#{report['verdict']}", f"scheme#{report['scheme']['id']}",
            f"day#{report['generated_on']}"]
    seen = set()
    for issue in report["issues"]:
        code = issue["code"]
        if code == "name_mismatch":
            code = f"name_mismatch:{issue['params']['doc']}"
        if code not in seen and code != "dbt_seeding":
            keys.append(f"issue#{code}")
            seen.add(code)
    try:
        table = _dynamo_table()
        for k in keys:
            table.update_item(Key={"pk": k}, UpdateExpression="ADD n :one",
                              ExpressionAttributeValues={":one": 1})
    except Exception as e:  # noqa: BLE001 - stats must never break a check
        log.warning(json.dumps({"stats_error": type(e).__name__}))


def _dynamo_table():
    import boto3
    return boto3.resource("dynamodb").Table(STATS_TABLE)


def route_stats(_body):
    if MOCK or not STATS_TABLE:
        items = []
    else:
        items = _dynamo_table().scan(Limit=500).get("Items", [])
    counts = {it["pk"]: int(it.get("n", 0)) for it in items}
    out = {"total": counts.get("total", 0), "issues": {}, "verdicts": {}, "schemes": {}, "days": {}}
    for k, n in counts.items():
        if "#" not in k:
            continue
        kind, name = k.split("#", 1)
        bucket = {"issue": "issues", "verdict": "verdicts", "scheme": "schemes", "day": "days"}.get(kind)
        if bucket:
            out[bucket][name] = n
    return out


ROUTES = {
    ("GET", "/api/health"): lambda b: {"ok": True, "mock": MOCK, "model": extractor.MODEL_ID},
    ("GET", "/api/schemes"): route_schemes,
    ("POST", "/api/extract"): route_extract,
    ("POST", "/api/check"): route_check,
    ("POST", "/api/translate"): route_translate,
    ("POST", "/api/speak"): route_speak,
    ("GET", "/api/stats"): route_stats,
}


def handler(event, _context=None):
    method = (event.get("requestContext", {}).get("http", {}).get("method")
              or event.get("httpMethod") or "GET").upper()
    path = event.get("rawPath") or event.get("path") or "/"
    if method == "OPTIONS":
        return response(204, {})
    fn = ROUTES.get((method, path.rstrip("/") or "/"))
    if not fn:
        return response(404, {"error": "Not found"})
    try:
        body = parse_body(event) if method == "POST" else {}
        return response(200, fn(body))
    except BadRequest as e:
        return response(400, {"error": str(e)})
    except Exception as e:  # noqa: BLE001
        log.exception("unhandled")
        return response(502, {"error": "Something went wrong reading this. Please try again or type the details manually.",
                              "detail": type(e).__name__})
