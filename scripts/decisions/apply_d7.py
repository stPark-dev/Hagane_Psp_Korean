"""Apply D7 term decisions to existing drafts (explicit per-line edits)."""
import json, sys
sys.path.insert(0, '.')
from tools import textcheck

EDITS = {
    'srt:M003_1b:176': [('선생님한테', '스승님한테')],
    'srt:M005_1:207': [('선생님의 가르침', '스승님의 가르침')],
    'srt:M002_1b:173': [('국가 연금술사@n“심사”', '국가 연금술사@n“자격 심사”')],
    'srt:M002_1b:319': [('심사를 통과해야만', '자격 심사를 통과해야만')],
    'srt:M003_1:26': [('“심사”가 가깝다고', '“자격 심사”가 가깝다고')],
    'srt:M003_1:75': [('“심사”에 늦지', '“자격 심사”에 늦지')],
    'srt:M005_2:22': [('윈리 님의', '윈리 양의')],
    'srt:M005_2:24': [('윈리 님의', '윈리 양의')],
    'srt:M004_1:194': [('대엘릭서', '대엘릭시르')],
    'srt:M002_1b:221': [('‘타격 강화’를 손에 넣었다!', '‘타격 강화’를 습득했다!')],
    'srt:M002_1b:230': [('‘내구 업・소’를 손에 넣었다!', '‘내구 업・소’를 습득했다!')],
    'srt:M002_1b:239': [('‘HP 업・소’를 손에 넣었다!', '‘HP 업・소’를 습득했다!')],
}
src = {f"srt:{d['file'][:-4]}:{d['idx']}": d['text'] for d in json.load(open('work/text/srt_src.json'))}
byfile = {}
for i in EDITS:
    byfile.setdefault(i.split(':')[1], []).append(i)
for name, ids in byfile.items():
    path = f'text/ko/srt/{name}.json'
    data = json.load(open(path))
    entries = []
    for e in data['entries']:
        if e['id'] in ids:
            ko = e['ko']
            for old, new in EDITS[e['id']]:
                assert ko.count(old) == 1, (e['id'], old)
                ko = ko.replace(old, new)
            assert not textcheck.check(src[e['id']], ko), e['id']
            e = {**e, 'ko': ko}
        entries.append(e)
    json.dump({**data, 'entries': entries}, open(path, 'w'), ensure_ascii=False, indent=1)
print('edited', sum(len(v) for v in EDITS.values()), 'lines in', len(byfile), 'files')
