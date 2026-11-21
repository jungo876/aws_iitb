"""Deterministic cross-document checks.

Input: the fields extracted from each document (after the student has reviewed
and corrected them). Output: a list of issues with severity, plus a readiness
score. Pure Python, no AWS calls, so it is fully unit-tested.
"""
from __future__ import annotations

import re
from datetime import date, datetime

from names import compare_names, tokens

SCHEMES = {
    "pms_sc": {
        "name": "Post-Matric Scholarship for SC Students",
        "name_hi": "अनुसूचित जाति के छात्रों के लिए पोस्ट-मैट्रिक स्कॉलरशिप",
        "income_limit": 250000,
        "required": ["aadhaar", "bank", "marksheet", "income", "caste"],
    },
    "pms_obc": {
        "name": "PM YASASVI Post-Matric Scholarship (OBC / EBC / DNT)",
        "name_hi": "पीएम यशस्वी पोस्ट-मैट्रिक स्कॉलरशिप (OBC / EBC / DNT)",
        "income_limit": 250000,
        "required": ["aadhaar", "bank", "marksheet", "income", "caste"],
    },
    "csss": {
        "name": "Central Sector Scheme of Scholarships (College & University)",
        "name_hi": "सेंट्रल सेक्टर स्कॉलरशिप योजना (कॉलेज व विश्वविद्यालय)",
        "income_limit": 450000,
        "required": ["aadhaar", "bank", "marksheet", "income"],
    },
    "topclass_sc": {
        "name": "Top Class Education Scholarship for SC Students",
        "name_hi": "अनुसूचित जाति के छात्रों के लिए टॉप क्लास शिक्षा स्कॉलरशिप",
        "income_limit": 450000,
        "required": ["aadhaar", "bank", "marksheet", "income", "caste"],
    },
    "other": {
        "name": "Other / State scholarship or DBT scheme",
        "name_hi": "अन्य / राज्य स्कॉलरशिप या DBT योजना",
        "income_limit": None,
        "required": ["aadhaar", "bank"],
    },
}

SEVERITY_PENALTY = {"critical": 35, "high": 20, "medium": 8, "info": 0}
SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "info": 3}

IFSC_RE = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")

# Severity for a name difference, by document and kind of difference.
NAME_SEVERITY = {
    "bank": {"different": "critical", "spelling": "high", "missing_part": "high",
             "abbreviation": "high", "initials": "high", "order": "high"},
    "marksheet": {"different": "critical", "spelling": "high", "missing_part": "high",
                  "abbreviation": "medium", "initials": "medium", "order": "medium"},
    "income": {"different": "high", "spelling": "medium", "missing_part": "medium",
               "abbreviation": "medium", "initials": "medium", "order": "medium"},
    "caste": {"different": "high", "spelling": "medium", "missing_part": "medium",
              "abbreviation": "medium", "initials": "medium", "order": "medium"},
}

NAME_FIELD = {"bank": "holder_name", "marksheet": "name", "income": "name", "caste": "name"}


# ---------------------------------------------------------------- parsing ---

def parse_date(value) -> date | None:
    if not value:
        return None
    s = str(value).strip()
    s = re.sub(r"\s+", "", s)
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def parse_year_only(value) -> int | None:
    if not value:
        return None
    s = str(value).strip()
    if re.fullmatch(r"(19|20)\d{2}", s):
        return int(s)
    return None


def parse_amount(value) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value).lower().replace(",", "").replace("₹", "").replace("rs.", "").replace("rs", "").strip()
    m = re.search(r"(\d+(?:\.\d+)?)\s*(lakh|lac|lakhs|l)?", s)
    if not m:
        return None
    num = float(m.group(1))
    if m.group(2):
        num *= 100000
    return int(num)


def norm_gender(value) -> str | None:
    if not value:
        return None
    s = str(value).strip().lower()
    if s in ("m", "male", "पुरुष", "boy"):
        return "male"
    if s in ("f", "female", "महिला", "स्त्री", "girl"):
        return "female"
    if s in ("t", "transgender", "other", "ट्रांसजेंडर"):
        return "transgender"
    return None


