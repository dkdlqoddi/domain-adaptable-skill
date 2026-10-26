> 입력: `/delegate S2`

S2 브리프 초안입니다. 재료는 TASKS S2 행, CONTRACT C·D, SPEC F3와 비목표, 현재 `regsum.py`, fixtures 세 쌍(`history_dma_case`·`history_seed_growth`·`expected/*`)에서 가져왔습니다. 현재 `check.sh`는 ①~④가 모두 FAIL입니다. S2 이후 기대값은 ①②③ PASS이고, ④는 S3 몫이라 FAIL로 남습니다.

---

# 작업 브리프: S2 비교 기준 고르기·새로 생김/계속 남음 나누기·seed 수 변화

## 목표 (1문장)
`python3 regsum.py <회귀 날짜 폴더> <보관 폴더>`가 보관 폴더에서 비교 기준(이번 날짜보다 앞선 가장 최근 `YYYY-MM-DD.tsv`)을 골라 첫 줄에 날짜를 보이고, 실패 묶음을 `[새로 생긴 실패]`와 `[계속 남은 실패]`로 나눕니다. 계속 남은 실패의 seed 수가 바뀌었으면 `1개에서 2개로`로 보입니다.

## 완료 기준
- [ ] `bash fixtures/check.sh` → `PASS ①`, `PASS ②`, `PASS ③` (프로젝트 루트에서. ④-a·④-b는 S3 몫이라 FAIL이어도 됩니다)
- [ ] `python3 -m unittest -q test_regsum` 통과 (S1 테스트 + S2에서 추가한 테스트)
- [ ] `LANG=C LC_ALL=C bash fixtures/check.sh`에서도 ①②③ PASS (S0 UTF-8 출력 방식 유지)

## 범위
- 쓰기 허용: `regsum.py`, `test_regsum.py`, `docs/TASKS.md`의 S2 행
- 읽기만: `fixtures/check.sh`, `fixtures/history*/`, `fixtures/expected/`, `samples/2026-10-24/`, `samples/2026-10-25/`
- 열지 말 것: `fixtures/` 수정 금지, `docs/`의 다른 파일, `.git`, `__pycache__`

## 지켜야 할 계약 (샘플 값 그대로)
### 비교 기준 고르기 (CONTRACT D)
- 비교 기준은 보관 폴더에서 이름이 `YYYY-MM-DD.tsv`이고, 날짜가 이번 회귀 날짜보다 **앞선** 파일 중 가장 최근 것입니다. 다른 파일(같은 날짜, 뒤 날짜, 다른 이름)은 무시합니다.
- 비교 기준은 오늘 보관 파일을 쓰기 **전에** 고르고 읽습니다. 같은 날짜로 다시 돌리면 오늘 파일은 덮어씁니다.
- 보관 파일 포맷은 UTF-8 TSV이고 첫 줄 머리는 `test⇥total⇥seeds⇥key`입니다(⇥ = 탭). 이후 한 줄이 실패 묶음 하나이고, seeds는 `,`로 구분합니다.
- 깨진 보관 파일 검사(머리 줄·열 4개·숫자 여부 → 종료코드 2)는 **S3 몫**입니다. 지금은 정상 파일만 가정하고 읽는 자리에 `shortcut:` 주석만 답니다.

### 나누기 (CONTRACT C)
- 새로 생긴 실패 = 비교 기준에 (테스트 이름, 묶음 기준 줄)이 없는 묶음입니다. 계속 남은 실패 = 있는 묶음입니다. 비교 기준이 없으면 전부 새로 생긴 실패입니다.
- 첫 줄은 비교 기준이 있으면 `회귀 2026-10-25 정리 (비교 기준: 2026-10-24 결과)`, 없으면 `회귀 <날짜> 정리 (비교 기준: 없음, 전부 새로 생긴 실패로 표시)`입니다.
- 계속 남은 실패에서 실패 seed 수가 지난번(보관 행의 seeds 개수)과 다르면 `- <테스트>, seed <전체>개 중 <지난 n>개에서 <n>개로(<seed들>): <원문>` 모양입니다. 줄어든 경우도 같은 모양이고, `<전체>`는 이번 실행 값입니다.
- 보관 파일에는 나누기와 무관하게 이번 묶음 전부를 씁니다(S1과 동일).
- 끊긴 로그는 비교하지 않습니다(S1과 동일).

### 기대 출력 (fixtures, 글자 단위로 일치)
① `samples/2026-10-24` → `samples/2026-10-25` 순서로 같은 보관 폴더를 쓸 때 두 번째 출력 (`fixtures/expected/2026-10-25.txt`):
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

② DMA 사례. 보관 파일 `fixtures/history_dma_case/2026-10-24.tsv`:
```
test⇥total⇥seeds⇥key
dma_burst⇥2⇥202⇥UVM_ERROR tb/env/dma_scoreboard.sv(#) @ #: uvm_test_top.env.scb [SCB] unexpected write response addr=# resp=#
pcie_link⇥2⇥11⇥UVM_FATAL tb/env/pcie_link_mon.sv(#) @ #: uvm_test_top.env.link_mon [LINK] timeout waiting for link up after # ps (ltssm=POLLING)
```
기대 출력 (`fixtures/expected/2026-10-25_dma_case.txt`):
```
회귀 2026-10-25 정리 (비교 기준: 2026-10-24 결과)

[끊긴 로그 — LSF 시간 제한, 또는 아직 실행 중]
- axi_stress, seed 2개 중 1개(55)

[새로 생긴 실패]
- dma_burst, seed 2개 중 2개(202, 203): UVM_ERROR tb/env/dma_scoreboard.sv(142) @ 812340: uvm_test_top.env.scb [SCB] data mismatch addr=0x00004f20 exp=0xdeadbeef act=0xdeadbeee
- uart_loop, seed 1개 중 1개(7): UVM_ERROR tb/env/uart_chk.sv(203) @ 640200: uvm_test_top.env.chk [PARITY] parity error on rx byte 0x5a (lane 0)

[계속 남은 실패]
- pcie_link, seed 2개 중 1개(11): UVM_FATAL tb/env/pcie_link_mon.sv(77) @ 5000000: uvm_test_top.env.link_mon [LINK] timeout waiting for link up after 5000000 ps (ltssm=POLLING)
```

