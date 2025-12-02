# 🏛️ STOIC CITADEL - WINDOWS QUICK START

**Всё что нужно для запуска и бэктестинга на Windows**

---

## ⚡ МГНОВЕННЫЙ СТАРТ (3 команды)

```powershell
# 1. Остановить всё что было
docker-compose down

# 2. Запустить бота (тестовый режим, без реальных денег)
docker-compose up -d freqtrade frequi

# 3. Проверить статус
docker-compose ps
```

**Открой дашборд:** http://localhost:3000  
**Логин:** `stoic_admin` | **Пароль:** `StoicGuard2024`

---

## 📊 БЭКТЕСТИНГ (правильные команды)

### ✅ Быстрый тест (с уже скачанными данными)

```powershell
docker-compose run --rm freqtrade backtesting `
  --config /freqtrade/user_data/config/config.json `
  --strategy SimpleTestStrategy `
  --timerange 20241001-20241202
```

### 📥 Скачать данные (если ещё не скачивал)

```powershell
# 90 дней, 5 минутный таймфрейм
docker-compose run --rm freqtrade download-data `
  --config /freqtrade/user_data/config/config.json `
  --exchange binance `
  --pairs BTC/USDT ETH/USDT BNB/USDT SOL/USDT XRP/USDT `
  --timeframe 5m `
  --days 90
```

### 🔬 Продвинутый бэктест (с деталями)

```powershell
# С детальными метриками
docker-compose run --rm freqtrade backtesting `
  --config /freqtrade/user_data/config/config.json `
  --strategy SimpleTestStrategy `
  --timerange 20241001-20241202 `
  --breakdown day

# Посмотреть результаты
docker-compose run --rm freqtrade backtesting-show
```

### 🎯 Сравнение стратегий

```powershell
# Тест простой стратегии
docker-compose run --rm freqtrade backtesting `
  --config /freqtrade/user_data/config/config.json `
  --strategy SimpleTestStrategy `
  --timerange 20241101-

# Тест продвинутой стратегии (требует BTC/USDT 1d данные)
docker-compose run --rm freqtrade download-data `
  --config /freqtrade/user_data/config/config.json `
  --exchange binance `
  --pairs BTC/USDT `
  --timeframe 1d `
  --days 365

docker-compose run --rm freqtrade backtesting `
  --config /freqtrade/user_data/config/config.json `
  --strategy StoicStrategyV1 `
  --timerange 20241101-
```

---

## 🔄 УПРАВЛЕНИЕ БОТОМ

```powershell
# Посмотреть логи в реальном времени
docker-compose logs -f freqtrade

# Остановить бота
docker-compose stop freqtrade

# Запустить снова
docker-compose start freqtrade

# Полная остановка всего
docker-compose down

# Перезапуск
docker-compose restart freqtrade

# Посмотреть статус всех контейнеров
docker-compose ps
```

---

## 🔧 СМЕНА СТРАТЕГИИ

### Вариант 1: Через docker-compose.yml (постоянно)

1. Открой `docker-compose.yml`
2. Найди строку: `--strategy SimpleTestStrategy`
3. Замени на: `--strategy StoicStrategyV1` (или другую)
4. Перезапусти:

```powershell
docker-compose down
docker-compose up -d freqtrade frequi
```

### Вариант 2: Временно для теста

```powershell
# Остановить текущий бот
docker-compose stop freqtrade

# Запустить с другой стратегией
docker-compose run -d `
  --name stoic_freqtrade `
  -p 127.0.0.1:8080:8080 `
  freqtrade trade `
  --config /freqtrade/user_data/config/config.json `
  --strategy StoicStrategyV1
```

---

## 📁 СТРУКТУРА ПРОЕКТА

```
C:\hft-algotrade-bot\
├── user_data/
│   ├── strategies/               ← Твои стратегии
│   │   ├── SimpleTestStrategy.py    (✅ работает)
│   │   ├── StoicStrategyV1.py       (продвинутая)
│   │   └── StoicEnsembleStrategy.py (ансамбль)
│   ├── data/binance/             ← Скачанные данные
│   │   ├── BTC_USDT-5m.json
│   │   ├── ETH_USDT-5m.json
│   │   └── ...
│   ├── logs/                     ← Логи бота
│   │   └── freqtrade.log
│   ├── config/
│   │   └── config.json           ← Главный конфиг
│   └── tradesv3.sqlite           ← База сделок
├── research/                     ← Jupyter ноутбуки
├── scripts/                      ← Вспомогательные скрипты
├── docker-compose.yml            ← Главный файл
└── START_WINDOWS.md              ← Этот файл
```

---

## 🐛 ОТЛАДКА И ЛОГИ

### Посмотреть логи

