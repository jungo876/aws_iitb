# KagazCheck: पहले जाँच, फिर apply

**Find the document mismatches that get scholarship and DBT applications rejected, before you apply.**

Students photograph their Aadhaar, bank passbook, marksheet and income/caste certificates. KagazCheck reads them with Amazon Bedrock and cross-checks names (Indian-name-aware), DOB, gender, father's name, income limit, certificate age, IFSC, account ownership and DBT seeding. It returns a fix-list in English, Hindi and 10 more Indian languages, with audio and WhatsApp sharing.

Built for the *Campus to Cloud Hackathon (AWS × Techfest IIT Bombay 2026-27)*.

- 🌐 Live: `<LIVE_URL>`
- 📄 [Idea brief](docs/IDEA_BRIEF.md) · 🛠 [Build summary](docs/BUILD_SUMMARY.md) · 🎬 [Demo script](docs/DEMO_VIDEO_SCRIPT.md)

## Repository layout
```
backend/            Lambda (Python 3.12, no dependencies beyond boto3)
  app.py            HTTP routing, validation, stats
  extract.py        Bedrock (Nova) vision extraction + Textract fallback + masking
  names.py          Indian-name-aware matcher
  rules.py          Cross-document rules engine & scheme config
  content.py        Hand-written explanations / fix steps (English + Hindi)
  tests/            pytest suite
frontend/           Static site (vanilla JS, no build step) + sample SPECIMEN documents
infra/
  template.yaml     CloudFormation: CloudFront, S3, API Gateway, Lambda, DynamoDB, IAM, alarm
  deploy.py         One-command deploy
tools/
  local_server.py   Run locally (mock AWS or --real)
  ui_test.py        Playwright end-to-end test (desktop + mobile), --live for real AWS
  make_samples.py   Regenerates the sample documents
```

## Run locally
```bash
python -m pytest backend/tests          # unit tests
python tools/local_server.py            # http://localhost:8765 (AWS mocked)
python tools/local_server.py --real     # uses your AWS credentials
```

## Deploy (AWS account with credentials configured)
```bash
pip install boto3
python infra/deploy.py                  # ap-south-1, prints the CloudFront URL
python infra/deploy.py --site-only      # frontend-only update
```

## End-to-end test
```bash
pip install playwright                  # uses installed Microsoft Edge
python tools/ui_test.py --url https://<your-cloudfront-domain> --live
```

## Privacy
Images are processed in memory and never stored. Aadhaar and account numbers are masked to the last 4 digits. Only anonymous issue counters are written to DynamoDB.

*Independent student project; not affiliated with UIDAI, NSP or any government body. Sample documents are synthetic and marked SPECIMEN.*
