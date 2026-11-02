param([switch]$Publish, [ValidateSet('07:00','12:00','17:00')][string]$Slot, [string]$Date)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$python = Join-Path (Get-Location) '.venv\Scripts\python.exe'
$mode = if ($Publish) { 'publish' } else { 'render' }
# Select a slot when the archive contains several articles on the same day.
$options = @()
if ($Slot) { $options += @('--slot', $Slot) }
if ($Date) { $options += @('--date', $Date) }
& $python scripts/english_media.py $mode @options
exit $LASTEXITCODE

