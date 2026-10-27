"""Run termlint over all translation files: python3 scripts/lint_all.py [NAME_PREFIX...]"""
import collections, csv, glob, json, sys
sys.path.insert(0, '.')
from tools import termlint

prefixes = tuple(sys.argv[1:]) or ('',)
src = {f"srt:{d['file'][:-4]}:{d['idx']}": d['text'] for d in json.load(open('work/text/srt_src.json'))}
G = list(csv.DictReader(open('text/glossary.tsv'), delimiter='\t'))
entries = [e for f in sorted(glob.glob('text/ko/srt/*.json')) if f.split('/')[-1].startswith(prefixes)
           for e in json.load(open(f))['entries']]
found = termlint.lint(entries, src, G)
for f in found:
    print(f.kind, f.id, f.message)
print(collections.Counter(f.kind for f in found))
