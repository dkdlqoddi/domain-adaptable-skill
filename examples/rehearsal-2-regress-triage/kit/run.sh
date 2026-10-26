#!/usr/bin/env bash
# 리허설 2: 하네스 명령을 새 세션으로 한 번 실행한다(= /clear 직후와 같다). 결과는 runs/<이름>.{json,md}
# 사용: run.sh <이름> <프롬프트> [이어갈 session_id]
set -uo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"
source "$R/kit/clean-env.sh"
args=(-p "$2" --output-format json --permission-mode bypassPermissions --strict-mcp-config --settings "$R/kit/settings.json")
[ -n "${3:-}" ] && args+=(--resume "$3")
start=$(date +%s)
( cd "$R/project" && cc "${args[@]}" < /dev/null > "$R/runs/$1.json" 2> "$R/runs/$1.err" )
code=$?
jq -r '.result // "(결과 없음)"' "$R/runs/$1.json" > "$R/runs/$1.md" 2>/dev/null
echo "exit=$code  $(( ($(date +%s) - start) / 60 ))분"
jq -c '{sid: .session_id, turns: .num_turns, usd: .total_cost_usd, models: (.modelUsage // {} | with_entries(.value |= {in: .inputTokens, cr: .cacheReadInputTokens, cw: .cacheCreationInputTokens, out: .outputTokens}))}' "$R/runs/$1.json" 2>/dev/null
