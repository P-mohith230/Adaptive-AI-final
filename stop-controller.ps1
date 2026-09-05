# AdaptiveAI Finance Controller Local Stop Script
Write-Host "Stopping AdaptiveAI Finance Controller local services..." -ForegroundColor Yellow

# Stop backend uvicorn
Get-Process | Where-Object { $_.CommandLine -like "*uvicorn*app.main:app*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Stop redis-server
Get-Process -Name "redis-server" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Stop postgres
$SCOOP_SHIMS = "$env:USERPROFILE\scoop\shims"
$PG_BIN = "$env:USERPROFILE\scoop\apps\postgresql\current\bin"
$PG_DATA = "$env:USERPROFILE\scoop\apps\postgresql\current\data"
$env:PATH = "$PG_BIN;$SCOOP_SHIMS;$env:PATH"
if (Get-Command pg_ctl -ErrorAction SilentlyContinue) {
    & pg_ctl -D "$PG_DATA" stop -m fast
} else {
    Get-Process -Name "postgres" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
}

Write-Host "✓ All AdaptiveAI Finance Controller services stopped." -ForegroundColor Green
