"""Apply D12 decisions to existing drafts (explicit per-line edits)."""
import json, sys
sys.path.insert(0, '.')
from tools import textcheck

EDITS = {
    'srt:M046_3:86': [('늙어 빠진 해충 같으니!!', '늙은 폐물 같으니!!')],
    'srt:M045_1:15': [('선발대로', '선견대로')],
    'srt:M046_1:137': [('선발대가', '선견대가')],
    'srt:M046_1:140': [('“선발대에', '“선견대에')],
    'srt:M046_2:90': [('선발대 수색도', '선견대 수색도')],
    'srt:M046_3:10': [('선발대 일은', '선견대 일은')],
    'srt:M045_1:368': [('예스, 맴!!', '알겠습니다!!')],
    'srt:M047_1:126': [('북쪽 지방용 오토메일로', '한랭지용 오토메일로')],
    'srt:M047_1:151': [('북쪽 지방용 오토메일로', '한랭지용 오토메일로')],
    'srt:M047_1:196': [('북쪽 지방용 오토메일은', '한랭지용 오토메일은')],
    'srt:M048_3:76': [('소녀여……', '아가씨……')],
    'srt:M048_3:104': [('소녀여, 너는', '아가씨, 너는')],
    'srt:M044_1:197': [('센트럴 놈들은', '센트럴 녀석들은')],
    'srt:M045_1:335': [('센트럴 놈들 같으니!', '센트럴 녀석들 같으니!')],
    'srt:M046_3:87': [('네년……!', '네놈……!')],
    'srt:M047_1:354': [('네놈, 그래서', '이 자식, 그래서')],
    'srt:M048_5:37': [('킴블리……네놈!', '킴블리……이 자식!')],
    'srt:M048_5:92': [('네놈……!', '이 자식……!')],
    'srt:M048_3:102': [('부정적인 감정에', '부정적 감정에'), ('긍정적인 감정을', '긍정적 감정을')],
}
# flags settled by D12 (speaker-identification flags stay)
FLAGS = {i: '' for i in (
    'srt:M045_1:167', 'srt:M045_1:174', 'srt:M045_1:182', 'srt:M045_1:368',
    'srt:M046_2:137', 'srt:M046_2:140', 'srt:M046_2:143', 'srt:M046_2:149',
    'srt:M046_3:86', 'srt:M046_3:87', 'srt:M046_3:157', 'srt:M047_1:126', 'srt:M047_1:239',
    'srt:M048_1_t:11', 'srt:M048_2:76', 'srt:M048_3:76', 'srt:M048_3:102', 'srt:M048_4:46',
    'srt:M051_1:32', 'srt:M051_1:59', 'srt:M051_3:76', 'srt:M051_3:79')}
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
