# CONTRACT — 모듈 간 인터페이스 계약

> **루트 세션만 수정.** 모듈 작업 중 변경이 필요하면 `TASKS.md`의 BLOCKER에 적고 멈춘다.
> 섹션마다 샘플 값이 있고 `fixtures/`에 파일로 있다. 구현은 이 샘플과 diff 0이 되게 만든다.

## 모듈과 경계
| 모듈(파일) | 아키타입 | 입력 | 출력 |
|---|---|---|---|
| `regsum.py` (하나) | CLI, Python 3.6 표준 라이브러리만 | 회귀 날짜 폴더, 보관 폴더 | 표준출력 = 게시용 글, 보관 폴더에 `<회귀 날짜>.tsv` |

모듈은 하나다. 검증 방법(샘플 → 기대 출력 diff)이 하나뿐이고 병렬로 나눌 만큼 크지 않다.
"모듈 사이"의 계약은 사실상 **어제의 실행 ↔ 오늘의 실행**(보관 파일)과 **도구 ↔ 사람**(CLI·글 모양)이다.

## A. 핵심 규칙 (함수 경계)
| 함수 | 입력 | 출력 | 예외 |
|---|---|---|---|
| `is_error_line(line) -> bool` | 로그 한 줄 | `UVM_ERROR ` 또는 `UVM_FATAL `로 시작하고 끝 요약 줄(`^UVM_(ERROR|FATAL)\s*:\s*\d+\s*$`)이 아니면 True | - |
| `is_truncated(lines) -> bool` | 로그 전체 줄 | `UVM Report Summary`를 포함한 줄도, `$finish`로 시작하는 줄도 없으면 True | - |
| `failure_key(line) -> str` | 첫 에러 줄 | 16진수 `0x[0-9a-fA-F]+` → `#`, 이어서 10진수 `\d+` → `#`, 탭 → 공백 | - |

`failure_key` 샘플 (`fixtures/keys.tsv`, 열: 첫 에러 줄 ⇥ 묶음 기준 줄):
```
UVM_ERROR tb/env/uart_chk.sv(203) @ 702880: uvm_test_top.env.chk [PARITY] parity error on rx byte 0x3c (lane 1)
→ UVM_ERROR tb/env/uart_chk.sv(#) @ #: uvm_test_top.env.chk [PARITY] parity error on rx byte # (lane #)
UVM_ERROR tb/env/uart_chk.sv(203) @ 640200: uvm_test_top.env.chk [PARITY] parity error on rx byte 0x5a (lane 0)
→ (위와 같음 = 같은 묶음)
UVM_ERROR tb/env/dma_scoreboard.sv(142) @ 655020: uvm_test_top.env.scb [SCB] data mismatch addr=0x00011a08 exp=0x0badf00d act=0x0badf00c
→ UVM_ERROR tb/env/dma_scoreboard.sv(#) @ #: uvm_test_top.env.scb [SCB] data mismatch addr=# exp=# act=#
```
주의: 10진수만 지우면 `0x0badf00d`가 `0xbadfd`로 남아 s202·s203이 갈라진다. 16진수를 먼저 지운다.

## C. CLI
```
python3 regsum.py <회귀 날짜 폴더> <보관 폴더>
```
- `<회귀 날짜 폴더>`: 이름이 `YYYY-MM-DD`인 폴더. 그 이름이 회귀 날짜다. 바로 아래 `*.log`만 읽는다.
- `<보관 폴더>`: 없으면 만든다. 담당자와 대리자가 같은 경로를 쓴다.
- 로그 파일 이름 `^(.+)__s(\d+)\.log$` → 테스트 이름, seed. 테스트의 전체 seed 수 = 폴더 안 그 테스트의 로그 파일 수.
- 로그는 UTF-8로 읽고 깨진 바이트는 대체 문자로 바꾼다. 출력·보관 파일은 로캘과 무관하게 UTF-8.

| 경우 | 표준출력 | 표준에러 | 종료코드 | 보관 파일 |
|---|---|---|---|---|
| 정상 (실패가 있어도) | 게시용 글 | - | 0 | `<보관 폴더>/<회귀 날짜>.tsv` 쓰기(같은 날짜면 덮어씀) |
| 이름이 `<테스트>__s<seed>.log` 모양이 아닌 `.log` | 나머지로 게시용 글 | `경고: 이름 모양이 달라 건너뜀: <파일>` | 0 | 씀 |
| 인자 수가 2개가 아님 | - | `사용법: python3 regsum.py <회귀 날짜 폴더> <보관 폴더>` | 2 | 안 씀 |
| 회귀 날짜 폴더가 없음 | - | `오류: 로그 폴더가 없습니다: <경로>` | 2 | 안 씀 |
| 폴더 이름이 `YYYY-MM-DD`가 아님 | - | `오류: 폴더 이름이 회귀 날짜(YYYY-MM-DD)가 아닙니다: <이름>` | 2 | 안 씀 |
| `.log` 파일이 0개 | - | `오류: 로그 파일이 없습니다: <경로>` | 2 | 안 씀 |
| 비교 기준 보관 파일 형식이 깨짐 | - | `오류: 보관 파일 형식이 맞지 않습니다: <파일> <N>번째 줄` | 2 | 안 씀 |

