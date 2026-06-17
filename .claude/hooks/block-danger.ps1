$inputJson = [Console]::In.ReadToEnd()
try { $data = $inputJson | ConvertFrom-Json } catch { exit 0 }
$cmd = ""
if ($data.tool_input -and $data.tool_input.command) { $cmd = [string]$data.tool_input.command }

$danger = @(
  'rm -rf /',
  'rm -rf ~',
  'Remove-Item -Recurse -Force $HOME',
  'format ',
  'del /s /q',
  'rd /s /q',
  'git reset --hard',
  'git clean -fdx'
)

foreach ($pattern in $danger) {
  if ($cmd -like "*$pattern*") {
    @{
      hookSpecificOutput = @{
        hookEventName = "PreToolUse"
        permissionDecision = "deny"
        permissionDecisionReason = "Blocked by Agent Balance Kit: destructive command pattern '$pattern'. Ask the user explicitly."
      }
    } | ConvertTo-Json -Depth 5
    exit 0
  }
}
exit 0
