# AFLC Specification v1.0

**Status:** Draft  
**Version:** 1.0.0  
**Date:** 2026-07-22  
**Author:** Elshan Aliev  

---

## 1. Purpose

AFLC (Adaptive Feedback Loop Core) is an industrial-grade framework for **AI agent self-correction**. It provides a modular, extensible pipeline for:

- Collecting action metrics
- Detecting anomalies (via pluggable detectors)
- Correlating detection results
- Assessing risk
- Making decisions (continue, pause, block, retry)
- Generating human-readable explanations
- Storing history for learning and audit

---

## 2. Core Pipeline

### 2.1 Execution Flow

```
Action
  ↓
Sensor (collect metrics)
  ↓
Detectors (parallel, pluggable)
  ↓
Correlator (merge results)
  ↓
Risk Engine (contextual risk)
  ↓
Policy (decision)
  ↓
Memory (store history)
  ↓
Explainer (generate explanation)
  ↓
Decision
```

### 2.2 Lifecycle

1. **Action** — User executes an action via `execute()` or `async_execute()`.
2. **Sensor** — Collects metrics (latency, error code, response size).
3. **Detectors** — Run all registered detectors (sync/async) in parallel.
4. **Correlator** — Merges multiple `Detection` objects into one.
5. **Risk Engine** — Evaluates context (endpoint, method, user, time).
6. **Policy** — Decides: continue, pause, block, retry.
7. **Memory** — Stores the decision and context.
8. **Explainer** — Generates a human-readable explanation.
9. **Decision** — Returns the final `Decision` object.

---

## 3. Data Contracts

### 3.1 ActionContext

**Purpose:** Immutable snapshot of an action execution.

**Fields:**

| Field | Type | Description | Invariants |
|-------|------|-------------|------------|
| `action_id` | `str` | Unique identifier | Non-empty |
| `endpoint` | `str` | Target endpoint | Non-empty |
| `method` | `str` | HTTP method (GET, POST, etc.) | Non-empty |
| `timestamp` | `float` | UNIX timestamp | > 0 |
| `latency_ms` | `float` | Execution time in ms | >= 0 |
| `error_code` | `int` | 0 = success, else error | >= 0 |
| `response_size` | `int` | Response body size in bytes | >= 0 |
| `user_id` | `Optional[str]` | User identifier | - |
| `history` | `List[Dict]` | Previous actions | - |

### 3.2 Detection

**Purpose:** Result of a single detector.

**Fields:**

| Field | Type | Description | Invariants |
|-------|------|-------------|------------|
| `source` | `str` | Detector name | Non-empty |
| `score` | `float` | Anomaly likelihood (0-1) | 0.0 - 1.0 |
| `confidence` | `float` | Detector trust (0-1) | 0.0 - 1.0 |
| `reason` | `str` | Human-readable explanation | Non-empty |
| `tags` | `List[str]` | Categorization tags | - |
| `metadata` | `Dict` | Additional data | - |

### 3.3 Decision

**Purpose:** Final decision by Policy.

**Fields:**

| Field | Type | Description | Invariants |
|-------|------|-------------|------------|
| `action` | `str` | continue, pause, block, retry | Must be one of the four |
| `reason` | `str` | Why this decision was made | Non-empty |
| `severity` | `float` | 0-1 (how severe) | 0.0 - 1.0 |
| `confidence` | `float` | 0-1 (decision confidence) | 0.0 - 1.0 |
| `risk_score` | `float` | 0-1 (combined risk) | 0.0 - 1.0 |
| `explanation` | `str` | Human-readable explanation | - |
| `metadata` | `Dict` | Additional data | - |

### 3.4 RiskScore

**Purpose:** Contextual risk assessment.

**Fields:**

| Field | Type | Description | Invariants |
|-------|------|-------------|------------|
| `value` | `float` | 0-1 (risk level) | 0.0 - 1.0 |
| `confidence` | `float` | 0-1 (risk confidence) | 0.0 - 1.0 |
| `components` | `Dict[str, float]` | Individual risk components | - |

---

## 4. Plugin Contracts

### 4.1 Detector Interface

**Purpose:** Detect anomalies in `ActionContext`.

```python
class Detector:
    """Sync detector"""
    def detect(self, context: ActionContext) -> Optional[Detection]:
        raise NotImplementedError

class AsyncDetector:
    """Async detector"""
    async def detect(self, context: ActionContext) -> Optional[Detection]:
        raise NotImplementedError
```

**Contract:**
- Returns `None` if no anomaly.
- Returns `Detection` if anomaly found.
- Must not throw exceptions (errors are caught and logged).

### 4.2 Correlator Interface

**Purpose:** Merge multiple detections into one.

```python
class Correlator:
    def correlate(self, detections: List[Detection]) -> Optional[Detection]:
        raise NotImplementedError
```

