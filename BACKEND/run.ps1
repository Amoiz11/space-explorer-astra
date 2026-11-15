$ErrorActionPreference = "Stop"

$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$RequirementsFile = Join-Path $PSScriptRoot "backend\requirements.txt"

# If .venv or python.exe does not exist, create it and install dependencies
if (-not (Test-Path $VenvPython)) {
    Write-Host "[run.ps1] Virtual environment not found. Creating .venv..." -ForegroundColor Cyan
    python -m venv (Join-Path $PSScriptRoot ".venv")
    Write-Host "[run.ps1] Upgrading pip and installing requirements from backend/requirements.txt..." -ForegroundColor Cyan
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -r $RequirementsFile
}

Write-Host "[run.ps1] Starting Space Explorer API server on http://0.0.0.0:8000..." -ForegroundColor Green
& $VenvPython -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
