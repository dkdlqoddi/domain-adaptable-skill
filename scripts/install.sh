#!/usr/bin/env bash
# 하네스를 대상 프로젝트에 설치한다. 기존 파일은 덮어쓰지 않는다.
# --force 는 .claude/ 와 CLAUDE.md 만 덮어쓴다. docs/ 는 작업 상태이므로 절대 덮어쓰지 않는다.
# 사용: scripts/install.sh <대상 디렉토리> [--force]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/harness"
DST="${1:-}"; FORCE="${2:-}"
if [ -z "$DST" ] || [ ! -d "$DST" ]; then
  echo "사용법: $0 <대상 디렉토리> [--force]"; exit 1
fi
DST="$(cd "$DST" && pwd)"
copied=0; skipped=0
copy() {
  if [ -e "$2" ] && [ "$FORCE" != "--force" ]; then
    echo "  skip  ${2#$DST/} (이미 있음)"; skipped=$((skipped+1)); return
  fi
  mkdir -p "$(dirname "$2")"; cp "$1" "$2"
  echo "  copy  ${2#$DST/}"; copied=$((copied+1))
}
echo "== 스킬 (.claude/) =="
while IFS= read -r -d '' f; do copy "$f" "$DST/${f#$SRC/}"; done < <(find "$SRC/.claude" -type f -print0 | sort -z)
echo "== CLAUDE.md =="
if [ -e "$DST/CLAUDE.md" ] && [ "$FORCE" != "--force" ]; then
  if cmp -s "$SRC/CLAUDE.md" "$DST/CLAUDE.md"; then
    echo "  skip  CLAUDE.md (이미 설치됨)"; skipped=$((skipped+1))
  elif [ -e "$DST/.claude/CLAUDE.md" ] && cmp -s "$SRC/CLAUDE.md" "$DST/.claude/CLAUDE.md"; then
    echo "  skip  .claude/CLAUDE.md (이미 설치됨)"; skipped=$((skipped+1))
  else
    copy "$SRC/CLAUDE.md" "$DST/.claude/CLAUDE.md"
    echo "  note  프로젝트의 기존 CLAUDE.md는 그대로 두고 .claude/CLAUDE.md 로 설치했습니다(둘 다 로드됨). 충돌하는 규칙이 없는지 훑어보세요."
  fi
else
  copy "$SRC/CLAUDE.md" "$DST/CLAUDE.md"
fi
echo "== docs/ 템플릿 (덮어쓰지 않음) =="
FORCE=""
TPL="$SRC/.claude/skills/kickoff/templates/docs"
while IFS= read -r -d '' f; do copy "$f" "$DST/docs/${f#$TPL/}"; done < <(find "$TPL" -type f -print0 | sort -z)
echo
echo "완료: 복사 $copied, 건너뜀 $skipped  →  $DST"
echo "다음:  cd \"$DST\" && claude   →   /kickoff"
