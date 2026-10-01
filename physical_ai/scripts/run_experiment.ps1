[CmdletBinding()]
param([string]$Config = 'configs/baseline.yaml', [switch]$Background)
$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { throw 'Run scripts\setup.ps1 first.' }
New-Item -ItemType Directory -Force -Path logs | Out-Null
if ($Background) {
    if (Test-Path 'run.pid') {
        $OldPid = [int](Get-Content 'run.pid')
        if (Get-Process -Id $OldPid -ErrorAction SilentlyContinue) { throw "Experiment is already running (PID $OldPid)." }
    }
    $Process = Start-Process -FilePath $Python -ArgumentList @('-m','src.experiments.run_baseline','--config',$Config) -WorkingDirectory $ProjectRoot -RedirectStandardOutput 'logs\runner.log' -RedirectStandardError 'logs\runner.error.log' -WindowStyle Hidden -PassThru
    Set-Content -Path 'run.pid' -Value $Process.Id
    Write-Host "Started background experiment PID $($Process.Id). Logs: logs\runner.log"
} else {
    & $Python -m src.experiments.run_baseline --config $Config
    exit $LASTEXITCODE
}
