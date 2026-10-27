"""Apply D15 decisions to existing drafts (explicit per-line edits)."""
import json, sys
sys.path.insert(0, '.')
from tools import textcheck

EDITS = {
    'srt:A038_014_1:39': [('차였구먼, 젊은이.', '차였구먼, 총각.')],
    'srt:A051_010_1:59': [('알겠습니다!!', '아이, 맴!!')],
    'srt:A041_010_1:41': [('……알겠습니다.@n⊥@n분부대로 하겠습니다.', '……아이, 맴!@n⊥@n알겠습니다!')],
    'srt:A024_022_1:107': [('머스탱 일당에게', '머스탱 팀에게')],
}
# flags settled by D15; hidden-speaker notes stay; フォトセット stays open (context check)
KEEP = {'srt:A036_020_1:111', 'srt:A041_010_2:18', 'srt:A039_011_1:114', 'srt:A039_011_1:129',
        'srt:A039_011_1:131', 'srt:A039_011_1:139', 'srt:A039_011_1:141', 'srt:A039_011_1:286',
        'srt:A044_002_1:48', 'srt:A047_048_2:23', 'srt:A047_048_2:26', 'srt:A049_002_1_t:35',
        'srt:A053_005_1:275', 'srt:A053_005_1:279', 'srt:A054_003_1:43', 'srt:A051_010_2:137',
        'srt:A048_106_2:54'}
import glob as _g
FLAGS = {}
for _p in _g.glob('text/ko/srt/A0[3-5]*.json'):
    for _e in json.load(open(_p))['entries']:
        if _e.get('flag') and _e['id'] >= 'srt:A035' and _e['id'] not in KEEP:
            FLAGS[_e['id']] = ''
FLAGS['srt:A055_011_1:150'] = 'D15-14 어둠의 사자 확정. 메뉴명 SPECIAL·クリアミッション은 메뉴 번역 확정 시 맞출 것'
FLAGS['srt:A048_106_2:54'] = 'D15-15: フォトセット 포토세트 잠정, 문맥 확인 대기'
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
