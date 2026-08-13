[CmdletBinding()]
param(
    [int]$ModelSeed = 42,
    [int]$Epochs = 30,
    [switch]$NewWindow
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
$Config = Join-Path $ProjectRoot 'configs\reinartz_f0_f1.yaml'

if (-not (Test-Path -LiteralPath $Python)) {
    throw 'Project virtual environment was not found. Run scripts\setup.ps1 first.'
}

$PythonArgs = @(
    '-u',
    '-m', 'src.experiments.reinartz_f0_f1',
    '--config', $Config,
    '--model-seed', $ModelSeed,
    '--epochs', $Epochs
)

if ($NewWindow) {
    $ArgumentList = @(
        '-NoExit',
        '-ExecutionPolicy', 'Bypass',
        '-Command',
        "Set-Location -LiteralPath '$ProjectRoot'; & '$Python' $($PythonArgs -join ' ')"
    )
    Start-Process powershell.exe -ArgumentList $ArgumentList -WorkingDirectory $ProjectRoot
    Write-Host "Visible training window opened: model seed $ModelSeed, epochs $Epochs"
    exit 0
}

Set-Location $ProjectRoot
Write-Host '============================================================'
Write-Host "Reinartz F0/F1 training | model seed=$ModelSeed | epochs=$Epochs"
Write-Host 'Progress is printed every 10% of each epoch.'
Write-Host '============================================================'
& $Python @PythonArgs
exit $LASTEXITCODE
