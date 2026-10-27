# EBOOT UI brief (shared by every EBOOT batch worker)

You are translating the **UI strings in the game executable** of the PSP game 鋼の錬金術師 FULLMETAL ALCHEMIST 約束の日へ into Korean: menus, system messages, skill names and descriptions, item names, name plates, gallery and mini-drama titles, mission names, goals and summaries. All dialogue (text/ko/srt) is already drafted; the UI must match it.

## Read first (authoritative, in this order)
1. `docs/style.md` and `docs/decisions.md` (D4–D18): the owner's decisions. Character names, ranks, terms and address forms are fixed there and in the glossary.
2. `text/glossary.tsv`: rows with state 승인/잠정승인 are binding; 제안 is usable; 결정필요 means draft + flag.
3. Your input `work/batches/in/<BATCH>.json`. Entries are in UI order (sorted by the pointer table that uses them):
   - `id` (eboot:<address>), `src`, `table` (the pointer table; neighbours in the same table belong to the same screen or list), `width` (display width per line of the source; full-width = 2, half-width = 1), `pointers` (how many places use it).
   - `same_as`: the same Japanese string appears earlier under that id. Translate it identically.
   - `fixed_ko`: already translated; context only.
4. The drafted dialogue in `text/ko/srt/*.json` (field `ko`) shows how names, skills, items and missions were rendered in-game. Search it before choosing a rendering:
   - Skill unlock lines ("…를 습득했다!"), item lines ("…를 손에 넣었다!"), EX mission unlock lines, mini-drama lines all name UI items that appear here.
   - Decided skill names: 지력 업・소, 파워 업・소, 손재주 업・소, HP 업・소, 백 가드, 프런트 가드, 타격 강화, 강철의 마음, 플라멜의/불사조의/노란 새의/백조의/흑조의 문장. Decided EX missions: 격전 배틀 로열, 숙명의 대결, 어둠의 사자, 사제 VS 국군 팀!, 동방검문록, 북부와 동부의 합동훈련.

## Hard rules (mechanically checked)
- Keep these exactly, same order and count: `@c<..>` (colour), `@s<..>` (speed), `%s` and other printf formats, button glyphs `∈ ∋ ⊆ ⊇ ↑ ↓ ← →`.
- `@n` is a line break: keep the same number of lines as the source.
- **Width:** each Korean line must be no wider than the same source line (Hangul and full-width = 2, ASCII and spaces = 1). Menu cells are fixed; a wider line may be cut off or overflow. If you cannot fit, write the best version and put a Korean note in `flag` (the validator lists these).
- Use only encodable characters: KS X 1001 Hangul (no 똠/햏/뷁), ASCII, and `…… ―― “ ” ‘ ’ ～ ♪ ・ ： ＋ ％ ＨＰ`-style full-width forms that already occur in the source. Never use `·` (U+00B7).
- Keep full-width digits/letters (１, ＨＰ, ＬＶ) as they are or turn them into half-width only if that is what makes a line fit; numbers must not change.
- Do not translate strings that are not shown to players if you are sure (e.g. "（３Dデモ用）※変更になりました" is a dev note): keep the Japanese and flag `개발용 문자열로 보임`.
- **Do not edit any file except your own output.** Report new term questions in your final message; never decide an open term on your own.

## Style for UI
- Menus and buttons: short nouns (갤러리, 스페셜, 팀 편성). System questions: 하시겠습니까? / 합니다. form ("세이브하시겠습니까?").
- Skill descriptions: concise noun-ending style matching the source (`錬成攻撃・直線２マス` → `연성 공격・직선 2칸`).
- Name plates and character lists: glossary names exactly (에드, 알, 로이 …; 真の姿 → (진짜 모습) etc. as decided).
- Mission goals and summaries: plain written style matching the dialogue drafts.

## Output
Write `work/batches/out/<BATCH>.json`: one JSON object mapping **every** entry id without `fixed_ko` to `{"ko": "...", "flag": "..."}`.

Validate from the repo root and fix until it prints `ok` (wide lines are allowed only with a flag):
```
B=<BATCH> python3 -c "
import json, os; from tools import ebootstr
B=os.environ['B']
b=json.load(open(f'work/batches/in/{B}.json')); o=json.load(open(f'work/batches/out/{B}.json'))
src={e['id']:e['src'] for e in b['entries'] if 'fixed_ko' not in e}
assert set(o)==set(src), (len(set(src)-set(o)), len(set(o)-set(src)))
bad={i:ebootstr.check(src[i],o[i]['ko']) for i in o}; bad={k:v for k,v in bad.items() if v}
lines={i:len(src[i].split('@n'))!=len(o[i]['ko'].split('@n')) for i in o}; lines=[k for k,v in lines.items() if v]
wide=[i for i in o if ebootstr.wider_lines(src[i],o[i]['ko']) and not o[i]['flag']]
same={}; incons=[]
for e in b['entries']:
    k=o.get(e['id'],{}).get('ko', e.get('fixed_ko'))
    if e['src'] in same and same[e['src']]!=k: incons.append(e['id'])
    same.setdefault(e['src'],k)
print('ok' if not (bad or lines or wide or incons) else dict(bad=bad, lines=lines, wide_without_flag=wide, inconsistent=incons))"
```

Final message, in Korean and short:
- Count of flagged entries, and how many are width overruns.
- New term questions (with your proposal and alternatives).
- Strings you believe are dev-only.

Do not paste translations.
