#!/usr/bin/env pwsh
# Stoic Citadel - Automated Deployment Script for Windows
# Полная автоматизация развертывания HFT бота

param(
    [switch]$SkipData,           # Пропустить загрузку данных
    [switch]$SkipBacktest,       # Пропустить бэктест
    [switch]$WithJupyter,        # Запустить Jupyter Lab
    [switch]$AllServices,        # Запустить все сервисы (включая PostgreSQL, Portainer)
    [int]$DataDays = 90,         # Количество дней данных для загрузки
    [string]$Strategy = "SimpleTestStrategy"  # Стратегия для бэктеста
)

# Цвета для вывода
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Step {
    param([string]$Message)
    Write-ColorOutput "`n=== $Message ===" "Cyan"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✅ $Message" "Green"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "❌ $Message" "Red"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "⚠️  $Message" "Yellow"
}

# Баннер
Write-Host @"

╔════════════════════════════════════════════════════════╗
║                                                        ║
║            STOIC CITADEL DEPLOYMENT                    ║
║         Automated HFT Bot Setup for Windows            ║
║                                                        ║
╚════════════════════════════════════════════════════════╝

"@ -ForegroundColor Magenta

# Проверка требований
Write-Step "Проверка системных требований"

# Docker
try {
    $dockerVersion = docker --version
    Write-Success "Docker найден: $dockerVersion"
} catch {
    Write-Error "Docker не найден! Установите Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
}

# Docker Compose
try {
    $composeVersion = docker-compose --version
    Write-Success "Docker Compose найден: $composeVersion"
} catch {
    Write-Error "Docker Compose не найден!"
    exit 1
}

# Git
try {
    $gitVersion = git --version
    Write-Success "Git найден: $gitVersion"
} catch {
    Write-Warning "Git не найден, но можно продолжить"
}

# Остановка существующих контейнеров
Write-Step "Остановка существующих контейнеров"
docker-compose down
Write-Success "Контейнеры остановлены"

# Обновление из Git (если доступен)
if (Test-Path ".git") {
    Write-Step "Обновление из Git репозитория"
    try {
        git pull origin simplify-architecture
        Write-Success "Репозиторий обновлен"
    } catch {
        Write-Warning "Не удалось обновить репозиторий, продолжаем с текущей версией"
    }
}

# Запуск сервисов
Write-Step "Запуск Docker сервисов"

if ($AllServices) {
    Write-ColorOutput "Запуск ВСЕХ сервисов (Freqtrade, FreqUI, Jupyter, PostgreSQL, Portainer)..." "Yellow"
    docker-compose up -d
} elseif ($WithJupyter) {
    Write-ColorOutput "Запуск основных сервисов + Jupyter Lab..." "Yellow"
    docker-compose up -d freqtrade frequi jupyter
} else {
    Write-ColorOutput "Запуск основных сервисов (Freqtrade, FreqUI)..." "Yellow"
    docker-compose up -d freqtrade frequi
}

# Ожидание запуска
Write-ColorOutput "Ожидание запуска контейнеров (30 секунд)..." "Yellow"
Start-Sleep -Seconds 30

# Проверка статуса
Write-Step "Проверка статуса контейнеров"
docker-compose ps

# Проверка health check
Write-ColorOutput "`nПроверка здоровья Freqtrade..." "Yellow"
$healthCheck = docker inspect stoic_freqtrade --format='{{.State.Health.Status}}' 2>$null
if ($healthCheck -eq "healthy") {
    Write-Success "Freqtrade запущен и здоров!"
} else {
    Write-Warning "Freqtrade еще запускается, подождите еще 30 секунд"
}

# Загрузка данных
if (-not $SkipData) {
    Write-Step "Загрузка исторических данных"
    Write-ColorOutput "Загрузка $DataDays дней данных по 5 парам (5m таймфрейм)..." "Yellow"
    
    docker-compose run --rm freqtrade download-data `
        --config /freqtrade/user_data/config/config.json `
        --exchange binance `
        --pairs BTC/USDT ETH/USDT BNB/USDT SOL/USDT XRP/USDT `
        --timeframe 5m `
        --days $DataDays
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Данные успешно загружены"
    } else {
        Write-Error "Ошибка при загрузке данных"
    }
    
    # Для продвинутых стратегий загружаем BTC 1d
    if ($Strategy -ne "SimpleTestStrategy") {
        Write-ColorOutput "Загрузка годовых данных BTC/USDT 1d для режимного фильтра..." "Yellow"
        docker-compose run --rm freqtrade download-data `
            --config /freqtrade/user_data/config/config.json `
            --exchange binance `
            --pairs BTC/USDT `
            --timeframe 1d `
            --days 365
    }
}

# Бэктестирование
if (-not $SkipBacktest) {
    Write-Step "Запуск бэктестирования"
    Write-ColorOutput "Тестирование стратегии: $Strategy" "Yellow"
    
    # Определяем timerange (последние 2 месяца)
    $endDate = Get-Date -Format "yyyyMMdd"
    $startDate = (Get-Date).AddMonths(-2).ToString("yyyyMMdd")
    $timerange = "${startDate}-${endDate}"
    
    docker-compose run --rm freqtrade backtesting `
        --config /freqtrade/user_data/config/config.json `
        --strategy $Strategy `
        --timerange $timerange
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Бэктест завершен успешно"
    } else {
        Write-Error "Ошибка при бэктесте"
    }
}

# Финальная информация
Write-Step "Развертывание завершено!"

Write-Host @"

╔════════════════════════════════════════════════════════╗
║                  ДОСТУП К СЕРВИСАМ                     ║
╚════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green

Write-ColorOutput "🌐 FreqUI Dashboard:  http://localhost:3000" "Cyan"
Write-ColorOutput "   Логин: stoic_admin  |  Пароль: StoicGuard2024`n" "Gray"

if ($WithJupyter -or $AllServices) {
    Write-ColorOutput "📊 Jupyter Lab:       http://localhost:8888" "Cyan"
    Write-ColorOutput "   Token: stoic2024`n" "Gray"
}

Write-ColorOutput "🔌 API Endpoint:      http://localhost:8080/api/v1/ping" "Cyan"
Write-ColorOutput "   Логин: stoic_admin  |  Пароль: StoicGuard2024`n" "Gray"

if ($AllServices) {
    Write-ColorOutput "🐳 Portainer:         http://localhost:9443" "Cyan"
    Write-ColorOutput "   (Настройка при первом запуске)`n" "Gray"
}

Write-Host @"

╔════════════════════════════════════════════════════════╗
║                  ПОЛЕЗНЫЕ КОМАНДЫ                      ║
╚════════════════════════════════════════════════════════╝

"@ -ForegroundColor Yellow

Write-Host @"
Просмотр логов:
  docker-compose logs -f freqtrade

Проверка статуса:
  docker-compose ps

Остановка сервисов:
  docker-compose down

Запуск бэктеста:
  .\scripts\windows\backtest.ps1 -Strategy "SimpleTestStrategy"

Загрузка данных:
  .\scripts\windows\download-data.ps1 -Days 90

"@ -ForegroundColor Gray

Write-Success "`n🚀 Все готово к работе! Удачной торговли!`n"
