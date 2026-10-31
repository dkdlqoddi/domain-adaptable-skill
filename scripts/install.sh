#!/usr/bin/env bash
# 사용: scripts/install.sh <대상 디렉토리> [--tool codex|claude|claude-commands] [--force]
# 기본: Codex 설치, 충돌 시 쓰기 전에 중단. --force: 백업 후 갱신. docs/는 항상 보존.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ROOT/scripts/install.py" "$@"
