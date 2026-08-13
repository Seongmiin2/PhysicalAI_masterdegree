[CmdletBinding()]
param([switch]$Force)
$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $ProjectRoot

function Test-Python([string]$Executable) {
    try { & $Executable -c "import encodings, sys; print(sys.version)" | Out-Host; return $LASTEXITCODE -eq 0 } catch { return $false }
}

$Candidates = @(
    (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'),
    (Get-Command python -ErrorAction SilentlyContinue).Source
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
$Python = $Candidates | Where-Object { Test-Python $_ } | Select-Object -First 1
if (-not $Python) {
    throw "Python is missing or damaged. Repair/install Python 3.11+ first; current interpreter cannot import encodings."
}
if ($Force -and (Test-Path '.venv')) { throw 'Refusing to overwrite .venv automatically. Remove it explicitly if replacement is intended.' }
if (-not (Test-Path '.venv\Scripts\python.exe')) { & $Python -m venv .venv }
& .venv\Scripts\python.exe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed.' }
& .venv\Scripts\python.exe -m pip install -e '.[dev]'
if ($LASTEXITCODE -ne 0) { throw 'Project dependency installation failed.' }
$Directories = @('data/raw/tep','data/processed/tep','db','logs','checkpoints')
foreach ($Directory in $Directories) { New-Item -ItemType Directory -Force -Path $Directory | Out-Null }
& .venv\Scripts\python.exe -m src.data.download
if ($LASTEXITCODE -ne 0) { throw 'TEP manifest creation failed.' }
& .venv\Scripts\python.exe -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Test suite failed.' }
Write-Host 'Setup complete.'
