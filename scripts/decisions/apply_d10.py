"""Apply D10 decisions to existing drafts (explicit per-line edits)."""
import json, sys
sys.path.insert(0, '.')
from tools import textcheck

EDITS = {
    'srt:M033_1_e:96': [('하인 님!', '하인님!')],
    'srt:M033_1_e:104': [('요키 님의 하인 님한테', '요키 씨의 하인님한테')],
    'srt:M033_2:41': [('(한 방 먹였군, 애송이)', '(한 방 먹였군, 풋내기)')],
    'srt:M038_4b_e:47': [('아버지 앞에 끌고 갈 때까지', '영감님 앞에 끌고 갈 때까지')],
    'srt:M038_5:10': [('아버지, 잡아 왔어!', '영감님, 잡아 왔어!')],
    'srt:M035_3_e:16': [('오빠! 놀자', '형아! 놀자')],
    'srt:M031_3:77': [('이슈발@n전투에 쓰였다고', '이슈발@n내란에 쓰였다고')],
    'srt:M038_3:134': [('순종하지 않는 민족인가.', '따르지 않는 백성인가.')],
    # 合成獣（キメラ）: 병기는 첫 등장(M001_1b:228)만
    'srt:M002_1:188': [('합성수(키메라)를', '합성수를')],
    'srt:M003_1:62': [('합성수(키메라)라네.', '합성수라네.')],
    'srt:M006_1b:64': [('터커의 합성수(키메라)@n사건도', '터커의 합성수@n사건도')],
    'srt:M015_3:44': [('합성수(키메라).', '합성수.')],
    'srt:M032_2:59': [('그 합성수(키메라)@n소녀를', '그 합성수@n소녀를')],
    'srt:M032_2_e:10': [('그 합성수(키메라)@n소녀를', '그 합성수@n소녀를')],
    'srt:M035_1b_e:29': [('합성수(키메라)한테', '합성수한테')],
    'srt:M035_1b_n1:1': [('합성수(키메라)한테', '합성수한테')],
}
# flags settled by D10
FLAGS = {'srt:M001_1b:228': '', 'srt:M033_1_e:96': '', 'srt:M033_1_e:104': '', 'srt:M033_1_e:108': '', 'srt:M035_1:30': '', 'srt:M035_3_e:16': '', 'srt:M037_1:51': '', 'srt:M038_3:90': '', 'srt:M038_3b:23': '', 'srt:M038_4:27': '', 'srt:M038_4b_e:47': '', 'srt:M038_5:10': ''}
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
