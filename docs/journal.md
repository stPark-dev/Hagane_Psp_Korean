# 작업 일지

시간순 기록. 현재 결론은 `docs/survey.md`가 기준이다.

## 2026-10-26

### 환경
- PPSSPP v1.20.4 (flatpak `org.ppsspp.PPSSPP`, --user), 설정 `RemoteDebuggerOnStartup = True`.
- 디렉터리 부팅: 압축 푼 트리의 **루트**(PSP_GAME의 부모)를 인자로 줘야 함. `PSP_GAME/SYSDIR/EBOOT.BIN`을 주면 "ISO looks bogus"로 실패.
- 화면 캡처: 디버거 `gpu.buffer.screenshot`은 "Could not download output"로 실패 → X11 창 캡처(`import -window`)로 대체 (`tools/ppdbg.py`).
- 디버거 WebSocket 핸드셰이크가 디렉터리 부팅 실행에서 응답 없음(원인 미조사, 캡처에는 불필요).
- pspdecrypt `c156627` (work/ext, 저장소 밖)로 EBOOT 복호화.

### PoC-F1 — 낱개 FAfont14.fon이 세이브 대화를 그리는가
- 기준: 원본 트리, 처음 부팅(세이브 없음) → "セーブデータがありません。…" 대화.
- 조작: `USRDIR/DATA/FAfont14.fon`의 `セ`(글리프 311)를 꽉 찬 사각형으로.
- 결과: 화면 변화 없음 → **기각**. 낱개 파일은 이 소비자의 공급원이 아님.

### PoC-F2 — 네 사본 판별
- 조작: `セ`에 CPK FAfont14 = 꽉 참, CPK cmex = 체크, 낱개 cmex = 가로줄, 낱개 FAfont14 = 세로줄. DAT000은 `tools/cpk.py rebuild`로 재구성(두 폰트 무압축 저장).
- 결과: 첫 줄 `セ`가 꽉 찬 사각형 → **CPK 안 FAfont14.fon 확인**. 재구성 DAT000으로 부팅 정상.
- 증명하지 않은 것: 대사창·메뉴·전투 UI의 글꼴, 글리프 수 증가 허용 여부.
