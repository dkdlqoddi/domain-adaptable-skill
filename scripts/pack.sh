#!/usr/bin/env bash
# 업로드용 zip 생성. 압축을 풀면 CLAUDE.md, .claude/, docs/ 가 프로젝트 루트에 바로 생긴다.
# 사용: scripts/pack.sh   →  dist/harness.zip
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/dist"; STAGE="$(mktemp -d)"
mkdir -p "$OUT"
cp -r "$ROOT/harness/." "$STAGE/"
mkdir -p "$STAGE/docs"
cp -r "$ROOT/harness/.claude/skills/kickoff/templates/docs/." "$STAGE/docs/"
cat > "$STAGE/INSTALL.txt" <<'EOF'
하네스 설치 (프로젝트 루트에서)
1) unzip -n harness.zip                                  # -n: 이미 있는 파일은 건너뜀
2) 기존 CLAUDE.md가 있어서 건너뛰었다면:
   unzip -p harness.zip CLAUDE.md > .claude/CLAUDE.md    # 둘 다 로드됨
3) claude 실행  →  /kickoff
EOF
( cd "$STAGE" && rm -f "$OUT/harness.zip" && zip -qr "$OUT/harness.zip" . )
rm -rf "$STAGE"
echo "생성: $OUT/harness.zip ($(du -h "$OUT/harness.zip" | cut -f1))"
unzip -Z1 "$OUT/harness.zip" | grep -v '/$' | sort | sed 's/^/  /'
