# TASKS — 작업 보드

> 슬라이스 = 끝까지 동작하는 가장 작은 기능 조각. P0부터. 상태: TODO / DOING / DONE / BLOCKED.
> 자기 행만 수정한다. 검증 명령이 없는 슬라이스는 시작하지 않는다.
> 작업판 확정: `/workspace all` 2026-10-23 (리허설 모드 — 결정 지점은 추천안 + `(가정)`, D-007·D-008).

## 시간 계획 (시작 18:51, 총 6h, 2026-10-23)
| 단계 | 마감 | 할 일 |
|---|---|---|
| 1 탐색·정의 | 19:51 | 인터뷰, SPEC 초안. 코딩 금지 |
| 2 계약·뼈대 | 20:51 | SPEC·CONTRACT 확정, 모듈 지침, S0 |
| 3 슬라이스 구현 | 23:36 | P0 슬라이스 위임→검증→정리→기록, 매시간 통합 확인 |
| 4 마무리·복기 | 00:51 | 잔재 정리, 화면 확인, 복기 문서 |

## 모듈 (CONTRACT "모듈과 경계" 그대로. 지침: `api/CLAUDE.md`, `ui/CLAUDE.md`)
| 폴더 | 아키타입 | 쓰기 | 읽기 전용 | 열지 않음 | 실행 명령 | 검증 명령 |
|---|---|---|---|---|---|---|
| `api/` | C 컨트롤러(+파일 저장) | `api/**` | CONTRACT A·B·C·D, SPEC P0·5절, `fixtures/*.json` | `ui/**`, `data/` | `UP` | `TEST` |
| `ui/` | D 인터페이스 | `ui/**` | CONTRACT A·B, SPEC F1·F2·4·5절, `fixtures/*.response.json`, GLOSSARY | `api/**` | `UP` → http://localhost:8765 | 브라우저 시나리오(SPEC F2·F1 완료 기준) |

## 검증 명령 약어 (아래 표에서 쓰는 이름)
- `UP` = `cp fixtures/records.sample.json /tmp/records.json && python3 api/server.py --data /tmp/records.json` — 픽스처 사본으로 서버 기동(픽스처를 더럽히지 않음). 끝나면 Ctrl+C.
- `TEST` = `python3 -m unittest discover -s api -p 'test_*.py'`
- `SMOKE` = 서버를 띄워 curl 한 번 하고 끈다: `cp fixtures/records.sample.json /tmp/records.json && (python3 api/server.py --data /tmp/records.json & P=$!; sleep 1; curl -s localhost:8765/api/players; echo; curl -s -o /dev/null -w 'GET / → %{http_code}\n' localhost:8765/; kill $P)`