### 게시용 글 모양 (표준출력)
```
회귀 2026-10-25 정리 (비교 기준: 2026-10-24 결과)

[끊긴 로그 — LSF 시간 제한, 또는 아직 실행 중]
- axi_stress, seed 2개 중 1개(55)

[새로 생긴 실패]
- dma_burst, seed 2개 중 2개(202, 203): UVM_ERROR tb/env/dma_scoreboard.sv(142) @ 812340: uvm_test_top.env.scb [SCB] data mismatch addr=0x00004f20 exp=0xdeadbeef act=0xdeadbeee

[계속 남은 실패]
- pcie_link, seed 2개 중 1개(11): UVM_FATAL tb/env/pcie_link_mon.sv(77) @ 5000000: uvm_test_top.env.link_mon [LINK] timeout waiting for link up after 5000000 ps (ltssm=POLLING)
- uart_loop, seed 1개 중 1개(7): UVM_ERROR tb/env/uart_chk.sv(203) @ 640200: uvm_test_top.env.chk [PARITY] parity error on rx byte 0x5a (lane 0)
```
- 첫 줄: 비교 기준이 없으면 `(비교 기준: 없음, 전부 새로 생긴 실패로 표시)`.
- 세 칸은 늘 이 순서로 모두 나온다. 비어 있으면 그 칸에 `없음` 한 줄.
- 끊긴 로그: 테스트별 한 줄 `- <테스트>, seed <전체>개 중 <n>개(<seed들>)`. 에러 줄이 있으면 첫 에러 줄(가장 작은 seed)을 `: <원문>`으로 붙인다. 보관·비교하지 않는다.
- 실패 묶음 한 줄: `- <테스트>, seed <전체>개 중 <n>개(<seed들>): <가장 작은 seed의 첫 에러 줄 원문>`.
- 계속 남은 실패에서 실패 seed 수가 지난번과 다르면: `seed <전체>개 중 <지난 n>개에서 <n>개로(<seed들>)`.
- seed는 숫자 오름차순, `, `로 구분. 칸 안의 줄은 테스트 이름 → 묶음 기준 줄 순으로 정렬.
- 새로 생긴 실패 = 비교 기준에 (테스트 이름, 묶음 기준 줄)이 없는 묶음. 계속 남은 실패 = 있는 묶음.

### 나눠 올리기 (F7, D-007)
위 글 전체가 **4000바이트(UTF-8, 끝 줄바꿈 포함) 이하면 그대로** 낸다. ①~③ 기대 출력은 모두 이 경우다.
넘으면 메시지 N개로 나눠 구분 줄을 사이에 두고 이어서 낸다. 샘플(`fixtures/expected/2026-10-26_split.txt`, 줄임):
```
회귀 2026-10-26 정리 (비교 기준: 2026-10-25 결과) [1/2]

[끊긴 로그 — LSF 시간 제한, 또는 아직 실행 중]
- pcie_l1ss, seed 1개 중 1개(31)

[새로 생긴 실패]
- apb_reg, seed 2개 중 1개(3): UVM_ERROR tb/env/apb_reg_chk.sv(88) @ 41200: ...
  (… 20줄 …)
- spi_loop, seed 2개 중 1개(24): UVM_ERROR tb/env/spi_chk.sv(66) @ 404000: ...

---------- 여기서 나눠 올림 ----------

회귀 2026-10-26 정리 [2/2]

[새로 생긴 실패] (이어서)
- timer_wdt, seed 1개 중 1개(25): UVM_FATAL tb/env/wdt_mon.sv(40) @ 15000000: ...

[계속 남은 실패]
- ddr_init, seed 1개 중 1개(12): ...
```
- 메시지 하나 = 첫 줄, 빈 줄, 칸들(칸 사이 빈 줄 하나). 메시지마다 (각 줄 + `\n`)의 UTF-8 바이트 합이 4000 이하.
- 첫 줄: 1번째는 원래 첫 줄 끝에 ` [1/N]`, 2번째부터는 `회귀 <회귀 날짜> 정리 [k/N]`.
- 칸 줄(묶음 줄·`없음`)을 순서대로 넣다가 다음 줄이 한도를 넘기면 새 메시지를 시작한다(앞에서부터 꽉 채움). 줄 중간은 자르지 않는다.
- 칸 제목은 그 칸의 첫 줄과 같은 메시지에 둔다(제목만 남기지 않음). 앞 메시지에서 이어지는 칸은 새 메시지에서 제목 뒤에 ` (이어서)`를 붙여 다시 쓴다.
- 메시지 사이: 빈 줄, `---------- 여기서 나눠 올림 ----------`, 빈 줄. 구분 줄은 메시지에 들지 않는다.
- N은 `[k/N]`을 포함해 나눈 결과의 개수(자릿수가 바뀌면 다시 나눈다).
- 보관 파일은 나누지 않는다(`fixtures/expected/2026-10-26_split.tsv`). 종료코드 0.
- 처리하지 않음: 묶음 줄 하나가 혼자 한도를 넘는 경우 → 자르지 않고 그 메시지만 넘긴다 (SPEC 비목표).

