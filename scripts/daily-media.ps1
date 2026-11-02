param([switch]$Publish)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$python = Join-Path (Get-Location) '.venv\Scripts\python.exe'
$mode = if ($Publish) { 'publish' } else { 'render' }
# No --date: process latest available formal article; repeat runs reuse saved state.
& $python scripts/english_media.py $mode
exit $LASTEXITCODE
