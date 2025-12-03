# ==============================================================================
# STOIC CITADEL - PowerShell Management Script v2.0
# ==============================================================================
# Complete rewrite with monitoring and security features
# ==============================================================================

param(
    [Parameter(Position=0)]
    [string]$Command = "help",
    
    [Parameter(Position=1)]
    [string]$Strategy = "StoicStrategyV1",
    
    [Parameter(Position=2)]
    [string]$Service = "freqtrade"
)

$ErrorActionPreference = "Stop"
$PROJECT_DIR = "C:\hft-algotrade-bot"

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

function Write-ColorOutput {
    param([string]$ForegroundColor, [string]$Message)
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    Write-Output $Message
    $host.UI.RawUI.ForegroundColor = $fc
}

function Show-Header {
    Write-Host ""
    Write-ColorOutput "Cyan" "╔════════════════════════════════════════════════════════════╗"
    Write-ColorOutput "Cyan" "║            STOIC CITADEL - TRADING BOT v2.0            ║"
    Write-ColorOutput "Cyan" "╚════════════════════════════════════════════════════════════╝"
    Write-Host ""
}

function Test-EnvFile {
    if (-not (Test-Path ".env")) {
        Write-ColorOutput "Yellow" "⚠️  .env файл не найден. Создаю из шаблона..."
        Copy-Item ".env.example" ".env"
        Write-ColorOutput "Green" "✅ Создан .env файл"
        Write-ColorOutput "Yellow" "⚠️  ВАЖНО: Настройте .env файл перед продолжением!"
        return $false
    }
    return $true
}

# ==============================================================================
# SECURITY FUNCTIONS
# ==============================================================================

function New-SecurePassword {
    param([int]$Length = 32)
    $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    $password = ""
    for ($i = 0; $i -lt $Length; $i++) {
        $password += $chars[(Get-Random -Minimum 0 -Maximum $chars.Length)]
    }
    return $password
}

function Invoke-GenerateSecrets {
    Show-Header
    Write-ColorOutput "Cyan" "🔐 Генерация безопасных паролей..."
    
    $freqtradePass = New-SecurePassword -Length 32
    $postgresPass = New-SecurePassword -Length 32
    $telegramToken = "<YOUR_TELEGRAM_BOT_TOKEN>"
    $telegramChatId = "<YOUR_TELEGRAM_CHAT_ID>"
    
    Write-ColorOutput "Green" "✅ Пароли сгенерированы!"
    Write-Host ""
    Write-ColorOutput "Yellow" "📋 Скопируйте эти значения в .env файл:"
    Write-Host ""
    Write-Host "FREQTRADE_API_PASSWORD=$freqtradePass"
    Write-Host "POSTGRES_PASSWORD=$postgresPass"
    Write-Host ""
    Write-ColorOutput "Cyan" "💾 Сохраню в .env.generated для справки..."
    
    $envContent = @"
FREQTRADE_API_PASSWORD=$freqtradePass
POSTGRES_PASSWORD=$postgresPass
TELEGRAM_TOKEN=$telegramToken
TELEGRAM_CHAT_ID=$telegramChatId
"@
    
    $envContent | Out-File -FilePath ".env.generated" -Encoding UTF8
    Write-ColorOutput "Green" "✅ Пароли сохранены в .env.generated"
    Write-ColorOutput "Yellow" "⚠️  Скопируйте их в .env вручную!"
}

# ==============================================================================
# MONITORING FUNCTIONS
# ==============================================================================

