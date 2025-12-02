# Stoic Citadel - Windows PowerShell Helper Script
# Quick commands for common operations

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"

function Show-Banner {
    Write-Host ""
    Write-Host "  ╔═══════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║                                               ║" -ForegroundColor Cyan
    Write-Host "  ║           STOIC CITADEL v1.0                  ║" -ForegroundColor Cyan
    Write-Host "  ║                                               ║" -ForegroundColor Cyan
    Write-Host "  ║     Where reason rules, not emotion           ║" -ForegroundColor Cyan
    Write-Host "  ║                                               ║" -ForegroundColor Cyan
    Write-Host "  ╚═══════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Show-Help {
    Show-Banner
    Write-Host "USAGE:" -ForegroundColor Yellow
    Write-Host "  .\citadel.ps1 <command>" -ForegroundColor White
    Write-Host ""
    Write-Host "COMMANDS:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  🚀 TRADING" -ForegroundColor Green
    Write-Host "    start          - Start trading bot (dry-run mode)" -ForegroundColor White
    Write-Host "    stop           - Stop all services" -ForegroundColor White
    Write-Host "    restart        - Restart trading bot" -ForegroundColor White
    Write-Host "    status         - Show container status" -ForegroundColor White
    Write-Host "    logs           - Show bot logs (real-time)" -ForegroundColor White
    Write-Host ""
    Write-Host "  📊 BACKTESTING" -ForegroundColor Green
    Write-Host "    backtest       - Run backtest (SimpleTestStrategy)" -ForegroundColor White
    Write-Host "    download       - Download 90 days of market data" -ForegroundColor White
    Write-Host "    download-long  - Download 180 days of market data" -ForegroundColor White
    Write-Host ""
    Write-Host "  🔧 MANAGEMENT" -ForegroundColor Green
    Write-Host "    dashboard      - Open dashboard in browser" -ForegroundColor White
    Write-Host "    strategies     - List all available strategies" -ForegroundColor White
    Write-Host "    clean          - Stop and remove all containers" -ForegroundColor White
    Write-Host ""
    Write-Host "EXAMPLES:" -ForegroundColor Yellow
    Write-Host "  .\citadel.ps1 start" -ForegroundColor Gray
    Write-Host "  .\citadel.ps1 download" -ForegroundColor Gray
    Write-Host "  .\citadel.ps1 backtest" -ForegroundColor Gray
    Write-Host ""
}

function Start-Bot {
    Show-Banner
    Write-Host "[INFO] Starting Stoic Citadel trading bot..." -ForegroundColor Cyan
    docker-compose up -d freqtrade frequi
    Write-Host ""
    Write-Host "[SUCCESS] Bot started!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Dashboard: http://localhost:3000" -ForegroundColor Yellow
    Write-Host "Login:     stoic_admin" -ForegroundColor Yellow
    Write-Host "Password:  StoicGuard2024" -ForegroundColor Yellow
    Write-Host ""
}

function Stop-Bot {
    Show-Banner
    Write-Host "[INFO] Stopping all services..." -ForegroundColor Cyan
    docker-compose down
    Write-Host "[SUCCESS] All services stopped!" -ForegroundColor Green
}

function Restart-Bot {
    Show-Banner
    Write-Host "[INFO] Restarting trading bot..." -ForegroundColor Cyan
    docker-compose restart freqtrade
    Write-Host "[SUCCESS] Bot restarted!" -ForegroundColor Green
}

function Show-Status {
    Show-Banner
    Write-Host "[INFO] Container status:" -ForegroundColor Cyan
    Write-Host ""
    docker-compose ps
}

function Show-Logs {
    Show-Banner
    Write-Host "[INFO] Showing bot logs (Ctrl+C to exit)..." -ForegroundColor Cyan
    Write-Host ""
    docker-compose logs -f freqtrade
}

function Run-Backtest {
    Show-Banner
    Write-Host "[INFO] Running backtest (SimpleTestStrategy)..." -ForegroundColor Cyan
    Write-Host ""
    docker-compose run --rm freqtrade backtesting `
        --config /freqtrade/user_data/config/config.json `
        --strategy SimpleTestStrategy `
        --timerange 20241001-20241202
    Write-Host ""
    Write-Host "[SUCCESS] Backtest completed!" -ForegroundColor Green
}

function Download-Data {
    Show-Banner
    Write-Host "[INFO] Downloading 90 days of market data..." -ForegroundColor Cyan
    Write-Host ""
    docker-compose run --rm freqtrade download-data `
        --config /freqtrade/user_data/config/config.json `
        --exchange binance `
        --pairs BTC/USDT ETH/USDT BNB/USDT SOL/USDT XRP/USDT `
        --timeframe 5m `
        --days 90
    Write-Host ""
    Write-Host "[SUCCESS] Data downloaded!" -ForegroundColor Green
}

function Download-LongData {
    Show-Banner
    Write-Host "[INFO] Downloading 180 days of market data..." -ForegroundColor Cyan
    Write-Host ""
    docker-compose run --rm freqtrade download-data `
        --config /freqtrade/user_data/config/config.json `
        --exchange binance `
        --pairs BTC/USDT ETH/USDT BNB/USDT SOL/USDT XRP/USDT `
        --timeframe 5m `
        --days 180
    Write-Host ""
    Write-Host "[SUCCESS] Data downloaded!" -ForegroundColor Green
}

function Open-Dashboard {
    Show-Banner
    Write-Host "[INFO] Opening dashboard in browser..." -ForegroundColor Cyan
    Start-Process "http://localhost:3000"
    Write-Host "[SUCCESS] Dashboard opened!" -ForegroundColor Green
}

function List-Strategies {
    Show-Banner
    Write-Host "[INFO] Available strategies:" -ForegroundColor Cyan
    Write-Host ""
    docker-compose run --rm freqtrade list-strategies `
        --config /freqtrade/user_data/config/config.json
}

function Clean-All {
    Show-Banner
    Write-Host "[WARNING] This will stop and remove all containers!" -ForegroundColor Yellow
    $confirm = Read-Host "Are you sure? (yes/no)"
    if ($confirm -eq "yes") {
        Write-Host "[INFO] Cleaning up..." -ForegroundColor Cyan
        docker-compose down -v
        Write-Host "[SUCCESS] Cleanup completed!" -ForegroundColor Green
    } else {
        Write-Host "[CANCELLED] Cleanup cancelled." -ForegroundColor Yellow
    }
}

# Main command router
switch ($Command.ToLower()) {
    "start"         { Start-Bot }
    "stop"          { Stop-Bot }
    "restart"       { Restart-Bot }
    "status"        { Show-Status }
    "logs"          { Show-Logs }
    "backtest"      { Run-Backtest }
    "download"      { Download-Data }
    "download-long" { Download-LongData }
    "dashboard"     { Open-Dashboard }
    "strategies"    { List-Strategies }
    "clean"         { Clean-All }
    "help"          { Show-Help }
    default         { Show-Help }
}
