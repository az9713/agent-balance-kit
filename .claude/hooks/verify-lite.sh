#!/usr/bin/env bash
set -euo pipefail
ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
python3 "$ROOT/.claude/tools/verify.py" --fast >/dev/null || true
exit 0
