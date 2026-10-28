# 이어서 작업하기 (2026-10-27 기준)

다른 컴퓨터에서 이어서 할 때 이 문서부터 읽는다. 결정은 `docs/decisions.md`(D1–D19), 문체는 `docs/style.md`, 경과는 `docs/journal.md`, 그림 텍스트는 `docs/graphics.md`.

## 1. 환경 준비
1. 저장소 두 갈래를 받는다.
   - `main`: 번역 데이터·도구·문서. 정식 패치 기준.
   - `poc/eboot-ui`: EBOOT를 고치는 기능(`ebootstr.apply`, `apply_utf8`, `prx.move_strings`/`overwrite`)과 시스템 화면 번역(`text/ko/eboot_utf8.json`). **실기 PSP 확인 전까지 main에 병합 금지(D7·D19 추가).**
   - 같은 폴더 옆에 worktree로 두면 편함: `git worktree add ../hagane-eboot poc/eboot-ui`.
2. 원본은 각자 가진 디스크 이미지에서 만든다(저장소에 넣지 않음).
   - `7z x -owork/iso <ULJS00292 iso>`
   - pspdecrypt로 `work/iso/PSP_GAME/SYSDIR/EBOOT.BIN` → `work/eboot/EBOOT.elf`
   - `python3 scripts/prepare_work.py` → `work/dat000/`, `work/text/srt_src.json`, `work/text/eboot_names.json`(이 PC의 파일과 바이트 동일함을 확인함)
   - Windows: 7z 대신 Bandizip `bz.exe x -o:work/iso <iso>`로 풀어도 됨. pspdecrypt는 GitHub 릴리스(John-K/pspdecrypt 1.0 windows)를 work/ext/pspdecrypt에 받아 실행. 파이썬은 `PYTHONUTF8=1`로 실행(기본 cp949 때문에 JSON 쓰기 실패).
3. 글꼴: 저장소 옆 `../galmuri/Galmuri11-Bold.bdf`(Galmuri, OFL). 테스트 `test_galmuri_covers_ks_hangul`이 경로를 확인.
4. 테스트: `python3 -m pytest -q`(main 109개 통과, 2026-10-27). Windows에서는 `python -m pytest -q --import-mode=importlib`(다른 `tests` 패키지와 이름 충돌).
5. PPSSPP(flatpak `org.ppsspp.PPSSPP`, 설정 RemoteDebuggerOnStartup=True)로 트리 폴더를 직접 실행. 입력·캡처 도구는 `tools/ppdbg.py`, `scripts/emu/drive.py`(단계 실행), `scripts/emu/mash.py`(버튼 연타 + 10초마다 캡처). 화면 전환 직후 입력은 2초쯤 기다려야 먹힘. 버튼 이름: circle, cross, triangle, square, start, select, up/down/left/right, ltrigger, rtrigger.

## 2. 빌드
- DAT000(대사 전체 + 한글 글꼴 + 그림 텍스트): `python3 -m tools.build work/iso/PSP_GAME/USRDIR/DATA/DAT000.cpk OUT/DAT000.cpk --bdf ../galmuri/Galmuri11-Bold.bdf --fonts ../fonts [--policy release]`(약 50초, numba·opencv·scipy 필요). 교체 파일은 CRILAYLA로 다시 압축(`tools/crilayla.py`).
- EBOOT(브랜치에서): `ebootstr.apply(원본 ELF, text/ko/eboot.json, 'dev')` 다음 `ebootstr.apply_utf8(결과, text/ko/eboot_utf8.json)`. 결과는 평문 ELF EBOOT.BIN(커스텀 펌웨어 필요 여부 실기 확인 대상).
- 테스트 트리: 원본 트리를 하드링크 복사(`cp -al work/iso work/poc/u2/tree`)하고 DAT000.cpk와 SYSDIR/EBOOT.BIN만 교체.

