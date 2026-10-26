import os
import shutil
import tempfile
import unittest

from regsum import (LIMIT, TSV_HEADER, _line, failure_key, is_error_line, is_truncated, pick_baseline,
                    read_history, split_messages)

HERE = os.path.dirname(os.path.abspath(__file__))


class FailureKeyTest(unittest.TestCase):
    def test_keys_fixture(self):
        with open(os.path.join(HERE, "fixtures", "keys.tsv"), encoding="utf-8") as f:
            rows = [line.rstrip("\n").split("\t") for line in f if line.strip()]
        self.assertTrue(rows)
        for line, key in rows:
            self.assertEqual(failure_key(line), key)

    def test_tab_becomes_space(self):
        self.assertEqual(failure_key("UVM_ERROR a\tb"), "UVM_ERROR a b")


class IsErrorLineTest(unittest.TestCase):
    def test_error_and_fatal(self):
        self.assertTrue(is_error_line("UVM_ERROR tb/x.sv(1) @ 2: top [X] bad\n"))
        self.assertTrue(is_error_line("UVM_FATAL tb/x.sv(1) @ 2: top [X] bad\n"))

    def test_summary_counts_are_not_errors(self):
        self.assertFalse(is_error_line("UVM_ERROR :    0\n"))
        self.assertFalse(is_error_line("UVM_ERROR :    2\n"))
        self.assertFalse(is_error_line("UVM_FATAL :    1\n"))

    def test_warning_is_not_error(self):
        self.assertFalse(is_error_line("UVM_WARNING tb/x.sv(1) @ 2: top [COV] hole\n"))


class IsTruncatedTest(unittest.TestCase):
    def test_summary_present(self):
        self.assertFalse(is_truncated(["UVM_INFO x\n", "--- UVM Report Summary ---\n"]))

    def test_finish_only(self):
        self.assertFalse(is_truncated(["UVM_INFO x\n", "$finish at simulation time 1 ps\n"]))

    def test_neither(self):
        self.assertTrue(is_truncated(["UVM_INFO x\n", "UVM_ERROR tb/x.sv(1) @ 2: top [X] bad"]))


class PickBaselineTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)

    def touch(self, *names):
        for name in names:
            open(os.path.join(self.dir, name), "w").close()

    def test_latest_before_date(self):
        self.touch("2026-10-23.tsv", "2026-10-24.tsv", "2026-10-25.tsv", "notes.tsv")
        self.assertEqual(pick_baseline(self.dir, "2026-10-25"), "2026-10-24")

    def test_none_before_date(self):
        self.touch("2026-10-25.tsv", "2026-10-26.tsv", "notes.tsv")
        self.assertIsNone(pick_baseline(self.dir, "2026-10-25"))


class SeedChangeLineTest(unittest.TestCase):
    def test_changed_count(self):
        self.assertEqual(_line("dma_burst", 2, ["202", "203"], "UVM_ERROR x", 1),
                         "- dma_burst, seed 2개 중 1개에서 2개로(202, 203): UVM_ERROR x")
        self.assertEqual(_line("dma_burst", 3, ["202"], "UVM_ERROR x", 2),
                         "- dma_burst, seed 3개 중 2개에서 1개로(202): UVM_ERROR x")

    def test_same_count(self):
        self.assertEqual(_line("uart_loop", 1, ["7"], "UVM_ERROR x", 1),
                         "- uart_loop, seed 1개 중 1개(7): UVM_ERROR x")


class ReadHistoryTest(unittest.TestCase):
    """깨진 보관 파일은 ValueError(머리 줄을 1로 센 줄 번호)."""
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)

    def history(self, text):
        path = os.path.join(self.dir, "2026-10-24.tsv")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def bad_line(self, text):
        with self.assertRaises(ValueError) as cm:
            read_history(self.history(text))
        return cm.exception.args[0]

    def test_wrong_header(self):
        self.assertEqual(self.bad_line("test\ttotal\tseed\tkey\nuart_loop\t1\t7\tK\n"), 1)

    def test_three_columns(self):
        self.assertEqual(self.bad_line(TSV_HEADER + "pcie_link\t2\t11\n"), 2)

    def test_total_not_number(self):
        self.assertEqual(self.bad_line(TSV_HEADER + "dma\t2\t3\tK1\nuart_loop\tone\t7\tK2\n"), 3)

    def test_ok(self):
        path = self.history(TSV_HEADER + "dma\t3\t202,203\tK1\nuart_loop\t1\t7\tK2\n")
        self.assertEqual(read_history(path), {("dma", "K1"): 2, ("uart_loop", "K2"): 1})


class SplitMessagesTest(unittest.TestCase):
    """나눠 올리기: 실제 LIMIT 상수로 긴 줄을 만들어 시험한다."""
    HEAD = "회귀 2026-10-26 정리 (비교 기준: 2026-10-25 결과)"

    def size(self, msg):
        return sum(len(l.encode("utf-8")) + 1 for l in msg)

    def test_small_not_split(self):
        msgs = split_messages("2026-10-26", self.HEAD, [("A", ["- a"]), ("B", ["없음"])])
        self.assertEqual(msgs, [[self.HEAD, "", "[A]", "- a", "", "[B]", "없음"]])

    def test_big_split(self):
        item = "- t, seed 1개 중 1개(1): " + "가" * 300   # 약 930바이트
        msgs = split_messages("2026-10-26", self.HEAD, [("A", ["없음"]), ("B", [item] * 6), ("C", [item])])
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0][0], self.HEAD + " [1/2]")
        self.assertEqual(msgs[1][:3], ["회귀 2026-10-26 정리 [2/2]", "", "[B] (이어서)"])
        for msg in msgs:
            self.assertLessEqual(self.size(msg), LIMIT)
            self.assertTrue(msg[-1].startswith(("- ", "없음")))   # 제목만 남은 메시지 없음
        self.assertEqual(sum(l == item for m in msgs for l in m), 7)   # 줄을 잃거나 자르지 않음

    def test_one_line_over_limit_ends(self):
        item = "- t: " + "x" * (LIMIT + 10)
        msgs = split_messages("2026-10-26", self.HEAD, [("A", ["- a", item, "- b"])])
        self.assertEqual([len(m) for m in msgs], [4, 4, 4])
        self.assertEqual(msgs[1][2:], ["[A] (이어서)", item])


if __name__ == "__main__":
    unittest.main()
