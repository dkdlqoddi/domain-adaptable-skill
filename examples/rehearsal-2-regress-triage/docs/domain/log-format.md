# 로그 모양 (samples/ 직접 확인)

> 출처: 과제 `samples/`의 두 밤(`2026-10-24` 7개, `2026-10-25` 8개). 실제 하룻밤 약 300개 중 일부다. 인터뷰가 아니라 데이터에서 본 사실이므로 `(samples)`로 표시한다.

## 폴더·파일
- `samples/<YYYY-MM-DD>/<테스트이름>__s<seed>.log`, 하위 폴더 없음. (samples)
- 로그 둘째 줄: `Run: <테스트이름>_test  seed=<n>  host=<농장 서버>  start=<날짜 시각>`. 파일 이름의 테스트 이름에는 `_test`가 붙지 않는다. (samples)
- 폴더 날짜 밤 22시쯤 시작하고 다음 날 새벽에 끝나기도 한다(axi_stress 01:5x 종료) → "회귀 날짜 = 시작한 밤"과 맞는다. (samples)
- 밤마다 실행 목록이 다르다. 지난밤에는 `axi_stress__s56`이 하나 더 있다. (samples)

## 에러 줄
- 모양: `UVM_ERROR|UVM_FATAL <소스파일>(<줄>) @ <시뮬 시간>: <컴포넌트 경로> [<태그>] <메시지>` (samples)
  - `UVM_ERROR tb/env/dma_scoreboard.sv(142) @ 655020: uvm_test_top.env.scb [SCB] data mismatch addr=0x00011a08 exp=0x0badf00d act=0x0badf00c`
  - `UVM_ERROR tb/env/uart_chk.sv(203) @ 702880: uvm_test_top.env.chk [PARITY] parity error on rx byte 0x3c (lane 1)`
  - `UVM_FATAL tb/env/pcie_link_mon.sv(77) @ 5000000: uvm_test_top.env.link_mon [LINK] timeout waiting for link up after 5000000 ps (ltssm=POLLING)`
- 한 로그에 에러 줄이 여러 개일 수 있다(지난밤 `dma_burst__s202`는 2줄). (samples)
- 메시지 안의 숫자: 시뮬 시간, 주소·기댓값·실제값(16진), 바이트 값, lane 번호. (samples)

## 함정
- **모든 로그**의 끝 요약에 `UVM_ERROR :    0`, `UVM_FATAL :    0` 줄이 있다. 단어만 찾으면 통과한 로그까지 전부 걸린다. (samples)
- **중간에 끊긴 로그**: 지난밤 `axi_stress__s55`는 7줄째 줄 중간(`4096 outsta`)에서 끝난다. 끝 요약, `$finish`, `run finished` 줄이 없고 에러 줄도 없다 → "에러 줄이 있으면 실패" 기준으로는 **실패로 잡히지 않는다**. 그 전날 밤 같은 seed는 정상 종료했다. (samples)
  - 원인: LSF 시간 제한(4시간)에 걸려 죽은 것. **실패다.** 특징은 끝에 `UVM Report Summary`도 `$finish`도 없음. (인터뷰 3회차)
  - 참고: 같은 밤 `axi_stress__s56`은 22:10→01:47(3시간 37분)로 제한에 가깝다. 끊긴 로그 자체에는 끝난 시각이 남지 않는다. `UVM_FATAL`로 끝난 pcie_link s11에도 요약과 `$finish`는 있다 → "끝 없음"으로 FATAL과 끊긴 로그가 섞이지 않는다. (samples)
- `TEST PASSED`/`TEST FAILED` 줄은 테스트마다 다르다. axi_stress에는 없고, FATAL로 끝난 로그에도 없다 → 통과/실패 판단에 쓸 수 없다. (samples)
- `UVM_WARNING ... [COV]` 줄은 모든 로그에 있고 실패가 아니다. (samples)

## 두 밤 비교 (첫 에러 줄 기준)
| 실행 | 그 전날 밤 (10-24) | 지난밤 (10-25) | 보이는 것 |
|---|---|---|---|
| pcie_link s11 | FATAL `[LINK] timeout ...` | 한 글자도 다르지 않음 | 계속 남은 실패 |
| uart_loop s7 | `[PARITY] ... 0x3c (lane 1)` | `[PARITY] ... 0x5a (lane 0)` | 숫자만 다름 → 같은 실패, lane은 참고로 표시 (인터뷰 3회차) |
| dma_burst s202 | 통과 | `[SCB] data mismatch addr=0x00004f20 ...` | 새로 생김 |
| dma_burst s203 | 통과 | `[SCB] data mismatch addr=0x00011a08 ...` | 새로 생김. s202와 숫자만 다름 → 같은 실패 묶음 후보 |
| axi_stress s55 | 통과 | 중간에 끊김 | 실패(LSF 시간 제한), 맨 위에 따로 (인터뷰 3회차) |
| axi_stress s56 | (없음) | 통과 | 새 실행 |
| dma_basic s101, pcie_link s12 | 통과 | 통과 | |
