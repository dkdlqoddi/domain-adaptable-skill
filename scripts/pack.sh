#!/usr/bin/env bash
# 업로드용 설치 키트 생성. 임시 폴더에 풀고 같은 설치기로 과제 프로젝트에 설치한다.
# 사용: scripts/pack.sh   →  dist/harness.zip
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/dist"; STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$OUT"
mkdir -p "$STAGE/payload/scripts"
cp -r "$ROOT/harness" "$STAGE/payload/harness"
cp "$ROOT/scripts/install.sh" "$ROOT/scripts/install.py" "$STAGE/payload/scripts/"
( cd "$STAGE/payload" && zip -qr "$STAGE/harness.zip" . )
zip -qz "$STAGE/harness.zip" <<'EOF'
하네스 설치 키트 — Bash, Python 3.8+ 필요 (unzip이 없으면 python3 -m zipfile -e)
과제 프로젝트 루트에서 실행 (프로젝트에 직접 압축을 풀지 않음):
  HARNESS_KIT=$(mktemp -d)
  unzip -q harness.zip -d "$HARNESS_KIT" || python3 -m zipfile -e harness.zip "$HARNESS_KIT"
  bash "$HARNESS_KIT/scripts/install.sh" "$PWD" && rm harness.zip
기본은 Codex(AGENTS.md + .agents/skills/). Claude: --tool claude / 구버전 Claude: --tool claude-commands
충돌 시 쓰기 전에 중단(zip은 남음). --force는 백업 후 교체. docs/는 항상 보존.
그다음 치트시트 준비 블록대로 Git 설정·첫 커밋 → codex → $kickoff README.md <마감 시각>.
EOF
mv "$STAGE/harness.zip" "$OUT/harness.zip"
echo "생성: $OUT/harness.zip ($(du -h "$OUT/harness.zip" | cut -f1))"
unzip -Z1 "$OUT/harness.zip" | grep -v '/$' | sort | sed 's/^/  /'
