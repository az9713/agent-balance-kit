$root = $env:CLAUDE_PROJECT_DIR
if (-not $root) { $root = (Get-Location).Path }
python "$root/.claude/tools/verify.py" --fast
if ($LASTEXITCODE -ne 0) {
  Write-Error "Verification failed. Fix failing checks before marking the task complete."
  exit 2
}
exit 0
