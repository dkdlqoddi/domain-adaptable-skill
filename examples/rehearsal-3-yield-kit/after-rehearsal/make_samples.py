"""리허설 3 샘플 데이터 생성기 (정답 포함 — 리허설이 끝난 뒤에 열 것).
사용: python3 make_samples.py <출력 폴더>   → <출력 폴더>/2026-10-25/eds_results.csv, mes_history.csv
제품·설비 이름과 숫자는 지어낸 것이다."""
import csv
import os
import random
import sys
from datetime import datetime, timedelta

OUT = os.path.join(sys.argv[1], "2026-10-25")
rnd = random.Random(20261025)
LOTS = [("L2610A01", "K4", "2026-10-23 06:00"), ("L2610A02", "K4", "2026-10-23 09:00"), ("L2610B01", "K8", "2026-10-23 12:00")]
BASE = {"K4": 93.0, "K8": 86.0}          # 제품별 평소 수율(%). 목표는 K4 92, K8 85 → 목표 -5%p 미만이 "떨어짐"
TOTAL = {"K4": 1286, "K8": 1102}         # 웨이퍼당 다이 수
CVD_SLOTS = [("CVD-07", "A")] * 6 + [("CVD-07", "B")] * 7 + [("CVD-09", "A")] * 6 + [("CVD-09", "B")] * 6
RETEST = {"L2610A02-07", "L2610A02-19", "L2610B01-11"}   # 첫 측정이 접촉 불량으로 낮게 나와 다시 잰 웨이퍼(마지막만 진짜)
REWORK = {"L2610A01-04", "L2610A01-16", "L2610A02-22", "L2610B01-03"}  # 노광 재작업(마지막 PHOTO만 진짜)
NOISE_LOW = {"L2610A01-21"}               # 원인과 무관하게 우연히 낮은 웨이퍼 1장
fmt = "%Y-%m-%d %H:%M:%S"

eds, mes = [], []
for lot, prod, start in LOTS:
    slots = CVD_SLOTS[:]
    rnd.shuffle(slots)
    t0 = datetime.strptime(start, "%Y-%m-%d %H:%M")
    for w in range(1, 26):
        wid = "%s-%02d" % (lot, w)
        t = t0 + timedelta(minutes=3 * w)
        if wid in REWORK:
            mes.append([lot, wid, "S110_PHOTO", "PHOTO-02", "-", t.strftime(fmt)])
            mes.append([lot, wid, "S110_PHOTO", "PHOTO-01", "-", (t + timedelta(hours=3)).strftime(fmt)])
        else:
            mes.append([lot, wid, "S110_PHOTO", "PHOTO-0%d" % (1 + w % 2), "-", t.strftime(fmt)])
        etch = ("ETCH-05", "AB"[w % 2]) if (wid in RETEST or w % 5 == 0) else ("ETCH-03", "ABC"[w % 3])
        cvd = ("CVD-09", "A") if wid in RETEST else slots[w - 1]
        mes.append([lot, wid, "S120_ETCH", etch[0], etch[1], (t + timedelta(hours=5)).strftime(fmt)])
        mes.append([lot, wid, "S130_CVD", cvd[0], cvd[1], (t + timedelta(hours=9)).strftime(fmt)])
        mes.append([lot, wid, "S140_CMP", "CMP-02", "-", (t + timedelta(hours=13)).strftime(fmt)])
        y = BASE[prod] + rnd.gauss(0, 0.9)
        if cvd == ("CVD-07", "B"):
            y -= 9.5 + rnd.gauss(0, 1.2)
        if wid in NOISE_LOW:
            y = BASE[prod] - 6.4
        y = max(50.0, min(99.0, y))
        end = datetime(2026, 10, 25, 1, 0) + timedelta(minutes=7 * (LOTS.index((lot, prod, start)) * 25 + w))
        if wid in RETEST:
            bad = 58.0 + rnd.random() * 6
            eds.append([lot, wid, prod, end.strftime(fmt), round(TOTAL[prod] * bad / 100), TOTAL[prod]])
            end = end + timedelta(minutes=95)
        eds.append([lot, wid, prod, end.strftime(fmt), round(TOTAL[prod] * y / 100), TOTAL[prod]])

eds.sort(key=lambda r: r[3])  # 내보내기는 테스트 끝난 시각 순
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "eds_results.csv"), "w", newline="", encoding="utf-8-sig") as f:  # 엑셀 내보내기처럼 BOM이 붙는다
    csv.writer(f).writerows([["lot_id", "wafer_id", "product", "test_end_time", "good_die", "total_die"]] + eds)
with open(os.path.join(OUT, "mes_history.csv"), "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows([["lot_id", "wafer_id", "step", "eqp_id", "chamber", "track_in_time"]] + mes)
print("eds %d줄, mes %d줄 → %s" % (len(eds), len(mes), OUT))
