$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot
python -m asset_analysis.ux.setup_check --config private/config.local.yaml --markdown reports/private/latest/setup_check.md
if ($LASTEXITCODE -ne 0) {
  Write-Host "Setup check failed. See reports/private/latest/setup_check.md"
  Write-Host "Init command: python -m asset_analysis.onboarding.init_project"
  exit $LASTEXITCODE
}
python -m asset_analysis.workflow.daily_run --config private/config.local.yaml
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}
Write-Host "Chat summary: reports/private/latest/chat_summary.txt"
