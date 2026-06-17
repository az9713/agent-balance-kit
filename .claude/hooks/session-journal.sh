#!/usr/bin/env bash
set -euo pipefail
ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
python3 "$ROOT/.claude/tools/session_journal.py"
exit 0
