$root = $env:CLAUDE_PROJECT_DIR
if (-not $root) { $root = (Get-Location).Path }
$inputJson = [Console]::In.ReadToEnd()
$inputJson | python "$root/.claude/tools/session_journal.py"
exit 0