## 슬라이스
| ID | 슬라이스 | SPEC | 쓰기 범위(폴더) | 검증 명령 | 상태 | 담당 |
|---|---|---|---|---|---|---|
| S0 | 걸어다니는 뼈대: `python3 api/server.py --data`로 서버가 뜨고(파일 없음=빈 상태, 손상·version≠1=stderr 한 줄+exit 1), `GET /`가 `ui/index.html`을, `GET /api/players`가 파일에서 **계산한** 선수 목록을 돌려주고, 화면의 선수 선택 목록이 그 응답으로 채워진다. **스텁**(`# S0 stub`, 파일 안 봄, S1·S3에서 교체): `GET /api/compare` player=김민수→`fixtures/compare.response.json`, 박지훈→`fixtures/compare.today.response.json`, 그 외→`today:null, previous:[]`. `PUT /api/records`→`fixtures/record.put.response.json` | F2 일부 | `api/**`, `ui/**` (뼈대라서 두 폴더를 한 에이전트가 순차로. 이후 슬라이스는 한 폴더씩) | `TEST`(records.sample → players.response 일치, 임시 포트로 `GET /` 200 왕복 1회) + `SMOKE` | DONE | 서브에이전트(루트 위임) 2026-10-23 |
| S1 | api 비교: `GET /api/compare?player&date` — `today`(그 날짜 기록 또는 `null`), `previous`(그 날짜보다 앞선 기록 최신 3건, 최신 먼저), `date` 생략=서버의 오늘, 400(`player` 누락·빈 값, `date` 형식), 모르는 선수=`previous: []`. 스텁 제거 | F2 | `api/**` | `TEST`(records.sample → compare.response·compare.today.response 일치, 400 2종, 모르는 선수 `[]`, 09-25 제외) | TODO | |
| S2 | ui 비교 화면: 선수를 고르면 지난 세 번 연습의 항목 3개 상·중·하가 한 화면(연습 날짜 열 × 항목 행)에 보인다. 3회 미만은 있는 만큼, 기록 없음·선수 없음은 빈 상태 문구. S0 스텁 응답으로 먼저 완성 | F2 | `ui/**` | `UP` → 브라우저: 김민수=10-16·10-09·10-02 보이고 09-25 안 보임, 박지훈=1회·레이아웃 정상, 이서준=2회, `--data /tmp/없음.json`=빈 상태 문구, 콘솔 에러 0 | TODO | |
| S3 | api 저장: `PUT /api/records` — A절 검증(필드 누락·30자·날짜·상중하·200자·줄바꿈·그 외 키 → 400 에러 형식), 같은 `(player, date)` 덮어쓰기 `replaced:true`, `(date, player)` 정렬 저장, 임시 파일→`os.replace`, 디렉터리 없으면 생성, 413(64KB), 500 시 기존 파일 보존, 그 외 `/api/*` 404·405. 스텁 제거 | F1 | `api/**` | `TEST`(record.put → record.put.response + 파일 9건 정렬, 같은 것 재PUT→`replaced:true`·9건 유지, record.put.invalid → error.response, 그 외 키 400, JSON 아님 400) + `UP` 후 `curl -s -X PUT localhost:8765/api/records -H 'Content-Type: application/json' -d @fixtures/record.put.json` → `replaced:false` | TODO | |
| S4 | ui 입력·저장: 같은 화면에서 날짜(기본 오늘, 바꿀 수 있음)·항목 3개 상·중·하를 골라 저장하면 지난 세 번 옆 "오늘" 칸에 바로 반영. `today`가 있으면 입력란에 기존 값 먼저 채움(D-004). 400이면 `error` 문구 표시 | F1 | `ui/**` | `UP` → 브라우저: 박지훈=입력란 사전 채움(중·중·중), 김민수 상·상·상 저장→"오늘" 칸 반영, 날짜 바꿔 저장, 한 항목 비우고 저장→문구 표시, 콘솔 에러 0 | TODO | |
| S5 | (P1 TODO) 메모: 입력란 한 줄(200자)과 지난 연습 칸마다 메모 표시. api는 v1부터 `memo`를 저장·검증(D-006)하므로 ui만 | F3 | `ui/**` | `UP` → 브라우저: 김민수 지난 메모 3개 보임, 메모 넣어 저장→오늘 칸에 보임, 비워도 저장 | TODO | |

순서: S0 → (S1 ‖ S2) → (S3 ‖ S4) → S5. `‖`는 쓰기 범위가 다르므로 `/delegate --parallel`(worktree) 가능. ui 슬라이스의 "실제 서버 연결" 확인은 api 슬라이스가 DONE된 뒤 통합 체크포인트에서 루트가 한다(Playwright, D-008).

