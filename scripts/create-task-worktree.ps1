param(
  [Parameter(Mandatory=$true)][string]$Task
)
python .claude/tools/agent_ready_loop.py --task $Task --open-code
