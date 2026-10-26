"""runs/*.json에서 세션별 시간·비용·토큰 표를 만든다. 사용: python3 summarize.py <runs 폴더>
주의: --resume으로 이어 간 세션의 total_cost_usd·modelUsage는 세션 누적값(서브에이전트 포함)이라
세션마다 마지막 호출 값만 쓴다. duration_ms는 호출별이라 더한다."""
import glob
import json
import os
import sys

sessions = {}  # session_id -> {"steps": [...], "sec": 합, "last": 마지막 json}
for path in sorted(glob.glob(os.path.join(sys.argv[1], "[0-9][0-9]-*.json"))):
    try:
        d = json.load(open(path))
    except ValueError:
        continue
    s = sessions.setdefault(d["session_id"], {"steps": [], "sec": 0.0, "last": None})
    s["steps"].append(os.path.basename(path)[:-5])
    s["sec"] += d.get("duration_ms", 0) / 1000
    s["last"] = d

print("| 세션(단계) | 누가 | 초 | USD | 입력+캐시쓰기 | 캐시읽기 | 출력 |")
print("|---|---|---:|---:|---:|---:|---:|")
tot = {}
for s in sessions.values():
    d = s["last"]
    t = [0, 0, 0]
    for m in (d.get("modelUsage") or {}).values():
        t[0] += m.get("inputTokens", 0) + m.get("cacheCreationInputTokens", 0)
        t[1] += m.get("cacheReadInputTokens", 0)
        t[2] += m.get("outputTokens", 0)
    who = "persona" if any("persona" in n for n in s["steps"]) else "harness"
    label = s["steps"][0] + ("" if len(s["steps"]) == 1 else " (+%d)" % (len(s["steps"]) - 1))
    print("| %s | %s | %d | %.2f | %d | %d | %d |" % (label, who, s["sec"], d.get("total_cost_usd", 0), t[0], t[1], t[2]))
    a = tot.setdefault(who, [0.0, 0.0, 0, 0, 0])
    a[0] += s["sec"]; a[1] += d.get("total_cost_usd", 0); a[2] += t[0]; a[3] += t[1]; a[4] += t[2]
for who, a in tot.items():
    print("| **합계 %s** | | %d | %.2f | %d | %d | %d |" % (who, a[0], a[1], a[2], a[3], a[4]))
