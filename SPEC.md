# AFLC Specification v1.0

## 1. Core Pipeline

### 1.1 Execution Flow
```
Action → Context → Detectors → Correlator → Risk → Policy → Decision → Memory → Explainer
```

### 1.2 Data Contracts

#### ActionContext
- **Purpose:** Immutable snapshot of an action execution.
- **Fields:**
  - `action_id: str` — Unique ID
  - `endpoint: str` — Target endpoint
  - `method: str` — HTTP method
  - `latency_ms: float` — Execution time
  - `error_code: int` — 0 = success
  - `response_size: int` — Bytes
- **Invariants:** `latency_ms >= 0`, `error_code >= 0`

#### Detection
- **Purpose:** Result of a single detector.
- **Fields:**
  - `source: str` — Detector name
  - `score: float` — 0.0-1.0 (anomaly likelihood)
  - `confidence: float` — 0.0-1.0 (detector trust)
  - `reason: str` — Human-readable explanation
- **Invariants:** `0.0 <= score <= 1.0`, `0.0 <= confidence <= 1.0`

#### Decision
- **Purpose:** Final decision by Policy.
- **Fields:**
  - `action: str` — "continue" | "pause" | "block" | "retry"
  - `reason: str`
  - `severity: float` — 0.0-1.0
  - `risk_score: float` — 0.0-1.0
- **Invariants:** `action in ['continue', 'pause', 'block', 'retry']`

## 2. Plugin Contracts

### 2.1 Detector Interface
```python
class Detector:
    def detect(self, context: ActionContext) -> Optional[Detection]:
        """Returns Detection if anomaly found, else None."""
```

### 2.2 Policy Interface
```python
class Policy:
    def decide(self, context: ActionContext, detection: Optional[Detection], risk: RiskScore) -> Decision:
        """Returns a Decision."""
```

## 3. Versioning

- **MAJOR** — Breaking changes to public API.
- **MINOR** — New features (backward compatible).
- **PATCH** — Bug fixes.
- v1.0.0 — Stable API with backward compatibility guarantees.
```

---

### 2. Рефакторинг: Общий Pipeline

Вместо дублирования кода в `_execute_action` и `async_execute`, мы создадим единый **`Pipeline`**, который умеет работать и синхронно, и асинхронно.

**Схема:**

```python
class Pipeline:
    def __init__(self, steps: List[PipelineStep]):
        self.steps = steps
    
    def run(self, context: ActionContext) -> Decision:
        # Синхронный запуск
        for step in self.steps:
            context = step.execute(context)
        return context.decision
    
    async def run_async(self, context: ActionContext) -> Decision:
        # Асинхронный запуск
        for step in self.steps:
            context = await step.execute_async(context)
        return context.decision
```

**Где каждый шаг — это:**

```python
class SensorStep(PipelineStep): ...
class DetectorStep(PipelineStep): ...
class CorrelatorStep(PipelineStep): ...
class RiskStep(PipelineStep): ...
class PolicyStep(PipelineStep): ...
class MemoryStep(PipelineStep): ...
class ExplainerStep(PipelineStep): ...
```

---

### 3. Разделить Registry на Factory + Registry

**Сейчас:** Registry делает всё.

**Стало:**
- `Registry` — хранит информацию о доступных классах.
- `Factory` — создаёт экземпляры с параметрами.
- `DI Container` — управляет зависимостями.

---

### 4. Сделать EventBus асинхронным и надёжным

Заменить синхронный вызов слушателей на:

```python
async def publish(self, event: Event):
    tasks = [listener(event) for listener in self._listeners.get(event.name, [])]
    await asyncio.gather(*tasks, return_exceptions=True)
```

Это не даст одному обработчику заблокировать остальные.

---

### 5. Добавить HistoryBackend

Вместо `self.history = []`:

```python
class HistoryBackend:
    def add(self, record: Dict): ...
    def get_recent(self, limit: int): ...
    def get_stats(self): ...
```

Реализации:
- `MemoryHistory` — для тестов.
- `SQLiteHistory` — для лёгких продакшен-систем.
- `RedisHistory` — для высоких нагрузок.

---

## 📋 Чек-лист к v1.0

| Задача | Приоритет | Статус |
|--------|-----------|--------|
| 1. Обновить `SPEC.md` | 🔥 Критический | ⬜ |
| 2. Создать `Pipeline` вместо дублирования | 🔥 Критический | ⬜ |
| 3. Разделить Registry → Factory + Registry | Высокий | ⬜ |
| 4. Сделать EventBus асинхронным | Высокий | ⬜ |
| 5. Добавить HistoryBackend | Средний | ⬜ |
| 6. Обновить документацию и примеры | Средний | ⬜ |