S0 인계(2026-10-23): 브라우저가 `/favicon.ico`를 자동 요청해 404 콘솔 에러 1건이 난다 → S2에서 `<link rel="icon" href="data:,">` 한 줄로 없앤다(가정). Windows 미확인 리스크(A9): stdout을 리다이렉트하면 첫 줄의 "—"가 cp949로 인코딩되지 않을 수 있고, `allow_reuse_address` 때문에 "포트 사용 중 → exit 1"이 동작하지 않을 수 있다. `/verify`(20:49) 추가: S0의 `fetch('/api/players')`에 실패 처리(`.catch`)가 없어 서버가 꺼져 있으면 콘솔에 unhandled rejection만 남는다 → S2에서 빈 상태·에러 문구와 함께 처리한다(가정). `/lean`(20:54) 추가: `test_broken_file_refuses_start`는 `main()`을 직접 불러 검증 실패에 기대므로, 검증을 통과하는 입력이 들어가면 8765에 바인드해 테스트가 끝나지 않는다 → S3에서 `read_records`를 고칠 때 이 테스트도 같이 본다(가정).

## BLOCKER (계약 변경 요청 — 루트가 처리)
| 시각 | 모듈 | 필요한 변경 | 이유 | 처리(DECISIONS 번호) |
|---|---|---|---|---|

## 통합 체크포인트 (매시간)
| 시각 | 확인한 것 | 결과 |
|---|---|---|
| 2026-10-23 20:41 | S0 통합: TEST·SMOKE 루트 재실행, 스텁 3종=픽스처, 경로 탈출·없는 파일 404, 손상·version≠1 → exit 1(파일 보존), Playwright: 선수 3명 가나다순·빈 상태 0명·콘솔 에러는 favicon 404 1건뿐 | 통과 |
| 2026-10-23 20:49 | `/verify all`(리허설, 루트): S0 TEST 4/4·SMOKE 통과. curl 왕복 8종(players·compare 스텁 3종·PUT 스텁·`GET /`=index.html·404 3종·포트 사용 중→exit 1) 계약 일치. 손상 파일 3종(JSON 아님·version 2·UTF-8 아님)→exit 1·stderr 1줄·파일 보존, 없는 파일→빈 상태·파일 안 만듦. Playwright: 선수 3명 가나다순, 빈 상태 0명·빈 문구 없음(S2), 콘솔 에러 favicon 404 1건뿐(S2 제거), 인라인 JS 문법 OK. 스크린샷 `.playwright-mcp/verify-s0-*.png`(폴더를 .gitignore에 추가, 가정) | 통과 |
| 2026-10-23 20:54 | `/lean diff`(리허설, 루트): S0 코드 diff 덩어리 13개를 SPEC F2·CONTRACT B·C·D·브리프와 대조. 흔한 후보(옵션·캐시·재시도·락·로깅·추상화) 0건, 근거 없는 사소한 것 3건(argparse help 문자열·body 스타일 1줄·`finally: server_close()`)은 유지(D-010). `shortcut:` 2건·`# S0 stub` 3건 표식 확인. TEST 4/4·SMOKE 재실행 통과 | 삭제·축소 0건 |
| 2026-10-23 21:02 | `/wrapup all`(리허설, 루트): TEST 4/4·SMOKE 재실행 통과(코드는 S0 커밋 1d04dda 이후 변경 없음 → curl 8종·손상 파일 3종은 20:49 결과 재사용). Playwright 재확인(사람 눈 확인은 리허설이라 루트가 대신, 가정): 첫 화면 선수 3명 가나다순·콘솔 에러 favicon 404 1건뿐, 빈 상태(`--data /tmp/없음.json`) 목록 비고 콘솔 에러 0·파일 안 만듦(스크린샷 `.playwright-mcp/wrapup-*.png`). README에 설치→실행→확인 3단계 추가. 잔재 grep: 삭제 대상 0건(`print(`은 CONTRACT C 첫 줄, `# S0 stub`은 S1·S3 교체 대상), 미추적 `api/__pycache__/`만 삭제. shortcut 2건+인계 리스크 → RETRO 7절. `docs/RETRO.md` 9절 작성 | 통과 (P0 미완 상태의 리허설 — 실제 마감이면 제출 불가) |
