param (
    [Parameter(Mandatory = $false)]
    [string]$BackendUrl = "http://localhost:8000",

    [Parameter(Mandatory = $false)]
    [string]$FrontendUrl = "http://localhost:5173"
)

$ErrorActionPreference = "Continue"

$BackendUrl = $BackendUrl.TrimEnd('/')
$FrontendUrl = $FrontendUrl.TrimEnd('/')

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Space Explorer Production Smoke Test" -ForegroundColor Cyan
Write-Host " Backend:  $BackendUrl" -ForegroundColor Cyan
Write-Host " Frontend: $FrontendUrl" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$allPassed = $true

function Report-Result {
    param (
        [string]$Name,
        [bool]$Success,
        [string]$Detail = ""
    )
    if ($Success) {
        Write-Host "PASS: $Name $Detail" -ForegroundColor Green
    } else {
        Write-Host "FAIL: $Name $Detail" -ForegroundColor Red
        $script:allPassed = $false
    }
}

# 1. Health check and wait for bootstrap_status == "done" (up to 10 minutes)
Write-Host "`n[1/7] Polling /health until bootstrap_status is 'done' (timeout 10 min)..."
$timeoutSeconds = 600
$startTime = [DateTime]::UtcNow
$healthDone = $false
$lastStatus = "unknown"

while (([DateTime]::UtcNow - $startTime).TotalSeconds -lt $timeoutSeconds) {
    try {
        $healthRes = Invoke-RestMethod -Uri "$BackendUrl/health" -Method Get -TimeoutSec 10 -ErrorAction Stop
        $lastStatus = $healthRes.bootstrap_status
        if ($lastStatus -eq "done") {
            $healthDone = $true
            break
        }
        if ($lastStatus -like "failed*") {
            break
        }
    } catch {
        $lastStatus = "unreachable ($($_.Exception.Message))"
    }
    Start-Sleep -Seconds 3
}

Report-Result -Name "GET /health" -Success $healthDone -Detail "(bootstrap_status: $lastStatus)"
if (-not $healthDone) {
    Write-Host "Aborting further tests because /health did not complete bootstrap." -ForegroundColor Red
    exit 1
}

# 2. Candidate lunar sites list
try {
    $sitesRes = Invoke-RestMethod -Uri "$BackendUrl/api/v1/lunar/sites" -Method Get -TimeoutSec 15 -ErrorAction Stop
    $count = if ($sitesRes -is [System.Array]) { $sitesRes.Count } else { ($sitesRes.items.Count) }
    Report-Result -Name "GET /api/v1/lunar/sites" -Success ($count -gt 0) -Detail "($count sites returned)"
} catch {
    Report-Result -Name "GET /api/v1/lunar/sites" -Success $false -Detail "($($_.Exception.Message))"
}

# 3. Illumination timeline
$illumUrl = "$BackendUrl/api/v1/lunar/sites/site-shackleton-01/illumination?start=2026-12-01&days=30&step_minutes=30"
try {
    $illumRes = Invoke-RestMethod -Uri $illumUrl -Method Get -TimeoutSec 30 -ErrorAction Stop
    $pts = if ($illumRes.series) { $illumRes.series.Count } else { 0 }
    Report-Result -Name "GET /api/v1/lunar/sites/site-shackleton-01/illumination" -Success ($pts -gt 0) -Detail "($pts timeline points)"
} catch {
    Report-Result -Name "GET /api/v1/lunar/sites/site-shackleton-01/illumination" -Success $false -Detail "($($_.Exception.Message))"
}

# 4. Earth visibility timeline
$earthUrl = "$BackendUrl/api/v1/lunar/sites/site-shackleton-01/earth-visibility?start=2026-12-01&days=30&step_minutes=30"
try {
    $earthRes = Invoke-RestMethod -Uri $earthUrl -Method Get -TimeoutSec 30 -ErrorAction Stop
    $epts = if ($earthRes.series) { $earthRes.series.Count } else { 0 }
    Report-Result -Name "GET /api/v1/lunar/sites/site-shackleton-01/earth-visibility" -Success ($epts -gt 0) -Detail "($epts timeline points)"
} catch {
    Report-Result -Name "GET /api/v1/lunar/sites/site-shackleton-01/earth-visibility" -Success $false -Detail "($($_.Exception.Message))"
}

# 5. Solar power opportunity estimate (POST)
$solarUrl = "$BackendUrl/api/v1/lunar/sites/site-shackleton-01/solar-estimate"
$solarBody = @{
    start = "2026-12-01"
    days = 30
    step_minutes = 30
} | ConvertTo-Json
try {
    $solarRes = Invoke-RestMethod -Uri $solarUrl -Method Post -Body $solarBody -ContentType "application/json" -TimeoutSec 30 -ErrorAction Stop
    $s_ok = ($null -ne $solarRes.illumination_opportunity)
    $litHours = if ($s_ok) { $solarRes.illumination_opportunity.hours_any_part_lit } else { 0 }
    Report-Result -Name "POST /api/v1/lunar/sites/site-shackleton-01/solar-estimate" -Success $s_ok -Detail "(illumination lit: $litHours hrs)"
} catch {
    Report-Result -Name "POST /api/v1/lunar/sites/site-shackleton-01/solar-estimate" -Success $false -Detail "($($_.Exception.Message))"
}

# 6. Perseverance latest location
$roverUrl = "$BackendUrl/api/v1/rovers/perseverance/latest-location"
try {
    $roverRes = Invoke-RestMethod -Uri $roverUrl -Method Get -TimeoutSec 15 -ErrorAction Stop
    $sol = $roverRes.sol
    Report-Result -Name "GET /api/v1/rovers/perseverance/latest-location" -Success ($null -ne $sol) -Detail "(Sol $sol)"
} catch {
    Report-Result -Name "GET /api/v1/rovers/perseverance/latest-location" -Success $false -Detail "($($_.Exception.Message))"
}

# 7. Frontend route /lunar
$frontendLunarUrl = "$FrontendUrl/lunar"
try {
    $fRes = Invoke-WebRequest -Uri $frontendLunarUrl -Method Get -UseBasicParsing -TimeoutSec 15 -ErrorAction Stop
    Report-Result -Name "GET frontend $frontendLunarUrl" -Success ($fRes.StatusCode -eq 200) -Detail "(HTTP $($fRes.StatusCode))"
} catch {
    Report-Result -Name "GET frontend $frontendLunarUrl" -Success $false -Detail "($($_.Exception.Message))"
}

Write-Host "`n----------------------------------------------------------"
if ($allPassed) {
    Write-Host "All production smoke checks PASSED." -ForegroundColor Green
    exit 0
} else {
    Write-Host "One or more production smoke checks FAILED." -ForegroundColor Red
    exit 1
}
