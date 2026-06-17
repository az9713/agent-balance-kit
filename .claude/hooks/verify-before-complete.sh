#!/usr/bin/env bash
set -euo pipefail
ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
if ! python3 "$ROOT/.claude/tools/verify.py" --fast; then
  echo "Verification failed. Fix failing checks before marking the task complete." >&2
  exit 2
fi
exit 0
