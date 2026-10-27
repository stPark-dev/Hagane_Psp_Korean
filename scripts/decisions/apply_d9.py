"""Apply D9 decisions to existing drafts (explicit per-line edits)."""
import json, sys
sys.path.insert(0, '.')
from tools import textcheck

EDITS = {
    'srt:M015_3:150': [('난 욕심이 많거든!', '난 탐욕스럽거든!')],
    'srt:M017_2:71': [('강욕의 그리드 님', '탐욕의 그리드 님')],
    'srt:M017_2:85': [('강욕!', '탐욕!')],
    # 人造人間（ホムンクルス）: 병기는 첫 등장(M015_3:93)만, 이후 호문쿨루스 (조사 맞춤)
    'srt:M015_4:50': [('인조인간(호문쿨루스)이야!', '호문쿨루스야!')],
    'srt:M016_1:23': [('인조인간(호문쿨루스)이라지만', '호문쿨루스라지만')],
    'srt:M017_1_t:15': [('인조인간(호문쿨루스)이었다.', '호문쿨루스였다.')],
    'srt:M021_2:48': [('‘현자의 돌’이랑 인조인간@n(호문쿨루스)에 대해서.', '‘현자의 돌’이랑@n호문쿨루스에 대해서.')],
    'srt:M025_1_t:11': [('인조인간(호문쿨루스)들이었다.', '호문쿨루스들이었다.')],
    'srt:M025_2:149': [('……인조인간(호문쿨루스),', '……호문쿨루스,')],
    'srt:M026_1:6': [('인조인간(호문쿨루스)과의 싸움을', '호문쿨루스와의 싸움을')],
    'srt:M017_3:296': [('을 손에 넣었다!', '을 습득했다!')],
    'srt:M025_2:115': [('로스 양을', '로스 님을')],
    'srt:M027_2:89': [('이제 당신이 있을 곳', '이제 네가 있을 곳')],
    'srt:M027_2:102': [('당신이 뭘 알아!', '네가 뭘 알아!')],
}
# flags settled by D9
FLAGS = {'srt:M017_2:71': '', 'srt:M017_2:85': '', 'srt:M017_3:296': '', 'srt:M020_3:57': '', 'srt:M020_3:156': '', 'srt:M020_3:160': '', 'srt:M020_3:248': '', 'srt:M020_1:179': '', 'srt:M021_1:32': '', 'srt:M021_1:41': '', 'srt:M023_1b:154': '', 'srt:M025_2:115': '', 'srt:M025_2:182': '', 'srt:M027_1:130': '', 'srt:M027_2:89': '', 'srt:M027_2:102': '', 'srt:M027_3:12': ''}
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
