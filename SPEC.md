# AFLC Specification v1.0

## 1. Core Concepts

### 1.1 ActionContext
Полный контекст выполнения действия. Содержит:
- `action_id`: уникальный идентификатор
- `endpoint`: целевой эндпоинт
- `method`: HTTP-метод
- `latency_ms`: время выполнения
- `error_code`: код ошибки
- `user_id`: идентификатор пользователя
- `history`: история предыдущих действий

### 1.2 Detection
Результат работы детектора:
- `source`: имя детектора
- `score`: 0.0-1.0 (уверенность в аномалии)
- `confidence`: 0.0-1.0 (доверие к детектору)
- `reason`: текстовое объяснение
- `tags`: метки для категоризации

### 1.3 Decision
Решение Policy Engine:
- `action`: continue / pause / block / retry
- `reason`: причина решения
- `severity`: 0.0-1.0
- `risk_score`: 0.0-1.0

## 2. Lifecycle

```
Action → Sensor → Detectors → Correlator → Risk → Policy → Memory → Explainer
```

Каждый этап имеет чёткий вход и выход.

## 3. Plugins

AFLC поддерживает плагины через интерфейсы:
- `Detector`
- `Correlator`
- `Policy`
- `Predictor`
- `MemoryBackend`

## 4. Configuration

Все настройки через YAML:
- `config.yaml` — основной файл
- Переменные окружения для секретов
```
