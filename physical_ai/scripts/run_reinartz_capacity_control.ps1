[CmdletBinding()]
param([switch]$NewWindow)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $Python)) { throw 'Project virtual environment not found.' }

if ($NewWindow) {
    $Command = "Set-Location -LiteralPath '$ProjectRoot'; & '$Python' -u -m src.experiments.reinartz_capacity_control"
    Start-Process powershell.exe -ArgumentList @('-NoExit', '-ExecutionPolicy', 'Bypass', '-Command', $Command) -WorkingDirectory $ProjectRoot
    Write-Host 'Visible F0-C training window opened.'
    exit 0
}

Set-Location $ProjectRoot
& $Python -u -m src.experiments.reinartz_capacity_control
exit $LASTEXITCODE
