"""Export EBOOT UI batches: python3 work/drafts/export_eboot.py -> work/batches/in/EB*.json

Strings are ordered by the pointer table that first references them (UI order),
grouped into tables (pointer gap > 0x40) and cut into batches of about SIZE
(at a table boundary when one comes within 60 entries)."""
import csv, json, sys
sys.path.insert(0, '.')
from tools import ebootstr

SIZE = 360
data = open('work/eboot/EBOOT.elf', 'rb').read()
ko = {e['id']: e for e in json.load(open('text/ko/eboot.json'))['entries']}
G = list(csv.DictReader(open('text/glossary.tsv'), delimiter='\t'))
cat = sorted(ebootstr.catalog(data), key=lambda t: t.refs[0])
first = {}
rows, table, last = [], None, None
for t in cat:
    if last is None or t.refs[0] - last > 0x40:
        table = t.refs[0]
    last = t.refs[0]
    row = {'id': t.id, 'table': f'{table:#x}', 'src': t.text,
           'width': ebootstr.line_widths(t.text), 'pointers': len(t.refs)}
    if t.text in first:
        row['same_as'] = first[t.text]
    first.setdefault(t.text, t.id)
    if ko[t.id]['state'] != 'untranslated':
        row['fixed_ko'] = ko[t.id]['ko']
    rows.append(row)
batches, cur = [], []
for r in rows:
    if len(cur) >= SIZE and (r['table'] != cur[-1]['table'] or len(cur) >= SIZE + 60):
        batches.append(cur); cur = []
    cur.append(r)
batches.append(cur)
for n, b in enumerate(batches, 1):
    text = ''.join(r['src'] for r in b)
    out = {'batch': f'EB{n}', 'entries': b,
           'glossary': [{'ja': g['ja'], 'ko': g['ko'], 'state': g['state']} for g in G if g['ja'] and g['ja'] in text]}
    json.dump(out, open(f'work/batches/in/EB{n}.json', 'w'), ensure_ascii=False, indent=1)
    print(out['batch'], len(b), b[0]['table'], '..', b[-1]['table'], 'glossary', len(out['glossary']))
