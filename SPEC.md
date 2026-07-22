# AFLC Specification v1.0

## 1. Core Concepts

### 1.1 ActionContext
Полный контекст выполнения действия.

**Поля:**
- `action_id: str` — уникальный идентификатор
- `endpoint: str` — целевой эндпоинт
- `method: str` — HTTP-метод
- `timestamp: float` — время выполнения
- `latency_ms: float` — задержка в миллисекундах
- `error_code: int` — код ошибки (0 = успех)
- `response_size: int` — размер ответа в байтах
- `user_id: Optional[str]` — идентификатор пользователя
- `history: List[Dict]` — история предыдущих действий

**Инварианты:**
- `latency_ms >= 0`
- `error_code >= 0`
- `response_size >= 0`

### 1.2 Detection
Результат работы детектора.

**Поля:**
- `source: str` — имя детектора
- `score: float` — уверенность в аномалии (0.0-1.0)
- `confidence: float` — доверие к детектору (0.0-1.0)
- `reason: str` — текстовое объяснение
- `tags: List[str]` — метки для категоризации

**Инварианты:**
- `0.0 <= score <= 1.0`
- `0.0 <= confidence <= 1.0`

### 1.3 Decision
Решение Policy Engine.

**Поля:**
- `action: str` — действие (continue, pause, block, retry)
- `reason: str` — причина решения
- `severity: float` — серьёзность (0.0-1.0)
- `confidence: float` — уверенность (0.0-1.0)
- `risk_score: float` — оценка риска (0.0-1.0)
- `explanation: str` — человекочитаемое объяснение

## 2. Lifecycle

```
Action
  ↓
Sensor (сбор данных)
  ↓
Detectors (параллельно)
  ↓
Correlator (объединение)
  ↓
Risk Engine (оценка риска)
  ↓
Policy (принятие решения)
  ↓
Memory (сохранение)
  ↓
Explainer (объяснение)
```

## 3. Interfaces

### 3.1 Detector
```python
class Detector:
    def detect(self, context: ActionContext) -> Optional[Detection]:
        ...
```

### 3.2 Correlator
```python
class Correlator:
    def correlate(self, detections: List[Detection]) -> Optional[Detection]:
        ...
```

### 3.3 Policy
```python
class Policy:
    def decide(self, context: ActionContext, detection: Optional[Detection], 
               risk: RiskScore) -> Decision:
        ...
```

## 4. Configuration

Все настройки через YAML. Основные параметры:
- `agent_id` — идентификатор агента
- `window_size` — размер окна для статистики
- `severity_threshold` — порог для принятия решений
- `detectors` — список активных детекторов с параметрами

## 5. Versioning

- Версия следует семантическому версионированию (MAJOR.MINOR.PATCH)
- v0.x — нестабильный API (до v1.0)
- v1.0 — стабильный API с обратной совместимостью
```

---

## 📊 Итоговый чек-лист

| Задача | Статус |
|--------|--------|
| Создать `SPEC.md` | ⬜ |
| Создать `src/registry.py` | ⬜ |
| Создать `integrations/langgraph.py` | ⬜ |
| Создать `benchmarks/` | ⬜ |
| Обновить `README.md` | ⬜ |
| Сделать релиз v0.6.0 | ⬜ |
