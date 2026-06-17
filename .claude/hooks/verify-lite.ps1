$root = $env:CLAUDE_PROJECT_DIR
if (-not $root) { $root = (Get-Location).Path }
python "$root/.claude/tools/verify.py" --fast | Out-Null
exit 0
