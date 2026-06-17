#!/usr/bin/env bash
set -euo pipefail
python "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/tools/require_evidence.py"
