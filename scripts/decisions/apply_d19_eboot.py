"""Apply D19 to text/ko/eboot.json (explicit per-line edits; 敵単体 by source match)."""
import json, sys
sys.path.insert(0, '.')
from tools import ebootstr

R = {  # id: (old, new)
    'eboot:0x158060': ('스테이터스', '상태'),
    'eboot:0x15af00': ('회심률 상승', '치명타율 상승'),
    'eboot:0x15d618': ('로드', '불러오기'),
    'eboot:0x15d620': ('세이브', '저장'),
    'eboot:0x15d6e0': ('데이터를 세이브／로드합니다.', '데이터를 저장하거나 불러옵니다.'),
    'eboot:0x15d7f0': ('세이브 데이터를 로드합니다.', '저장 데이터를 불러옵니다.'),
    'eboot:0x15d810': ('데이터를 세이브합니다.', '데이터를 저장합니다.'),
    'eboot:0x15d334': ('레베카 카테리나', '레베카 카탈리나'),
    'eboot:0x15eb50': ('수복 미션', '복구 미션'),
    'eboot:0x15f180': ('스테이터스 화면에서', '상태 화면에서'),
    'eboot:0x15f1f0': ('회심률이', '치명타율이'),
    'eboot:0x15f278': ('스테이터스가 다운되는', '능력치가 다운되는'),   # stats go down (D19-4)
    'eboot:0x15f3e4': ('스테이터스가 다운됩니다.', '능력치가 다운됩니다.'),
    'eboot:0x15f494': ('스테이터스 표시에서', '상태 표시에서'),
    'eboot:0x1603a4': ('수복 미션과', '복구 미션과'),
    'eboot:0x160d68': ('수복해 버리자', '복구해 버리자'),
    'eboot:0x1612ec': ('수복은 부탁해', '복구는 부탁해'),
    'eboot:0x165a44': ('반군 조직의', '군내 범죄 조직의'),
    'eboot:0x165a94': ('반군 조직의', '군내 범죄 조직의'),
    'eboot:0x169e6c': ('로드하시겠습니까?', '불러오시겠습니까?'),
    'eboot:0x169e80': ('로드하지 않아도', '불러오지 않아도'),
    'eboot:0x169ea0': ('로드 중입니다.', '불러오는 중입니다.'),
    'eboot:0x169eb4': ('로드했습니다.', '불러왔습니다.'),
    'eboot:0x169ec8': ('로드에 실패했습니다.', '불러오기에 실패했습니다.'),
    'eboot:0x169efc': ('세이브하시겠습니까?', '저장하시겠습니까?'),
    'eboot:0x169f10': ('세이브하지 않아도', '저장하지 않아도'),
    'eboot:0x169f44': ('세이브 중입니다.', '저장 중입니다.'),
    'eboot:0x169f58': ('세이브 중입니다.', '저장 중입니다.'),
    'eboot:0x169f80': ('세이브했습니다.', '저장했습니다.'),
    'eboot:0x169f94': ('세이브에 실패했습니다.', '저장에 실패했습니다.'),
    'eboot:0x169fe8': ('세이브하려면', '저장하려면'),
    'eboot:0x16a030': ('세이브하려면', '저장하려면'),
    'eboot:0x16a0e0': ('세이브 데이터가', '저장 데이터가'),
    'eboot:0x16a19c': ('세이브할 수 없습니다.', '저장할 수 없습니다.'),
    'eboot:0x16a1c0': ('세이브 데이터가', '저장 데이터가'),
    'eboot:0x16a238': ('세이브 데이터를 세이브하려면', '데이터를 저장하려면'),
    'eboot:0x16a2d4': ('로드 중입니다.', '불러오는 중입니다.'),
    'eboot:0x16a378': ('세이브 데이터입니다.', '저장 데이터입니다.'),
    'eboot:0x16a410': ('세이브를 종료하시겠습니까?', '저장을 종료하시겠습니까?'),
    'eboot:0x16a428': ('로드를 종료하시겠습니까?', '불러오기를 종료하시겠습니까?'),
    'eboot:0x16a458': ('로드를 종료하고', '불러오기를 종료하고'),
}
SOLID = {'石拳錬成': ('돌주먹 연성', '돌주먹연성'), '尖角連続錬成': ('가시 연속연성', '가시연속연성')}  # D19-5, applied once by hand
MULTI = {'eboot:0x1602f8': [('수복하는', '복구하는'), ('수복한 것이', '복구한 것이'), ('수복 순서도', '복구 순서도')]}

data = open('work/eboot/EBOOT.elf', 'rb').read()
src = {t.id: t.text for t in ebootstr.catalog(data)}
path = 'text/ko/eboot.json'
f = json.load(open(path))
edited = 0
for e in f['entries']:
    i, ko = e['id'], e['ko']
    pairs = MULTI.get(i, []) + ([R[i]] if i in R else [])
    if ('敵単体' in src[i] or '敵を単体' in src[i]) and '적 하나' in ko:
        pairs.append(('적 하나', '적 1체'))
    if not pairs:
        continue
    for old, new in pairs:
        assert ko.count(old) >= 1, (i, old, ko)
        ko = ko.replace(old, new)
    assert not ebootstr.check(src[i], ko), (i, ebootstr.check(src[i], ko))
    wide = ebootstr.wider_lines(src[i], ko)
    e['ko'] = ko
    e['flag'] = f'폭 초과 {wide} (D19 반영 후, 실기 확인)' if wide else ''
    edited += 1
json.dump(f, open(path, 'w'), ensure_ascii=False, indent=1)
print('edited', edited)
