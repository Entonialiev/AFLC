```markdown
# 🔁 AFLC — Adaptive Feedback Loop Core

[![CI Tests](https://github.com/Entonialiev/AFLC/actions/workflows/test.yml/badge.svg)](https://github.com/Entonialiev/AFLC/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**Industrial-grade framework for AI agent self-correction and lifecycle management.**

---

## 🧠 What is AFLC?

AFLC is a **modular, extensible framework** that gives AI agents the ability to:
- **Evaluate consequences** of their actions in real time
- **Autonomously stop** when anomalies are detected
- **Manage full lifecycle** of actions from submission to archival
- **Explain decisions** in human-readable format
- **Store and audit** all actions and decisions

It's not just a library — it's a **cognitive control loop**:

> **Action → Observations → Findings → Risk Assessment → Decision → Explanation → Memory → Archive**

---

## 🏗️ Architecture

AFLC follows **Clean Architecture** principles with four layers:

```
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                          │
│  • Aggregates (Execution)                                  │
│  • Entities (Action, Command, Observation, Finding)        │
│  • Value Objects (RiskScore, Confidence, Explanation)      │
│  • Domain Events & State Machine                           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                       │
│  • Use Cases (SubmitAction, ProcessExecution)              │
│  • Orchestrator (ExecutionEngine)                          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                     │
│  • Event Bus (sync/async)                                  │
│  • Storage (Memory, SQLite)                                │
│  • Repository (SQLiteExecutionRepository)                  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Interfaces Layer                        │
│  • Contracts (EventBus, ExecutionRepository)               │
│  • Plugin API                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/Entonialiev/AFLC.git
cd AFLC
pip install -r requirements.txt
```

### Basic Usage

```python
from aflc.bootstrap import create_aflc

# Create AFLC instance
aflc = create_aflc("aflc.db")
engine = aflc.get_engine()

# Submit an action
execution = engine.submit_action(
    agent_id="my-agent",
    endpoint="/api/users",
    method="POST",
    payload={"name": "John"}
)

# Process through lifecycle
execution.submit()
execution.start_processing()

# Add observations and findings
engine.add_observation(
    execution_id=execution.execution_id,
    metric="latency_ms",
    value=150.0
)

engine.add_finding(
    execution_id=execution.execution_id,
    source="rule",
    score=0.7,
    confidence=0.9,
    reason="High latency",
    tags=["performance"]
)

# Complete assessment and make decision
execution.complete_processing()
engine.complete_assessment(
    execution_id=execution.execution_id,
    risk_value=0.85,
    confidence=0.9,
    components={"rule": 0.7}
)

engine.make_decision(
    execution_id=execution.execution_id,
    action="block",
    reason="High risk",
    severity=0.85
)

# Archive
engine.archive_execution(execution.execution_id)

print(f"Decision: {execution.decision['action'].value}")
```

### Run Demo

```bash
python examples/full_demo.py
```

---

## 📊 Features

| Feature | Status |
|---------|--------|
| **Domain-Driven Design** | ✅ |
| **Event-Driven Architecture** | ✅ |
| **State Machine** | ✅ |
| **Async Support** | ✅ |
| **SQLite Storage** | ✅ |
| **In-Memory Storage** | ✅ |
| **Event Bus** | ✅ |
| **Plugin System** | ✅ |
| **Comprehensive Tests** | ✅ |
| **CI/CD** | ✅ |
| **MIT License** | ✅ |

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ --cov=src --cov-report=term

# Run domain tests only
pytest tests/unit/domain/ -v

# Run integration tests
pytest tests/unit/infrastructure/ -v
```

---

## 📁 Project Structure

```
aflc/
├── domain/                 # Domain Layer
│   ├── enums.py           # Enums (ExecutionStatus, DecisionAction, EventType)
│   ├── events.py          # Domain Events
│   ├── exceptions.py      # Domain Exceptions
│   ├── execution.py       # Aggregate Root
│   └── value_objects.py   # Value Objects
├── application/           # Application Layer
│   ├── engine.py          # Orchestrator
│   ├── interfaces.py      # Contracts
│   └── use_cases.py       # Use Cases
├── infrastructure/        # Infrastructure Layer
│   ├── event_bus/         # Event Bus
│   ├── repositories/      # Repositories
│   └── storage/           # Storage Adapters
└── bootstrap.py           # DI Container

tests/
├── unit/                  # Unit Tests
│   ├── application/
│   ├── domain/
│   └── infrastructure/
└── architecture/          # Fitness Functions

examples/
└── full_demo.py           # Full Demo

architecture/              # Architecture Documents
├── vision.md
├── principles.md
├── invariants.md
├── glossary.md
└── domain/
```

---

## 🛠️ Development

### Requirements

- Python 3.9+
- SQLite3 (included in Python)

### Install Dev Dependencies

```bash
pip install -r requirements.txt
pip install pytest pytest-cov
```

### Run Linters

```bash
ruff check .
black .
```

---

## 🤝 Contributing

We welcome contributions! Please see:

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [RFC_PROCESS.md](RFC_PROCESS.md)
- [GOVERNANCE.md](GOVERNANCE.md)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Elshan Aliev**
- GitHub: [Entonialiev](https://github.com/Entonialiev)
- IETF Draft: [draft-aliev-flc-00](https://datatracker.ietf.org/doc/draft-aliev-flc/)
- VC.ru: [article](https://vc.ru/id5878447/3036483-feedback-loop-core-ii-otsenka-posledstviy-deystviy)

---

## ⭐ Star the Project

If you find AFLC useful, please give it a star on GitHub!

---

## 📚 Documentation

- [Architecture Guide](architecture/architecture.md)
- [SPEC v2.0](SPEC_v2.md)
- [ROADMAP](ROADMAP.md)
- [RFC Process](RFC_PROCESS.md)

---

## 🔗 Links

- [GitHub Repository](https://github.com/Entonialiev/AFLC)
- [IETF Draft](https://datatracker.ietf.org/doc/draft-aliev-flc/)
- [VC.ru Article](https://vc.ru/id5878447/3036483-feedback-loop-core-ii-otsenka-posledstviy-deystviy)

---

**Built with ❤️ for safe AI agents.**
```
