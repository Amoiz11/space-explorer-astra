#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"

Write-Host "Pushing main to origin..."
git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to push to origin"
    exit $LASTEXITCODE
}

Write-Host "Pushing main to mine..."
git push mine main
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to push to mine"
    exit $LASTEXITCODE
}

Write-Host "Pushed to all remotes successfully."
