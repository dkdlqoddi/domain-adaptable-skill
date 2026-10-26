# TASKS — 작업 보드

## 시간 계획 (시작 17:21, 총 6h → 종료 23:21)
| 단계 | 마감 시각 | 할 일 | 명령 |
|---|---|---|---|
| 1 탐색·정의 | 18:21 | 인터뷰, SPEC 초안. **코딩 금지** | `/interview` 반복 |
| 2 계약·뼈대 | 19:21 | SPEC·CONTRACT 확정, 모듈 지침, 걸어다니는 뼈대(S0) | `/spec` `/workspace` `/delegate S0` |
| 3 슬라이스 구현 | 22:06 | P0 슬라이스 위임→검증→정리→기록, 매시간 통합 확인 | `/delegate` `/verify` `/lean` `/decide` |
| 4 마무리·복기 | 23:21 | 잔재 정리, 화면 확인, 복기 문서 | `/wrapup` |

> 슬라이스 = 끝까지 동작하는 가장 작은 기능 조각. P0부터. 상태: TODO / DOING / DONE / BLOCKED.
> 자기 행만 수정한다. 검증 명령이 없는 슬라이스는 시작하지 않는다.

## 슬라이스
| ID | 슬라이스 | SPEC | 쓰기 범위(폴더) | 검증 명령 | 상태 | 담당 |
|---|---|---|---|---|---|---|
| S0 | 걸어다니는 뼈대: 인자 2개를 받아 첫 줄과 세 칸(모두 `없음`)을 출력하고 머리 줄만 있는 `<날짜>.tsv`를 쓴다. 내용은 하드코딩이어도 된다 | CONTRACT C·D | `regsum.py` | `h=$(mktemp -d); python3 regsum.py samples/2026-10-24 $h \| grep -c '^\['; head -1 $h/2026-10-24.tsv` → `3`과 머리 줄 | DONE | S0 서브에이전트 |
| S1 | 실패 로그·끊긴 로그 찾기, 묶음 기준 줄, 묶기, 보관 행 쓰기(비교 없음 = 전부 새로 생김) | F1·F2, CONTRACT A·C·D | `regsum.py`, `test_regsum.py` | `python3 -m unittest -q test_regsum && h=$(mktemp -d) && python3 regsum.py samples/2026-10-24 $h \| diff - fixtures/expected/2026-10-24.txt && diff $h/2026-10-24.tsv fixtures/history/2026-10-24.tsv` | DONE | S1 서브에이전트 |
| S2 | 비교 기준 고르기, 새로 생김/계속 남음 나누기, seed 수 변화 표시 | F3, CONTRACT C·D | `regsum.py`, `test_regsum.py` | `bash fixtures/check.sh` → ①②③ PASS | DONE | S2 서브에이전트 |
| S3 | CONTRACT C 표의 오류 경로(종료코드 2, 경고), 보관 파일 임시 파일→이름 바꾸기 | F3, CONTRACT C·D | `regsum.py`, `test_regsum.py` | `bash fixtures/check.sh` → ①~④ PASS(⑤는 F7 슬라이스 몫). ④에 없는 오류 행(인자 수, 폴더 이름, `.log` 0개, 이름 모양)은 손으로 1회씩 | DONE | S3 서브에이전트 |
| S4 | (P1, S3 다음) 나눠 올리기: 글이 4000바이트를 넘는 날에만 묶음 줄 경계에서 메시지 N개로 나눈다. 보관 파일은 나누지 않는다 | F7, CONTRACT C "나눠 올리기", D-007 | `regsum.py`, `test_regsum.py` | `python3 -m unittest -q test_regsum && bash fixtures/check.sh` → ①~⑤ PASS | DONE | S4 서브에이전트 |

## BLOCKER (계약 변경 요청 — 루트가 처리)
| 시각 | 모듈 | 필요한 변경 | 이유 | 처리(DECISIONS 번호) |
|---|---|---|---|---|

## 통합 체크포인트 (매시간)
> 확인 명령: `bash fixtures/check.sh` (`fixtures/check.sh`는 루트 소유, 슬라이스에서는 읽기 전용)

| 시각 | 확인한 것 | 결과 |
|---|---|---|
| 18:12 | /verify all: S0·S1·S2·S3 검증 명령, check.sh ①~⑤, S3 손 확인 오류 4행 + 인자 3개, 24→25 보관 파일 왕복(글·TSV diff 0), 같은 날짜 재실행, 임시 파일 잔재 | S0~S3 PASS, check.sh ①~④ PASS, ⑤ FAIL(S4 TODO — 예상대로). 수정 없음 |
| wrapup | /wrapup all: 단위 테스트 19개, check.sh ①~⑤, 손 확인 오류 4행 + 인자 3개, 같은 날짜 재실행·`.tmp` 잔재, `LANG=C` 출력 동일, 합성 로그 300개(0.03초, 메시지 10개 모두 4000바이트 이하), 잔재 grep 0건 | 전부 PASS. Python 3.6 실행은 확인 못 함(로컬 3.10). README 사용법 추가, RETRO 작성 |
