"""Apply D8 decisions to existing drafts (explicit per-line edits)."""
import json, sys
sys.path.insert(0, '.')
from tools import textcheck

EDITS = {
    'srt:M008_3:89': [('강철의 꼬맹이 씨.', '강철의 꼬맹이.')],
    'srt:M015_3:72': [('형들,', '아저씨들,')],
    'srt:M015_3:152': [('하지만 형은', '하지만 아저씨는')],
    'srt:M011_1:120': [('벼락 경기의 골짜기', '반짝 호황의 골짜기')],
    'srt:M011_1:173': [('기교 업・소', '손재주 업・소')],
}
# flags settled by D6-D8: '' clears, other text keeps only the still-open part
FLAGS = {
    'srt:M001_1:71': '', 'srt:M002_1:61': '', 'srt:M002_1:122': '', 'srt:M002_1_t:5': '',
    'srt:M002_1:207': 'ショウ・タッカー → ‘쇼우 터커’(용어집 제안, 정발 확인 필요)',
    'srt:M002_1b:173': '', 'srt:M002_1b:271': '', 'srt:M003_1:49': '', 'srt:M003_1:193': '',
    'srt:M002_1b:221': '스킬명(타격 강화, 내구 업・소, HP 업・소)은 메뉴 번역 확정 시 맞출 것',
    'srt:M003_1b:176': '', 'srt:M003_3:54': '', 'srt:M003_5:105': '', 'srt:M004_1:194': '',
    'srt:M003_5:23': '血の紋 → ‘피의 문장’(용어집 제안)',
    'srt:M005_1:31': '', 'srt:M005_2:9': '', 'srt:M004_1:294': '', 'srt:M006_1:205': '',
    'srt:M006_1_t:9': '', 'srt:M008_3:86': '', 'srt:M008_3:89': '', 'srt:M009_1:298': '',
    'srt:M010_3:302': '', 'srt:M011_1:120': '', 'srt:M011_1:142': '', 'srt:M013_2_e:21': '',
    'srt:M011_1:173': '器用さ → 손재주(D8). 능력치 기능·메뉴 표기 확인 필요',
    'srt:M014_1:132': 'ヨック島 → 요크섬(용어집 없음)', 'srt:M015_2:10': '', 'srt:M015_3:72': '',
}
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
