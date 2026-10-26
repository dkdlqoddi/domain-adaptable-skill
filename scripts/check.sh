#!/usr/bin/env bash
# 하네스 점검: 줄 수 예산, 프런트매터, 참조 파일, 매 세션 항상 로드되는 토큰 근사치.
# 사용: scripts/check.sh
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; H="$ROOT/harness"; fail=0
tok() { echo $(( $(wc -c < "$1") / 4 )); }   # 근사: 4바이트 ≈ 1토큰 (한글 기준 보수적 추정)
budget() {
  local n; n=$(wc -l < "$1")
  printf "  %-52s %4d줄  ~%5d tok  한도 %3d  " "${1#$H/}" "$n" "$(tok "$1")" "$2"
  if [ "$n" -le "$2" ]; then echo OK; else echo "초과"; fail=1; fi
}
echo "== 줄 수 예산 =="
budget "$H/CLAUDE.md" 80
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
    echo "  $d: (참고) 모델 자동 호출 허용 — 설명 ~$(( ${#desc} / 2 )) tok 이 매 세션 컨텍스트에 실림"
    always_desc=$(( always_desc + ${#desc} / 2 ))
  fi
done
echo "  스킬 $(ls -d "$H"/.claude/skills/*/ | wc -l)개 확인"

echo "== 참조 파일 =="
missing=0
for s in "$H"/.claude/skills/*/SKILL.md; do
  dir=$(dirname "$s")
  for ref in $(grep -o '](\([A-Za-z0-9_./-]*\.md\))' "$s" | sed 's/^](//; s/)$//'); do
    [ -e "$dir/$ref" ] || { echo "  $(basename "$dir"): 없는 참조 $ref"; missing=1; }
  done
done
[ $missing -eq 0 ] && echo "  모두 존재" || fail=1

echo "== 매 세션 항상 로드되는 양 (근사) =="
always=$(tok "$H/CLAUDE.md")
echo "  CLAUDE.md ~${always} tok  +  스킬 설명 ~${always_desc} tok  =  ~$(( always + always_desc )) tok"
echo
[ $fail -eq 0 ] && echo "모두 통과" || { echo "실패 항목이 있습니다"; exit 1; }
