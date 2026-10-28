"""Mechanical checks for a translated text unit against its source.

Protected tokens (voice cues, page controls, colour/speed codes) must appear
in the same order with the same arguments; `@n` line breaks may move.
"""
import re

from tools import kofont

PROTECTED = re.compile(r"<~[^>]*>|@[cs]<[^>]*>|[⊥⊿]")


def protected_tokens(text):
    return PROTECTED.findall(text)


def pages(text):
    """Visible lines per page; a line holding only control tokens is not shown."""
    out = []
    for page in re.split("[⊥⊿]", text):
        lines = [l for l in page.split("@n") if PROTECTED.sub("", re.sub(r"@[a-z](?:<[^>]*>)?", "", l)).strip()]
        out.append(lines)
    return out


def check(src, ko, max_lines=3):
    errs = []
    if protected_tokens(src) != protected_tokens(ko):
        errs.append(f"protected token sequence differs: {protected_tokens(src)} != {protected_tokens(ko)}")
    try:
        kofont.encode(ko)
    except ValueError as e:
        errs.append(f"cannot encode: {e}")
    for i, lines in enumerate(pages(ko)):
        if len(lines) > max_lines:
            errs.append(f"page {i + 1} has {len(lines)} lines (max {max_lines})")
    return errs
