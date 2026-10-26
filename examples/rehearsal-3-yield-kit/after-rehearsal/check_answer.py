"""리허설 3 정답 확인 (리허설이 끝난 뒤에 열 것). 사용: python3 check_answer.py <samples/2026-10-25 폴더>
올바른 규칙으로 의심 설비·챔버 순위를 계산하고, 흔한 실수를 했을 때 순위가 어떻게 달라지는지 함께 보여 준다."""
import csv
import os
import sys
from collections import defaultdict

D = sys.argv[1]
TARGET = {"K4": 92.0, "K8": 85.0}


def load(name, enc):
    with open(os.path.join(D, name), newline="", encoding=enc) as f:
        return list(csv.DictReader(f))


def analyze(eds, mes, last_test=True, threshold=None, by_chamber=True, last_photo=True, by_count=False):
    tests = {}
    for r in sorted(eds, key=lambda r: r["test_end_time"]):
        if last_test or r["wafer_id"] not in tests:
            tests[r["wafer_id"]] = r
    low = set()
    for w, r in tests.items():
        y = 100.0 * int(r["good_die"]) / int(r["total_die"])
        if y < (threshold if threshold is not None else TARGET[r["product"]] - 5):
            low.add(w)
    path = {}
    for r in sorted(mes, key=lambda r: r["track_in_time"]):
        key = (r["wafer_id"], r["step"])
        if last_photo or key not in path:
            path[key] = (r["eqp_id"], r["chamber"]) if by_chamber else (r["eqp_id"], "")
    stats = defaultdict(lambda: [0, 0])
    for (w, step), tool in path.items():
        s = stats[(step,) + tool]
        s[0] += 1
        s[1] += w in low
    rows = []
    for (step, eqp, ch), (n, k) in stats.items():
        rest_n = sum(v[0] for kk, v in stats.items() if kk[0] == step) - n
        rest_k = sum(v[1] for kk, v in stats.items() if kk[0] == step) - k
        if not rest_n and not by_count:  # 그 공정에 설비가 하나뿐이면 비교할 대상이 없다
            continue
        rest = 100.0 * rest_k / rest_n if rest_n else 0.0
        rows.append((k if by_count else 100.0 * k / n - rest, step, eqp, ch, n, k, 100.0 * k / n, rest))
    rows.sort(reverse=True)
    return len(tests), len(low), rows[:3]


eds = load("eds_results.csv", "utf-8-sig")
mes = load("mes_history.csv", "utf-8")
cases = [
    ("정답: 마지막 측정, 제품별 기준(목표-5%p), 챔버까지, 마지막 PHOTO, 비율 비교", {}),
    ("실수: 떨어진 웨이퍼 '개수'로 순위", {"by_count": True}),
    ("실수: 설비 단위만(챔버 무시)", {"by_chamber": False}),
    ("실수: 첫 측정 사용(재측정 무시)", {"last_test": False}),
    ("실수: 기준 하나(87%)로 전 제품", {"threshold": 87.0}),
]
for title, kw in cases:
    n, k, top = analyze(eds, mes, **kw)
    print("== %s — 웨이퍼 %d장 중 떨어짐 %d장" % (title, n, k))
    for score, step, eqp, ch, n_, k_, rate, rest in top:
        print("   %-10s %-8s %-2s  지난 %2d장 중 %2d장(%.0f%%) vs 나머지 %.0f%%" % (step, eqp, ch or "", n_, k_, rate, rest))
