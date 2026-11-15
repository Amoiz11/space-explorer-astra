$ErrorActionPreference = "Stop"

$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$RequirementsFile = Join-Path $PSScriptRoot "backend\requirements.txt"

# Ensure .venv exists and dependencies are installed
if (-not (Test-Path $VenvPython)) {
    Write-Host "[test.ps1] Virtual environment not found. Creating .venv..." -ForegroundColor Cyan
    python -m venv (Join-Path $PSScriptRoot ".venv")
    Write-Host "[test.ps1] Installing dependencies from backend/requirements.txt..." -ForegroundColor Cyan
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -r $RequirementsFile
}

# Run pytest on backend/tests
& $VenvPython -m pytest backend/tests $args
