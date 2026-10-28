"""Bulk review checks run after a draft batch is merged.

Warnings, not build errors: a missing glossary term may be justified by
context (pronoun, omission), so each finding goes to a reviewer.

- term:    source has an approved glossary term, Korean lacks its rendering
- pending: source has an undecided term (state 결정필요) and the entry has no flag
- width:   a visible line is wider than the dialogue box (max_bytes in the game's encoding)
"""
import re
from dataclasses import dataclass

from tools import kofont, textcheck

CHECKED_STATES = ("승인", "잠정승인")
CHECKED_KINDS = ("name", "place", "term", "rank")
PENDING_STATE = "결정필요"


@dataclass(frozen=True)
class Finding:
    id: str
    kind: str
    message: str


def _squash(text):
    return re.sub(r"@n|\s", "", text)


def _checked(row):
    ko = row["ko"]
    return (row["state"] in CHECKED_STATES and row["kind"] in CHECKED_KINDS
            and ko and "/" not in ko and "~" not in ko)


KATAKANA = "ァ-ヺー"


def _pattern(ja):
    """A katakana-only term must not be part of a longer katakana word (ハン in ゴハン)."""
    p = re.escape(ja)
    if re.fullmatch(f"[{KATAKANA}・]+", ja):
        p = f"(?<![{KATAKANA}]){p}(?![{KATAKANA}])"
    return re.compile(p)


def _compiled(rows):
    """(row, pattern), longest ja first; compiled once per run since the re cache holds only 512."""
    return [(row, _pattern(row["ja"])) for row in sorted(rows, key=lambda r: -len(r["ja"])) if row["ja"]]


def _source_terms(src, compiled):
    """Rows whose ja occurs in src; a longer term hides the shorter ones inside it."""
    found = []
    for row, pat in compiled:
        if pat.search(src):
            found.append(row)
            src = pat.sub("\0", src)
    return found


def lint(entries, src, glossary, max_bytes=40):
    out = []
    compiled = _compiled(glossary)
    for e in entries:
        if e["state"] == "untranslated":
            continue
        ko = _squash(e["ko"])
        for row in _source_terms(src[e["id"]].replace("@n", ""), compiled):
            if row["state"] == PENDING_STATE and not e.get("flag"):
                out.append(Finding(e["id"], "pending", f"{row['ja']} is undecided; flag the entry"))
            elif _checked(row) and _squash(row["ko"]) not in ko:
                out.append(Finding(e["id"], "term", f"{row['ja']} → {row['ko']} not found"))
        for page in textcheck.pages(e["ko"]):
            for line in page:
                width = len(kofont.encode(textcheck.PROTECTED.sub("", line)))
                if width > max_bytes:
                    out.append(Finding(e["id"], "width", f"{width} bytes: {line}"))
    return out
