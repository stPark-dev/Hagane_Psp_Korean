"""Merge EBOOT UI batches into text/ko/eboot.json: python3 work/drafts/merge_eboot.py EB1 EB2 ...

Every merged line passes ebootstr.check; identical source strings must get
identical Korean across batches; prints termlint term findings."""
import collections, csv, json, sys
sys.path.insert(0, '.')
from tools import ebootstr, kotext, termlint

data = open('work/eboot/EBOOT.elf', 'rb').read()
src = {t.id: t for t in ebootstr.catalog(data)}
path = 'text/ko/eboot.json'
kofile = json.load(open(path))
entries = {e['id']: dict(e) for e in kofile['entries']}
problems = []
for b in sys.argv[1:]:
    for i, d in json.load(open(f'work/batches/out/{b}.json')).items():
        e = entries.get(i)
        if e is None or e['state'] not in ('untranslated', 'draft'):
            problems.append(f'{i}: unknown or already reviewed'); continue
        if e['src_sha1'] != kotext.src_hash(src[i].raw):
            problems.append(f'{i}: stale'); continue
        errs = ebootstr.check(src[i].text, d['ko'])
        if errs:
            problems.extend(f'{i}: {x}' for x in errs); continue
        e.update(ko=d['ko'], flag=d.get('flag', ''), state='draft')
same = collections.defaultdict(set)
for i, e in entries.items():
    if e['state'] != 'untranslated':
        same[src[i].text].add(e['ko'])
split = {s: k for s, k in same.items() if len(k) > 1}
if problems:
    sys.exit('\n'.join(problems))
kofile['entries'] = [entries[e['id']] for e in kofile['entries']]
json.dump(kofile, open(path, 'w'), ensure_ascii=False, indent=1)
G = list(csv.DictReader(open('text/glossary.tsv'), delimiter='\t'))
terms = [f for f in termlint.lint(list(entries.values()), {i: t.text for i, t in src.items()}, G) if f.kind == 'term']
done = sum(e['state'] != 'untranslated' for e in entries.values())
print('merged; drafted', done, '/', len(entries), 'flags', sum(bool(e['flag']) for e in entries.values()))
print('same source, different Korean:', len(split))
for s, k in list(split.items()):
    print('  ', s.replace('@n', '/')[:30], '->', ' | '.join(x.replace('@n', '/')[:20] for x in k))
print('term findings:', len(terms))
for f in terms:
    print('  ', f.id, f.message)