**Contract:**
- Returns `None` if no detections.
- Returns a single `Detection` with merged score/confidence.

### 4.3 Policy Interface

**Purpose:** Make a decision based on detection and risk.

```python
class Policy:
    """Sync policy"""
    def decide(self, context: ActionContext, detection: Optional[Detection], 
               risk: RiskScore) -> Decision:
        raise NotImplementedError

class AsyncPolicy:
    """Async policy"""
    async def decide(self, context: ActionContext, detection: Optional[Detection], 
                     risk: RiskScore) -> Decision:
        raise NotImplementedError
```

**Contract:**
- Always returns a `Decision`.
- Must not throw exceptions.

### 4.4 Memory Interface

**Purpose:** Store history of actions and decisions.

```python
class Memory:
    def store(self, context: ActionContext, detection: Optional[Detection],
              decision: Decision, risk: RiskScore) -> None:
        raise NotImplementedError
```

**Contract:**
- Must be non-blocking (fast).
- Must handle errors gracefully.

### 4.5 Explainer Interface

**Purpose:** Generate human-readable explanations.

```python
class Explainer:
    def explain(self, context: ActionContext, detection: Optional[Detection],
                decision: Decision, risk: Optional[RiskScore]) -> str:
        raise NotImplementedError
```

**Contract:**
- Always returns a string.
- Must not throw exceptions.

### 4.6 Predictor Interface

**Purpose:** Predict future anomalies.

```python
class Predictor:
    def predict(self, context: ActionContext, horizon: int = 10) -> Dict[str, float]:
        raise NotImplementedError
```

**Contract:**
- Returns dict with prediction probabilities.
- Must not throw exceptions.

---

## 5. Configuration

### 5.1 YAML Schema

```yaml
agent_id: str
window_size: int
severity_threshold: float

detectors:
  name:
    enabled: bool
    params: dict

correlator:
  type: str
  params: dict

risk:
  endpoint_base_risk: dict
  method_risk: dict
  user_risk: dict

policy:
  type: str
  params: dict

memory:
  type: str
  params: dict
```

### 5.2 Default Values

| Parameter | Default |
|-----------|---------|
| `agent_id` | "default-agent" |
| `window_size` | 30 |
| `severity_threshold` | 0.3 |
| `correlator.type` | "weighted" |
| `policy.type` | "default" |
| `memory.type` | "default" |

---

## 6. Events

### 6.1 Event Types

| Event Name | Payload | Description |
|------------|---------|-------------|
| `action_started` | `{"action_id": str, "context": ActionContext}` | Action execution started |
| `detections_created` | `{"detections": List[Detection]}` | Detectors finished |
| `decision_made` | `{"decision": Decision}` | Policy made a decision |
| `anomaly_detected` | `{"detection": Detection}` | Anomaly found (severity > 0) |

### 6.2 Event Bus Contract

```python
class EventBus:
    def subscribe(self, event_name: str) -> Callable:
        """Decorator for sync/async listeners."""
    
    def publish(self, event: Event) -> None:
        """Sync publish (fast, non-blocking)."""
    
    async def publish_async(self, event: Event) -> None:
        """Async publish (parallel execution)."""
```

---

## 7. Versioning

### 7.1 Semantic Versioning

- **MAJOR** — Breaking changes to public API.
- **MINOR** — New features (backward compatible).
- **PATCH** — Bug fixes.

### 7.2 Stability Guarantees

| Version | API Stability |
|---------|---------------|
| v0.x.x | Unstable (experimental) |
| v1.0.0 | Stable (backward compatible) |
| v1.x.x | Minor additions, no breaking changes |
| v2.0.0 | Breaking changes allowed |

---

## 8. Security

### 8.1 Requirements

- All detectors must be isolated (no side effects).
- Policy must not expose sensitive data.
- Memory must support encryption (future).

### 8.2 Defaults

- No sensitive data stored by default.
- Logging sanitized (no PII).

---

## 9. Testing

### 9.1 Required Tests

- Unit tests for each component.
- Integration tests for full pipeline.
- Performance benchmarks.

### 9.2 Coverage Target

- Core: 90%+
- Detectors: 80%+
- Risk/Policies: 80%+

---

## 10. Roadmap to v1.0

| Version | Features |
|---------|----------|
| v0.6.0 | Async pipeline, Event Bus, Plugin Registry, Logging |
| v0.7.0 | History Backend (SQLite), ISolation Forest Detector |
| v0.8.0 | Predictor, Graph-based correlator |
| v0.9.0 | Full documentation, Integration examples |
| v1.0.0 | Stable API, Benchmark suite, Production-ready |

---

## 11. Author

**Elshan Aliev**
- GitHub: [Entonialiev](https://github.com/Entonialiev)
- IETF: [draft-aliev-flc-00](https://datatracker.ietf.org/doc/draft-aliev-flc/)
```
