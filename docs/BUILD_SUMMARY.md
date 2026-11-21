# KagazCheck: Build Summary

Live: `<LIVE_URL>` · Region: **ap-south-1 (Mumbai)** · Infra as code: [`infra/template.yaml`](../infra/template.yaml)

## Architecture
```
Phone browser ──HTTPS──▶ Amazon CloudFront ──/*──────▶ Amazon S3 (private, OAC)  static site
                               │
                               └──/api/*──▶ API Gateway (HTTP API, throttled)
                                                   │
                                                   ▼
                                     AWS Lambda (Python 3.12, arm64)
                       ┌───────────────┬────────────┼──────────────┬──────────────┐
                       ▼               ▼            ▼              ▼              ▼
                Amazon Bedrock   Amazon Textract  Amazon       Amazon Polly   Amazon DynamoDB
                (Nova, vision)   (OCR fallback)   Translate    (Hindi audio)  (anon. counters)
                                                                                  │
                                                         Amazon CloudWatch logs + error alarm
```

## AWS services and why each one

| Service | What it does in KagazCheck | Why this choice |
|---|---|---|
| **Amazon Bedrock (Amazon Nova)** | Reads each document photo and returns strict JSON: names exactly as printed, DOB, IFSC, income, issue date, detected document type and photo quality | A multimodal model handles real-world variety (passbooks from hundreds of banks, state-specific certificates) without per-format templates. Called through the Converse API with temperature 0 and a JSON-only prompt. Cross-region inference profile keeps it fast from Mumbai. |
| **Amazon Textract** | Automatic OCR fallback (DetectDocumentText + heuristics) if Bedrock errors | The demo and real users never hit a dead end. Resilience by design. |
| **Amazon Translate** | Translates the fix-list into Marathi, Bengali, Tamil, Telugu, Gujarati, Kannada, Malayalam, Punjabi, Odia and Urdu | Hindi and English advice is hand-written for accuracy; Translate extends reach to 10 more languages at near-zero cost. Results are cached in memory. |
| **Amazon Polly** | Reads the report aloud in Hindi / Indian English (Kajal neural voice, falls back to Aditi/Raveena) | Low-literacy users and parents can *listen* to what to do. |
| **AWS Lambda** | One Python function: routing, validation, extraction, rules engine, stats | Pay-per-request, scales to zero, comfortably within Free Tier. arm64 for lower cost. 1024 MB for fast image handling. |
| **Amazon API Gateway (HTTP API)** | `/api/*` endpoints | Cheapest API Gateway type; stage-level throttling (15 rps, burst 30) protects free-tier credits. |
| **Amazon S3** | Hosts the static frontend | Private bucket, encryption on, public access blocked. Only CloudFront can read it (Origin Access Control). |
| **Amazon CloudFront** | Single HTTPS domain for site + API, caching, compression, HTTP/3, security headers | Fast in India via edge locations; same-origin API means no CORS; managed SecurityHeaders policy. |
| **Amazon DynamoDB** | Anonymous counters (`issue#name_mismatch:bank`, `verdict#fix_first`, …) powering the Insights page | Atomic `ADD` updates, provisioned 5 RCU/WCU, within Free Tier. **No PII is ever written.** |
| **Amazon CloudWatch** | Structured logs (route, engine, latency; no personal data), 14-day retention, error alarm | Operability during Demo Day. |
| **AWS CloudFormation** | Entire stack as code; `python infra/deploy.py` deploys everything | Reproducible; judges can read exactly what runs. |
| **IAM** | Least-privilege role: Nova models only, specific DynamoDB table, Textract/Translate/Polly actions | Security by default. |

## Key engineering decisions
1. **LLM reads, rules decide.** Bedrock only extracts fields; all verdicts come from a deterministic, unit-tested Python rules engine ([`backend/rules.py`](../backend/rules.py)), and all advice text is hand-written ([`backend/content.py`](../backend/content.py)). This keeps the output predictable, explainable and free of hallucinated advice.
2. **Indian-name matcher** ([`backend/names.py`](../backend/names.py)): honorific stripping (Shri/Smt/Kumari/Ku.), relation clauses (S/O, D/O), abbreviation table (MD/MOHD/MOHAMMAD, KR/KUMAR), initials, a phonetic key for romanised Indian names (ee→i, w→v, x→ks, sh→s, …), edit distance, and token alignment. It classifies the *type* of mismatch because each type needs a different fix.
3. **Human-in-the-loop.** The student reviews and edits every extracted value before checking.
4. **Privacy.** Images stay in memory and are never written to disk, S3 or logs. Aadhaar and account numbers are masked twice (prompt plus regex). Mumbai region. Client-side re-encode to JPEG strips EXIF/GPS metadata.
5. **Built for Bharat bandwidth.** Photos are resized on the phone (≤1600 px, about 200–400 KB). Vanilla JS with no framework, so the whole app is under 60 KB of code. Works on low-end Android.
6. **Graceful degradation.** Bedrock fails over to Textract; Polly neural fails over to a standard voice; stats failures never block a check; users can always type details manually.

## Development process
- **Backend first, test-driven:** 33 unit tests (name matcher cases, every rule, every issue rendered in both languages with no missing placeholders, masking, handler validation). `pytest backend/tests`
- **Local mock server** ([`tools/local_server.py`](../tools/local_server.py)) runs the real Lambda handler with AWS mocked, for fast UI iteration.
- **Automated browser tests** ([`tools/ui_test.py`](../tools/ui_test.py)) on desktop and mobile viewports: full judge flow, Hindi switch, translation, audio, insights, validation, no console errors, no horizontal scroll. Run against the **live URL** with `--live` to assert real Bedrock extraction accuracy on the sample documents.
- **Synthetic sample documents** ([`tools/make_samples.py`](../tools/make_samples.py)) clearly marked SPECIMEN, with a fictional student, so anyone can try the full flow in one click without uploading real IDs.
- **One-command deploy** ([`infra/deploy.py`](../infra/deploy.py)): packages Lambda, probes which Bedrock model is enabled in the account, deploys CloudFormation, uploads the site and invalidates CloudFront.

## Cost (Free Tier)
Lambda, API Gateway, DynamoDB, CloudFront, S3 and CloudWatch usage stays inside Free Tier limits. Textract, Translate and Polly have free-tier allowances. A Nova Lite document read costs a fraction of a paisa and is covered by Free Tier credits. API throttling caps worst-case spend.
