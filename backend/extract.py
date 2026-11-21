"""Read fields from a document photo.

Primary path : Amazon Bedrock (Amazon Nova, multimodal) -> strict JSON.
Fallback path: Amazon Textract DetectDocumentText + regex heuristics, used
               automatically if Bedrock is unavailable or returns garbage.

Images are processed in memory only and never written to storage. Any 12-digit
Aadhaar-like number in the output is masked to the last 4 digits.
"""
from __future__ import annotations

import json
import os
import re

DOC_TYPES = ("aadhaar", "bank", "marksheet", "income", "caste")

FIELDS = {
    "aadhaar": {
        "name": "Full name of the card holder in English, exactly as printed",
        "dob": "Date of birth as DD/MM/YYYY. If only the year of birth is printed, return just the 4-digit year",
        "gender": "MALE / FEMALE / TRANSGENDER",
        "aadhaar_last4": "ONLY the last 4 digits of the 12-digit Aadhaar number",
    },
    "bank": {
        "holder_name": "Account holder name in English, exactly as printed (for joint accounts, the first holder)",
        "ifsc": "IFSC code exactly as printed (11 characters)",
        "bank_name": "Name of the bank",
        "branch": "Branch name",
        "account_last4": "ONLY the last 4 digits of the account number",
    },
    "marksheet": {
        "name": "Student / candidate name in English, exactly as printed",
        "father_name": "Father's name in English",
        "mother_name": "Mother's name in English",
        "dob": "Date of birth as DD/MM/YYYY",
        "board": "Name of the examination board",
        "year": "Year of passing (4 digits)",
    },
    "income": {
        "name": "Name of the applicant / person the certificate is issued to, in English",
        "father_name": "Father's (or husband's) name in English",
        "annual_income": "Total annual family income in rupees as a plain integer, e.g. 180000",
        "issue_date": "Date of issue as DD/MM/YYYY",
        "issuing_authority": "Issuing office / authority",
    },
    "caste": {
        "name": "Name of the person the certificate is issued to, in English",
        "father_name": "Father's name in English",
        "category": "Caste category, e.g. SC / ST / OBC / EBC",
        "caste": "Caste / sub-caste name",
        "issue_date": "Date of issue as DD/MM/YYYY",
    },
}

DOC_DESCRIPTIONS = {
    "aadhaar": "an Indian Aadhaar card (front side)",
    "bank": "the first page of an Indian bank passbook",
    "marksheet": "a Class 10 marksheet / certificate from an Indian school board",
    "income": "an income certificate issued by an Indian state government office",
    "caste": "a caste certificate issued by an Indian state government office",
}

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "apac.amazon.nova-lite-v1:0")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", os.environ.get("AWS_REGION", "ap-south-1"))
MOCK = os.environ.get("MOCK_AWS") == "1"

_clients: dict = {}


def _client(name: str, region: str | None = None):
    key = (name, region)
    if key not in _clients:
        import boto3
        from botocore.config import Config
        cfg = Config(retries={"max_attempts": 2, "mode": "standard"}, read_timeout=25, connect_timeout=5)
        _clients[key] = boto3.client(name, region_name=region, config=cfg)
    return _clients[key]


def build_prompt(doc_type: str) -> str:
    fields = FIELDS[doc_type]
    schema = ",\n".join(f'  "{k}": "<{v}>"' for k, v in fields.items())
    return f"""You are reading a photo that should be {DOC_DESCRIPTIONS[doc_type]}.
Extract the fields below. Rules:
- Copy names EXACTLY as printed in English letters, including spelling mistakes and initials. Never correct or complete a name.
- If a field is not visible or not readable, use null. Never guess.
- Never output a full Aadhaar or bank account number; only the last 4 digits.
- "detected_type" must be one of: aadhaar, bank, marksheet, income, caste, other.
- "quality" must be "good", "blurry", "cropped" or "dark".
Respond with ONLY a JSON object, no extra text:
{{
  "detected_type": "<type>",
  "quality": "<quality>",
{schema}
}}"""