## D. 파일 포맷 — 보관 파일
| 파일 | 생산자 → 소비자 | 포맷·패턴 | 샘플 위치(fixtures/) |
|---|---|---|---|
| `<보관 폴더>/<YYYY-MM-DD>.tsv` | 그날 실행 → 다음 실행 | UTF-8 TSV, 첫 줄 머리 `test⇥total⇥seeds⇥key`, 이후 실패 묶음당 한 줄. 끊긴 로그는 넣지 않음. 정렬은 게시 글과 같음 | `fixtures/history/2026-10-24.tsv`, `fixtures/expected/2026-10-25.tsv`, `fixtures/history_split/2026-10-25.tsv` |

```
test	total	seeds	key
dma_burst	2	202,203	UVM_ERROR tb/env/dma_scoreboard.sv(#) @ #: uvm_test_top.env.scb [SCB] data mismatch addr=# exp=# act=#
```
- 비교 기준 = 보관 폴더에서 이름이 `YYYY-MM-DD.tsv`이고 날짜가 이번 회귀 날짜보다 앞선 파일 중 가장 최근 것. 다른 파일은 무시.
- 형식이 깨짐 = 머리 줄이 다르거나, 열이 4개가 아니거나, total·seeds가 숫자가 아님 → 종료코드 2 (조용히 넘기면 모든 실패가 "새로 생김"이나 "계속 남음"으로 잘못 뜬다).
- 쓰기는 임시 파일에 쓴 뒤 이름 바꾸기 (중간에 죽어도 지난 보관 파일이 깨지지 않게).

## 샘플 검증 명령 (구현 슬라이스의 완료 기준)
```bash
# ① 두 밤 순서대로 (F1·F2·F3)
h=$(mktemp -d)
python3 regsum.py samples/2026-10-24 $h | diff - fixtures/expected/2026-10-24.txt && diff $h/2026-10-24.tsv fixtures/history/2026-10-24.tsv
python3 regsum.py samples/2026-10-25 $h | diff - fixtures/expected/2026-10-25.txt && diff $h/2026-10-25.tsv fixtures/expected/2026-10-25.tsv
# ② DMA 사례: 같은 테스트·같은 [SCB], 뒤쪽 메시지만 다름 → 새로 생긴 실패
h=$(mktemp -d); cp fixtures/history_dma_case/*.tsv $h/
python3 regsum.py samples/2026-10-25 $h | diff - fixtures/expected/2026-10-25_dma_case.txt
# ③ seed 증가 → "1개에서 2개로"
h=$(mktemp -d); cp fixtures/history_seed_growth/*.tsv $h/
python3 regsum.py samples/2026-10-25 $h | diff - fixtures/expected/2026-10-25_seed_growth.txt
# ④ 실패 경로: 종료코드 2, 보관 파일 안 씀
python3 regsum.py samples/2026-10-99 /tmp/x; echo $?            # → 2
h=$(mktemp -d); cp fixtures/history_broken/*.tsv $h/
python3 regsum.py samples/2026-10-25 $h; echo $?; ls $h          # → 2, 2026-10-24.tsv만
# ⑤ 4000바이트 넘는 날 → 줄 경계에서 메시지 2개 (F7)
h=$(mktemp -d); cp fixtures/history_split/*.tsv $h/
python3 regsum.py fixtures/split_logs/2026-10-26 $h | diff - fixtures/expected/2026-10-26_split.txt && diff $h/2026-10-26.tsv fixtures/expected/2026-10-26_split.tsv
```

## 변경 이력
| 버전 | 변경 | 이유(DECISIONS 번호) |
|---|---|---|
| v1 | 최초 확정: 단일 CLI, 묶음 기준 줄 규칙, 게시 글 모양, 보관 TSV | D-001~D-005 |
| v2 | C에 "나눠 올리기" 추가(4000바이트 넘을 때만, 줄 경계, `[k/N]`·`(이어서)`·구분 줄), 검증 ⑤와 fixtures(`split_logs/`, `history_split/`, `expected/2026-10-26_split.*`) 추가. 4000 이하 출력·보관 파일·CLI·오류 경로는 그대로 | D-007 |
