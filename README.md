# 🔁 AFLC — Adaptive Feedback Loop Core

**Industrial-grade framework for AI agent self-correction**

---

## 🧠 What is AFLC?

AFLC is a modular, extensible framework that gives AI agents the ability to **evaluate consequences of their actions in real time** and **autonomously stop** when anomalies are detected.

It's not just a library — it's a **cognitive control loop**:
> Action → Sensor → Detectors → Correlator → Risk → Predictor → Policy → Explainer → Memory

---

## 🏗️ Architecture

```
src/
├── core.py          # Orchestrator
├── detectors/       # Pluggable detectors (rule, statistical, ML)
├── correlator.py    # Event correlation
├── risk.py          # Risk engine
├── predictor.py     # Anomaly prediction
├── policy.py        # Decision engine
├── explainer.py     # Explainability
└── memory.py        # History & learning
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/Entonialiev/AFLC.git
cd AFLC
pip install -r requirements.txt
python examples/demo.py
```

---

## 📊 Status

- **v0.1.0** — Architectural foundation (core entities, interfaces, RuleDetector)
- **v0.2.0** — StatisticalDetector + EWMA baseline
- **v0.3.0** — Correlator + Risk Engine
- **v1.0.0** — Full cognitive loop

---

## 📄 License

MIT

---

## 👤 Author

**Elshan Aliev**
- [GitHub](https://github.com/Entonialiev)
- [IETF Draft](https://datatracker.ietf.org/doc/draft-aliev-flc/)
```

---
