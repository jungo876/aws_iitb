"""Indian-name-aware comparison.

Government portals (NSP / PFMS / state DBT portals) compare names as strings, so
"PRIANKA KUMARI" in a bank record and "PRIYANKA KUMARI" on Aadhaar can fail a
payment even though a human sees the same person. This module classifies *how*
two names differ so we can tell the student exactly what to fix.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# Prefixes that are not part of the legal name.
HONORIFICS = {
    "MR", "MRS", "MS", "MISS", "SHRI", "SHREE", "SRI", "SH", "SMT", "SHRIMATI",
    "KU", "KUM", "SUSHRI", "SUSRI", "DR", "MASTER", "KUMARI_PREFIX",
}
# Relationship markers sometimes captured along with a name: "S/O", "D/O", ...
RELATION_MARKERS = {"SO", "DO", "WO", "CO"}

# Common abbreviations -> canonical full token(s).
ABBREVIATIONS = {
    "MD": {"MOHAMMAD"},
    "MOHD": {"MOHAMMAD"},
    "MOHAMMED": {"MOHAMMAD"},
    "MUHAMMAD": {"MOHAMMAD"},
    "MOHAMED": {"MOHAMMAD"},
    "MOHAMAD": {"MOHAMMAD"},
    "MOHAMMAD": {"MOHAMMAD"},
    "KR": {"KUMAR", "KUMARI"},
    "KMR": {"KUMAR"},
    "KMRI": {"KUMARI"},
    "PD": {"PRASAD"},
    "PRA": {"PRASAD"},
    "CH": {"CHAND", "CHANDRA", "CHOUDHARY", "CHAUDHARY"},
    "CHD": {"CHAND"},
    "BHAI": {"BHAI"},
}

SEVERITY_ORDER = ["match", "format", "order", "initials", "abbreviation", "missing_part", "spelling", "different"]


@dataclass
class NameComparison:
    kind: str                      # one of SEVERITY_ORDER, or "unknown"
    a: str                         # reference name as given
    b: str                         # compared name as given
    details: list[dict] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.kind in ("match", "format")

    def to_dict(self) -> dict:
        return {"kind": self.kind, "a": self.a, "b": self.b, "details": self.details}


def tokens(name: str | None) -> list[str]:
    """Normalise a name into upper-case Latin tokens with honorifics removed."""
    if not name:
        return []
    s = unicodedata.normalize("NFKD", str(name))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).upper()
    # Cut off relation clauses: "RAVI S/O RAMESH" -> "RAVI"
    s = re.split(r"\b[SDWC]\s*/\s*O\b", s)[0]
    s = re.sub(r"[^A-Z\s]", " ", s)
    toks = s.split()
    while toks and (toks[0] in HONORIFICS or toks[0] in RELATION_MARKERS):
        toks = toks[1:]
    # "KUMARI PRIYANKA" (prefix form) vs "PRIYANKA KUMARI" (suffix) - treat a
    # leading KUMARI followed by >=1 token as an honorific.
    if len(toks) > 1 and toks[0] == "KUMARI":
        toks = toks[1:]
    return toks


def phonetic(tok: str) -> str:
    """A coarse phonetic key tuned for romanised Indian names."""
    t = tok.lower()
    for a, b in (
        ("ph", "f"), ("bh", "b"), ("dh", "d"), ("th", "t"), ("kh", "k"),
        ("gh", "g"), ("jh", "j"), ("sh", "s"), ("ch", "c"), ("w", "v"),
        ("z", "j"), ("q", "k"), ("ck", "k"), ("x", "ks"),
    ):
        t = t.replace(a, b)
    t = t.replace("iy", "i").replace("ey", "e").replace("ay", "ai")
    t = t.replace("ee", "i").replace("oo", "u")  # suneeta ~ sunita
    t = re.sub(r"(.)\1+", r"\1", t)            # collapse doubles: aa->a
    t = re.sub(r"(?<=.)y(?=[aeiou])", "", t)  # priyanka ~ prianka
    t = t.replace("ou", "u").replace("au", "o")
    if len(t) > 3 and t.endswith("a"):        # rama ~ ram, krishna ~ krishn
        t = t[:-1]
    if len(t) > 3 and t.endswith("h"):
        t = t[:-1]
    return t


def edit_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _token_relation(ref: str, tok: str) -> str | None:
    """How does `tok` relate to reference token `ref`? None = unrelated."""
    if ref == tok:
        return "exact"
    full_tok = ABBREVIATIONS.get(tok, {tok})
    full_ref = ABBREVIATIONS.get(ref, {ref})
    if full_tok & full_ref:
        return "abbreviation"
    if len(tok) == 1 and ref.startswith(tok):
        return "initials"
    if len(ref) == 1 and tok.startswith(ref):
        return "initials"
    if phonetic(ref) == phonetic(tok):
        return "spelling"
    longest = max(len(ref), len(tok))
    if min(len(ref), len(tok)) >= 3 and edit_distance(ref, tok) <= max(1, longest // 4):
        return "spelling"
    return None


_REL_RANK = {"exact": 0, "abbreviation": 2, "initials": 1, "spelling": 3}


def compare_names(reference: str | None, other: str | None) -> NameComparison:
    """Compare `other` against `reference` (usually the Aadhaar name)."""
    ref_t, oth_t = tokens(reference), tokens(other)
    result = NameComparison(kind="unknown", a=reference or "", b=other or "")
    if not ref_t or not oth_t:
        return result

    if ref_t == oth_t:
        raw_same = re.sub(r"\s+", " ", (reference or "").strip().upper()) == re.sub(
            r"\s+", " ", (other or "").strip().upper())
        result.kind = "match" if raw_same else "format"
        return result

    # Greedy alignment: best relation for each token of `other`.
    unmatched_ref = list(range(len(ref_t)))
    pairs: list[tuple[int, int, str]] = []
    unmatched_oth: list[int] = []
    for j, tok in enumerate(oth_t):
        best = None
        for i in unmatched_ref:
            rel = _token_relation(ref_t[i], tok)
            if rel is None:
                continue
            if best is None or _REL_RANK[rel] < _REL_RANK[best[1]]:
                best = (i, rel)
        if best is None:
            unmatched_oth.append(j)
        else:
            unmatched_ref.remove(best[0])
            pairs.append((best[0], j, best[1]))

    kinds = set()
    for i, j, rel in pairs:
        if rel != "exact":
            kinds.add(rel)
            result.details.append({"type": rel, "expected": ref_t[i], "found": oth_t[j]})
    for i in unmatched_ref:
        result.details.append({"type": "missing", "expected": ref_t[i], "found": None})
    for j in unmatched_oth:
        result.details.append({"type": "extra", "expected": None, "found": oth_t[j]})

    if not pairs or (unmatched_ref and unmatched_oth):
        result.kind = "different"
        return result
    if unmatched_ref or unmatched_oth:
        kinds.add("missing_part")
    ref_order = [i for i, _, _ in sorted(pairs, key=lambda p: p[1])]
    if ref_order != sorted(ref_order):
        kinds.add("order")
        result.details.append({"type": "order", "expected": " ".join(ref_t), "found": " ".join(oth_t)})
    result.kind = max(kinds, key=SEVERITY_ORDER.index) if kinds else "format"
    return result
