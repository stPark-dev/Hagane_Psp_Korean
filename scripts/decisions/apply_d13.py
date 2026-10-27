"""Apply D13 decisions to existing drafts (explicit per-line edits)."""
import json, sys
sys.path.insert(0, '.')
from tools import textcheck

EDITS = {
    'srt:M052_1:29': [('네놈은 너무 크니까', '너는 너무 크니까')],
    'srt:M053_4:18': [('네놈은@n연금술로', '너는@n연금술로')],
    'srt:M053_3:91': [('싱 계집도', '싱 여자도')],
    'srt:M053_6:112': [('당신은 잊지 않을게요!', '요키 씨 일은 잊지 않을게요!')],
    'srt:M054_1:247': [('아버지!', '아빠!')],
    'srt:M054_2:30': [('아버지가 있어서', '아빠가 있어서')],
    'srt:M054_2:32': [('아버지랑 똑같이', '아빠랑 똑같이'), ('아버지랑 무관하다고는', '아빠랑 무관하다고는')],
    'srt:M054_2:95': [('아버지의……피로', '아빠의……피로')],
    'srt:M054_2:103': [('아버지의……이름을', '아빠의……이름을')],
    'srt:M054_3:30': [('노예가 아버지고', '노예가 아빠고')],
    'srt:M054_3:52': [('아버지는 ‘현자의 돌’', '아빠는 ‘현자의 돌’')],
    'srt:M054_3:152': [('아버지……', '아빠……')],
    'srt:M054_3:187': [('아버지, 스승님을', '아빠, 스승님을')],
    'srt:M056_2:88': [('내가 친히', '이 에드워드 님께서')],
    'srt:M054_1_t:5': [('아스벡에서', '아스베크에서')],
    'srt:M055_1_t:19': [('노스시티로', '노스 시티로')],
    'srt:M056_1_t:6': [('노스시티의', '노스 시티의')],
    'srt:M053_6:215': [('역전의 연성진', '반전의 연성진')],
    'srt:M053_6:223': [('역전의@n연성진의', '반전의@n연성진의')],
    'srt:M054_3:97': [('역전의 연성진', '반전의 연성진')],
    'srt:M054_3:45': [('“있을 수 없는 일은 있을 수 없다”', '“불가능이란 있을 수 없다”')],
    'srt:M054_2:160': [('‘문을 열게 해 줬다’”고.', '‘문을 열었지’”라고.')],
}
# flags settled by D13; M054_2:160 and M054_3:45 stay open for licensed-manga/context checks
FLAGS = {i: '' for i in (
    'srt:M052_1:29', 'srt:M052_1:124', 'srt:M053_1:31', 'srt:M053_1_t:4', 'srt:M053_1_t:8',
    'srt:M053_2:38', 'srt:M053_3:91', 'srt:M053_4:18', 'srt:M053_6:112', 'srt:M053_6:123',
    'srt:M053_6:177', 'srt:M053_6:215', 'srt:M053_6:223', 'srt:M054_1:50', 'srt:M054_1:54',
    'srt:M054_1:144', 'srt:M054_1:162', 'srt:M054_1:227', 'srt:M054_1:247', 'srt:M054_1_t:5',
    'srt:M054_2:94', 'srt:M054_2:191', 'srt:M054_3:97', 'srt:M054_3:140', 'srt:M054_3:150',
    'srt:M054_3:163', 'srt:M055_1_t:19', 'srt:M056_1_t:6', 'srt:M056_2:72', 'srt:M056_2:74',
    'srt:M056_2:76', 'srt:M056_2:88', 'srt:M056_2:296')}
FLAGS['srt:M054_3:45'] = 'D13-17: 그리드 명대사 “불가능이란 있을 수 없다”. 정발판 실물 문구 확인 대상'
FLAGS['srt:M054_2:160'] = 'D13-21: ‘문을 열었지’ 잠정 채택. 전후 문맥 확인 후 확정'
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
