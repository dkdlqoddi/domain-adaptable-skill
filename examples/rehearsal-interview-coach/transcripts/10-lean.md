`/lean diff` 결과: **S0 diff에서 삭제·축소할 덩어리는 0건**입니다. 검토 기록을 D-010과 TASKS 체크포인트에 남기고 커밋했습니다(`ebb86bc`).

**대상 diff**: 작업 트리가 깨끗해 직전 슬라이스 커밋 S0(`26503a8..1d04dda`)의 코드 diff를 읽었고, 그 뒤 verify·harness 커밋은 문서·`.gitignore`뿐이라 후보가 없었습니다(가정).

## 덩어리별 대조

| 파일:범위 | 무엇 | 근거 | 제안 | 이유 |
|---|---|---|---|---|
| server.py:1-11 | 모듈 docstring, import 7개 | CONTRACT C(`--data`)·B(쿼리), 브리프 허용 목록 | 유지 | 전부 사용 중. `datetime`·`parse_qs`는 스텁 전용 |
| server.py:13-16 | `PORT`·`ROOT`·`UI_DIR`·`FIXTURES` | CONTRACT 상수 8765, 브리프 경로 규칙 | 유지 | `FIXTURES`는 "S1·S3에서 지운다" 표식 있음 |
| server.py:19-30 | `read_records`: 없음=[], 손상→한 줄 ValueError, version·records 검사 | SPEC 5절, CONTRACT D | 유지 | 신뢰 경계·데이터 보호. `OSError`도 "stderr 한 줄" 계약(C)을 위해 필요 |
| server.py:33-35 | `list_players` | CONTRACT B | 유지 | 한 줄 |
| server.py:41-45 | `GET /api/players` 요청마다 읽기 | CONTRACT B "캐시 없음" | 유지 | shortcut 주석 있음 |
| server.py:46-55 | compare 스텁(픽스처 2종·빈 응답·date 기본 오늘) | D-007, TASKS S0 | 유지 | S1이 교체. 브리프 명세 그대로 |
| server.py:59-65 | PUT 스텁 + 경로 404 가드 2줄 | D-007 | 유지 | 가드가 없으면 모든 PUT이 픽스처를 돌려줌. S3이 404·405 JSON으로 교체 |
| server.py:67-73 | `send_json` 헤더 2개·`ensure_ascii=False` | CONTRACT B | 유지 | |
| server.py:76-81 | `make_server`: `ThreadingHTTPServer`, 127.0.0.1, `port` 인자 | D-009, 브리프(테스트 포트 0) | 유지 | `port`는 테스트가 씀, "나중을 위한" 파라미터 아님 |
| server.py:84-104 | `main`: `--data`만, 바인드 전 검증, 포트 오류 한 줄, 첫 줄 flush, Ctrl+C | CONTRACT C | 유지 | `description`·`help` 문자열과 `finally: server_close()`만 근거 없음 → 아래 |
| test_server.py 전체 | 테스트 4개 + Content-Type·한글·index.html 본문 단언, 손상 3종 | 브리프 ①~④, CONTRACT B·C·D | 유지 | 추가 단언은 전부 계약 항목 |
| index.html:1-5, 12-23 | 골격·label·select·fetch | 브리프 | 유지 | `.catch` 없음은 이미 S2 인계 |
| index.html:6-8, 11 | `body` 스타일 1줄, `<h1>` | 없음(브리프 "필요 최소") | 유지 | h1은 접근성. 스타일은 아래 |

## 축소·삭제 묶음 결정 (가정)

근거 없이 들어온 것은 3건뿐이고, 셋 다 사다리 1칸(기능·옵션·확장성·추상화)에 해당하지 않아 **유지**로 정했습니다.

- **argparse `description`·`help` 문자열**: `--help`는 argparse 기본 동작이라 옵션 추가가 아닙니다.
- **`body` 스타일 1줄**: 지우면 S2가 비교 표를 만들 때 되돌리는 왕복만 생깁니다.
- **`finally: server_close()`**: `with` 문과 같은 길이의 표준 종료 절차입니다.

흔한 후보(옵션·환경변수·캐시·재시도·락·로깅 설정·라우터 추상화·범용 에러 래퍼)는 S0 브리프의 "하지 말 것"이 사전에 막아 diff에 아예 없었습니다. `ThreadingHTTPServer`는 D-009에서 이미 대안 비교를 거쳤습니다.

## 기록·검증

- TEST 4/4, SMOKE(선수 3명·`GET /` 200) 재실행 통과.
- `shortcut:` 2건, `# S0 stub` 3건 표식 확인. 새로 달 지름길 없음.
- `docs/DECISIONS.md`에 D-010(유지 결정과 다시 볼 조건: S1·S3이 스텁을 지울 때 `datetime`·`parse_qs`·`FIXTURES` 미사용 여부), `docs/TASKS.md`에 체크포인트 행과 S0 인계 한 줄 추가.

추가하지 않은 것: 코드 변경 0건. 테스트 보강이나 스타일 정리는 lean 범위 밖이라 손대지 않았다.
확인하지 못한 것·리스크: `test_broken_file_refuses_start`는 `main()`을 직접 불러 검증 실패에 기대므로, 검증이 통과하는 입력이 들어가면 8765에 바인드해 테스트가 끝나지 않는다(S3 인계에 적음). 유지한 3건은 사람 확인 없이 추천안으로 정했다.