_AADHAAR_RE = re.compile(r"\b\d{4}\s?\d{4}\s?(\d{4})\b")
_LONG_DIGITS_RE = re.compile(r"\b\d{6,}(\d{4})\b")


def mask_sensitive(value):
    """Mask Aadhaar / account numbers anywhere in the extracted data."""
    if isinstance(value, dict):
        return {k: mask_sensitive(v) for k, v in value.items()}
    if isinstance(value, list):
        return [mask_sensitive(v) for v in value]
    if isinstance(value, str):
        value = _AADHAAR_RE.sub(lambda m: "XXXX XXXX " + m.group(1), value)
        value = _LONG_DIGITS_RE.sub(lambda m: "XXXX" + m.group(1), value)
    return value


def _clean(doc_type: str, data: dict) -> dict:
    out = {}
    for key in FIELDS[doc_type]:
        v = data.get(key)
        if isinstance(v, str):
            v = v.strip()
            if v.lower() in ("", "null", "none", "n/a", "na", "not visible", "unknown"):
                v = None
        out[key] = v
    for key in ("aadhaar_last4", "account_last4"):
        if key in out and out[key]:
            digits = re.sub(r"\D", "", str(out[key]))
            out[key] = digits[-4:] if digits else None
    if out.get("ifsc"):
        out["ifsc"] = re.sub(r"\s+", "", str(out["ifsc"])).upper()
    if out.get("annual_income") is not None:
        digits = re.sub(r"[^\d]", "", str(out["annual_income"]).split(".")[0])
        out["annual_income"] = int(digits) if digits else None
    return mask_sensitive(out)


def _parse_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON in model output")
    return json.loads(m.group(0))


def extract_with_bedrock(doc_type: str, image: bytes, fmt: str) -> dict:
    resp = _client("bedrock-runtime", BEDROCK_REGION).converse(
        modelId=MODEL_ID,
        messages=[{
            "role": "user",
            "content": [
                {"image": {"format": fmt, "source": {"bytes": image}}},
                {"text": build_prompt(doc_type)},
            ],
        }],
        inferenceConfig={"maxTokens": 700, "temperature": 0},
    )
    text = "".join(c.get("text", "") for c in resp["output"]["message"]["content"])
    data = _parse_json(text)
    return {
        "fields": _clean(doc_type, data),
        "detected_type": data.get("detected_type"),
        "quality": data.get("quality"),
        "engine": "bedrock",
    }


# ---------------------------------------------------------- Textract path ---

_DATE_RE = re.compile(r"\b(\d{2})[/\-.](\d{2})[/\-.](\d{4})\b")
_IFSC_RE = re.compile(r"\b([A-Z]{4}0[A-Z0-9]{6})\b")


def _after_label(lines: list[str], labels: tuple[str, ...]) -> str | None:
    for i, line in enumerate(lines):
        low = line.lower()
        for lab in labels:
            if lab in low:
                rest = re.split(re.escape(lab), line, flags=re.I, maxsplit=1)[-1]
                rest = rest.strip(" :-.\t")
                if len(re.sub(r"[^A-Za-z]", "", rest)) >= 3:
                    return rest
                if i + 1 < len(lines):
                    return lines[i + 1].strip(" :-.")
    return None