function Invoke-HealthCheck {
    Show-Header
    Write-ColorOutput "Cyan" "🏥 Проверка здоровья всех сервисов..."
    Write-Host ""
    
    Set-Location $PROJECT_DIR
    
    # Check Docker
    try {
        docker ps | Out-Null
        Write-ColorOutput "Green" "✅ Docker работает"
    } catch {
        Write-ColorOutput "Red" "❌ Docker не запущен"
        return
    }
    
    # Check containers
    $containers = @("stoic_freqtrade", "stoic_frequi", "stoic_postgres", "stoic_jupyter")
    
    foreach ($container in $containers) {
        $status = docker inspect -f '{{.State.Health.Status}}' $container 2>$null
        if ($status -eq "healthy") {
            Write-ColorOutput "Green" "✅ $container - HEALTHY"
        } elseif ($status -eq "starting") {
            Write-ColorOutput "Yellow" "⏳ $container - STARTING"
        } else {
            Write-ColorOutput "Red" "❌ $container - UNHEALTHY or NOT RUNNING"
        }
    }
    
    Write-Host ""
    Write-ColorOutput "Cyan" "📊 Использование ресурсов:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" $containers
}

function Invoke-WatchHealth {
    Show-Header
    Write-ColorOutput "Cyan" "👀 Непрерывный мониторинг (Ctrl+C для выхода)..."
    
    while ($true) {
        Clear-Host
        Invoke-HealthCheck
        Start-Sleep -Seconds 10
    }
}

# ==============================================================================
# SETUP AND MANAGEMENT
# ==============================================================================

function Invoke-Setup {
    Show-Header
    Write-ColorOutput "Cyan" "🚀 Запуск мастера настройки Stoic Citadel..."
    
    Set-Location $PROJECT_DIR
    
    # Check Docker
    Write-ColorOutput "Cyan" "📋 Проверка Docker..."
    try {
        docker --version | Out-Null
        docker-compose --version | Out-Null
        Write-ColorOutput "Green" "✅ Docker установлен"
    } catch {
        Write-ColorOutput "Red" "❌ Docker не найден. Установите Docker Desktop"
        exit 1
    }
    
    # Create .env if not exists
    Test-EnvFile | Out-Null
    
    # Create directories
    Write-ColorOutput "Cyan" "📁 Создание необходимых директорий..."
    $dirs = @(
        "user_data/data/binance",
        "user_data/logs", 
        "user_data/backtest_results",
        "user_data/hyperopt_results",
        "user_data/notebooks",
        "backups",
        "reports"
    )
    
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    Write-ColorOutput "Green" "✅ Директории созданы"
    
    Write-ColorOutput "Green" "✅ Настройка завершена!"
    Write-Host ""
    Write-ColorOutput "Cyan" "📊 Следующие шаги:"
    Write-Host "  1. .\stoic.ps1 generate-secrets  # Генерация паролей"
    Write-Host "  2. .\stoic.ps1 download-data     # Скачать данные"
    Write-Host "  3. .\stoic.ps1 trade-dry         # Запустить бота"
    Write-Host ""
}

function Invoke-Start {
    Show-Header
    Write-ColorOutput "Cyan" "🚀 Запуск Stoic Citadel сервисов..."
    
    Set-Location $PROJECT_DIR
    if (-not (Test-EnvFile)) { return }
    
    docker-compose up -d
    Start-Sleep -Seconds 5
    
    Write-ColorOutput "Green" "✅ Все сервисы запущены!"
    Write-Host ""
    Write-ColorOutput "Cyan" "📊 Точки доступа:"
    Write-Host "  FreqUI:    http://localhost:3000"
    Write-Host "  Jupyter:   http://localhost:8888 (token: stoic2024)"
    Write-Host "  Portainer: http://localhost:9000"
    Write-Host "  PostgreSQL: localhost:5433"
    Write-Host ""
}

function Invoke-Stop {
    Write-ColorOutput "Yellow" "⏹️  Остановка всех сервисов..."
    Set-Location $PROJECT_DIR
    docker-compose down
    Write-ColorOutput "Green" "✅ Все сервисы остановлены"
}

function Invoke-Restart {
    Write-ColorOutput "Cyan" "🔄 Перезапуск сервисов..."
    Invoke-Stop
    Start-Sleep -Seconds 2
    Invoke-Start
}

