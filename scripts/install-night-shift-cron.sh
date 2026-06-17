#!/usr/bin/env bash
set -euo pipefail
REPO="$(pwd)"
LINE="*/15 * * * * cd '$REPO' && python .claude/tools/night_shift.py --sync --max-tasks 1 >> .agent-harness/night-shift.log 2>&1"
( crontab -l 2>/dev/null | grep -v "agent_balance_kit night_shift" ; echo "$LINE # agent_balance_kit night_shift" ) | crontab -
echo "Installed cron entry: $LINE"
