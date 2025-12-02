#!/usr/bin/env pwsh
# Stoic Citadel - Backtesting Script for Windows
# Запуск бэктестов с гибкими параметрами

param(
    [Parameter(Mandatory=$false)]
    [string]$Strategy = "SimpleTestStrategy",
    
    [Parameter(Mandatory=$false)]
    [string]$Timerange = "",
    
    [Parameter(Mandatory=$false)]
    [int]$StartDaysAgo = 60,
    
    [Parameter(Mandatory=$false)]
    [string]$Pairs = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$EnablePositionStacking,
    
    [Parameter(Mandatory=$false)]
    [int]$MaxOpenTrades = 3,
    
    [Parameter(Mandatory=$false)]
    [switch]$ExportTrades,
    
    [Parameter(Mandatory=$false)]
    [switch]$Breakdown
)

# Цвета
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
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

# Баннер
Write-Host @"

╔════════════════════════════════════════════════════════╗
║           STOIC CITADEL - BACKTESTING                  ║
╚════════════════════════════════════════════════════════╝

"@ -ForegroundColor Magenta

# Определяем timerange если не задан
if ([string]::IsNullOrEmpty($Timerange)) {
    $endDate = Get-Date -Format "yyyyMMdd"
    $startDate = (Get-Date).AddDays(-$StartDaysAgo).ToString("yyyyMMdd")
    $Timerange = "${startDate}-${endDate}"
    Write-ColorOutput "📅 Автоматический timerange: $Timerange (последние $StartDaysAgo дней)" "Yellow"
}

# Формируем команду
Write-Step "Параметры бэктеста"
Write-ColorOutput "Стратегия:        $Strategy" "Cyan"
Write-ColorOutput "Период:           $Timerange" "Cyan"
Write-ColorOutput "Max открытых:     $MaxOpenTrades" "Cyan"

$command = @(
    "docker-compose", "run", "--rm", "freqtrade", "backtesting",
    "--config", "/freqtrade/user_data/config/config.json",
    "--strategy", $Strategy,
    "--timerange", $Timerange
)

# Дополнительные параметры
if ($EnablePositionStacking) {
    $command += "--enable-position-stacking"
    Write-ColorOutput "Стекинг позиций:  ВКЛЮЧЕН" "Yellow"
}

if ($MaxOpenTrades -ne 3) {
    $command += "--max-open-trades"
    $command += $MaxOpenTrades.ToString()
}

if (-not [string]::IsNullOrEmpty($Pairs)) {
    $command += "--pairs"
    $command += $Pairs
    Write-ColorOutput "Пары:             $Pairs" "Cyan"
}

if ($ExportTrades) {
    $command += "--export", "trades"
    $command += "--export-filename", "user_data/backtest_results/backtest-result-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
    Write-ColorOutput "Экспорт сделок:   ВКЛЮЧЕН" "Yellow"
}

if ($Breakdown) {
    $command += "--breakdown", "day", "week", "month"
    Write-ColorOutput "Детализация:      ВКЛЮЧЕНА (день/неделя/месяц)" "Yellow"
}

# Запуск
Write-Step "Запуск бэктестирования"
Write-ColorOutput "Команда: $($command -join ' ')" "Gray"
Write-Host ""

& $command[0] $command[1..($command.Length-1)]

# Результат
if ($LASTEXITCODE -eq 0) {
    Write-Success "`n✨ Бэктест завершен успешно!"
    
    if ($ExportTrades) {
        Write-ColorOutput "`n📂 Результаты сохранены в: user_data/backtest_results/" "Cyan"
    }
    
    Write-Host @"

╔════════════════════════════════════════════════════════╗
║                  СЛЕДУЮЩИЕ ШАГИ                        ║
╚════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green
    
    Write-Host @"
Анализ результатов в Jupyter:
  1. Запустить Jupyter: docker-compose up -d jupyter
  2. Открыть: http://localhost:8888
  3. Token: stoic2024
  4. Открыть: research/01_strategy_template.ipynb

Оптимизация параметров (HyperOpt):
  docker-compose run --rm freqtrade hyperopt \
    --config /freqtrade/user_data/config/config.json \
    --hyperopt-loss SharpeHyperOptLoss \
    --strategy $Strategy \
    --epochs 100 \
    --spaces buy sell roi stoploss

Запуск с другой стратегией:
  .\scripts\windows\backtest.ps1 -Strategy "StoicStrategyV1"

"@ -ForegroundColor Gray

} else {
    Write-Error "`n❌ Ошибка при выполнении бэктеста!"
    Write-ColorOutput "`nПроверьте:" "Yellow"
    Write-ColorOutput "  1. Наличие исторических данных: .\scripts\windows\download-data.ps1" "Gray"
    Write-ColorOutput "  2. Корректность стратегии: docker-compose exec freqtrade ls /freqtrade/user_data/strategies/" "Gray"
    Write-ColorOutput "  3. Логи: docker-compose logs freqtrade" "Gray"
}
