#!/usr/bin/env bash
# 리허설 2: 페르소나(검증팀 담당자) 역할 AI. 도구 없음, 숨은 사실은 persona.md에만 있다.
# 사용: persona.sh <이름> <메시지> [이어갈 session_id]
set -uo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"
source "$R/kit/clean-env.sh"
args=(-p "$2" --output-format json --model sonnet --effort low --tools "" --strict-mcp-config --settings "$R/kit/settings.json" --system-prompt "$(cat "$R/kit/persona.md")")
[ -n "${3:-}" ] && args+=(--resume "$3")
( cd "$R/persona-home" && cc "${args[@]}" < /dev/null > "$R/runs/$1.json" 2> "$R/runs/$1.err" )
echo "exit=$?"
jq -r '.result // "(결과 없음)"' "$R/runs/$1.json" | tee "$R/runs/$1.md"
jq -c '{sid: .session_id, usd: .total_cost_usd}' "$R/runs/$1.json"
