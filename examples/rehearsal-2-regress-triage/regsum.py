"""회귀 날짜 폴더의 로그를 게시용 글과 보관 TSV로 정리한다."""
import glob
import os
import re
import sys
from collections import defaultdict

TSV_HEADER = "test\ttotal\tseeds\tkey\n"
LOG_NAME = re.compile(r"^(.+)__s(\d+)\.log$")
SUMMARY_COUNT = re.compile(r"^UVM_(ERROR|FATAL)\s*:\s*\d+\s*$")
HISTORY_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})\.tsv$")
RUN_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LIMIT = 4000  # 메시지 하나의 UTF-8 바이트 한도 (계약 C "나눠 올리기")
SPLIT_LINE = "---------- 여기서 나눠 올림 ----------"
USAGE = "사용법: python3 regsum.py <회귀 날짜 폴더> <보관 폴더>"


def err(text):
    # 표준출력과 같은 이유로 UTF-8 바이트로 직접 쓴다
    sys.stderr.buffer.write((text + "\n").encode("utf-8"))
    sys.stderr.flush()


def is_error_line(line):
    return line.startswith(("UVM_ERROR ", "UVM_FATAL ")) and not SUMMARY_COUNT.match(line)


def is_truncated(lines):
    return not any("UVM Report Summary" in l or l.startswith("$finish") for l in lines)


def failure_key(line):
    line = re.sub(r"0x[0-9a-fA-F]+", "#", line)
    line = re.sub(r"\d+", "#", line)
    return line.replace("\t", " ")


def collect(run_dir):
    """로그를 읽어 (테스트별 전체 seed 수, 끊긴 로그 줄 목록, 실패 묶음 목록)을 돌려준다.

    끊긴 로그 줄 = (테스트, seed들, 첫 에러 줄 또는 None)
    실패 묶음   = (테스트, seed들, 묶음 기준 줄, 가장 작은 seed의 첫 에러 줄)
    seed들은 숫자 오름차순 문자열 목록, 두 목록 모두 테스트 이름 → 기준 줄 순으로 정렬.
    """
    totals = defaultdict(int)
    cut = defaultdict(list)       # 테스트 -> [(seed, 첫 에러 줄 또는 None)]
    failed = defaultdict(list)    # (테스트, 기준 줄) -> [(seed, 첫 에러 줄)]
    for path in sorted(glob.glob(os.path.join(run_dir, "*.log"))):
        m = LOG_NAME.match(os.path.basename(path))
        if not m:
            err("경고: 이름 모양이 달라 건너뜀: " + path)
            continue
        test, seed = m.group(1), m.group(2)
        totals[test] += 1
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
        first = next((l for l in lines if is_error_line(l)), None)
        if is_truncated(lines):
            cut[test].append((int(seed), seed, first))
        elif first is not None:
            failed[(test, failure_key(first))].append((int(seed), seed, first))

    truncated = []
    for test in sorted(cut):
        runs = sorted(cut[test])
        firsts = [r[2] for r in runs if r[2] is not None]
        truncated.append((test, [r[1] for r in runs], firsts[0] if firsts else None))
    groups = []
    for test, key in sorted(failed):
        runs = sorted(failed[(test, key)])
        groups.append((test, [r[1] for r in runs], key, runs[0][2]))
    return totals, truncated, groups


def pick_baseline(history_dir, date):
    """보관 폴더에서 date보다 앞선 가장 최근 YYYY-MM-DD.tsv의 날짜, 없으면 None."""
    names = os.listdir(history_dir) if os.path.isdir(history_dir) else []
    earlier = [m.group(1) for m in map(HISTORY_NAME.match, names) if m and m.group(1) < date]
    return max(earlier) if earlier else None


def read_history(path):
    """보관 TSV → {(테스트, 묶음 기준 줄): 지난 실패 seed 수}.

    형식이 깨지면 ValueError(머리 줄을 1로 센 줄 번호). 빈 줄도 깨진 줄로 본다.
    """
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    if not lines or lines[0] != TSV_HEADER:
        raise ValueError(1)
    prev = {}
    for n, line in enumerate(lines[1:], 2):
        cols = line.rstrip("\n").split("\t")
        if len(cols) != 4 or not all(v.isdigit() for v in [cols[1]] + cols[2].split(",")):
            raise ValueError(n)
        prev[(cols[0], cols[3])] = len(cols[2].split(","))
    return prev


def _line(test, total, seeds, first, prev=None):
    n = "{}개".format(len(seeds))
    if prev not in (None, len(seeds)):
        n = "{}개에서 {}로".format(prev, n)
    text = "- {}, seed {}개 중 {}({})".format(test, total, n, ", ".join(seeds))
    return text + (": " + first if first is not None else "")


def _size(lines):
    return sum(len(l.encode("utf-8")) + 1 for l in lines)


