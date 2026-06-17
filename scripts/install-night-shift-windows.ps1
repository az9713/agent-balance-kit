param(
  [string]$TaskName = "AgentBalanceNightShift",
  [string]$RepoPath = (Get-Location).Path,
  [string]$IntervalMinutes = "15"
)
$Action = New-ScheduledTaskAction -Execute "pwsh.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$RepoPath\scripts\night-shift-once.ps1`"" -WorkingDirectory $RepoPath
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes ([int]$IntervalMinutes))
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Description "Agent Balance Kit conservative night-shift poller" -Force
Write-Host "Installed scheduled task $TaskName every $IntervalMinutes minutes for $RepoPath"
