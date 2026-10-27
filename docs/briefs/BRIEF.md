# Draft brief (shared by every parallel batch worker)

You are drafting Korean for one batch of the PSP game script 鋼の錬金術師 FULLMETAL ALCHEMIST 約束の日へ. Missions M001–M056 are already drafted and approved in direction. Several workers run in parallel on other batches, each using this same brief.

Side events (A series, e.g. `A001_018_1`): the second number appears to be the main mission the event belongs to (018 → M018). Read that mission's drafted Korean for who knows whom, address forms and story state at that point.
Field events (F series, e.g. `F000_006_009`): the second number likewise appears to be the main mission (006 → M006); `999` seems to mean no fixed point in the story. Check the dialogue itself for story state.
Bonus scenarios (IF and E series): short battle scenes outside the main timeline (revived enemies, unusual pairings). Characters who never meet in the story may talk; keep each one's established voice and address forms.

## Read first (authoritative, in this order)
1. `docs/style.md`. §0 (style guide v1.0) and the subsections "호칭 세부 (D6)" and "호칭·문체 세부 (D7)" are binding. §1–§3 give detailed rules; §2 covers control tokens.
2. `docs/decisions.md`, D4–D19. These are the owner's decisions.
3. Your input batch `work/batches/in/<BATCH>.json`. Entries are in script order with `id`, `speaker` (Japanese plus approved Korean; `?` = no glossary entry, so translate generic roles like 店主/中央軍人Ａ naturally), `kind` and `src`.
   - Glossary rows in `glossary` were matched by substring. Apply a row only where the Japanese really means that name (ロウ in スロウス or 蝋 is not 로그 로우; リン as an element is 인; ハン in ゴハン is not a name).
   - Glossary `state`:
     - 승인/잠정승인: binding.
     - 제안: usable but not final; use it consistently.
     - 결정필요: the owner has not decided. Draft your best reading and put a note in `flag` naming the term.
4. For consistency, reuse the drafted Korean in `text/ko/srt/M0*.json` (M001–M056, especially the missions right before yours) (field `ko`) wherever the same phrasing, terms or address forms recur.
   - Recurring: 강철의, 콩알만 한 꼬맹이, 엄마, 합성수(키메라), 오토메일, 연성, 인체연성.
   - Ranks: 대령, 중령, 소령, 대위, 중위, 소위, 준위, 준장, 상사.

## Decided (D7, short form)
- 綴命の錬金術師 철명의 연금술사. 人柱 제물 (인간 제물 in explanations). 査定 심사, but the national alchemist evaluation is 자격 심사.
- 師匠 스승님. 准尉 준위. 傷の男 = descriptive wording before his identity is revealed, 스카 after.
- 鋼の大将 강철의 대장. 君 = 자네 or 너 by relation. お兄ちゃん 오빠. ばっちゃん 할머니. 殿 = 님/공/양 by target. 鋼の坊や 강철의 꼬마.
- Recap (`_t` files) 해라체. Item gain "~을 손에 넣었다!". Skill gain "~을 습득했다!".
- 中央 as the city name (セントラル, 中央（セントラル）, bare 中央 meaning the city) = 센트럴. Compounds 中央司令部 중앙사령부, 中央軍 중앙군, (国立)中央図書館 (국립)중앙도서관.
- 현자의 돌 aliases: 철학자의 돌 / 천상의 돌 / 대엘릭시르 / 붉은 팅크투라 / 제5실체.

## Decided (D8, short form)
- Envy→Ed 鋼のおチビさん: 강철의 꼬맹이. Hughes→Ed 豆: 콩알. Al→Greed お兄さん: 아저씨. Paninya→Ed 兄ちゃん: 너 (adjust by context). 鎧クン: 갑옷 군. Bradley→brothers 君: 자네.
- 構築式 구축식. 一は全、全は一 하나는 전체, 전체는 하나. にわか景気の谷 반짝 호황의 골짜기. ゴッズ 갓즈. 第五研究所 제5연구소. 器用さ 손재주 (器用さアップ・小 → 손재주 업・소). 軍法会議所 군법회의소.
- Speaker labels: if a label looks wrong, still translate by the real speaker and flag it (labels are fixed separately).

