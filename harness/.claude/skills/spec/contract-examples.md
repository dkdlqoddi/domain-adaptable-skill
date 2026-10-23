# CONTRACT.md 작성 예시 (도메인별)

공통 원칙: 섹션마다 **샘플 값 1개**를 넣고 그 샘플을 `fixtures/`에 파일로 저장한다. 모듈은 상대 모듈의 코드가 아니라 이 샘플로 개발하고 검증한다.

## 1. 웹 애플리케이션 (ui ↔ api)
| Method | Path | 요청(샘플) | 응답(샘플) | 에러 |
|---|---|---|---|---|
| POST | /api/feedback | `{"answerId":"a1","text":"..."}` | `201 {"id":"f1","score":4,"comment":"..."}` | 400 필드 누락 / 404 answerId 없음 |

샘플: `fixtures/feedback.response.json`. ui는 이 파일을 Mock으로 읽어 화면을 먼저 완성하고, api가 DONE이 되면 주소만 바꾼다.

## 2. CLI 도구 / 데이터 파이프라인 (ingest → transform → report)
| 단계 | 명령 | 입력 | 출력 | 종료코드 |
|---|---|---|---|---|
| transform | `tool transform --in raw.csv --out clean.csv` | CSV(열: id,ts,value) | CSV(같은 열 + flag) | 0 정상 / 2 스키마 불일치 |

샘플: `fixtures/raw.sample.csv`(10행), `fixtures/clean.expected.csv`. 검증 = 샘플 입력 → 기대 출력과 diff.

## 3. 외부 도구 제어 (예: EDA 툴 — generator → runner → parser)
| 산출물 | 생산자 → 소비자 | 포맷·패턴 | 샘플 |
|---|---|---|---|
| 제어 스크립트 | generator → runner | `.tcl`, 명령 순서 고정 | `fixtures/run.expected.tcl` |
| 실행 로그 | runner(툴) → parser | 텍스트, `^Slack\s*:\s*(-?\d+\.\d+)` | `fixtures/sta.sample.log` |
| 요약 리포트 | parser → report | JSON `{"wns":-0.12,"tns":-3.4,"violations":17}` | `fixtures/summary.expected.json` |

실제 툴·라이선스가 없어도 개발된다: runner는 `--dry-run`이면 샘플 로그를 그대로 내놓는다. 실제 연동은 마지막 슬라이스.

## 4. 함수 경계 (모듈 하나짜리 프로젝트)
| 함수 | 입력 | 출력 | 예외 |
|---|---|---|---|
| `score(answer: str, rubric: Rubric) -> Score` | 비어 있지 않은 문자열, Rubric | 0~5 정수 + 코멘트 | `ValueError` 빈 입력 |

모듈이 하나면 CONTRACT는 이 표 하나로 충분하다. 억지로 모듈을 나누지 않는다.

## 5. 상태 전이가 있을 때 (작업 큐, 파이프라인)
| 상태 | 전이 조건 | 다음 상태 | 실패 시 |
|---|---|---|---|
| QUEUED | 워커가 집음 | RUNNING | - |
| RUNNING | 종료코드 0 | DONE | FAILED (재시도 없음 — SPEC 비목표) |

전이표에 없는 상태는 코드에도 없어야 한다.
