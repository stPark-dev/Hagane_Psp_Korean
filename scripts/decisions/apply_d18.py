"""Apply D18 decisions to existing drafts (explicit per-line edits)."""
import json, sys
sys.path.insert(0, '.')
from tools import textcheck

EDITS = {
    'srt:F011_006_008:53': [('후 영감이 란팡의', '후 할아버지가 란팡의')],
    'srt:E02_1_e:27': [('과연……당신 말대로', '과연……말씀하신 대로')],
    'srt:E02_1_e:38': [('당신은 제 안에서@n계속 살아갈 수', '제 안에서@n계속 살아갈 수')],
    # Al answers Zampano's request (:35) in 해요체 (D18-8); :75 is to Winry and stays 반말
    'srt:F014_999_025:36': [('응.@n사실 몰라.@n', '네.@n사실 몰라요.@n')],
    'srt:F014_999_025:41': [('응.@n⊥', '네.@n⊥'), ('현상을 말해.', '현상을 말해요.'), ('새카매지는 거야.', '새카매지는 거예요.')],
    'srt:F014_999_025:48': [('뭐, 나도 책에서밖에', '뭐, 저도 책에서밖에'), ('없지만. 몇 년에', '없지만요. 몇 년에'),
                            ('모양이야.', '모양이에요.'), ('가려지는 게 있어.', '가려지는 게 있어요.')],
    'srt:F014_999_025:51': [('사실 몰라.', '사실 몰라요.')],
    'srt:F014_999_025:53': [('잠파노 씨는 알아?', '잠파노 씨는 알아요?')],
    'srt:F014_999_025:76': [('‘좀먹을 식’ 자로 적던@n시기도 있었지.', '태양이 좀먹힌다는 뜻으로@n적던 시기도 있었지.')],
    'srt:F013_106_002:22': [('일심동체라 불리는', '한 덩어리라 불리는')],
    'srt:F013_106_002:37': [('일심동체의 군단으로서, 그 이름을@n떨치고 있는 거다.', '한 덩어리로 뭉친 군단으로서,@n그 이름을 떨치고 있는 거다.')],
    'srt:F011_999_021_2_e:53': [('그놈들도 한통속은', '그놈들도 한 덩어리는')],
    'srt:F013_106_002:108': [('‘신춘・냉수 수행’', '‘새해 찬물 수행’')],
    'srt:F012_999_022_1:386': [('‘북부와 동부의 합동 연습’', '‘북부와 동부의 합동훈련’')],
    'srt:A046_014_1:54': [('북부와 동부의 합동 연습이', '북부와 동부의 합동훈련이')],
    'srt:E04_1_e:70': [('고맙소!', '감사합니다!')],
    'srt:IF09_2:16': [('강철의 꼬마 군?', '강철의 꼬맹이 군?')],
    'srt:IF02_1_e:39': [('역시@n중앙군이야.', '역시@n중앙군 소속 군인이네.')],
    # found by termlint after the D18 glossary rows went in
    'srt:A048_020_1:49': [('브릭스 병사의@n결속력과 강함은 상당한 수준이라,@n쉽게 될 것 같지는……',
                           '브릭스 병사가@n한 덩어리로 뭉친 모습과 강함은@n상당한 수준이라, 쉽게 될 것 같지는……')],
    'srt:F001_014_001:103': [('주관하는 국가시험을 치러 합격했지.', '주관하는 국가 자격 심사를 치러@n합격했지.')],
}
# flags settled by D18; hidden speakers, voice reuse and undecided readings stay
KEEP = {'srt:F010_999_019_2_e:55', 'srt:F010_999_019_2_e:57', 'srt:F011_999_021_2_e:75',
        'srt:F011_001_008:138', 'srt:F011_999_021_1:109', 'srt:F011_999_021_1:138', 'srt:IF05_1:29',
        'srt:IF09_1:9', 'srt:E02_1_e:27', 'srt:E05_1:25', 'srt:E06_1:31', 'srt:E06_1:36'}
import glob as _g
FLAGS = {}
for _pat in ('F01[0-4]*', 'IF*', 'E0*'):
    for _p in _g.glob(f'text/ko/srt/{_pat}.json'):
        for _e in json.load(open(_p))['entries']:
            if _e.get('flag') and _e['id'] not in KEEP:
                FLAGS[_e['id']] = ''
FLAGS['srt:E06_1:47'] = 'D18-13 파괴하는 자 채택. 정발판 실물 문구 검증 대기'
FLAGS['srt:IF05_1:29'] = 'D18-11: ？？？ 이름표 유지(의도적 정체 은폐, 화자 이즈미). 실기 연출 확인'
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
