#!/usr/bin/env bash
set -euo pipefail
TASK="${1:?Usage: scripts/start-task-session.sh TASK-001 [--remote-control]}"
python .claude/tools/agent_ready_loop.py --task "$TASK"
cd ".worktrees/$TASK"
if [[ "${2:-}" == "--remote-control" ]]; then
  claude remote-control --name "$TASK"
else
  claude
fi
