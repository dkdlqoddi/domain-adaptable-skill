"""리허설 2용 가짜 회귀 로그를 만든다. 사용: python3 make_samples.py <출력 폴더>
밤 두 번(2026-10-24, 2026-10-25). 시뮬레이터 이름과 형식은 지어낸 것이다(UVM 보고 줄 형식만 흉내)."""
import os
import sys

OUT = sys.argv[1]

# (밤, 테스트, seed, 결과, 시작 시각, 종료 시각)
# 결과: pass | pass_quiet(TEST 줄 없음) | scb2 | scb1 | link | parity_5a | parity_3c | killed
RUNS = [
    ("2026-10-24", "dma_basic", 101, "pass", "22:04:11", "22:06:52"),
    ("2026-10-24", "dma_burst", 202, "pass", "22:04:15", "22:09:03"),
    ("2026-10-24", "dma_burst", 203, "pass", "22:04:16", "22:08:41"),
    ("2026-10-24", "pcie_link", 11, "link", "22:05:02", "22:31:40"),
    ("2026-10-24", "pcie_link", 12, "pass", "22:05:03", "22:29:18"),
    ("2026-10-24", "uart_loop", 7, "parity_3c", "22:06:30", "22:07:12"),
    ("2026-10-24", "axi_stress", 55, "pass_quiet", "22:10:44", "01:52:09"),
    ("2026-10-25", "dma_basic", 101, "pass", "22:03:58", "22:06:31"),
    ("2026-10-25", "dma_burst", 202, "scb2", "22:04:02", "22:07:45"),
    ("2026-10-25", "dma_burst", 203, "scb1", "22:04:03", "22:07:20"),
    ("2026-10-25", "pcie_link", 11, "link", "22:04:50", "22:31:02"),
    ("2026-10-25", "pcie_link", 12, "pass", "22:04:51", "22:28:57"),
    ("2026-10-25", "uart_loop", 7, "parity_5a", "22:06:12", "22:06:58"),
    ("2026-10-25", "axi_stress", 55, "killed", "22:10:31", ""),
    ("2026-10-25", "axi_stress", 56, "pass_quiet", "22:10:33", "01:47:26"),
]

ERRORS = {
    "scb2": [
        ("UVM_ERROR", "tb/env/dma_scoreboard.sv(142) @ 812340: uvm_test_top.env.scb [SCB] data mismatch addr=0x00004f20 exp=0xdeadbeef act=0xdeadbeee"),
        ("UVM_ERROR", "tb/env/dma_scoreboard.sv(142) @ 812410: uvm_test_top.env.scb [SCB] data mismatch addr=0x00004f24 exp=0x12345678 act=0x12345670"),
    ],
    "scb1": [
        ("UVM_ERROR", "tb/env/dma_scoreboard.sv(142) @ 655020: uvm_test_top.env.scb [SCB] data mismatch addr=0x00011a08 exp=0x0badf00d act=0x0badf00c"),
    ],
    "link": [
        ("UVM_FATAL", "tb/env/pcie_link_mon.sv(77) @ 5000000: uvm_test_top.env.link_mon [LINK] timeout waiting for link up after 5000000 ps (ltssm=POLLING)"),
    ],
    "parity_5a": [
        ("UVM_ERROR", "tb/env/uart_chk.sv(203) @ 640200: uvm_test_top.env.chk [PARITY] parity error on rx byte 0x5a (lane 0)"),
    ],
    "parity_3c": [
        ("UVM_ERROR", "tb/env/uart_chk.sv(203) @ 702880: uvm_test_top.env.chk [PARITY] parity error on rx byte 0x3c (lane 1)"),
    ],
}

END_NS = {"dma_basic": 1200000, "dma_burst": 1500000, "pcie_link": 5000000, "uart_loop": 900000, "axi_stress": 48000000}


def next_day(night):
    return night[:-2] + "%02d" % (int(night[-2:]) + 1)


def log_text(night, test, seed, kind, start, end):
    blk = test.split("_")[0]
    lines = [
        "simx 2024.09 -- event-driven simulator (rehearsal mock)",
        "Run: %s_test  seed=%d  host=farm%02d  start=%s %s" % (test, seed, seed % 17, night, start),
        "UVM_INFO @ 0: reporter [RNTST] Running test %s_test..." % test,
        "UVM_INFO tb/env/%s_env.sv(64) @ 0: uvm_test_top.env [ENV] build_phase done" % blk,
        "UVM_INFO tb/seq/%s_seq.sv(41) @ 120000: uvm_test_top.env.agt.sqr@@seq [SEQ] %d transactions issued" % (test, 64 + seed % 50),
    ]
    if test == "axi_stress":
        for t in (2000000, 3900000):
            lines.append("UVM_INFO tb/seq/axi_stress_seq.sv(90) @ %d: uvm_test_top.env.agt.sqr@@seq [SEQ] 4096 outstanding transactions" % t)
    if kind == "killed":  # LSF 시간 제한으로 죽음: 줄 중간에서 끊기고 요약이 없다
        return "\n".join(lines) + "\nUVM_INFO tb/seq/axi_stress_seq.sv(90) @ 5800000: uvm_test_top.env.agt.sqr@@seq [SEQ] 4096 outsta"
    lines.append("UVM_WARNING tb/env/%s_cov.sv(17) @ 980000: uvm_test_top.env.cov [COV] bin %s_len_max not hit" % (blk, blk))
    errs = ERRORS.get(kind, [])
    lines += ["%s %s" % e for e in errs]
    n_err = sum(1 for s, _ in errs if s == "UVM_ERROR")
    n_fat = sum(1 for s, _ in errs if s == "UVM_FATAL")
    end_ns = END_NS[test]
    if kind != "pass_quiet" and n_fat == 0:
        verdict = "FAILED" if n_err else "PASSED"
        lines.append("UVM_INFO tb/test/%s_test.sv(55) @ %d: uvm_test_top [TEST] TEST %s" % (test, end_ns, verdict))
    end_day = next_day(night) if end < start else night
    lines += [
        "--- UVM Report Summary ---",
        "",
        "** Report counts by severity",
        "UVM_INFO :   %d" % (40 + seed % 30),
        "UVM_WARNING :    1",
        "UVM_ERROR :    %d" % n_err,
        "UVM_FATAL :    %d" % n_fat,
        "",
        "$finish at simulation time %d ps" % end_ns,
        "simx: run finished  end=%s %s  cpu=%.1fs" % (end_day, end, 60 + seed * 1.3),
    ]
    return "\n".join(lines) + "\n"


for night, test, seed, kind, start, end in RUNS:
    d = os.path.join(OUT, night)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "%s__s%d.log" % (test, seed)), "w") as f:
        f.write(log_text(night, test, seed, kind, start, end))
print("%d개 로그 → %s" % (len(RUNS), OUT))
