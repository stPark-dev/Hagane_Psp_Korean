"""Apply D16 decisions to existing drafts (explicit per-line edits)."""
import json, sys
sys.path.insert(0, '.')
from tools import textcheck

EDITS = {
    'srt:F002_001_003:323': [('‘노랑새의 문장’', '‘노란 새의 문장’')],
    'srt:F002_049_001:52': [('선임 대위 같은 식으로', '상급 대위 같은 식으로')],
    'srt:F000_014_006:89': [('쥐 불어나듯 하는@n이상론이다.', '쥐처럼 불어나는@n이상론이다.')],
    'srt:F000_014_006:90': [('쥐 불어나듯 하는 이상론?', '쥐처럼 불어나는 이상론?')],
    'srt:F000_014_006:96': [('쥐 무리의 맨@n꼭대기에', '쥐 무리의@n꼭대기에')],
    'srt:F000_014_005_2:6': [('“병은 졸속을 귀히 여긴다” 싸움은@n빨리 공격해서 승부를 내는 편이@n좋으니까. 속공으로 끝내지.',
                              '“전쟁에서는 졸속이라도@n신속함을 중시한다” 싸움은 빨리@n공격해서 승부를 내는 편이 좋으니까.@n속공으로 끝내지.')],
    'srt:F000_014_005_2_e:21': [('“화나게 해서@n흐트러뜨려라” 내 도발에 넘어가@n냉정함을 잃은 게 패인이다.',
                                 '“적을 노하게@n하여 혼란에 빠뜨려라” 내 도발에@n넘어가 냉정함을 잃은 게 패인이다.')],
    'srt:F000_015_003:142': [('“얼간이”라고', '“겁쟁이”라고')],
    'srt:F000_015_003:87': [('이슈발인 모자를.', '이슈발인 부모와 아이를.')],
    'srt:F000_015_003:88': [('명령을 어기고 그 모자를 도망치게 했지.', '명령을 어기고 그 부모와 아이를@n도망치게 했지.')],
    'srt:F000_015_003:89': [('소령은 그 모자를@n구해 줬다는 거잖아?', '소령은@n그 부모와 아이를 구해 줬다는 거잖아?')],
    'srt:F000_015_003:90': [('그때 이 몸이 그 모자를@n발견하지 않았다면, 그대로 숨어서@n살아남을 수 있었을지도 모른다.',
                             '그때 이 몸이@n그 부모와 아이를 발견하지 않았다면,@n그대로 숨어서 살아남을 수 있었을지도@n모른다.')],
    'srt:F000_015_003:96': [('했을 터인 모자는, 이 몸의 눈앞에서……@n다른 국가 연금술사에게 살해당했다.',
                             '했을 터인 부모와 아이는, 이 몸의@n눈앞에서…… 다른 국가 연금술사에게@n살해당했다.')],
    'srt:F000_015_003:102': [('그때, 모자를 죽인', '그때, 부모와 아이를 죽인')],
    'srt:F001_017_001:94': [('‘쇼기’라는', '‘장기’라는')],
    'srt:F001_999_001_2_e:19': [('대중을 위해 있으라”', '대중을 위해 존재하라”')],
}
# D16-A1: name plate fix (EBOOT plate table: 0 エド, 1 アル). Applied at build by kotext.apply_srt.
SPEAKER_FIXES = {'srt:F001_011_002:68': {'from': 0, 'to': 1}}
# flags settled by D16; voice-reuse branches stay for runtime checks (D16-A2)
KEEP = {'srt:F002_999_002_2_e:68', 'srt:F002_999_002_2_e:70', 'srt:F001_999_001_2_e:40',
        'srt:F001_001_001_2_e:25',
        # not covered by D16: source typos, timeline and subject readings, plate-less choice prompt
        'srt:F001_014_001:51', 'srt:F002_013_002:117', 'srt:F002_001_003:9', 'srt:F001_011_002:56',
        'srt:F000_048_009:202'}
import glob as _g
FLAGS = {}
for _p in _g.glob('text/ko/srt/F00[0-3]*.json'):
    for _e in json.load(open(_p))['entries']:
        if _e.get('flag') and _e['id'] not in KEEP:
            FLAGS[_e['id']] = ''
FLAGS['srt:F002_015_001_2_e:27'] = 'D16-9 채택. 정발판 실물 문구 검증 대기'
FLAGS['srt:F002_015_001_2_e:35'] = 'D16-9 채택. 정발판 실물 문구 검증 대기'
src = {f"srt:{d['file'][:-4]}:{d['idx']}": d['text'] for d in json.load(open('work/text/srt_src.json'))}
byfile = {}
for i in set(EDITS) | set(FLAGS) | set(SPEAKER_FIXES):
    byfile.setdefault(i.split(':')[1], []).append(i)
for name, ids in byfile.items():
    path = f'text/ko/srt/{name}.json'
    data = json.load(open(path))
    entries = []
    for e in data['entries']:
        if e['id'] in FLAGS:
            e = {**e, 'flag': FLAGS[e['id']]}
        if e['id'] in SPEAKER_FIXES:
            e = {**e, 'speaker_fix': SPEAKER_FIXES[e['id']]}
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
