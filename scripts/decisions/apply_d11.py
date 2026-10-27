"""Apply D11 decisions to existing drafts (explicit per-line edits)."""
import json, sys
sys.path.insert(0, '.')
from tools import textcheck

EDITS = {
    'srt:M040_1:129': [('어머, 언제든 괜찮은데.', '어머, 언제든 괜찮은데요.')],
    'srt:M034_4:36': [('잠깐만.', '잠깐만요.')],
    'srt:M040_1:141': [('윈리가 표적이', '윈리 양이 표적이')],
    'srt:M040_1:192': [('무척 좋아하잖아요,@n윈리를.', '무척 좋아하잖아요,@n윈리 양을.')],
    'srt:M040_2:61': [('“그대 한 사람의 목숨과', '“네놈 한 사람의 목숨과')],
    'srt:M042_2:47': [('할아버님', '할아버지')],
    'srt:M042_2:118': [('할아버님', '할아버지')],
    'srt:M043_1:251': [('아버지께', '아빠께')],
    'srt:M044_1_t:11': [('험준한 땅,', '천험의 땅,')],
    'srt:M044_2:173': [('험준한 땅,', '천험의 땅,')],
    'srt:M044_2:151': [('‘일일일선’', '‘하루 한 가지 선행’')],
    'srt:M044_2:167': [('‘일일일선’', '‘하루 한 가지 선행’')],
    'srt:M039_1:185': [('주인 있는 개는 될지언정', '길들여진 개는 될지언정')],
}
# flags settled by D11
FLAGS = {'srt:M039_1:121': '', 'srt:M039_1:185': '', 'srt:M039_1:304': '', 'srt:M040_1:141': '', 'srt:M040_2:31': '', 'srt:M041_2:63': '', 'srt:M041_2:166': '', 'srt:M042_2:47': '', 'srt:M042_2:118': '', 'srt:M042_4:80': '', 'srt:M042_4:86': '', 'srt:M043_1:99': '', 'srt:M044_1:92': '', 'srt:M040_2:61': '', 'srt:M040_2:63': '', 'srt:M043_2:42': '', 'srt:M044_2:173': ''}
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
