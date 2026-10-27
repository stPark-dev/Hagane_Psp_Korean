"""Apply D14 decisions to existing drafts (explicit per-line edits)."""
import json, sys
sys.path.insert(0, '.')
from tools import textcheck

EDITS = {
    'srt:A015_014_4:57': [('엔비, 당신은 좀 너무', '엔비, 좀 너무')],
    'srt:A024_022_1:13': [('당신답지 않군요', '평소답지 않군요')],
    'srt:A024_022_1:24': [('라스.@n당신은 너무 오래', '라스.@n너무 오래')],
    'srt:A015_014_4:65': [('입 다무세요, 애송이.', '입 다무세요, 꼬맹이.')],
    'srt:A016_014_3:253': [('너……너 이 녀석이이이이!!', '네……네노오오오옴!!')],
    'srt:A031_014_1:151': [('어머, 로이 꼬마, 오랜만이네.', '어머, 우리 로이, 오랜만이네.')],
    'srt:A008_016_1:121': [('자리에서 쫓아내 주겠다!', '모가지를 날려 주겠다!')],
    'srt:A033_008_1:45': [('억양이 있네요.', '말투가 조금 독특하네요.')],
}
# flags settled by D14; speaker notes on disguised/hidden speakers stay for runtime review
KEEP = {'srt:A005_1:243', 'srt:A015_014_4:47', 'srt:A016_014_4:54', 'srt:A024_022_1:11',
        'srt:A025_014_1:94', 'srt:A031_014_2:21', 'srt:A033_008_1:43', 'srt:A016_014_4_e:9'}
import glob as _g
FLAGS = {}
for _p in _g.glob('text/ko/srt/A0[0-3]*.json'):
    for _e in json.load(open(_p))['entries']:
        if _e.get('flag') and _e['id'] not in KEEP:
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