```powershell
# Логи бота (последние 100 строк)
docker-compose logs --tail=100 freqtrade

# Логи дашборда
docker-compose logs --tail=100 frequi

# Следить в реальном времени
docker-compose logs -f freqtrade

# Сохранить логи в файл
docker-compose logs freqtrade > logs.txt
```

### Посмотреть файл с логами

```powershell
# Открыть в блокноте
notepad user_data/logs/freqtrade.log

# Или в PowerShell
Get-Content user_data/logs/freqtrade.log -Tail 50
```

### Проверить что не так

```powershell
# Статус контейнеров
docker-compose ps

# Проверить Docker
docker --version
docker ps

# Проверить занятость портов
netstat -ano | findstr :3000
netstat -ano | findstr :8080
```

---

## ⚠️ ЧАСТЫЕ ПРОБЛЕМЫ

### Проблема: "Config file not found"

**Причина:** Неправильный путь к конфигу в команде бэктеста

**Решение:**
```powershell
# ❌ НЕПРАВИЛЬНО
docker-compose run --rm freqtrade backtesting --strategy SimpleTestStrategy

# ✅ ПРАВИЛЬНО
docker-compose run --rm freqtrade backtesting `
  --config /freqtrade/user_data/config/config.json `
  --strategy SimpleTestStrategy
```

### Проблема: Контейнер не запускается

```powershell
# Посмотреть что случилось
docker-compose logs freqtrade | Select-String "ERROR"

# Полная перезагрузка
docker-compose down
docker-compose up -d
```

### Проблема: Порт уже занят

```powershell
# Найти процесс на порту 8080
netstat -ano | findstr :8080

# Убить процесс (замени PID на реальный)
Stop-Process -Id <PID> -Force

# Или просто перезапусти Docker Desktop
```

### Проблема: Jupyter не собирается

```powershell
# Jupyter не нужен для торговли, можно пропустить
# Если очень нужен:
docker-compose build --no-cache jupyter
docker-compose up -d jupyter

# Займёт ~10 минут первый раз
```

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

### 1. Протестируй SimpleTestStrategy

```powershell
# Убедись что всё работает
docker-compose run --rm freqtrade backtesting `
  --config /freqtrade/user_data/config/config.json `
  --strategy SimpleTestStrategy `
  --timerange 20241001-
```

### 2. Скачай больше данных

```powershell
# 180 дней для лучших результатов
docker-compose run --rm freqtrade download-data `
  --config /freqtrade/user_data/config/config.json `
  --exchange binance `
  --pairs BTC/USDT ETH/USDT BNB/USDT SOL/USDT XRP/USDT `
  --timeframe 5m `
  --days 180
```

### 3. Попробуй продвинутую стратегию

```powershell
# Скачай данные для BTC 1d (нужны для StoicStrategyV1)
docker-compose run --rm freqtrade download-data `
  --config /freqtrade/user_data/config/config.json `
  --exchange binance `
  --pairs BTC/USDT `
  --timeframe 1d `
  --days 365

# Запусти бэктест
docker-compose run --rm freqtrade backtesting `
  --config /freqtrade/user_data/config/config.json `
  --strategy StoicStrategyV1 `
  --timerange 20240601-
```

### 4. Оптимизируй параметры (HyperOpt)

```powershell
# Найти лучшие параметры для стратегии
docker-compose run --rm freqtrade hyperopt `
  --config /freqtrade/user_data/config/config.json `
  --strategy StoicStrategyV1 `
  --hyperopt-loss SharpeHyperOptLoss `
  --epochs 100 `
  --spaces buy sell

# Займёт ~30-60 минут
```

### 5. Запусти в продакшене (ОСТОРОЖНО!)

```powershell
# 1. Измени dry_run: false в user_data/config/config.json
# 2. Добавь API ключи биржи
# 3. Настрой Telegram уведомления (опционально)
# 4. Запусти:

docker-compose down
docker-compose up -d freqtrade frequi

# ⚠️ БУДУТ ИСПОЛЬЗОВАТЬСЯ РЕАЛЬНЫЕ ДЕНЬГИ!
```

---

## 📚 ПОЛЕЗНЫЕ ССЫЛКИ

- **Дашборд:** http://localhost:3000
- **API Docs:** http://localhost:8080/api/v1/ui
- **Freqtrade Docs:** https://www.freqtrade.io/en/stable/
- **GitHub Repo:** https://github.com/kandibobe/hft-algotrade-bot

---

## 🆘 НУЖНА ПОМОЩЬ?

```powershell
# Список всех команд Freqtrade
docker-compose run --rm freqtrade --help

# Список стратегий
docker-compose run --rm freqtrade list-strategies `
  --config /freqtrade/user_data/config/config.json

# Список доступных пар на бирже
docker-compose run --rm freqtrade list-pairs `
  --config /freqtrade/user_data/config/config.json `
  --exchange binance
```

---

**🏛️ Stoic Citadel** - Where reason rules, not emotion.
