# api 지침

역할: C 컨트롤러(+ 파일 저장) — HTTP 요청을 받아 기록 파일(`data/records.json`)을 읽고 쓰고, `ui/`를 정적으로 서빙한다. Python 3 표준 라이브러리만(`http.server`, `json`, `argparse`, `tempfile`).

## 범위
- 쓰기: `api/**`, `docs/TASKS.md`(내 행만)
- 읽기 전용: `docs/CONTRACT.md`(A·B·C·D절), `docs/SPEC.md`(3절 P0, 5절 제약), `fixtures/*.json`
- 열지 않음: `ui/**` 전부(파일을 그대로 서빙만 한다), `data/`(선수 실명). 화면의 동작은 CONTRACT B절의 샘플 값으로 대신한다.

## 실행·검증
- 실행: `cp fixtures/records.sample.json /tmp/records.json && python3 api/server.py --data /tmp/records.json`
- 검증: `python3 -m unittest discover -s api -p 'test_*.py'` — 슬라이스를 끝내기 전에 반드시 통과시킨다.
- 순서: `fixtures/records.sample.json` → `fixtures/*.response.json`이 **계산으로** 나오게 먼저 맞추고 → curl 1회 왕복.
- 테스트는 포트 8765를 쓰지 않는다(임시 포트 0). 픽스처는 읽기만, 쓰기 테스트는 `tempfile`에 복사해서 한다.

## 규칙
- 계약(CONTRACT.md)을 바꾸지 않는다. 바꿔야 하면 `docs/TASKS.md` BLOCKER에 적고 멈춘다.
- C: 상태는 CONTRACT 전이표에 있는 것만(전이표가 없으므로 상태 없음). 재시도·큐·락·캐시·로깅 설정은 SPEC에 없으면 넣지 않는다.
- 신뢰 경계: 요청 본문 검증(A절)은 여기서만 한다. 에러 문구는 코치가 읽을 한국어 한 문장 + `field`.
- 데이터 유실 방지: 쓰기는 임시 파일 → `os.replace`. 손상된 파일은 덮어쓰지 않고 시작을 거부한다(exit 1, stderr 한 줄).
- 루트 `CLAUDE.md`의 작은 코드 원칙이 그대로 적용된다.
- 끝낼 때 보고: 검증 명령과 출력, 바꾼 파일, `추가하지 않은 것:`, `확인하지 못한 것·리스크:`