③ seed 증가. 보관 파일 `fixtures/history_seed_growth/2026-10-24.tsv`:
```
test⇥total⇥seeds⇥key
dma_burst⇥2⇥202⇥UVM_ERROR tb/env/dma_scoreboard.sv(#) @ #: uvm_test_top.env.scb [SCB] data mismatch addr=# exp=# act=#
pcie_link⇥2⇥11⇥UVM_FATAL tb/env/pcie_link_mon.sv(#) @ #: uvm_test_top.env.link_mon [LINK] timeout waiting for link up after # ps (ltssm=POLLING)
uart_loop⇥1⇥7⇥UVM_ERROR tb/env/uart_chk.sv(#) @ #: uvm_test_top.env.chk [PARITY] parity error on rx byte # (lane #)
```
기대 출력 (`fixtures/expected/2026-10-25_seed_growth.txt`):
```
회귀 2026-10-25 정리 (비교 기준: 2026-10-24 결과)

[끊긴 로그 — LSF 시간 제한, 또는 아직 실행 중]
- axi_stress, seed 2개 중 1개(55)

[새로 생긴 실패]
없음

[계속 남은 실패]
- dma_burst, seed 2개 중 1개에서 2개로(202, 203): UVM_ERROR tb/env/dma_scoreboard.sv(142) @ 812340: uvm_test_top.env.scb [SCB] data mismatch addr=0x00004f20 exp=0xdeadbeef act=0xdeadbeee
- pcie_link, seed 2개 중 1개(11): UVM_FATAL tb/env/pcie_link_mon.sv(77) @ 5000000: uvm_test_top.env.link_mon [LINK] timeout waiting for link up after 5000000 ps (ltssm=POLLING)
- uart_loop, seed 1개 중 1개(7): UVM_ERROR tb/env/uart_chk.sv(203) @ 640200: uvm_test_top.env.chk [PARITY] parity error on rx byte 0x5a (lane 0)
```

## 현재 코드 (S1 결과, 이 위에 고칩니다)
- `collect(run_dir)` → `(totals, truncated, groups)`이고, 묶음은 `(테스트, seed들, 묶음 기준 줄, 원문)` 모양입니다.
- `render(date, totals, truncated, new_groups, kept_groups)`는 첫 줄을 `없음`으로 하드코딩하고 있습니다.
- `main`의 `# shortcut: 비교 없이 전부 새로 생긴 실패로 두고 ...` 줄이 이번에 바꿀 자리입니다. 바꾸고 나면 그 shortcut 주석은 지웁니다.
- `kept_groups` 매개변수는 S1 `/lean`에서 이번에 쓰라고 남겨 둔 것입니다(D-006).

## 하지 말 것
- 이번 슬라이스 밖: 오류 경로 전부(인자 수, 폴더 없음, 폴더 이름, `.log` 0개, 이름 모양 경고, 깨진 보관 파일 → 종료코드 2)와 임시 파일→이름 바꾸기는 S3 몫입니다.
- SPEC 비목표: 사라진 실패 표시(F5), 사이 밤 실패 확인(F6), 기준 날짜 수동 지정 등 옵션 플래그, 설정 파일, 캐시, 재시도, 보관 파일 정리·백업, 외부 패키지, Python 3.7+ 전용 기능(`dataclasses`, `from __future__ import annotations` 등).
- argparse·logging·클래스·`csv` 모듈 도입 금지. `str.split("\t")`로 충분합니다.
- 테스트는 작게, `unittest`만 씁니다. 하나는 비교 기준 고르기(임시 폴더에 `2026-10-23.tsv`, `2026-10-24.tsv`, `2026-10-25.tsv`, `notes.tsv`를 두고 회귀 날짜 2026-10-25 → `2026-10-24` 선택, 앞선 파일이 없으면 None), 다른 하나는 seed 수 변화 한 줄 모양입니다. 나머지는 check.sh가 확인합니다.
- 계약 변경 금지. 막히면 `docs/TASKS.md` BLOCKER 표에 적고 멈춥니다.

## 작업 순서
1. 테스트 추가 후 실패 확인 → 2. 최소 구현 → 3. 완료 기준 3개 통과 → 4. `docs/TASKS.md` S2 상태를 DONE으로 바꿈 → 5. 보고 (커밋은 하지 말 것, 루트가 함)

## 보고 형식 (이 순서로, 짧게)
1. 검증 명령과 실제 출력(마지막 10줄)
2. 바꾼 파일 목록
3. 추가하지 않은 것:
4. 확인하지 못한 것·리스크:

---

이대로 위임할까요? 줄이거나 바꿀 것이 있으면 적어주세요.

추가하지 않은 것: 깨진 보관 파일 검사(S3로 미루고 shortcut 주석으로 표시하게 함)
확인하지 못한 것·리스크: S2 이후 깨진 보관 파일을 넣으면 종료코드 2 대신 파이썬 예외로 죽을 수 있습니다. S3 전까지는 이 상태가 남습니다.
