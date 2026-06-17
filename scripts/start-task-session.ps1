param(
  [Parameter(Mandatory=$true)][string]$Task,
  [switch]$RemoteControl
)
$ErrorActionPreference = "Stop"
python .claude/tools/agent_ready_loop.py --task $Task
$worktree = Join-Path ".worktrees" $Task
Set-Location $worktree
if ($RemoteControl) {
  claude remote-control --name $Task
} else {
  claude
}
