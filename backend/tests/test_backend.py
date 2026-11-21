import base64
import json
import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["MOCK_AWS"] = "1"

import app  # noqa: E402
import content  # noqa: E402
import extract  # noqa: E402
import rules  # noqa: E402
from names import compare_names, tokens  # noqa: E402

TODAY = date(2026, 11, 21)


# ------------------------------------------------------------------ names ---

@pytest.mark.parametrize("a,b,kind", [
    ("Priyanka Kumari", "PRIYANKA KUMARI", "match"),  # case is ignored
    ("Priyanka Kumari", "Priyanka Kumari", "match"),
    ("Priyanka Kumari", "Ms. Priyanka  Kumari", "format"),
    ("Priyanka Kumari", "PRIANKA KUMARI", "spelling"),
    ("Mohammad Arif Khan", "MD ARIF KHAN", "abbreviation"),
    ("Mohammad Arif Khan", "MOHD. ARIF KHAN", "abbreviation"),
    ("Rahul Kumar Singh", "Rahul Singh", "missing_part"),
    ("Rahul Kumar Singh", "R. K. Singh", "initials"),
    ("Rahul Kumar Singh", "Singh Rahul Kumar", "order"),
    ("Rahul Kumar", "Amit Sharma", "different"),
    ("Rahul Kumar", "Rahul Sharma", "different"),
    ("Sunita Devi", "SUNEETA DEVI", "spelling"),
    ("Lakshmi Narayanan", "LAXMI NARAYANAN", "spelling"),
    ("Rakesh Kumar", "Rakesh Kr.", "abbreviation"),
])
def test_compare_names(a, b, kind):
    assert compare_names(a, b).kind == kind


def test_tokens_strip_honorifics_and_relations():
    assert tokens("Shri Ramesh Prasad S/O Late Mahesh") == ["RAMESH", "PRASAD"]
    assert tokens("Kumari Priyanka") == ["PRIYANKA"]
    assert tokens("") == []
    assert compare_names(None, "X").kind == "unknown"


def test_spelling_details_point_at_token():
    c = compare_names("Priyanka Kumari", "PRIANKA KUMARI")
    assert {"type": "spelling", "expected": "PRIYANKA", "found": "PRIANKA"} in c.details


# ------------------------------------------------------------------ rules ---

def sample_docs():
    return {k: dict(v) for k, v in extract.MOCK_FIXTURES.items()}


def codes(report):
    return [i["code"] for i in report["issues"]]


def test_sample_persona_flags_bank_spelling_and_old_income_certificate():
    r = rules.run_checks("pms_sc", sample_docs(), today=TODAY)
    assert "name_mismatch" in codes(r)
    nm = next(i for i in r["issues"] if i["code"] == "name_mismatch")
    assert nm["params"]["doc"] == "bank" and nm["params"]["kind"] == "spelling" and nm["severity"] == "high"
    assert "income_cert_expired" in codes(r)
    assert "dbt_seeding" in codes(r)
    assert r["verdict"] == "fix_first"
    assert r["issues"][-1]["code"] == "dbt_seeding"  # info sorted last


def test_clean_documents_are_ready():
    d = sample_docs()
    d["bank"]["holder_name"] = "PRIYANKA KUMARI"
    d["income"]["issue_date"] = "10/06/2026"
    r = rules.run_checks("pms_sc", d, today=TODAY)
    assert codes(r) == ["dbt_seeding"]
    assert r["verdict"] == "ready" and r["score"] == 100


def test_parent_account_detected():
    d = sample_docs()
    d["bank"]["holder_name"] = "RAMESH PRASAD"
    r = rules.run_checks("pms_sc", d, today=TODAY)
    issue = next(i for i in r["issues"] if i["code"] == "bank_not_own_account")
    assert issue["params"]["relation"] == "father" and issue["severity"] == "critical"
    assert r["verdict"] == "not_ready"


def test_income_over_limit_and_override():
    d = sample_docs()
    d["income"]["annual_income"] = "3,20,000"
    assert "income_over_limit" in codes(rules.run_checks("pms_sc", d, today=TODAY))
    assert "income_over_limit" not in codes(rules.run_checks("csss", d, today=TODAY))
    assert "income_over_limit" in codes(rules.run_checks("other", d, today=TODAY, income_limit_override=300000))


def test_dob_mismatch_and_year_only():
    d = sample_docs()
    d["marksheet"]["dob"] = "15/08/2005"
    assert "dob_mismatch" in codes(rules.run_checks("pms_sc", d, today=TODAY))
    d = sample_docs()
    d["aadhaar"]["dob"] = "2005"
    assert "dob_year_only" in codes(rules.run_checks("pms_sc", d, today=TODAY))


def test_ifsc_validation():
    d = sample_docs()
    d["bank"]["ifsc"] = "SBIN004587"
    assert "ifsc_invalid" in codes(rules.run_checks("pms_sc", d, today=TODAY))
    d["bank"]["ifsc"] = ""
    assert "ifsc_missing" in codes(rules.run_checks("pms_sc", d, today=TODAY))


def test_income_certificate_previous_fy():
    d = sample_docs()
    d["income"]["issue_date"] = "15/02/2026"  # < 12 months, but before 1 Apr 2026
    assert "income_cert_old_fy" in codes(rules.run_checks("pms_sc", d, today=TODAY))


def test_missing_documents_reported_per_scheme():
    d = {"aadhaar": sample_docs()["aadhaar"]}
    r = rules.run_checks("pms_sc", d, today=TODAY)
    missing = sorted(i["params"]["doc"] for i in r["issues"] if i["code"] == "doc_missing")
    assert missing == ["bank", "caste", "income", "marksheet"]


