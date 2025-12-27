# Руководство по ночной оптимизации гиперпараметров

## Обзор

Ночная оптимизация гиперпараметров — это автоматизированный процесс, который выполняется каждые 3 дня для поиска оптимальных параметров модели XGBoost. Система использует Optuna для оптимизации коэффициента Шарпа на исторических данных.

## Архитектура

### Компоненты

1. **`scripts/nightly_hyperopt.py`** — основной скрипт оптимизации
2. **`scripts/nightly_monitor.py`** — мониторинг и отчётность
3. **`scripts/setup_nightly_task.ps1`** — настройка планировщика задач Windows
4. **`src/ml/training/feature_engineering.py`** — генерация признаков
5. **`src/ml/training/labeling.py`** — разметка данных

### Поток данных

```
Загрузка данных → Генерация признаков → Разметка → Оптимизация → Сохранение результатов → Отчётность
```

## Настройка

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
pip install optuna xgboost psutil
```

### 2. Настройка планировщика задач (Windows)

Запустите PowerShell **от имени администратора**:

```powershell
cd C:\mft-algotrade-bot
powershell -ExecutionPolicy Bypass -File scripts\setup_nightly_task.ps1
```

Параметры по умолчанию:
- **Время запуска**: 23:00
- **Интервал**: 3 дня
- **Количество испытаний**: 500
- **Таймаут**: 8 часов
- **Проверка данных**: включена

### 3. Настройка Telegram уведомлений (опционально)

Добавьте в переменные окружения:
```bash
TELEGRAM_BOT_TOKEN=ваш_токен
TELEGRAM_CHAT_ID=ваш_chat_id
```

## Использование

### Ручной запуск

```bash
# Быстрый тест (10 испытаний)
python scripts/nightly_hyperopt.py --trials 10 --quick

# Полная оптимизация
python scripts/nightly_hyperopt.py --trials 500 --timeout 28800 --check-data

# Только проверка данных
python scripts/nightly_hyperopt.py --check-data
```

### Мониторинг

```bash
# Проверить новые результаты
python scripts/nightly_monitor.py --check-results

# Сгенерировать отчёт
python scripts/nightly_monitor.py --send-report

# Проверить ресурсы системы
python scripts/nightly_monitor.py --check-resources
```

## Результаты

Результаты сохраняются в `user_data/nightly_hyperopt/`:

- `best_params_nightly.json` — лучшие параметры
- `full_results_nightly.json` — полные результаты
- `optimization_report.md` — отчёт в формате Markdown
- `feature_importance_nightly.png` — важность признаков
- `nightly_hyperopt.db` — база данных Optuna (для возобновления)

## Метрики оптимизации

### Целевая функция
**Коэффициент Шарпа** — максимизируется с помощью TimeSeriesSplit (5 фолдов).

### Гиперпараметры XGBoost
- `max_depth`: 2-5
- `learning_rate`: 0.005-0.05
- `n_estimators`: 100-800
- `subsample`: 0.6-0.9
- `colsample_bytree`: 0.6-0.9
- `gamma`: 0.1-5.0
- `reg_alpha`: 0.0-1.0
- `reg_lambda`: 0.5-2.0
- `min_child_weight`: 1-10

### Стратегия торговли
- **Сигнал**: вероятность > 0.55
- **Позиция**: LONG
- **Удержание**: 1 период (5 минут)
- **Комиссии**: не учитываются (упрощённая модель)

## Мониторинг ресурсов

Система отслеживает:
- Использование памяти (макс. 32 ГБ)
- Свободное место на диске (мин. 10 ГБ)
- Загрузку CPU (макс. 95%)
- Время выполнения

При превышении лимитов испытания прерываются.

## Восстановление после сбоев

### Автоматическое возобновление
Оптимизация автоматически возобновляется с последней точки благодаря:
- SQLite базе данных Optuna
- Промежуточному сохранению каждые 50 испытаний
- Проверке целостности данных

### Ручное восстановление
```bash
# Удалить повреждённую базу данных
del user_data\nightly_hyperopt\nightly_hyperopt.db

# Начать заново
python scripts/nightly_hyperopt.py --no-resume
```

## Интеграция с торговой стратегией

### Обновление параметров
После успешной оптимизации:
1. Параметры сохраняются в `user_data/model_best_params_nightly.json`
2. Стратегия `StoicEnsembleStrategyV4` автоматически загружает их
3. Для применения требуется перезапуск бота

### Сравнение с предыдущей версией
Система сравнивает новые параметры с `model_best_params_3y.json` и рекомендует:
- **Улучшение >5%**: обновить параметры
- **Улучшение <5%**: сохранить текущие
- **Ухудшение**: сохранить текущие

## Устранение неполадок

### Проблема: "Data is too old"
**Решение**: обновите данные
```bash
python scripts/download_data.py --pair BTC/USDT --days 30
```

### Проблема: "Memory usage exceeded"
**Решение**: уменьшите количество параллельных задач
```bash
python scripts/nightly_hyperopt.py --n-jobs 2
```

### Проблема: "Study already exists"
**Решение**: удалите старую базу данных
```bash
del user_data\nightly_hyperopt\nightly_hyperopt.db
```

### Проблема: "CPU load > 95%"
**Решение**: система автоматически прерывает испытания, можно уменьшить `n_jobs`

## Производительность

### Ожидаемое время
- **10 испытаний**: ~1 минута
- **100 испытаний**: ~10 минут
- **500 испытаний**: ~2-4 часа
- **1000 испытаний**: ~6-8 часов

### Использование памяти
- **Без XGBoost**: ~2-4 ГБ
- **С XGBoost**: ~4-8 ГБ
- **Пиковое**: до 16 ГБ

## Кастомизация

### Изменение целевой функции
Отредактируйте `NightlySharpeRatioObjective.calculate_strategy_returns()` в `nightly_hyperopt.py`.

### Добавление новых гиперпараметров
Измените `NightlySharpeRatioObjective.__call__()` в `nightly_hyperopt.py`.

### Изменение частоты запуска
Отредактируйте параметры в `setup_nightly_task.ps1`:
```powershell
-DaysInterval 1  # Ежедневно
-StartTime "02:00"  # В 2:00 ночи
```

## Безопасность

### Учётные данные
- API ключи хранятся в `.env`
- Планировщик задач запускается под SYSTEM
- Логи не содержат чувствительной информации

### Резервное копирование
- Результаты автоматически сохраняются
- Рекомендуется настроить backup `user_data/nightly_hyperopt/`

## Лицензия

Система является частью Stoic Citadel Trading Bot и распространяется под лицензией MIT.

## Поддержка

- Документация: `docs/NIGHTLY_HYPEROPT_GUIDE.md`
- Исходный код: `scripts/nightly_hyperopt.py`
- Вопросы: GitHub Issues

---

*Последнее обновление: 25 декабря 2025*
*Версия: 1.0.0*
