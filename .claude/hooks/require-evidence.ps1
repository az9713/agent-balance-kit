$ErrorActionPreference = "Stop"
$root = $env:CLAUDE_PROJECT_DIR
if (-not $root) { $root = (Get-Location).Path }
python "$root/.claude/tools/require_evidence.py"
exit $LASTEXITCODE
