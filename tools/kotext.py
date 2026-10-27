"""Korean translation files for FSRT scripts.

text/ko/srt/<NAME>.json holds, per text command: stable id, hash of the
source text it was written against, Korean text, review state and a flag
for unresolved meaning. Source text itself stays out of the repository and
is regenerated from the disc (source_view).

An entry may carry speaker_fix {"from": n, "to": m} to correct a name plate
the original data gets wrong; the command's current speaker must equal
"from", and only that command's first argument changes.
"""
import hashlib

from tools import kofont, srt, textcheck

STATES = ("untranslated", "draft", "needs_review", "needs_human_review", "approved")
DEV_STATES = ("draft", "needs_review", "needs_human_review", "approved")


class TranslationError(ValueError):
    def __init__(self, problems):
        super().__init__("\n".join(problems))
        self.problems = problems


def src_hash(raw):
    return hashlib.sha1(raw).hexdigest()[:12]


def _speaker(script, t):
    c = script.commands[t.index]
    return c.int_arg(0) if c.argc > 1 else None


def source_view(name, raw):
    s = srt.parse(raw)
    return [{"id": f"srt:{name}:{t.index}", "op": t.op, "speaker": _speaker(s, t), "src": t.text}
            for t in s.texts()]


def template(name, raw):
    s = srt.parse(raw)
    return {"source": name,
            "entries": [{"id": f"srt:{name}:{t.index}", "src_sha1": src_hash(t.raw),
                         "ko": "", "state": "untranslated", "flag": ""} for t in s.texts()]}


def apply_srt(name, raw, kofile, policy):
    """Return the script with translations applied; raise TranslationError on
    any mismatch or check failure. policy: 'dev' or 'release'."""
    if policy not in ("dev", "release"):
        raise ValueError(policy)
    s = srt.parse(raw)
    texts = {f"srt:{name}:{t.index}": t for t in s.texts()}
    problems = []
    entries = {e["id"]: e for e in kofile["entries"]}
    if kofile.get("source") != name:
        problems.append(f"file is for {kofile.get('source')!r}, not {name!r}")
    for i in sorted(set(texts) - set(entries)):
        problems.append(f"{i}: missing from translation file")
    for i in sorted(set(entries) - set(texts)):
        problems.append(f"{i}: not a text command in the source")
    for i, t in texts.items():
        e = entries.get(i)
        if e is None:
            continue
        if e["state"] not in STATES:
            problems.append(f"{i}: unknown state {e['state']!r}")
            continue
        if e["src_sha1"] != src_hash(t.raw):
            problems.append(f"{i}: stale translation (source text changed)")
            continue
        fix = e.get("speaker_fix")
        if fix:
            if _speaker(s, t) != fix["from"]:
                problems.append(f"{i}: speaker_fix expects speaker {fix['from']}, found {_speaker(s, t)}")
                continue
            s.commands[t.index] = s.commands[t.index].with_int_arg(0, fix["to"])
        if policy == "release" and (e["state"] != "approved" or e.get("flag")):
            why = f"flag {e['flag']!r}" if e.get("flag") else f"state {e['state']}"
            problems.append(f"{i}: not release eligible ({why})")
            continue
        if e["state"] not in DEV_STATES:
            continue  # dev: keep the source text
        errs = textcheck.check(t.text, e["ko"])
        if errs:
            problems.extend(f"{i}: {err}" for err in errs)
            continue
        s.set_text(t.index, kofont.encode(e["ko"]))
    if problems:
        raise TranslationError(problems)
    return srt.build(s)


def merge_draft(name, raw, kofile, drafts):
    """Return a copy of kofile with agent drafts merged in.

    drafts: {id: {"ko": str, "flag": str}}. Only wording, flag and state are
    taken from the drafts; ids, hashes and entries already past 'draft' are
    never overwritten."""
    texts = {f"srt:{name}:{t.index}": t for t in srt.parse(raw).texts()}
    out = {**kofile, "entries": [dict(e) for e in kofile["entries"]]}
    entries = {e["id"]: e for e in out["entries"]}
    problems = []
    for i, d in drafts.items():
        e = entries.get(i)
        if e is None or i not in texts:
            problems.append(f"{i}: unknown id")
            continue
        if e["state"] not in ("untranslated", "draft"):
            problems.append(f"{i}: already {e['state']}, not overwritten")
            continue
        if e["src_sha1"] != src_hash(texts[i].raw):
            problems.append(f"{i}: stale translation file (source text changed)")
            continue
        errs = textcheck.check(texts[i].text, d["ko"])
        if errs:
            problems.extend(f"{i}: {err}" for err in errs)
            continue
        e.update(ko=d["ko"], flag=d.get("flag", ""), state="draft")
    if problems:
        raise TranslationError(problems)
    return out
