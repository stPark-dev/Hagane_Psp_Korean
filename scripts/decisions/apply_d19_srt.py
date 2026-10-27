"""Apply D19 decisions to dialogue drafts (explicit per-line edits)."""
import json, sys
sys.path.insert(0, '.')
from tools import textcheck

EDITS = {
    # 修復 -> 복구 (D19-2); the technique name 修復錬成 stays 수복연성
    'srt:F014_999_024_1:30': [('큰 수복 작업을', '큰 복구 작업을')],
    'srt:F014_999_024_2:80': [('수복에 집중해', '복구에 집중해')],
    'srt:M001_1b:262': [('건물 수복 같은', '건물 복구 같은')],
    'srt:F009_999_016_1:34': [('그걸 고쳐@n주실 수', '그걸 복구해@n주실 수')],  # matches the mission goal 항아리 복구!
    'srt:M001_3:186': [('건물 수복 등에', '건물 복구 등에'), ('“수복 연성”', '“수복연성”'), ('건물이 수복돼', '건물이 복구돼')],
    'srt:M001_3:187': [('“수복 연성”', '“수복연성”')],
    # technique names written solid (D19-5); ドラマチック錬成 is the system feature, 遠隔錬成 in A035 is the general idea
    'srt:M001_3:134': [('“석벽 연성”', '“석벽연성”')],
    'srt:M001_3:166': [('“철구 연성”', '“철구연성”')],
    # ステータス -> 상태 (D19-4)
    'srt:M001_1b:282': [('우리 스테이터스를', '우리 상태를')],
    'srt:M001_1b:345': [('“스테이터스”에서는', '“상태”에서는')],
    'srt:M001_1b:359': [('적의 스테이터스는', '적의 상태는')],
}
FLAGS = {}
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