function Invoke-Status {
    Show-Header
    Write-ColorOutput "Cyan" "📊 Статус сервисов:"
    Write-Host ""
    Set-Location $PROJECT_DIR
    docker-compose ps
}

function Invoke-Logs {
    Write-ColorOutput "Cyan" "📋 Логи для $Service (Ctrl+C для выхода):"
    Write-Host ""
    Set-Location $PROJECT_DIR
    docker-compose logs -f --tail=100 $Service
}

# ==============================================================================
# TRADING FUNCTIONS
# ==============================================================================

function Invoke-TradeDry {
    Show-Header
    Write-ColorOutput "Cyan" "📈 Запуск trading бота в DRY-RUN режиме..."
    
    Set-Location $PROJECT_DIR
    if (-not (Test-EnvFile)) { return }
    
    docker-compose up -d freqtrade frequi postgres
    Start-Sleep -Seconds 5
    
    Write-ColorOutput "Green" "✅ Trading бот запущен (dry-run режим)"
    Write-Host ""
    Write-ColorOutput "Cyan" "📊 Мониторинг:"
    Write-Host "  Dashboard: http://localhost:3000"
    Write-Host "  Логи:      .\stoic.ps1 logs freqtrade"
    Write-Host "  Health:    .\stoic.ps1 health"
    Write-Host ""
}

function Invoke-TradeLive {
    Show-Header
    Write-ColorOutput "Red" "╔════════════════════════════════════════════════════════════╗"
    Write-ColorOutput "Red" "║              ⚠️  LIVE TRADING MODE ⚠️                       ║"
    Write-ColorOutput "Red" "║                                                            ║"
    Write-ColorOutput "Red" "║  THIS WILL USE REAL MONEY!                                 ║"
    Write-ColorOutput "Red" "╚════════════════════════════════════════════════════════════╝"
    Write-Host ""
    
    $confirm = Read-Host "Введите 'Я ПОНИМАЮ РИСКИ' для продолжения"
    if ($confirm -ne "Я ПОНИМАЮ РИСКИ") {
        Write-ColorOutput "Yellow" "⚠️  Live trading отменён"
        return
    }
    
    Set-Location $PROJECT_DIR
    if (-not (Test-EnvFile)) { return }
    
    docker-compose up -d freqtrade frequi postgres
    
    Write-ColorOutput "Green" "✅ Live trading запущен!"
    Write-ColorOutput "Red" "⚠️  МОНИТОРЬТЕ ПОСТОЯННО!"
}