## Decided (D9, short form)
- 若 도련님. 皇子/皇女 황자/황녀. 強欲 탐욕 (탐욕의 그리드). 真理の記憶 진리의 기억; its unlock message is "‘진리의 기억’을 습득했다!".
- 人造人間（ホムンクルス）: 인조인간(호문쿨루스) only at the very first appearance (already done in M015). From then on use 호문쿨루스. Plain 人造人間 without ruby → 인조인간.
- Ed→Hohenheim 너 (네놈 only when extremely heated). Pinako→Hohenheim 자네. Fu→Ross 로스 님. Fu→Ed 애송이. Breda→Fu 후 영감. No.66→Lin 실눈, →Ross 아가씨. Ed→Ran Fan 아가씨 (light or teasing only). Martel→Greed 그리드 씨. Armstrong→Hughes 휴즈 공.
- Xing characters speak standard Korean. The only exception is a scene where Lin deliberately exaggerates a foreign accent as a gag (M020_3:57 "모른다해~").
- 武僧 무승. 東/西の賢者 동쪽/서쪽의 현자. イシュヴァール人 이슈발인. イシュヴァールの民 이슈발 민족. イシュヴァール戦 이슈발 내란. お人好し by context (호인 / 좋은 사람 / 착해 빠졌다). クレタ 크레타. ヨック島 요크섬. 拒絶反応 거부 반응.

## Decided (D10, short form)
- Address forms:
  - May→Scar 下僕さん 하인님. May↔Ed 豆男/豆女 콩알 남자/콩알 여자. May→Yoki ヨキさん 요키 씨.
  - Bradley→Roy 若僧 풋내기. Greed→Father 親父殿 영감님. Scar/Envy→Al 鎧の錬金術師 갑옷의 연금술사.
  - Envy→Ed/Lin ガキども 꼬맹이들. Al→Roy 大佐殿 대령님. Ed→MP 憲兵さん 헌병 아저씨 (헌병님 or omitted by age/situation).
  - The child voice inside Envy, お兄ちゃん: 형아 (provisional).
- Register:
  - Hawkeye→Roy: 하십시오체 in official/military situations, 해요체 allowed in private ones.
  - Winry to Gracia: "아버지와 어머니"; with Ed/Al: "아빠랑 엄마".
- 合成獣（キメラ）: 합성수(키메라) only at the very first appearance (done in M001). After that: 합성수.
- イシュヴァールの戦い 이슈발 내란 (a specific single battle may be distinguished by context). 軍曹 중사. リバウンド 리바운드.
- 順わぬ民 따르지 않는 백성. 人体錬成の陣 인체연성진. 傷の男さん (May) 스카 씨.

## Decided (D11, short form)
- Ed→Bradley: keep the source's sarcastic polite speech (approved exception, M039_1:121/123).
- Hawkeye→Ed: 해요체 by default; 반말 only where the source shows a clear emotional shift. Hawkeye→Winry ウィンリィちゃん: 윈리 양.
- 貴様: Bradley→Rogue Lowe, and Olivier/Buccaneer→Ed: 네놈.
- Address forms:
  - May→Al 鎧さン 갑옷 씨; Lin's 鎧さン stays 갑옷 양반.
  - Ran Fan→Fu 爺様 할아버지. Olivier→Ed 赤チビ 빨간 꼬맹이. Villager→Al 鎧のあんちゃん 갑옷 총각.
  - Selim→Bradley お義父さん 아빠. Al→Selim 셀림 군 (may be dropped when repeated).
  - Mrs Bradley/Selim→Ed 에드워드 씨. Guard→Mrs Bradley 사모님, →Selim 셀림 님.
  - Miles→Ed 君 자네 (반말).
