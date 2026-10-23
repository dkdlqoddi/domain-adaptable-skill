# CONTRACT — 모듈 간 인터페이스 계약 (v2)

> **루트 세션만 수정.** 모듈 작업 중 변경이 필요하면 `TASKS.md`의 BLOCKER에 적고 멈춘다.
> 모듈은 서로의 코드가 아니라 이 문서와 `fixtures/`의 샘플을 보고 개발·검증한다. 이름은 `GLOSSARY.md`의 "코드 표기" 열을 따른다(D-003).

## 모듈과 경계
| 모듈(폴더) | 아키타입 | 입력 | 출력 |
|---|---|---|---|
| `api/` | C 컨트롤러(+ 파일 저장) — Python 3 표준 라이브러리만 | HTTP 요청(B), `data/records.json`(D) | JSON 응답(B), `data/records.json` 갱신(D), `ui/` 정적 파일 서빙 |
| `ui/` | D 인터페이스 — HTML/CSS/JS 한 장, 빌드·패키지 없음 | `GET /api/players`, `GET /api/compare` 응답 | 비교 화면, `PUT /api/records` 요청 |

- 둘로 나누는 이유: 검증 방법이 다르다(api = curl·unittest, ui = 브라우저). 병렬 개발 가능(ui는 `fixtures/*.response.json`을 Mock으로 먼저 완성).
- 공유 모듈(E)은 두지 않는다. 스키마는 이 문서 A절이 유일한 원본. 상태 전이(E절)는 없다 — 큐·재시도·락 없음.
- 상수: 비교 범위 = 3회(`previous` 최대 길이). 포트 = 8765.

## A. 공통 데이터 스키마 — 기록(`record`)
선수 한 명 × 연습 날짜 하나 = 기록 1건. 같은 `(player, date)`는 하나만 존재한다.

```json
{
  "player": "김민수",
  "date": "2026-10-16",
  "items": { "key_message": "상", "avoid_negative": "상", "answer_length": "중" },
  "memo": "세 가지 모두 안정적. 다음엔 돌발 질문 추가"
}
```

| 필드 | 용어 | 타입·규칙(검증은 `api/`가 한다 — 신뢰 경계) |
|---|---|---|
| `player` | 선수 | 문자열. 앞뒤 공백 제거 후 1~30자, 줄바꿈 없음. 이름 그대로가 식별자(D-005) |
| `date` | 연습 날짜 | `YYYY-MM-DD` 실제 날짜. 미래 날짜도 허용(가정) |
| `items` | 체크리스트 | 객체. 키는 정확히 세 개: `key_message`(핵심 메시지 전달) · `avoid_negative`(부정적 표현 회피) · `answer_length`(답변 길이). 값은 각각 `"상"` `"중"` `"하"` 중 하나 — 한글 그대로 저장, 숫자로 바꾸지 않는다. 셋 다 있어야 한다(가정 A2) |
| `memo` | 메모 | 문자열 0~200자, 줄바꿈 없음. 생략하면 `""` |
| 그 외 키 | — | 거부(400). 계약 밖 필드가 스며드는 것을 막는다 |

## B. API (`api/`가 제공, `ui/`가 소비)
모든 JSON 응답은 `Content-Type: application/json; charset=utf-8`, 한글은 이스케이프하지 않는다. 쿼리의 한글은 URL 인코딩한다(`김민수` → `%EA%B9%80%EB%AF%BC%EC%88%98`).

| Method | Path | 요청(샘플) | 응답(샘플) | 에러 |
|---|---|---|---|---|
| GET | `/`, `/<파일>` | — | `ui/index.html` 등 `ui/` 안의 파일 | 404 없는 파일·`ui/` 밖 경로 |
| GET | `/api/players` | — | `200 {"players":["김민수","박지훈","이서준"]}` — 기록이 있는 선수 이름, 가나다순, 중복 없음. 기록이 없으면 `{"players":[]}` → `fixtures/players.response.json` | — |
| GET | `/api/compare?player=<이름>&date=<YYYY-MM-DD>` | `?player=김민수&date=2026-10-23` | `200 {"player":"김민수","date":"2026-10-23","today":null,"previous":[<10-16>,<10-09>,<10-02>]}` → `fixtures/compare.response.json`. `today` = 그 날짜의 기록 또는 `null`. `previous` = `date`보다 앞선 기록 중 최신 3건, 최신 먼저(3회 미만이면 있는 만큼, 없으면 `[]`). 오늘 것이 이미 있는 경우 → `fixtures/compare.today.response.json`(박지훈) | 400 `player` 누락·빈 값 / 400 `date` 형식 오류. `date` 생략 시 서버의 오늘. 모르는 선수는 에러가 아니라 `previous: []`(첫 참여) |
| PUT | `/api/records` | A절 기록 1건 → `fixtures/record.put.json` | `200 {"record":<저장된 기록>,"replaced":false}` → `fixtures/record.put.response.json`. 같은 `(player, date)`가 있었으면 덮어쓰고 `"replaced":true`(D-004). 저장된 기록은 공백 정리 후 값 | 400 검증 실패(아래 에러 형식; `fixtures/record.put.invalid.json` → `fixtures/error.response.json`) / 400 JSON 아님 / 413 본문 64KB 초과 / 500 파일 쓰기 실패(기존 파일은 보존) |
| * | 그 외 `/api/*` | — | — | 404 `{"error":"없는 경로입니다"}` / 405 메서드 불일치 |