function Invoke-Backtest {
    Write-ColorOutput "Cyan" "🧪 Запуск бэктеста для стратегии: $Strategy"
    Set-Location $PROJECT_DIR
    
    docker-compose run --rm freqtrade backtesting `
        --strategy $Strategy `
        --timerange 20240101- `
        --enable-protections
    
    Write-ColorOutput "Green" "✅ Бэктест завершён!"
}

# ==============================================================================
# DATA FUNCTIONS
# ==============================================================================

function Invoke-DownloadData {
    Write-ColorOutput "Cyan" "📥 Скачивание исторических данных..."
    Set-Location $PROJECT_DIR
    
    docker-compose run --rm freqtrade download-data `
        --exchange binance `
        --pairs BTC/USDT ETH/USDT BNB/USDT SOL/USDT XRP/USDT ADA/USDT `
        --timeframes 5m 15m 1h `
        --days 90
    
    Write-ColorOutput "Green" "✅ Данные скачаны!"
}

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

function Invoke-Dashboard {
    Write-ColorOutput "Cyan" "📊 Открытие FreqUI Dashboard..."
    Start-Process "http://localhost:3000"
    Write-ColorOutput "Green" "✅ Dashboard открыт"
}

function Invoke-Research {
    Show-Header
    Write-ColorOutput "Cyan" "🔬 Запуск Jupyter Lab..."
    
    Set-Location $PROJECT_DIR
    docker-compose up -d jupyter
    Start-Sleep -Seconds 5
    
    Write-ColorOutput "Green" "✅ Jupyter Lab запущен!"
    Write-Host ""
    Write-ColorOutput "Cyan" "🌐 http://localhost:8888"
    Write-ColorOutput "Cyan" "🔑 Token: stoic2024"
    
    Start-Process "http://localhost:8888"
}

function Invoke-Clean {
    Write-ColorOutput "Yellow" "⚠️  Это удалит все контейнеры..."
    $confirm = Read-Host "Продолжить? (yes/no)"
    
    if ($confirm -eq "yes") {
        Write-ColorOutput "Cyan" "🧹 Очистка..."
        Set-Location $PROJECT_DIR
        docker-compose down
        Write-ColorOutput "Green" "✅ Очистка завершена"
    }
}

# ==============================================================================
# HELP
# ==============================================================================

function Show-Help {
    Show-Header
    Write-ColorOutput "Green" "📋 ДОСТУПНЫЕ КОМАНДЫ:"
    Write-Host ""
    Write-ColorOutput "Yellow" "Управление:"
    Write-Host "  help              - Показать справку"
    Write-Host "  setup             - Первоначальная настройка"
    Write-Host "  start             - Запустить все сервисы"
    Write-Host "  stop              - Остановить сервисы"
    Write-Host "  restart           - Перезапустить"
    Write-Host "  status            - Статус сервисов"
    Write-Host "  logs [service]    - Показать логи"
    Write-Host ""
    Write-ColorOutput "Yellow" "Безопасность:"
    Write-Host "  generate-secrets  - Генерация паролей"
    Write-Host ""
    Write-ColorOutput "Yellow" "Мониторинг:"
    Write-Host "  health            - Проверка здоровья"
    Write-Host "  health-watch      - Непрерывный мониторинг"
    Write-Host "  dashboard         - Открыть dashboard"
    Write-Host ""
    Write-ColorOutput "Yellow" "Трейдинг:"
    Write-Host "  trade-dry         - Paper trading"
    Write-Host "  trade-live        - Live trading (ОСТОРОЖНО!)"
    Write-Host "  backtest [strat]  - Бэктест"
    Write-Host ""
    Write-ColorOutput "Yellow" "Данные:"
    Write-Host "  download-data     - Скачать исторические данные"
    Write-Host "  research          - Запустить Jupyter"
    Write-Host ""
    Write-ColorOutput "Yellow" "Обслуживание:"
    Write-Host "  clean             - Очистить контейнеры"
    Write-Host ""
}

# ==============================================================================
# MAIN SWITCH
# ==============================================================================

Set-Location $PROJECT_DIR

switch ($Command.ToLower()) {
    "help" { Show-Help }
    "setup" { Invoke-Setup }
    "start" { Invoke-Start }
    "stop" { Invoke-Stop }
    "restart" { Invoke-Restart }
    "status" { Invoke-Status }
    "logs" { Invoke-Logs }
    
    "generate-secrets" { Invoke-GenerateSecrets }
    
    "health" { Invoke-HealthCheck }
    "health-watch" { Invoke-WatchHealth }
    "dashboard" { Invoke-Dashboard }
    
    "trade-dry" { Invoke-TradeDry }
    "trade-live" { Invoke-TradeLive }
    "backtest" { Invoke-Backtest }
    
    "download-data" { Invoke-DownloadData }
    "research" { Invoke-Research }
    
    "clean" { Invoke-Clean }
    
    default {
        Write-ColorOutput "Red" "❌ Неизвестная команда: $Command"
        Write-Host ""
        Show-Help
        exit 1
    }
}

Write-Host ""
Write-ColorOutput "Cyan" "🏛️  Stoic Citadel - Trade with wisdom, not emotion."
Write-Host ""
