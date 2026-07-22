"""
AFLC - Adaptive Feedback Loop Core
Industrial-grade framework for AI agent self-correction
Version: 0.4.0 (with YAML config support)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
import time


# --- БАЗОВЫЕ СУЩНОСТИ ---

@dataclass
class ActionContext:
    """Полный контекст выполнения действия"""
    action_id: str
    endpoint: str
    method: str
    timestamp: float = field(default_factory=time.time)
    payload: Optional[Dict] = None
    headers: Optional[Dict] = None
    response: Optional[Dict] = None
    latency_ms: float = 0.0
    error_code: int = 0
    response_size: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    history: List[Dict] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}


@dataclass
class Detection:
    """Результат работы одного детектора"""
    source: str
    score: float
    confidence: float
    reason: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Decision:
    """Решение, принятое Policy Engine"""
    action: str
    reason: str
    severity: float
    confidence: float
    risk_score: float
    explanation: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskScore:
    """Оценка риска"""
    value: float
    confidence: float
    components: Dict[str, float] = field(default_factory=dict)


# --- ИНТЕРФЕЙСЫ ---

class Detector:
    def detect(self, context: ActionContext) -> Optional[Detection]:
        raise NotImplementedError


class Correlator:
    def correlate(self, detections: List[Detection]) -> Optional[Detection]:
        raise NotImplementedError


class Predictor:
    def predict(self, context: ActionContext, horizon: int = 10) -> Dict[str, float]:
        raise NotImplementedError


class Policy:
    def decide(self, context: ActionContext, detection: Optional[Detection], 
               risk: RiskScore) -> Decision:
        raise NotImplementedError


class Explainer:
    def explain(self, context: ActionContext, detection: Optional[Detection],
                decision: Decision, risk: Optional[RiskScore]) -> str:
        raise NotImplementedError


class Memory:
    def store(self, context: ActionContext, detection: Optional[Detection],
              decision: Decision, risk: RiskScore) -> None:
        raise NotImplementedError


# --- ГЛАВНЫЙ ОРКЕСТРАТОР ---

class AdaptiveFeedbackLoopCore:
    """
    Главный класс AFLC. Оркестрирует все компоненты.
    
    Usage:
        flc = AdaptiveFeedbackLoopCore(agent_id="my-agent")
        flc.register_detector(RuleDetector())
        flc.register_correlator(Correlator())
        flc.register_risk_engine(RiskEngine())
        flc.register_policy(DefaultPolicy())
        flc.register_explainer(Explainer())
        flc.register_memory(Memory())
        
        decision = flc.execute(my_action, endpoint="/api/users", method="GET")
    """
    
    def __init__(self, agent_id: str, config: Optional[Dict] = None):
        self.agent_id = agent_id
        self.config = config or {}
        
        self.detectors: List[Detector] = []
        self.correlator: Optional[Correlator] = None
        self.predictor: Optional[Predictor] = None
        self.risk_engine: Optional['RiskEngine'] = None
        self.policy: Optional[Policy] = None
        self.explainer: Optional[Explainer] = None
        self.memory: Optional[Memory] = None
        
        self.action_counter = 0
        self.history: List[Dict] = []
        self.last_decision: Optional[Decision] = None
    
    @classmethod
    def from_config(cls, config_path: str) -> 'AdaptiveFeedbackLoopCore':
        """
        Создаёт экземпляр AFLC из YAML-конфигурации.
        Требуется установить pyyaml: pip install pyyaml
        """
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls.from_config_dict(data)
    
    @classmethod
    def from_config_dict(cls, data: Dict[str, Any]) -> 'AdaptiveFeedbackLoopCore':
        """Создаёт экземпляр AFLC из словаря конфигурации"""
        from .detectors import RuleDetector, StatisticalDetector
        from .correlator import Correlator
        from .risk import RiskEngine
        from .memory import Memory
        
        agent_id = data.get("agent_id", "default-agent")
        flc = cls(agent_id=agent_id, config=data)
        
        # Регистрируем детекторы
        for name, detector_config in data.get("detectors", {}).items():
            if not detector_config.get("enabled", True):
                continue
            
            params = detector_config.get("params", {})
            
            if name == "rule":
                flc.register_detector(RuleDetector(params))
            elif name == "statistical":
                flc.register_detector(StatisticalDetector(params))
            # Добавляйте другие детекторы по мере появления
        
        # Коррелятор
        flc.register_correlator(Correlator(data.get("correlator", {})))
        
        # Risk Engine
        flc.register_risk_engine(RiskEngine(data.get("risk", {})))
        
        # Policy
        flc.register_policy(DefaultPolicy())
        
        # Memory
        memory_config = data.get("memory", {})
        flc.register_memory(Memory(**memory_config))
        
        return flc
    
    def register_detector(self, detector: Detector) -> 'AdaptiveFeedbackLoopCore':
        self.detectors.append(detector)
        return self
    
    def register_correlator(self, correlator: Correlator) -> 'AdaptiveFeedbackLoopCore':
        self.correlator = correlator
        return self
    
    def register_predictor(self, predictor: Predictor) -> 'AdaptiveFeedbackLoopCore':
        self.predictor = predictor
        return self
    
    def register_risk_engine(self, risk_engine: 'RiskEngine') -> 'AdaptiveFeedbackLoopCore':
        self.risk_engine = risk_engine
        return self
    
    def register_policy(self, policy: Policy) -> 'AdaptiveFeedbackLoopCore':
        self.policy = policy
        return self
    
    def register_explainer(self, explainer: Explainer) -> 'AdaptiveFeedbackLoopCore':
        self.explainer = explainer
        return self
    
    def register_memory(self, memory: Memory) -> 'AdaptiveFeedbackLoopCore':
        self.memory = memory
        return self
    
    def execute(self, action_func: Callable, *args, **kwargs) -> Decision:
        self.action_counter += 1
        action_id = f"{self.agent_id}-{self.action_counter:04d}"
        
        # --- 1. Выполняем действие ---
        start_time = time.time()
        try:
            result = action_func(*args, **kwargs)
            error_code = 0
            response_body = str(result) if result else ""
        except Exception as e:
            result = {"error": str(e)}
            error_code = 500
            response_body = str(e)
        
        latency_ms = (time.time() - start_time) * 1000
        response_size = len(response_body) if response_body else 0
        
        context = ActionContext(
            action_id=action_id,
            endpoint=kwargs.get("endpoint", "default"),
            method=kwargs.get("method", "GET"),
            payload=kwargs.get("payload", {}),
            latency_ms=latency_ms,
            error_code=error_code,
            response_size=response_size,
            response=result,
            user_id=kwargs.get("user_id", None),
            session_id=kwargs.get("session_id", None),
            history=self.history
        )
        
        # --- 2. Детекторы ---
        detections = []
        for detector in self.detectors:
            try:
                detection = detector.detect(context)
                if detection:
                    detections.append(detection)
            except Exception as e:
                print(f"⚠️ Detector error: {e}")
                continue
        
        # --- 3. Коррелятор ---
        final_detection = None
        if self.correlator and detections:
            final_detection = self.correlator.correlate(detections)
        elif detections:
            final_detection = max(detections, key=lambda x: x.score)
        
        # --- 4. Прогнозирование (заглушка) ---
        if self.predictor:
            predictions = self.predictor.predict(context)
        else:
            predictions = {}
        
        # --- 5. Risk Engine ---
        if self.risk_engine and final_detection:
            risk = self.risk_engine.evaluate(context, final_detection)
        else:
            risk = RiskScore(value=0.0, confidence=0.0)
            if final_detection:
                risk = RiskScore(
                    value=final_detection.score,
                    confidence=final_detection.confidence,
                    components={"detection_score": final_detection.score}
                )
        
        # --- 6. Policy ---
        if self.policy:
            decision = self.policy.decide(context, final_detection, risk)
        else:
            if final_detection and final_detection.score > 0.3:
                decision = Decision(
                    action="pause",
                    reason=final_detection.reason,
                    severity=final_detection.score,
                    confidence=final_detection.confidence,
                    risk_score=risk.value,
                    explanation=f"Anomaly detected by {final_detection.source}"
                )
            else:
                decision = Decision(
                    action="continue",
                    reason="No anomalies detected",
                    severity=0.0,
                    confidence=1.0,
                    risk_score=0.0,
                    explanation="All systems nominal"
                )
        
        # --- 7. Memory ---
        if self.memory:
            self.memory.store(context, final_detection, decision, risk)
        
        # --- 8. Explainer ---
        if self.explainer:
            explanation = self.explainer.explain(context, final_detection, decision, risk)
            decision.explanation = explanation
        
        # --- 9. История ---
        self.history.append({
            "action_id": action_id,
            "timestamp": time.time(),
            "endpoint": context.endpoint,
            "method": context.method,
            "latency_ms": latency_ms,
            "error_code": error_code,
            "decision": decision.action,
            "severity": decision.severity,
            "risk_score": decision.risk_score
        })
        self.last_decision = decision
        
        return decision
    
    def reset(self):
        self.action_counter = 0
        self.history = []
        self.last_decision = None
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "actions": self.action_counter,
            "detectors": [d.__class__.__name__ for d in self.detectors],
            "has_correlator": self.correlator is not None,
            "has_risk_engine": self.risk_engine is not None,
            "has_policy": self.policy is not None,
            "has_explainer": self.explainer is not None,
            "has_memory": self.memory is not None,
            "last_decision": self.last_decision.action if self.last_decision else None
        }


# --- ВСТРОЕННЫЕ РЕАЛИЗАЦИИ ---

class DefaultPolicy(Policy):
    def decide(self, context: ActionContext, detection: Optional[Detection],
               risk: RiskScore) -> Decision:
        if detection and detection.score > 0.3:
            return Decision(
                action="pause",
                reason=detection.reason,
                severity=detection.score,
                confidence=detection.confidence,
                risk_score=risk.value,
                explanation=f"Anomaly detected by {detection.source}"
            )
        return Decision(
            action="continue",
            reason="No anomalies detected",
            severity=0.0,
            confidence=1.0,
            risk_score=0.0,
            explanation="All systems nominal"
        )


class SimpleCorrelator(Correlator):
    def correlate(self, detections: List[Detection]) -> Optional[Detection]:
        if not detections:
            return None
        return max(detections, key=lambda x: x.score)


# --- ПРИМЕР ---

if __name__ == "__main__":
    print("🔁 AFLC v0.4.0 — Full Pipeline")
    print("=" * 50)
    
    flc = AdaptiveFeedbackLoopCore(agent_id="demo-agent")
    flc.register_policy(DefaultPolicy())
    flc.register_correlator(SimpleCorrelator())
    
    def my_action(delay_ms=100):
        import time
        time.sleep(delay_ms / 1000.0)
        return {"status": "ok"}
    
    for i in range(5):
        decision = flc.execute(
            my_action, 50 + i * 10,
            endpoint="/api/test",
            method="GET"
        )
        print(f"  {i+1}: {decision.action} (severity: {decision.severity:.2f})")
    
    print("\n🔴 Аномальное действие:")
    decision = flc.execute(
        my_action, 3000,
        endpoint="/api/test",
        method="GET"
    )
    print(f"  → {decision.action}: {decision.reason}")
    
    print(f"\n📊 Статистика: {flc.get_stats()}")