def test_father_name_mismatch():
    d = sample_docs()
    d["caste"]["father_name"] = "Suresh Paswan"
    assert "father_name_mismatch" in codes(rules.run_checks("pms_sc", d, today=TODAY))


def test_helpers():
    assert rules.fmt_inr(250000) == "2,50,000"
    assert rules.fmt_inr(12345678) == "1,23,45,678"
    assert rules.parse_amount("Rs. 1,80,000/-") == 180000
    assert rules.parse_amount("2.5 lakh") == 250000
    assert rules.financial_year_start(TODAY) == date(2026, 4, 1)
    assert rules.financial_year_start(date(2027, 2, 1)) == date(2026, 4, 1)


# ---------------------------------------------------------------- content ---

def test_every_issue_renders_in_both_languages_without_placeholders():
    d = sample_docs()
    d["bank"]["holder_name"] = "RAMESH PRASAD"
    d["marksheet"]["dob"] = "15/08/2005"
    d["marksheet"]["gender"] = "MALE"
    d["income"]["annual_income"] = 900000
    d["caste"]["father_name"] = "Suresh"
    d["caste"]["name"] = "Priyanka"
    reports = [
        rules.run_checks("pms_sc", d, today=TODAY),
        rules.run_checks("pms_sc", {"aadhaar": {"name": "A B", "dob": "2005"}, "bank": {"holder_name": "A B", "ifsc": "BAD"}}, today=TODAY),
        rules.run_checks("pms_sc", sample_docs(), today=TODAY),
    ]
    seen = set()
    for r in reports:
        for issue in r["issues"]:
            seen.add(issue["code"])
            for lang in ("en", "hi"):
                t = content.render_issue(issue, lang)
                blob = t["title"] + t["why"] + "".join(t["fix"])
                assert "{" not in blob and t["title"] and t["fix"], (issue["code"], lang, blob)
    assert len(seen) >= 9


# ---------------------------------------------------------------- extract ---

def test_mask_sensitive():
    assert extract.mask_sensitive("1234 5678 9012") == "XXXX XXXX 9012"
    assert extract.mask_sensitive({"x": "acct 123456789012345"}) == {"x": "acct XXXX2345"}
    assert extract.mask_sensitive("14/08/2005") == "14/08/2005"


def test_textract_heuristics():
    lines = ["Government of India", "Priyanka Kumari", "DOB: 14/08/2005", "FEMALE", "1234 5678 4821"]
    f = extract._clean("aadhaar", extract.parse_lines("aadhaar", lines))
    assert f["name"] == "Priyanka Kumari" and f["dob"] == "14/08/2005" and f["aadhaar_last4"] == "4821"
    lines = ["STATE BANK OF INDIA", "Account Holder Name: PRIANKA KUMARI", "IFSC: SBIN0004587"]
    f = extract._clean("bank", extract.parse_lines("bank", lines))
    assert f["holder_name"] == "PRIANKA KUMARI" and f["ifsc"] == "SBIN0004587"
    lines = ["INCOME CERTIFICATE", "Certified that Priyanka Kumari", "D/O Ramesh Prasad",
             "annual income Rs. 1,80,000", "Date of issue: 12/03/2025"]
    f = extract._clean("income", extract.parse_lines("income", lines))
    assert f["annual_income"] == 180000 and f["issue_date"] == "12/03/2025"


def test_prompt_lists_all_fields():
    for t in extract.DOC_TYPES:
        p = extract.build_prompt(t)
        for field in extract.FIELDS[t]:
            assert f'"{field}"' in p


# ---------------------------------------------------------------- handler ---

def call(method, path, body=None):
    ev = {"rawPath": path, "requestContext": {"http": {"method": method}}}
    if body is not None:
        ev["body"] = json.dumps(body)
    r = app.handler(ev)
    return r["statusCode"], json.loads(r["body"])


PNG_1PX = base64.b64encode(bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082")).decode()


def test_handler_routes():
    assert call("GET", "/api/health")[0] == 200
    s, b = call("GET", "/api/schemes")
    assert s == 200 and any(x["id"] == "pms_sc" for x in b["schemes"])
    s, b = call("POST", "/api/extract", {"doc_type": "bank", "image": "data:image/png;base64," + PNG_1PX})
    assert s == 200 and b["fields"]["holder_name"] == "PRIANKA KUMARI"
    s, b = call("POST", "/api/check", {"scheme": "pms_sc", "docs": sample_docs()})
    assert s == 200 and b["issues"][0]["text"]["hi"]["title"]
    s, b = call("POST", "/api/translate", {"texts": ["hello"], "target": "mr"})
    assert s == 200 and b["texts"] == ["[mr] hello"]
    assert call("GET", "/api/stats")[0] == 200


def test_handler_validation():
    assert call("POST", "/api/extract", {"doc_type": "passport", "image": PNG_1PX})[0] == 400
    assert call("POST", "/api/extract", {"doc_type": "bank", "image": base64.b64encode(b"hello").decode()})[0] == 400
    assert call("POST", "/api/check", {"docs": {}})[0] == 400
    assert call("POST", "/api/translate", {"texts": ["x"], "target": "fr"})[0] == 400
    assert call("GET", "/api/nope")[0] == 404
    r = app.handler({"rawPath": "/api/check", "requestContext": {"http": {"method": "POST"}}, "body": "{bad"})
    assert r["statusCode"] == 400


def test_passed_checks_reported():
    r = rules.run_checks("pms_sc", sample_docs(), today=TODAY)
    p = {(x["code"], x.get("doc")) for x in r["passed"]}
    assert ("name_ok", "marksheet") in p and ("dob_ok", None) in p and ("ifsc_ok", None) in p
    assert ("income_ok", None) in p and ("name_ok", "bank") not in p