- Terms:
  - 天険の地 천험의 땅. 少将 소장. 中将 중장. センズ 센즈.
  - イシュヴァール殲滅戦 이슈발 섬멸전 (the military's name; keep it distinct from 이슈발 내란).
  - ブリッグズの掟 브릭스의 철칙: 弱肉強食 약육강식, 一日一善 하루 한 가지 선행. ブリッグズの北壁 브릭스의 북벽.
  - 大総統令 대총통령. 飼い犬/負け犬 pun: 길들여진 개 / 패배한 개.
  - クロコダイル 크로커다일. 密偵 첩자. ダリハ地区 다리하 지구. 少佐相当官 소령 상당관. 粗忽者 덜렁이. ドラクマ 드라크마.

## Decided (D12, short form)
- Ed→Raven: keep the grudging polite speech (해요체, approved exception, M046_2).
- 貴様: Raven→Olivier 네놈 (네년 only for a clearly gendered insult); Miles→Kimblee 네놈.
- Ed→Kimblee: キンブリーさんよ 킴블리 씨, あんた 당신, てめぇ 이 자식. (Ed→others' てめぇ is unchanged: 네놈.)
- Kimblee→Winry: ウィンリィさん 윈리 씨, ロックベル嬢 록벨 양. Miles→Winry: ロックベルのお嬢さん 록벨 아가씨, ロックベル嬢 록벨 양.
- Scar→Winry 娘(よ) 아가씨. Scar's 師父 사부님, 兄者 형님. May→Al アルフォンス様 알폰스 님. Zelso→Al 鎧の 갑옷. Neil→Olivier 少将 소장님.
- Terms: 国土錬成陣 국토연성진. 血の紋 피의 문장. 北国用/寒冷地用 (automail) 한랭지용 (the region itself: 북쪽 지방). 正/負の感情 긍정적/부정적 감정. 中央のヤツら 센트럴 녀석들. アイマム 알겠습니다!! 老害 늙은 폐물. 先遣隊 선견대. 竪坑 수직갱. 紅蓮の術 홍련의 술법.
- Names (provisional, not verified against the licensed manga): ニール 닐, ミック 믹, リヴィエア 리비에아, カメロン 카메론, ソープマン 소프먼, ウェルズリ 웰즐리, ペンドルトン 펜들턴, マッドベアＧ 매드베어 G.

## Decided (D13, short form)
- Scar→Al 貴様 너 (others stay 네놈). Yoki→Scar 傷のダンナ 스카 나리, short ダンナ 나리.
- Envy: 鎧の弟クン 갑옷 동생 군, シンの女 싱 여자, 小娘 계집애; ゴミ 쓰레기, ゴミ虫 벌레 같은 것들, クズ 버러지.
- Al→Yoki 요키 씨 (or omit), 해요체. Al→Hohenheim 父さん 아빠 (아버지 when Al talks about him to others). Villager→Hohenheim ホーさん 호 씨. Hohenheim→Winry 윈리.
- Rosé: after the Lior reunion (M054) she may use 반말 to the brothers as the source does; Rosé→Winry 해요체 + 윈리 씨.
- Ed→Greed オレ様 이 에드워드 님께서 (내가 친히 if the line is too long). Darius→Ed 兄貴 형. Heinkel→Ed こつぶ 쥐방울.
- Terms: アスベック 아스베크, ノースシティ 노스 시티, グリリン 그리린 (provisional). 逆転の錬成陣 반전의 연성진. 来るべき日 다가올 그날, 約束の日 약속의 날. フラスコの中の小人（ホムンクルス） 플라스크 속의 난쟁이(호문쿨루스), later without ruby. ありえないなんてことはありえない 불가능이란 있을 수 없다 (never "있을 수 없는 일은 있을 수 없다"). 龍脈 용맥. 魂の容れ物 영혼의 그릇. 闇医者 무면허 의사 (뒷골목 의사 for a licensed doctor treating in secret). 日陰者 음지 인생 in dialogue, 음지에서 사는 신세 in narration. 三文芝居 삼류 연극.

## Decided (D14, short form)
- Pride: 父上 아버님; 君 to Wrath/Envy 자네, dropped when it clashes with 해요체; 小童 꼬맹이. Bradley's 父上 is also 아버님.
- Barry: Hawkeye 姐さん 누님, Falman ダンナ 양반, Havoc タバコのあんちゃん 담배 형씨. Hawkeye→Barry 반말. Hawkeye→Lust きさま 네놈.
- Roy→Havoc 貴様 이 녀석, おまえ 자네. Knox→Roy おまえさん 자네. Hughes→Winry 윈리. Madame Christmas→Roy ロイ坊 우리 로이 (로이 녀석 when teasing). Scar→May 娘 꼬마. Bradley→wife 당신, wife→Bradley 여보.
- Seven sins: 色欲 색욕, 暴食 폭식, 嫉妬 질투, 怠惰 나태, 憤怒 분노, 強欲 탐욕, 傲慢 오만. 最強の矛 최강의 창.
- Terms: 発火布 발화포, 術法増幅器 술법 증폭기, 銀の錬金術師 은의 연금술사, 鷹の眼 매의 눈, 矜恃（プライド） 긍지(프라이드) only when the ruby is there, 中央上層部 중앙 상층부, 保安隊 보안대, ６６事件 66 사건, 大熊猫 판다, 上客 귀한 손님, ボイン 글래머, クビにしてやる 모가지를 날려 주겠다 (rough threats only), EX missions 격전 배틀 로열 / 숙명의 대결.
- Names (provisional): 뉴 옵틴, 칸다 지구, 창족, 솔라리스, 헨리. Code names stay as spoken: 엘리자베스 (Hawkeye), 케이트 (Fuery), 재클린 (Havoc).
- May: standard Korean; only scenes where her accent is the topic may differ (e.g. "말투가 조금 독특하네요").

## Decided (D15, short form)
- Olivier→Roy 貴様 네놈, 青二才 풋내기. Selim→Mrs Bradley お義母さん 엄마. Hohenheim→Trisha 君 당신, Trisha→Hohenheim あなた 여보. Izumi→Sig あんた 여보. Flower-shop woman→Roy お兄さん 총각. Guard→Bradley 旦那様 각하. Catherine→Alex 兄様 오라버니.
- アイマム/アイサー as a normal military reply: 알겠습니다. Only Armstrong imitating Briggs style: 아이, 맴!!
- Terms: 国家錬金法 국가 연금법, 三大制限 3대 제한, 始まりの人造人間 최초의 인조인간, 傲慢（プライド） 오만(프라이드), マスタング組 머스탱 팀 (元～ 옛 머스탱 팀; 머스탱 일당 only when sneering), ラサーヤナ 라사야나, アウレリアン 아우렐리안, 真人 진인, 金人 금인, 闇の使者 어둠의 사자.
- Names (provisional): ガードナー 가드너, フォトセット 포토세트, Xerxes names and cipher names in the glossary. Keep cipher initials as half-width Latin letters.
- Side events A001–A055 are drafted; reuse them for recurring characters.

## Decided (D16, short form)
- Ed's polite speech where the source has it (to Armstrong, Tucker, shop staff, strangers) is an approved exception: keep it.
- Al→Hawkeye/Armstrong: 해요체, address by rank (중위님, 소령님); 반말 only in self-talk. 鎧のお兄さん 갑옷 총각.
- Skills: 知力アップ・小 지력 업・소, パワーアップ・小 파워 업・소, バックガード 백 가드, フラメル/不死鳥/黄色鳥/白鳥/黒鳥の紋章 플라멜의/불사조의/노란 새의/백조의/흑조의 문장.
- Ranks: 将官 장성, 佐官 영관, 尉官 위관, 准士官 준사관, 下士官 부사관, 伍長 하사, 等兵 병, 上級大尉 상급 대위, 大将 대장, 大総統府 대총통부. (鋼の大将 is a nickname: 강철의 대장.)
- 「錬金術師よ、大衆のためにあれ」 연금술사여, 대중을 위해 존재하라. 自然摂理 자연섭리, 質量保存 질량 보존, 爆砕 폭쇄, 鉄血の錬金術師 철혈의 연금술사.
- ネズミ算の理想論 쥐처럼 불어나는 이상론, ネズミの天辺 쥐 무리의 꼭대기. 兵は拙速を貴ぶ 전쟁에서는 졸속이라도 신속함을 중시한다, 怒らせてこれを乱せ 적을 노하게 하여 혼란에 빠뜨려라.
- 腑抜け 겁쟁이 (by context), 親子 부모와 아이, ショーギ 장기 (쇼기 only if Japanese shogi is explicit), 親友（とも） 벗, 学級委員長 반장, 色ボケ軍曹 연애 바보 중사, リゼンブールの女豹 리젠블의 암표범.
- Names (provisional): クラウディオ・リコ・アエルゴ 클라우디오 리코 아에르고 (keep 王子 왕자 / 皇子 황자 as the source has them), フェスラー 페슬러, オウガーヘッド 오거헤드, スカルヘッド 스컬헤드.
- File numbers are not a reliable timeline; judge story state from the dialogue (e.g. F002_013 is before M011).
- A wrong name plate is reported in `flag`, never fixed by you; the owner decides and the fix goes in as `speaker_fix`.

## Decided (D17, short form)
- Passers-by/mechanics/shopkeepers→Ed 兄ちゃん 형씨 (鎧の兄ちゃん stays 갑옷 총각). 親子 부모와 아이 (Ed and Hohenheim: 부자지간).
- Ran Fan→Al 貴様 너 이 녀석 (flustered). Winry→Hawkeye リザさん 리자 씨. Ed→Ran Fan ねーちゃん 그 아가씨 (이 누나/그 누나 when teasing). Locals→Izumi イズミ先生 이즈미 선생님. Izumi→Sig 旦那: 그이 in third person, 여보 to his face.
- カルタ 카루타, タコヤキ 타코야키, マーボードーフ 마파두부, トーフ 두부, 宵の明星 개밥바라기별, 鋼のこころ 강철의 마음, EX missions 사제 VS 국군 팀! / 동방검문록, 天然の女タラシ 타고난 바람둥이, とほほ 에휴…… (keep the 형 wording if the source also says 兄さん), 青春小僧 청춘 녀석, 一飯の貸し 밥 한 끼 빚.
- Names (provisional): シルバ・スタイナー 실바 스타이너, ゴルド 골드.

## Decided (D18, short form)
- Fu is called: by Al and Winry 후 할아버지, by Breda and Ed 후 영감, by Ran Fan 할아버지.
- Pride→Kimblee 君: drop it, 해요체 (당신 only for emphasis). Ran Fan→Ed 貴様 너, →Greed 네놈. Mechanics/Neil→Winry 윈리 양. No.48→Ed 鋼の小僧くん 강철의 꼬맹이 군. Greed→Izumi おねえさん 누님. Armstrong→Izumi 殿 이즈미 님, かたじけない 감사합니다! Al→Zampano 잠파노 씨 + 해요체. Hohenheim→shopkeeper オヤジさん 주인 아저씨.
- Terms: 仮想東方軍 가상 동방군, ブリッグズの女豹 브릭스의 암표범, 人形兵 인형 병사, 破壊する者 파괴하는 자, 一枚岩 한 덩어리, 新春・寒水の行 새해 찬물 수행, 大陸暦 대륙력, 北と東の合同演習 북부와 동부의 합동훈련, 人造人間たち 인조인간들, 中央軍人 중앙군 소속 군인 (중앙군 병사), ヒゲヤロー 수염 자식, 国家試験 국가 자격 심사. Name: エレナ 엘레나 (provisional).

## Decided (D19, short form, UI terms that also appear in dialogue)
- 修復 복구 (the technique 修復錬成 수복연성), ステータス 상태 (능력치 for stat values), セーブ/ロード 저장/불러오기, 会心率 치명타율, 敵単体 적 1체, 絆レベル 유대 레벨, 組手 대련.
- Technique names ending in 錬成 are written solid when named (수복연성, 석벽연성, 철구연성); the general act of transmuting stays spaced (연성하다, 원격 연성의 원리).

## Hard rules (mechanically checked; violations get rejected)
- Keep every protected token exactly, in the same order and count: `<~VOICE_ID>`, `⊥`, `⊿`, `@c<..>`, `@s<..>`.
  - `@n` is a line break; you may move it.
  - End each text the way the source does (usually `@n⊿@n`).
  - A voice cue opens its page and is followed by `@n`.
- At most 4 visible lines per page. A page is the text between `⊥`/`⊿`; a line holding only a voice cue doesn't count.
  - **At most 22 characters per line**, counting spaces and punctuation; aim for 21.
- Use only encodable characters:
  - All KS X 1001 Hangul is fine; rare syllables like 똠/햏/뷁 are not.
  - Also usable: ASCII and `…… ―― “ ” ‘ ’ ～ ♪ ・`.
  - 「」→“ ”, 『』→‘ ’, half-width `? ! , .`. Never use `·` (U+00B7).
- Choice lists keep their number of `@n`-separated items, with a trailing `@n`.
- Drop reading furigana like `隠居（いんきょ）`. Term ruby follows style.md ST-03.
- If meaning, the speaker relation, or a reference is genuinely unclear, draft your best reading and put a short Korean note in `flag`. Also flag a likely speaker-label error.
- **Do not edit any file except your own output.** Don't touch the glossary, style guide, decisions or `text/ko`. Report new term or address questions in your final message instead. Never decide an open term on your own; draft it, flag it and list it.

## Output
Write `work/batches/out/<BATCH>.json`: one JSON object mapping **every** entry id in the batch to `{"ko": "...", "flag": "..."}`.

Validate from the repo root and fix until it prints `ok`:
```
B=<BATCH> python3 -c "
import json, os; from tools import textcheck, termlint
B=os.environ['B']
b=json.load(open(f'work/batches/in/{B}.json')); o=json.load(open(f'work/batches/out/{B}.json'))
src={e['id']:e['src'] for s in b['scripts'] for e in s['entries'] if 'fixed_ko' not in e}
assert set(o)==set(src), (len(set(src)-set(o)), len(set(o)-set(src)))
bad={i:textcheck.check(src[i],o[i]['ko']) for i in o}; bad={k:v for k,v in bad.items() if v}
wide=[f for f in termlint.lint([{'id':i,'ko':v['ko'],'flag':v['flag'],'state':'draft'} for i,v in o.items()], src, []) if f.kind=='width']
print('ok' if not bad and not wide else (bad, wide))"
```

Final message, in Korean and short:
- The count of flagged entries.
- Speaker-label anomalies.
- New term or address questions, each with your proposal and the alternatives.

Do not paste translations.
