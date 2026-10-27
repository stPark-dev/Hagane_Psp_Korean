"""Apply D17 decisions to existing drafts (explicit per-line edits)."""
import json, sys
sys.path.insert(0, '.')
from tools import textcheck

EDITS = {
    'srt:F003_048_001:164': [('금발 총각도', '금발 형씨도')],
    'srt:F003_048_001:78': [('총각이 달고 있는', '형씨가 달고 있는')],
    'srt:F003_048_001:79': [('그 총각한테', '그 형씨한테')],
    'srt:F003_999_003_1:29': [('총각 오토메일,', '형씨 오토메일,')],
    'srt:F003_999_003_2_e:40': [('총각한텐 어지간히', '형씨한텐 어지간히')],
    'srt:F008_002_001:125': [('너희 부모와 아이는 말이다.', '너희 부자지간은 말이다.')],
    'srt:F006_006_003:95': [('그 누나……', '그 아가씨……')],
    'srt:F004_003_002_1:11': [('남편이 손을 뗄 수가', '그이가 손을 뗄 수가')],
    'srt:F004_003_002_1:64': [('남편이 말하던,', '그이가 말하던,')],
    'srt:F004_999_007_1:30': [('그런데 남편은 지금', '그런데 그이는 지금')],
    'srt:F004_999_007_2_e:32': [('남편도 돌아왔으니', '그이도 돌아왔으니')],
    'srt:F005_048_004_2:135': [('‘태백성’이라고', '‘개밥바라기별’이라고')],
    'srt:F009_048_008:261': [('청춘 소년이라니까', '청춘 녀석이라니까')],
}
# とほほ lines keep their wording: the source also calls 兄さん (D17-13).
import glob as _g
KEEP = {'srt:F004_003_002_2_e:82', 'srt:F004_003_002_2_e:84', 'srt:F008_999_015_2_e:39',
        'srt:F006_999_011_2_e:50', 'srt:F003_999_006_1:56', 'srt:F007_014_002:69',
        'srt:F008_999_014_1:19',
        # not covered by D17: reading of ヤツ, 何回焼けば, Al's mixed register
        'srt:F009_999_018_2:17', 'srt:F006_999_013:340', 'srt:F007_017_004:23'}
FLAGS = {}
for _p in _g.glob('text/ko/srt/F00[3-9]*.json'):
    for _e in json.load(open(_p))['entries']:
        if _e.get('flag') and _e['id'] >= 'srt:F003_999_003_1' and _e['id'] not in KEEP:
            FLAGS[_e['id']] = ''
src = {f"srt:{d['file'][:-4]}:{d['idx']}": d['text'] for d in json.load(open('work/text/srt_src.json'))}
byfile = {}
for i in set(EDITS) | set(FLAGS):
    byfile.setdefault(i.split(':')[1], []).append(i)
for name, ids in byfile.items():
    path = f'text/ko/srt/{name}.json'
    data = json.load(open(path))
    entries = []
    for e in data['entries']:
        if e['id'] in FLAGS:
            e = {**e, 'flag': FLAGS[e['id']]}
        if e['id'] in EDITS:
            ko = e['ko']
            for old, new in EDITS[e['id']]:
                assert ko.count(old) == 1, (e['id'], old)
                ko = ko.replace(old, new)
            assert not textcheck.check(src[e['id']], ko), e['id']
            e = {**e, 'ko': ko}
        entries.append(e)
    json.dump({**data, 'entries': entries}, open(path, 'w'), ensure_ascii=False, indent=1)
print('edited', sum(len(v) for v in EDITS.values()), 'lines in', len(byfile), 'files')
