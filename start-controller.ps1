# AdaptiveAI Finance Controller Local Start Script
$ErrorActionPreference = "Continue"

$SCOOP_SHIMS = "$env:USERPROFILE\scoop\shims"
$PG_BIN = "$env:USERPROFILE\scoop\apps\postgresql\current\bin"
$PG_DATA = "$env:USERPROFILE\scoop\apps\postgresql\current\data"
$env:PATH = "$PG_BIN;$SCOOP_SHIMS;$env:PATH"

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "     Starting AdaptiveAI Finance Controller      " -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# 1. Start PostgreSQL if not running
$pgRunning = Get-Process -Name "postgres" -ErrorAction SilentlyContinue
if (-not $pgRunning) {
    Write-Host "[1/4] Starting PostgreSQL..." -ForegroundColor Yellow
    Start-Process -FilePath "postgres.exe" -ArgumentList "-D", "`"$PG_DATA`"" -WindowStyle Hidden
    Start-Sleep -Seconds 2
} else {
    Write-Host "[1/4] PostgreSQL is already running." -ForegroundColor Green
}

# 2. Start Redis if not running
$redisRunning = Get-Process -Name "redis-server" -ErrorAction SilentlyContinue
if (-not $redisRunning) {
    Write-Host "[2/4] Starting Redis..." -ForegroundColor Yellow
    Start-Process -FilePath "redis-server.exe" -WindowStyle Hidden
    Start-Sleep -Seconds 1
} else {
    Write-Host "[2/4] Redis is already running." -ForegroundColor Green
}

# 3. Start Backend
$backendDir = Join-Path $PSScriptRoot "backend"
$uvicornExe = Join-Path $backendDir ".venv\Scripts\uvicorn.exe"
Write-Host "[3/4] Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Yellow
Start-Process -FilePath $uvicornExe -ArgumentList "app.main:app", "--host", "127.0.0.1", "--port", "8000" -WorkingDirectory $backendDir -WindowStyle Minimized

# 4. Start Frontend
$frontendDir = Join-Path $PSScriptRoot "frontend"
Write-Host "[4/4] Starting Frontend Vite Server on http://localhost:5173..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm run dev" -WorkingDirectory $frontendDir -WindowStyle Minimized

Start-Sleep -Seconds 3
Write-Host "`nAll services started successfully!" -ForegroundColor Green
Write-Host "  - Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "  - Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