def fmt_inr(n: int) -> str:
    """Indian digit grouping: 250000 -> 2,50,000."""
    s = str(int(n))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts) + "," + tail


def fmt_date(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def financial_year_start(today: date) -> date:
    return date(today.year if today.month >= 4 else today.year - 1, 4, 1)


def months_between(a: date, b: date) -> int:
    return (b.year - a.year) * 12 + (b.month - a.month) - (1 if b.day < a.day else 0)


# ----------------------------------------------------------------- checks ---

def _issue(code, severity, docs, **params):
    return {"code": code, "severity": severity, "docs": docs, "params": params}


def run_checks(scheme_id: str, docs: dict, today: date | None = None,
               income_limit_override: int | None = None) -> dict:
    today = today or date.today()
    scheme = SCHEMES.get(scheme_id, SCHEMES["other"])
    docs = {k: (v or {}) for k, v in (docs or {}).items() if v}
    issues: list[dict] = []
    passed: list[dict] = []

    aadhaar = docs.get("aadhaar", {})
    marksheet = docs.get("marksheet", {})
    bank = docs.get("bank", {})
    income = docs.get("income", {})
    caste = docs.get("caste", {})

    ref_name = aadhaar.get("name") or marksheet.get("name")
    ref_doc = "aadhaar" if aadhaar.get("name") else "marksheet"
    father = marksheet.get("father_name") or income.get("father_name") or caste.get("father_name")
    mother = marksheet.get("mother_name")

    # 1. Names across documents ------------------------------------------
    for doc_key in ("bank", "marksheet", "income", "caste"):
        if doc_key == ref_doc or doc_key not in docs:
            continue
        other = docs[doc_key].get(NAME_FIELD[doc_key])
        if not other or not ref_name:
            continue
        cmp = compare_names(ref_name, other)
        if cmp.ok:
            passed.append({"code": "name_ok", "doc": doc_key})
        if cmp.ok or cmp.kind == "unknown":
            continue
        if doc_key == "bank" and cmp.kind == "different":
            relation = None
            if father and compare_names(father, other).kind in ("match", "format", "spelling", "initials", "abbreviation"):
                relation = "father"
            elif mother and compare_names(mother, other).kind in ("match", "format", "spelling", "initials", "abbreviation"):
                relation = "mother"
            # Same surname but different given name -> probably a relative.
            elif tokens(ref_name)[-1:] == tokens(other)[-1:]:
                relation = "other"
            if relation:
                issues.append(_issue("bank_not_own_account", "critical", ["bank"],
                                     ref=ref_name, found=other, relation=relation))
                continue
        issues.append(_issue("name_mismatch", NAME_SEVERITY[doc_key][cmp.kind], [ref_doc, doc_key],
                             doc=doc_key, kind=cmp.kind, ref=ref_name, found=other,
                             details=cmp.details))

    # 2. Date of birth -----------------------------------------------------
    a_dob = parse_date(aadhaar.get("dob"))
    m_dob = parse_date(marksheet.get("dob"))
    a_year = parse_year_only(aadhaar.get("dob")) or parse_year_only(aadhaar.get("year_of_birth"))
    if aadhaar and not a_dob and a_year:
        issues.append(_issue("dob_year_only", "medium", ["aadhaar"], year=a_year))
    if a_dob and m_dob and a_dob != m_dob:
        issues.append(_issue("dob_mismatch", "high", ["aadhaar", "marksheet"],
                             aadhaar_dob=fmt_date(a_dob), marksheet_dob=fmt_date(m_dob)))
    elif a_dob and m_dob:
        passed.append({"code": "dob_ok"})

    # 3. Gender ------------------------------------------------------------
    a_g = norm_gender(aadhaar.get("gender"))
    for doc_key in ("marksheet", "caste"):
        o_g = norm_gender(docs.get(doc_key, {}).get("gender"))
        if a_g and o_g and a_g != o_g:
            issues.append(_issue("gender_mismatch", "medium", ["aadhaar", doc_key], doc=doc_key,
                                 aadhaar_gender=aadhaar.get("gender"),
                                 other_gender=docs[doc_key].get("gender")))

    # 4. Father's name across certificates ---------------------------------
    m_father = marksheet.get("father_name")
    if m_father:
        for doc_key in ("income", "caste"):
            f = docs.get(doc_key, {}).get("father_name")
            if not f:
                continue
            cmp = compare_names(m_father, f)
            if cmp.ok or cmp.kind in ("unknown", "order"):
                if cmp.ok:
                    passed.append({"code": "father_ok", "doc": doc_key})
                continue
            sev = "high" if cmp.kind == "different" else "medium"
            issues.append(_issue("father_name_mismatch", sev, ["marksheet", doc_key],
                                 doc=doc_key, ref=m_father, found=f))

    # 5. Income certificate -----------------------------------------------
    if income:
        limit = income_limit_override or scheme["income_limit"]
        amount = parse_amount(income.get("annual_income"))
        if limit and amount is not None and amount > limit:
            issues.append(_issue("income_over_limit", "critical", ["income"],
                                 income=fmt_inr(amount), limit=fmt_inr(limit), scheme=scheme["name"]))
        elif limit and amount is not None:
            passed.append({"code": "income_ok", "income": fmt_inr(amount), "limit": fmt_inr(limit)})
        issued = parse_date(income.get("issue_date"))
        if not issued:
            issues.append(_issue("income_cert_no_date", "medium", ["income"]))
        else:
            months = months_between(issued, today)
            fy_start = financial_year_start(today)
            if months >= 12:
                issues.append(_issue("income_cert_expired", "high", ["income"],
                                     issue_date=fmt_date(issued), months=months))
            elif issued < fy_start:
                issues.append(_issue("income_cert_old_fy", "medium", ["income"],
                                     issue_date=fmt_date(issued), fy_start=fmt_date(fy_start)))
            else:
                passed.append({"code": "income_cert_fresh", "issue_date": fmt_date(issued)})

    # 6. Bank details --------------------------------------------------------
    if bank:
        ifsc = re.sub(r"\s+", "", str(bank.get("ifsc") or "")).upper()
        if not ifsc:
            issues.append(_issue("ifsc_missing", "medium", ["bank"]))
        elif not IFSC_RE.match(ifsc):
            issues.append(_issue("ifsc_invalid", "high", ["bank"], ifsc=ifsc))
        else:
            passed.append({"code": "ifsc_ok", "ifsc": ifsc})

    # 7. Documents the scheme needs that weren't provided ------------------
    for doc_key in scheme["required"]:
        if doc_key not in docs:
            issues.append(_issue("doc_missing", "medium", [doc_key], doc=doc_key))

    # 8. DBT seeding can't be seen on paper - always remind. ----------------
    issues.append(_issue("dbt_seeding", "info", ["aadhaar", "bank"]))

    issues.sort(key=lambda i: SEVERITY_RANK[i["severity"]])
    score = max(0, 100 - sum(SEVERITY_PENALTY[i["severity"]] for i in issues))
    blocking = sum(1 for i in issues if i["severity"] in ("critical", "high"))
    if any(i["severity"] == "critical" for i in issues):
        verdict = "not_ready"
    elif blocking:
        verdict = "fix_first"
    elif any(i["severity"] == "medium" for i in issues):
        verdict = "almost"
    else:
        verdict = "ready"

    return {
        "scheme": {"id": scheme_id if scheme_id in SCHEMES else "other", "name": scheme["name"],
                   "name_hi": scheme["name_hi"]},
        "score": score,
        "verdict": verdict,
        "blocking": blocking,
        "checked_docs": sorted(docs.keys()),
        "issues": issues,
        "passed": passed,
    }