def _pack(date, head, sections, n):
    """칸 줄을 앞에서부터 꽉 채워 메시지 목록(줄 목록들)을 만든다. 첫 줄의 N은 n으로 쓴다."""
    msgs = []

    def start():
        k = len(msgs) + 1
        first = head if k == 1 else "회귀 {} 정리".format(date)
        msgs.append([first + " [{}/{}]".format(k, n), ""])

    start()
    for title, items in sections:
        opened = False
        for i, item in enumerate(items):
            cur = msgs[-1]
            add = [item] if opened else ([""] if len(cur) > 2 else []) + ["[{}]".format(title), item]
            # 빈 메시지에서는 새로 시작하지 않는다: 한 줄이 혼자 한도를 넘어도 끝난다
            # shortcut: 묶음 줄 하나가 혼자 4000바이트를 넘으면 그 메시지만 한도를 넘김(SPEC 비목표), 첫 에러 줄이 수천 자인 로그가 나오면 줄 안에서 자르기
            if len(cur) > 2 and _size(cur + add) > LIMIT:
                start()
                add = ["[{}]{}".format(title, " (이어서)" if i else ""), item]
            msgs[-1] += add
            opened = True
    return msgs


def split_messages(date, head, sections):
    """sections = [(칸 제목, 줄 목록)] → 메시지 목록. 한도 이하면 메시지 하나(나누지 않음)."""
    whole = [head]
    for title, items in sections:
        whole += ["", "[{}]".format(title)] + items
    if _size(whole) <= LIMIT:
        return [whole]
    n = 2
    msgs = _pack(date, head, sections, n)
    while len(msgs) != n:   # [k/N] 자릿수가 바뀌면 다시 나눈다
        n = len(msgs)
        msgs = _pack(date, head, sections, n)
    return msgs


def render(date, base, totals, truncated, new_groups, kept_groups, prev):
    head = "회귀 {} 정리 (비교 기준: {})".format(
        date, "{} 결과".format(base) if base else "없음, 전부 새로 생긴 실패로 표시")
    sections = [
        ("끊긴 로그 — LSF 시간 제한, 또는 아직 실행 중",
         [_line(t, totals[t], s, f) for t, s, f in truncated]),
        ("새로 생긴 실패", [_line(t, totals[t], s, f) for t, s, k, f in new_groups]),
        ("계속 남은 실패", [_line(t, totals[t], s, f, prev[(t, k)]) for t, s, k, f in kept_groups]),
    ]
    msgs = split_messages(date, head, [(title, items or ["없음"]) for title, items in sections])
    return "\n{}\n\n".format(SPLIT_LINE).join("\n".join(m) + "\n" for m in msgs)


def history_text(totals, groups):
    rows = ["{}\t{}\t{}\t{}\n".format(t, totals[t], ",".join(s), k) for t, s, k, f in groups]
    return TSV_HEADER + "".join(rows)


def main(argv):
    # 오류 검사는 계약 C 표 순서대로, 보관 폴더를 만들거나 쓰기 전에 모두 끝낸다
    if len(argv) != 3:
        err(USAGE)
        return 2
    run_dir, history_dir = argv[1], argv[2]
    if not os.path.isdir(run_dir):
        err("오류: 로그 폴더가 없습니다: " + run_dir)
        return 2
    date = os.path.basename(os.path.normpath(run_dir))
    if not RUN_DATE.match(date):
        err("오류: 폴더 이름이 회귀 날짜(YYYY-MM-DD)가 아닙니다: " + date)
        return 2
    if not glob.glob(os.path.join(run_dir, "*.log")):
        err("오류: 로그 파일이 없습니다: " + run_dir)
        return 2
    totals, truncated, groups = collect(run_dir)
    # 비교 기준은 오늘 보관 파일을 쓰기 전에 고르고 읽는다
    base = pick_baseline(history_dir, date)
    prev = {}
    if base:
        base_path = os.path.join(history_dir, base + ".tsv")
        try:
            prev = read_history(base_path)
        except ValueError as e:
            err("오류: 보관 파일 형식이 맞지 않습니다: {} {}번째 줄".format(base_path, e.args[0]))
            return 2
    new_groups = [g for g in groups if (g[0], g[2]) not in prev]
    kept_groups = [g for g in groups if (g[0], g[2]) in prev]
    os.makedirs(history_dir, exist_ok=True)
    # 임시 파일에 다 쓴 뒤 이름을 바꿔, 중간에 죽어도 지난 보관 파일이 깨지지 않게 한다
    out = os.path.join(history_dir, date + ".tsv")
    with open(out + ".tmp", "w", encoding="utf-8", newline="\n") as f:
        f.write(history_text(totals, groups))
    os.replace(out + ".tmp", out)
    # 로캘과 무관하게 UTF-8로 내보낸다 (Python 3.6 C 로캘에서 print는 한글에서 죽는다)
    sys.stdout.buffer.write(render(date, base, totals, truncated, new_groups, kept_groups, prev).encode("utf-8"))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