def parse_lines(doc_type: str, lines: list[str]) -> dict:
    """Best-effort heuristics over OCR lines (fallback only)."""
    text = "\n".join(lines)
    d: dict = {}
    dates = ["/".join(m) for m in _DATE_RE.findall(text)]
    if doc_type == "aadhaar":
        for i, line in enumerate(lines):
            if re.search(r"(DOB|Date of Birth|Year of Birth|जन्म)", line, re.I):
                m = _DATE_RE.search(line) or re.search(r"\b(19|20)\d{2}\b", line)
                if m:
                    d["dob"] = "/".join(m.groups()) if m.re is _DATE_RE else m.group(0)
                for j in range(i - 1, -1, -1):
                    cand = lines[j].strip()
                    if re.fullmatch(r"[A-Za-z .]{3,}", cand) and "government" not in cand.lower():
                        d["name"] = cand
                        break
                break
        g = re.search(r"\b(MALE|FEMALE|TRANSGENDER)\b", text, re.I)
        d["gender"] = g.group(1).upper() if g else None
        a = _AADHAAR_RE.search(text)
        d["aadhaar_last4"] = a.group(1) if a else None
    elif doc_type == "bank":
        d["holder_name"] = _after_label(lines, ("account holder name", "name of account holder", "customer name", "name"))
        m = _IFSC_RE.search(text.replace(" ", ""))
        d["ifsc"] = m.group(1) if m else None
        d["bank_name"] = next((l for l in lines if "bank" in l.lower()), None)
    elif doc_type == "marksheet":
        d["name"] = _after_label(lines, ("candidate's name", "candidate name", "name of student", "student name", "name"))
        d["father_name"] = _after_label(lines, ("father's name", "father name"))
        d["mother_name"] = _after_label(lines, ("mother's name", "mother name"))
        d["dob"] = dates[0] if dates else None
    elif doc_type in ("income", "caste"):
        d["name"] = _after_label(lines, ("certified that", "this is to certify that", "name of applicant", "name"))
        d["father_name"] = _after_label(lines, ("s/o", "d/o", "son of", "daughter of", "father's name", "father name"))
        if doc_type == "income":
            m = re.search(r"(?:Rs\.?|₹|INR)\s*([\d,]{4,})", text, re.I)
            d["annual_income"] = m.group(1) if m else None
        else:
            m = re.search(r"\b(SC|ST|OBC|EBC)\b", text)
            d["category"] = m.group(1) if m else None
        issue = re.search(r"(?:date of issue|issue date|issued on|dated?)\s*[:\-]?\s*(\d{2}[/\-.]\d{2}[/\-.]\d{4})", text, re.I)
        d["issue_date"] = issue.group(1) if issue else (dates[-1] if dates else None)
    return d


def extract_with_textract(doc_type: str, image: bytes) -> dict:
    resp = _client("textract").detect_document_text(Document={"Bytes": image})
    lines = [b["Text"] for b in resp.get("Blocks", []) if b.get("BlockType") == "LINE"]
    return {"fields": _clean(doc_type, parse_lines(doc_type, lines)),
            "detected_type": None, "quality": None, "engine": "textract"}


# ------------------------------------------------------------------ mock ---

MOCK_FIXTURES = {
    "aadhaar": {"name": "Priyanka Kumari", "dob": "14/08/2005", "gender": "FEMALE", "aadhaar_last4": "4821"},
    "bank": {"holder_name": "PRIANKA KUMARI", "ifsc": "DEMO0004587", "bank_name": "Demo Gramin Bank",
             "branch": "Gaya Main", "account_last4": "7712"},
    "marksheet": {"name": "PRIYANKA KUMARI", "father_name": "RAMESH PRASAD", "mother_name": "SUNITA DEVI",
                  "dob": "14/08/2005", "board": "State School Examination Board", "year": "2021"},
    "income": {"name": "Priyanka Kumari", "father_name": "Ramesh Prasad", "annual_income": 180000,
               "issue_date": "12/03/2025", "issuing_authority": "Circle Officer, Gaya Sadar"},
    "caste": {"name": "Priyanka Kumari", "father_name": "Ramesh Prasad", "category": "SC",
              "caste": "Ravidas", "issue_date": "05/06/2022"},
}


def extract(doc_type: str, image: bytes, fmt: str) -> dict:
    if doc_type not in DOC_TYPES:
        raise ValueError("unknown document type")
    if MOCK:
        return {"fields": _clean(doc_type, MOCK_FIXTURES[doc_type]), "detected_type": doc_type,
                "quality": "good", "engine": "mock"}
    errors = []
    try:
        return extract_with_bedrock(doc_type, image, fmt)
    except Exception as e:  # noqa: BLE001 - fall back on any Bedrock failure
        errors.append(f"bedrock: {type(e).__name__}")
    try:
        result = extract_with_textract(doc_type, image)
        result["fallback_reason"] = errors[0]
        return result
    except Exception as e:  # noqa: BLE001
        errors.append(f"textract: {type(e).__name__}")
    raise RuntimeError("; ".join(errors))
