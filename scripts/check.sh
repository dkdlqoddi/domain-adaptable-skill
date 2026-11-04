#!/usr/bin/env bash
# 하네스 점검: 줄 수·프런트매터·참조·추가 토큰 근사치와 설치 회귀 검증.
# 사용: scripts/check.sh
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; H="$ROOT/harness"; fail=0
tok() { echo $(( $(wc -c < "$1") / 4 )); }   # 크기 비교용 바이트/4. 실제 tokenizer·세션 사용량이 아니다.
budget() {
  local n; n=$(wc -l < "$1")
  printf "  %-52s %4d줄  ~%5d tok  한도 %3d  " "${1#$H/}" "$n" "$(tok "$1")" "$2"
  if [ "$n" -le "$2" ]; then echo OK; else echo "초과"; fail=1; fi
}
echo "== 줄 수 예산 =="
budget "$H/CLAUDE.md" 80
root_bytes=$(wc -c < "$H/CLAUDE.md")
if [ "$root_bytes" -gt 5000 ]; then echo "  CLAUDE.md 상시 문맥 예산 초과: ${root_bytes}/5000 bytes"; fail=1; fi
for s in "$H"/.claude/skills/*/SKILL.md; do budget "$s" 120; done
for t in "$H"/.claude/skills/*/*.md; do case "$t" in */SKILL.md) ;; *) budget "$t" 80 ;; esac; done
P="$H/.claude/skills/kickoff/templates/docs/domain/primer.md"; [ -f "$P" ] && budget "$P" 80

echo "== 프런트매터 =="
always_desc=0
for s in "$H"/.claude/skills/*/SKILL.md; do
  d=$(basename "$(dirname "$s")")
  [ "$(head -1 "$s")" = "---" ] || { echo "  $d: 첫 줄이 --- 가 아님"; fail=1; }
  n=$(awk '/^---$/{c++; next} c==1 && /^name:/{sub(/^name:[ ]*/,""); print; exit}' "$s")
  [ "$n" = "$d" ] || { echo "  $d: name '$n' ≠ 폴더명"; fail=1; }
  desc=$(awk '/^---$/{c++; next} c==1 && /^description:/{sub(/^description:[ ]*/,""); print; exit}' "$s")
  [ -n "$desc" ] || { echo "  $d: description 없음"; fail=1; }
  if ! awk '/^---$/{c++; next} c==1 && /^disable-model-invocation: *true/{f=1} END{exit !f}' "$s"; then
    echo "  $d: 사용자 호출 전용 정책 누락 (disable-model-invocation: true)"
    always_desc=$(( always_desc + ${#desc} / 2 ))
    fail=1
  fi
done
echo "  스킬 $(ls -d "$H"/.claude/skills/*/ | wc -l)개 확인"

echo "== 참조 파일 =="
missing=0
for s in "$H"/.claude/skills/*/*.md; do
  dir=$(dirname "$s")
  for ref in $(grep -oE ']\([A-Za-z0-9_./-]+\.(md|py)\)' "$s" | sed 's/^](//; s/)$//'); do
    [ -e "$dir/$ref" ] || { echo "  $(basename "$dir"): 없는 참조 $ref"; missing=1; }
  done
done
[ $missing -eq 0 ] && echo "  모두 존재" || fail=1

echo "== 상시 문맥 크기 (바이트/4 비교값, 실제 토큰 아님; 시스템·도구·대화 제외) =="
always=$(tok "$H/CLAUDE.md")
echo "  CLAUDE.md ~${always} tok  +  스킬 설명 ~${always_desc} tok  =  ~$(( always + always_desc )) tok"
echo "  CLAUDE.md ${root_bytes}/5000 bytes; 실제 Codex 작업자 토큰: tmux_codex.py usage"
echo "== 설치·패키징 회귀 검증 =="
for script in "$ROOT"/scripts/*.sh; do bash -n "$script" || fail=1; done
python3 -B -m unittest discover -s "$ROOT/scripts" -p 'test_*.py' || fail=1
echo
[ $fail -eq 0 ] && echo "모두 통과" || { echo "실패 항목이 있습니다"; exit 1; }
