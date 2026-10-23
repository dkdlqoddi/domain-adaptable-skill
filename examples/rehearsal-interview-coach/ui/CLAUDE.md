# ui 지침

역할: D 인터페이스 — 비교 화면(선수 선택 → 지난 세 번 연습 + 그 자리에서 오늘 것 입력·저장). HTML/CSS/JS 한 장(`ui/index.html`), 빌드·패키지·프레임워크 없음.

## 범위
- 쓰기: `ui/**`, `docs/TASKS.md`(내 행만)
- 읽기 전용: `docs/CONTRACT.md`(A·B절), `docs/SPEC.md`(F1·F2 완료 기준, 4절 비목표, 5절 엣지), `fixtures/*.response.json`, `docs/GLOSSARY.md`(화면 글자)
- 열지 않음: `api/**` 전부. 서버는 실행만 한다. 응답 모양은 CONTRACT B절과 `fixtures/`의 샘플 값으로 대신한다.

## 실행·검증
- 실행: `cp fixtures/records.sample.json /tmp/records.json && python3 api/server.py --data /tmp/records.json` → http://localhost:8765
  S0 뼈대 서버는 `GET /api/compare`·`PUT /api/records`를 `fixtures/*.response.json` 내용으로 응답한다(= Mock, D-007). api 슬라이스가 끝나면 같은 명령이 실제 응답을 낸다.
- 검증: 브라우저에서 SPEC F2·F1 완료 기준 시나리오(김민수 3회 · 박지훈 1회+오늘 · 저장 후 "오늘" 칸 반영). 빈 상태는 `--data /tmp/없음.json`(없는 파일)로, 에러 상태는 `fixtures/error.response.json` 모양으로 확인. 콘솔 에러 0.
- 순서: Mock 응답으로 화면을 완성 → 마지막에 실제 서버로 같은 시나리오(루트 통합 체크포인트에서 확인).

## 규칙
- 계약(CONTRACT.md)을 바꾸지 않는다. 바꿔야 하면 `docs/TASKS.md` BLOCKER에 적고 멈춘다.
- D: 다른 모듈 코드를 열지 않는다. `fixtures/` 샘플로 화면·출력을 먼저 완성하고 마지막에 연결한다. 빈 상태·에러 상태도 보이게.
- 화면 글자는 GLOSSARY 용어 그대로(선수·연습·핵심 메시지 전달·부정적 표현 회피·답변 길이·상·중·하·메모). 점수·그래프·자동 판정 없음(SPEC 4절).
- 입력 검증의 원본은 api다. 화면은 `required` 정도만 하고, 400 응답의 `error` 문구를 그대로 보여준다.
- 루트 `CLAUDE.md`의 작은 코드 원칙이 그대로 적용된다.
- 끝낼 때 보고: 검증 명령과 출력, 바꾼 파일, `추가하지 않은 것:`, `확인하지 못한 것·리스크:`
