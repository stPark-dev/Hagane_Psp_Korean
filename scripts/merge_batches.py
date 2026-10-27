"""Merge dialogue draft batches into text/ko/srt: python3 scripts/merge_batches.py B44 B45 ...

Reads work/batches/out/<B>.json ({id: {"ko", "flag"}}) and merges with
kotext.merge_draft (checks ids, source hashes, protected tokens, encoding)."""
import json
import sys

sys.path.insert(0, ".")
from tools import kotext  # noqa: E402

total = flags = 0
for b in sys.argv[1:]:
    out = json.load(open(f"work/batches/out/{b}.json"))
    by = {}
    for i, d in out.items():
        by.setdefault(i.split(":")[1], {})[i] = d
    for name, drafts in by.items():
        p = f"text/ko/srt/{name}.json"
        raw = open(f"work/dat000/FLASH/{name}.srt", "rb").read()
        new = kotext.merge_draft(name, raw, json.load(open(p)), drafts)
        json.dump(new, open(p, "w"), ensure_ascii=False, indent=1)
    total += len(out)
    flags += sum(1 for d in out.values() if d.get("flag"))
print("merged", total, "flags", flags)