## 3. 현재 상태
- 대사 초벌 12,640 / 12,644(Script00 디버그 4줄 제외), D4–D19 반영. 상태는 모두 draft(검수 전).
- EBOOT UI 2,137개 초벌·D19 반영(main `text/ko/eboot.json`), 시스템 화면 UTF-8 15개(브랜치).
- PPSSPP 확인: 부팅·타이틀·로드·갤러리·환경 설정·M001 대화·선택지·로그·전투 준비 메뉴(유닛·스킬·유대·미션 정보) 한국어 정상, 저장·불러오기 정상(PoC-U1·U2·S1).
- 알려진 오탐/승인 예외는 `docs/decisions.md` D15 표(termlint 경고 11건이 정상).

## 4. 다음 작업 (사용자 지정 순서: 1 → 2 → 3)
1. **그림 텍스트**(D20: A+B+C+D, 구현 완료 2026-10-27 — `docs/graphics.md` 구현 상태)
   - Linux: `pip install --user --break-system-packages numba`, 글꼴은 `https://github.com/notofonts/noto-cjk/raw/main/{Serif,Sans}/SubsetOTF/KR/<파일>`을 curl로 받음.
   - 글꼴: `../fonts/`에 notofonts/noto-cjk SubsetOTF/KR의 NotoSerifKR-Black·Bold, NotoSansKR-Bold·Black(OFL)과 LICENSE. 작은 UI 글자는 `../galmuri/`.
   - 남은 것: 전투 UI 그림(m_menu #2, battle01 #0·#2)과 미션 시작 연출 로고(NEW GAME 직후 로딩 화면에도 보임, journal PoC-G1), 전투 준비 메뉴 화면 확인(장소 표시는 2026-10-28 확인), 컷인 그림 속 글씨 목록·범위, 작업자 판단 용어 검수(D20 끝).
   - PPSSPP(Windows): 설정 `Documents/PPSSPP/PSP/SYSTEM/ppsspp.ini`의 [General] RemoteDebuggerOnStartup = True. 트리 폴더의 절대 경로로 실행. 시험 트리는 `work/poc/g1/tree`(원본 하드링크 + 새 DAT000), 부팅 확인 스크립트 `work/poc/boot_test.sh`(저장소 밖).
   - 그림 작업 스크립트는 work/gfx(저장소 밖)에 시험용으로만 있음. 재현에 필요한 것은 `scripts/gfx/`(gfx_index → gfx_sheets → gfx_label_score/crops, gfx_titles)와 `text/ko/graphics.json`의 상자 좌표.
2. **실기 테스트용 ISO**
   - 지금 상태(대사 전체 + UI + 시스템 화면 한국어)로 ISO를 만들어 사용자가 실제 PSP(커스텀 펌웨어)에서 확인.
   - 확인 항목: 평문 ELF EBOOT 실행 여부, 한글 표시, XMB 세이브 정보 한글(시스템 글꼴), 저장·불러오기·덮어쓰기·삭제, 설치 데이터(INS000.DNS, D2) 동작.
   - ISO 재구성 도구는 아직 없음(mkisofs/genisoimage 계열 또는 UMDGen 류 조사 필요). 설치 데이터는 PGD 재암호화(work/ext/pgdtool, 키는 사용자 EBOOT 파일 오프셋 0x1a5c50에서 읽음 — 키 값을 저장소에 쓰지 말 것).
3. **게임 진행 확인**: 전투 UI, 아이템, 스킬서·곡명 목록, 갤러리 해금 목록 등 폭이 좁은 칸(EBOOT 폭 초과 플래그 241줄)의 실제 잘림.

## 5. 작업 방식 메모
- 번역 묶음 작업: `scripts/export_batch.py`(대사) / `scripts/export_eboot.py`(UI)로 `work/batches/in/`에 입력을 만들고, 작업 지침은 `docs/briefs/BRIEF.md`·`BRIEF_EBOOT.md`를 `work/batches/`에 복사해 쓴다. 병합은 `scripts/merge_batches.py` / `scripts/merge_eboot.py`, 검수는 `scripts/lint_all.py`.
- 소유자 결정(Dn)은 줄별 스크립트(`scripts/decisions/apply_dN.py`, 바꿀 문자열이 정확히 1번 나와야 함)로 반영하고 문서·용어집·BRIEF를 함께 갱신한다. 문맥에 따라 달라지는 호칭은 일괄 치환하지 않는다.
- 정발판 실물로 확인하지 못한 고유명사는 `잠정승인`으로 두고 "공식 확인 완료"로 표시하지 않는다.
