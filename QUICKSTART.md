# 🚀 STOIC CITADEL - QUICK START (WINDOWS)

**3 команды до запуска:**

```powershell
# 1. Стопни всё что было
docker-compose down

# 2. Подтяни последние изменения
git pull origin simplify-architecture

# 3. Запусти (простая стратегия, без Jupyter)
docker-compose up -d freqtrade frequi
```

**Дашборд:** http://localhost:3000  
**Логин:** `stoic_admin`  
**Пароль:** `StoicGuard2024`

---

## 📊 Проверка статуса

```powershell
# Статус контейнеров
docker-compose ps

# Логи в реальном времени
docker-compose logs -f freqtrade

# Остановить
docker-compose down
```

---

## 🧪 Бэктестинг

### Вариант 1: Быстрый тест (без данных)

```powershell
# Тест простой стратегии за последние 30 дней
docker-compose run --rm freqtrade backtesting `
  --strategy SimpleTestStrategy `
  --timerange 20241101-
```

### Вариант 2: С историческими данными

```powershell
# 1. Скачай данные (90 дней, 5m таймфрейм)
docker-compose run --rm freqtrade download-data `
  --exchange binance `
  --pairs BTC/USDT ETH/USDT BNB/USDT SOL/USDT XRP/USDT `
  --timeframe 5m `
  --days 90

# 2. Запусти бэктест
docker-compose run --rm freqtrade backtesting `
  --strategy SimpleTestStrategy `
  --timerange 20241001-20241202

# 3. Посмотри результаты
docker-compose run --rm freqtrade backtesting-show
```

### Вариант 3: Продвинутая стратегия

```powershell
# Бэктест StoicStrategyV1 (требует данные BTC/USDT 1d)
docker-compose run --rm freqtrade download-data `
  --exchange binance `
  --pairs BTC/USDT `
  --timeframe 1d `
  --days 365

docker-compose run --rm freqtrade backtesting `
  --strategy StoicStrategyV1 `
  --timerange 20241001-
```

---

## 📂 Где что находится

```
C:\hft-algotrade-bot\
├── user_data/
│   ├── strategies/              ← Твои стратегии
│   │   ├── SimpleTestStrategy.py    (простая, работает)
│   │   ├── StoicStrategyV1.py       (продвинутая)
│   │   └── StoicEnsembleStrategy.py (ансамбль)
│   ├── data/binance/            ← Скачанные данные
│   ├── logs/                    ← Логи
│   ├── config/config.json       ← Главный конфиг
│   └── tradesv3.sqlite          ← База сделок
├── research/                    ← Jupyter ноутбуки
└── docker-compose.yml           ← Главный файл
```

---

## 🔧 Сменить стратегию

**Вариант 1: Через docker-compose.yml**

Открой `docker-compose.yml`, найди строку:
```yaml
--strategy SimpleTestStrategy
```

Замени на:
```yaml
--strategy StoicStrategyV1
```

Перезапусти:
```powershell
docker-compose down
docker-compose up -d freqtrade frequi
```

**Вариант 2: Напрямую**

```powershell
# Стопни текущий бот
docker-compose stop freqtrade

# Запусти с другой стратегией
docker-compose run -d --name stoic_freqtrade freqtrade trade `
  --strategy StoicStrategyV1 `
  --config /freqtrade/user_data/config/config.json
```

---

## 🔬 Jupyter Lab (для исследований)

```powershell
# Запусти Jupyter (первый раз долго ~5-10 мин)
docker-compose up -d jupyter

# Проверь статус
docker-compose logs jupyter
```

**Открой:** http://localhost:8888  
**Token:** `stoic2024`

---

## ⚠️ Частые проблемы

### Проблема: Стратегия не загружается
```powershell
# Проверь логи
docker-compose logs freqtrade | Select-String "ERROR"

# Переключись на простую стратегию
# Измени в docker-compose.yml на SimpleTestStrategy
```

### Проблема: Контейнеры не стартуют
```powershell
# Полная перезагрузка
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Проблема: Нет данных для бэктеста
```powershell
# Скачай данные заново
docker-compose run --rm freqtrade download-data `
  --exchange binance `
  --pairs BTC/USDT ETH/USDT `
  --timeframe 5m `
  --days 90
```

---

## 🎯 Следующие шаги

1. **Протестируй SimpleTestStrategy** - убедись что всё работает
2. **Скачай данные** - за 90 дней на всех парах
3. **Запусти бэктесты** - сравни разные стратегии
4. **Оптимизируй параметры** - используй HyperOpt
5. **Запусти live** - когда будешь готов (см. START.md)

---

**Stoic Citadel** - Where reason rules, not emotion.
