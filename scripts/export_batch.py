"""Export a translation batch: python3 work/drafts/export_batch.py BATCH NAME... -> work/batches/in/BATCH.json"""
import csv, json, sys
sys.path.insert(0, '.')
from tools import kotext

names = json.load(open('work/text/eboot_names.json'))  # plate table EBOOT 0x199890, not mes_j
G = list(csv.DictReader(open('text/glossary.tsv'), delimiter='\t'))
gko = {g['ja']: g['ko'] for g in G}
SPEAKER_OPS = {0, 1, 2, 3, 4, 5, 6, 7, 0x1D, 0x1E, 0x1F, 0x21}
KIND = {0x3B: '선택지(항목을 @n으로 구분, 항목 수 유지)', 0x3A: '시스템/선택 안내', 0x3C: '시스템 안내', 0x6E: '시스템 안내'}

batch, files = sys.argv[1], sys.argv[2:]
out = {'batch': batch, 'scripts': []}
alltext = ''
for name in files:
    raw = open(f'work/dat000/FLASH/{name}.srt', 'rb').read()
    ko = {e['id']: e for e in json.load(open(f'text/ko/srt/{name}.json'))['entries']}
    rows = []
    for v in kotext.source_view(name, raw):
        sp = None
        if v['op'] in SPEAKER_OPS and v['speaker'] is not None and v['speaker'] < len(names) and names[v['speaker']]:
            ja = names[v['speaker']].strip()
            sp = f"{ja} ({gko.get(ja, '?')})"
        e = ko[v['id']]
        row = {'id': v['id'], 'speaker': sp, 'kind': KIND.get(v['op'], '대사'), 'src': v['src']}
        if e['state'] != 'untranslated':
            row['fixed_ko'] = e['ko']  # already reviewed/drafted: context only, do not retranslate
        rows.append(row)
        alltext += v['src']
    out['scripts'].append({'name': name, 'entries': rows})
out['glossary'] = [{'ja': g['ja'], 'ko': g['ko'], 'state': g['state']} for g in G if g['ja'] in alltext]
json.dump(out, open(f'work/batches/in/{batch}.json', 'w'), ensure_ascii=False, indent=1)
n = sum(len(s['entries']) for s in out['scripts'])
todo = sum(1 for s in out['scripts'] for e in s['entries'] if 'fixed_ko' not in e)
print(batch, 'entries', n, 'to translate', todo, 'glossary rows', len(out['glossary']))