에러 형식(4xx·5xx 공통): `{"error":"<코치가 읽을 한국어 한 문장>","field":"<문제 필드. 없으면 생략>"}`
```json
{ "error": "items.answer_length 값은 상·중·하 중 하나여야 합니다", "field": "items.answer_length" }
```

## C. CLI — 실행 명령 (제출물 "실행 방법")
| 명령 | 인자·플래그 | 표준출력(샘플) | 종료코드 |
|---|---|---|---|
| `python3 api/server.py` | `--data <경로>` 기록 파일(기본 `data/records.json`). 다른 옵션 없음 | 첫 줄 `인터뷰 연습 기록 — http://localhost:8765  (기록 파일: data/records.json)`, 이후 요청 로그 | 0 Ctrl+C로 종료 / 1 시작 실패(기록 파일 손상, 포트 8765 사용 중 — 이유를 stderr에 한 줄) |

- 데모·검증은 픽스처를 **복사해서** 띄운다(픽스처를 더럽히지 않음): `cp fixtures/records.sample.json /tmp/records.json && python3 api/server.py --data /tmp/records.json`
- 테스트: `python3 -m unittest discover -s api -p 'test_*.py'`. 슬라이스별 검증 명령은 `TASKS.md`.

## D. 파일 포맷 — 기록 파일
| 파일 | 생산자 → 소비자 | 포맷·패턴 | 샘플 위치(fixtures/) |
|---|---|---|---|
| `data/records.json` | `api/` → `api/` (사람이 직접 열어 보거나 고칠 수도 있다 — F8 대안) | UTF-8 JSON, 들여쓰기 2, 한글 그대로. `{"version":1,"records":[<A절 기록>…]}`. `records`는 `(date, player)` 오름차순으로 저장 | `fixtures/records.sample.json` — 선수 3명·기록 8건: 김민수 4회(→3회 제한 확인), 이서준 2회(메모 빈 것 포함), 박지훈 2회 중 1건이 2026-10-23 "오늘" |

- 없으면 첫 저장 때 디렉터리와 함께 만든다. 서버 시작 시 파일이 없는 것은 정상(빈 상태).
- 쓰기는 임시 파일에 전체를 쓴 뒤 `os.replace`로 교체한다. 중간에 꺼져도 직전 파일이 남는다.
- 읽기 실패(JSON 파싱 오류, `version` 불일치)면 서버는 시작하지 않고 경로를 알린다. **절대 빈 파일로 덮어쓰지 않는다.**
- `data/`는 `.gitignore`에 넣는다 — 선수 실명이 들어간 파일은 저장소에 올리지 않는다.

## 픽스처 목록
| 파일 | 무엇 | 쓰는 모듈 |
|---|---|---|
| `fixtures/records.sample.json` | D절 기록 파일 샘플(8건) | api 테스트 입력, 데모 |
| `fixtures/players.response.json` | `GET /api/players` 응답 | api 기대값, ui Mock |
| `fixtures/compare.response.json` | `GET /api/compare?player=김민수&date=2026-10-23` 응답(today 없음, previous 3) | api 기대값, ui Mock |
| `fixtures/compare.today.response.json` | `GET /api/compare?player=박지훈&date=2026-10-23` 응답(today 있음, previous 1) | api 기대값, ui Mock(사전 채움·3회 미만) |
| `fixtures/record.put.json` | `PUT /api/records` 요청 본문 | api 테스트, curl 검증 |
| `fixtures/record.put.response.json` | 위 요청의 응답 | api 기대값 |
| `fixtures/record.put.invalid.json` | 잘못된 요청(`answer_length: "최상"`) | api 테스트 |
| `fixtures/error.response.json` | 위 요청의 400 응답 | api 기대값, ui 에러 표시 |

검증 규칙: `records.sample.json`에서 두 compare 응답과 players 응답이 **계산으로 나와야** 한다(api 테스트가 이것을 확인한다).

## 변경 이력
| 버전 | 변경 | 이유(DECISIONS 번호) |
|---|---|---|
| v1 | 최초 확정 | |
| v1 | D. 파일 포맷: 코칭 기록 저장소 = 로컬 JSON 파일 1개 (경로·스키마는 미정) | D-001 |
| v2 | 전체 확정: 모듈 2개(`api/`·`ui/`), A 기록 스키마, B API 4종, C 실행 명령, D 파일 경로·스키마·원자적 쓰기. E 상태 전이 삭제(큐 없음). 픽스처 8개 | D-002 실행 형태, D-003 코드 이름, D-004 덮어쓰기, D-005 선수 식별, D-006 메모 스키마 포함 |
