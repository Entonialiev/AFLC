"""
AFLC - Adaptive Feedback Loop Core
Version: 0.6.0
- Async pipeline support
- Plugin Registry integration
- Event Bus for loose coupling
- Logging system
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Union
import time
import asyncio
import logging

from .events import EventBus, Event
from .registry import registry

# Настройка логирования
logger = logging.getLogger("aflc")


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
    """Синхронный детектор"""
    def detect(self, context: ActionContext) -> Optional[Detection]:
        raise NotImplementedError


class AsyncDetector:
    """Асинхронный детектор"""
    async def detect(self, context: ActionContext) -> Optional[Detection]:
        raise NotImplementedError


class Correlator:
    def correlate(self, detections: List[Detection]) -> Optional[Detection]:
        raise NotImplementedError


class Predictor:
    def predict(self, context: ActionContext, horizon: int = 10) -> Dict[str, float]:
        raise NotImplementedError


class Policy:
    """Синхронная политика"""
    def decide(self, context: ActionContext, detection: Optional[Detection], 
               risk: RiskScore) -> Decision:
        raise NotImplementedError


class AsyncPolicy:
    """Асинхронная политика"""
    async def decide(self, context: ActionContext, detection: Optional[Detection], 
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
        
        # Синхронный вызов
        decision = flc.execute(my_action, endpoint="/api/users", method="GET")
        
        # Асинхронный вызов
        decision = await flc.async_execute(my_action, endpoint="/api/users", method="GET")
    """
    
    def __init__(self, agent_id: str, config: Optional[Dict] = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.event_bus = EventBus()
        
        self.detectors: List[Union[Detector, AsyncDetector]] = []
        self.correlator: Optional[Correlator] = None
        self.predictor: Optional[Predictor] = None
        self.risk_engine: Optional['RiskEngine'] = None
        self.policy: Optional[Union[Policy, AsyncPolicy]] = None
        self.explainer: Optional[Explainer] = None
        self.memory: Optional[Memory] = None
        
        self.action_counter = 0
        self.history: List[Dict] = []
        self.last_decision: Optional[Decision] = None
        
        # Подписываемся на события по умолчанию
        self._setup_default_event_handlers()
    
    def _setup_default_event_handlers(self):
        """Настраивает стандартные обработчики событий"""
        @self.event_bus.subscribe("action_started")
        def on_action_started(event: Event):
            logger.debug(f"Action started: {event.data.get('action_id')}")
        
        @self.event_bus.subscribe("decision_made")
        def on_decision_made(event: Event):
            logger.info(f"Decision made: {event.data.get('decision').action}")
        
        @self.event_bus.subscribe("anomaly_detected")
        def on_anomaly_detected(event: Event):
            logger.warning(f"Anomaly detected: {event.data.get('detection').reason}")
    
    @classmethod
    def from_config(cls, config_path: str) -> 'AdaptiveFeedbackLoopCore':
        """Создаёт экземпляр AFLC из YAML-конфигурации."""
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls.from_config_dict(data)
    
    @classmethod
    def from_config_dict(cls, data: Dict[str, Any]) -> 'AdaptiveFeedbackLoopCore':
        """Создаёт экземпляр AFLC из словаря конфигурации через Plugin Registry."""
        agent_id = data.get("agent_id", "default-agent")
        flc = cls(agent_id=agent_id, config=data)
        
        # Регистрируем детекторы из конфига через реестр
        for name, detector_config in data.get("detectors", {}).items():
            if not detector_config.get("enabled", True):
                continue
            
            detector = registry.create_detector(name, detector_config.get("params", {}))
            if detector:
                flc.register_detector(detector)
                logger.info(f"Registered detector: {name}")
            else:
                logger.warning(f"Detector not found in registry: {name}")
        
        # Коррелятор
        correlator_name = data.get("correlator", {}).get("type", "weighted")
        correlator = registry.create_correlator(correlator_name, data.get("correlator", {}))
        if correlator:
            flc.register_correlator(correlator)
        
        # Risk Engine
        risk_engine = registry.create_risk_engine(data.get("risk", {}))
        if risk_engine:
            flc.register_risk_engine(risk_engine)
        
        # Policy
        policy_name = data.get("policy", {}).get("type", "default")
        policy = registry.create_policy(policy_name, data.get("policy", {}))
        if policy:
            flc.register_policy(policy)
        
        # Memory
        memory_config = data.get("memory", {})
        memory = registry.create_memory(memory_config.get("type", "default"), memory_config)
        if memory:
            flc.register_memory(memory)
        
        return flc
    
    def register_detector(self, detector: Union[Detector, AsyncDetector]) -> 'AdaptiveFeedbackLoopCore':
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
    
    def register_policy(self, policy: Union[Policy, AsyncPolicy]) -> 'AdaptiveFeedbackLoopCore':
        self.policy = policy
        return self
    
    def register_explainer(self, explainer: Explainer) -> 'AdaptiveFeedbackLoopCore':
        self.explainer = explainer
        return self
    
    def register_memory(self, memory: Memory) -> 'AdaptiveFeedbackLoopCore':
        self.memory = memory
        return self
    
    def _execute_action(self, action_func: Callable, *args, **kwargs) -> tuple:
        """Выполняет действие и возвращает (context, detections, decision)"""
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
        
        self.event_bus.publish(Event("action_started", {"action_id": action_id, "context": context}))
        
        # --- 2. Детекторы ---
        detections = []
        for detector in self.detectors:
            try:
                detection = detector.detect(context)
                if detection:
                    detections.append(detection)
            except Exception as e:
                logger.error(f"Detector error: {e}")
                continue
        
        if detections:
            self.event_bus.publish(Event("detections_created", {"detections": detections}))
        
        # --- 3. Коррелятор ---
        final_detection = None
        if self.correlator and detections:
            final_detection = self.correlator.correlate(detections)
        elif detections:
            final_detection = max(detections, key=lambda x: x.score)
        
        # --- 4. Прогнозирование ---
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
        
        self.event_bus.publish(Event("decision_made", {"decision": decision}))
        
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
        
        return context, detections, decision
    
    def execute(self, action_func: Callable, *args, **kwargs) -> Decision:
        """Синхронное выполнение действия."""
        _, _, decision = self._execute_action(action_func, *args, **kwargs)
        return decision
    
    async def async_execute(self, action_func: Callable, *args, **kwargs) -> Decision:
        """
        Асинхронное выполнение действия с поддержкой асинхронных компонентов.
        """
        self.action_counter += 1
        action_id = f"{self.agent_id}-{self.action_counter:04d}"
        
        # --- 1. Выполняем действие ---
        start_time = time.time()
        try:
            # Если action_func асинхронная
            if asyncio.iscoroutinefunction(action_func):
                result = await action_func(*args, **kwargs)
            else:
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
        
        await self.event_bus.publish_async(Event("action_started", {"action_id": action_id, "context": context}))
        
        # --- 2. Детекторы (поддерживаем и синхронные, и асинхронные) ---
        detections = []
        for detector in self.detectors:
            try:
                if hasattr(detector, 'detect') and asyncio.iscoroutinefunction(detector.detect):
                    detection = await detector.detect(context)
                else:
                    detection = detector.detect(context)
                if detection:
                    detections.append(detection)
            except Exception as e:
                logger.error(f"Detector error: {e}")
                continue
        
        if detections:
            await self.event_bus.publish_async(Event("detections_created", {"detections": detections}))
        
        # --- 3. Коррелятор ---
        final_detection = None
        if self.correlator and detections:
            final_detection = self.correlator.correlate(detections)
        elif detections:
            final_detection = max(detections, key=lambda x: x.score)
        
        # --- 4. Прогнозирование ---
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
        
        # --- 6. Policy (поддерживаем и синхронную, и асинхронную) ---
        if self.policy:
            if hasattr(self.policy, 'decide') and asyncio.iscoroutinefunction(self.policy.decide):
                decision = await self.policy.decide(context, final_detection, risk)
            else:
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
        
        await self.event_bus.publish_async(Event("decision_made", {"decision": decision}))
        
        # --- 7. Memory ---
        if self.memory:
            if hasattr(self.memory, 'store') and asyncio.iscoroutinefunction(self.memory.store):
                await self.memory.store(context, final_detection, decision, risk)
            else:
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
    print("🔁 AFLC v0.6.0 — Full Pipeline with Async")
    print("=" * 50)
    
    flc = AdaptiveFeedbackLoopCore(agent_id="demo-agent")
    flc.register_policy(DefaultPolicy())
    flc.register_correlator(SimpleCorrelator())
    
    def my_action(delay_ms=100):
        import time
        time.sleep(delay_ms / 1000.0)
        return {"status": "ok"}
    
    # Синхронный вызов
    print("\n🔄 Синхронный вызов:")
    for i in range(3):
        decision = flc.execute(
            my_action, 50 + i * 10,
            endpoint="/api/test",
            method="GET"
        )
        print(f"  {i+1}: {decision.action} (severity: {decision.severity:.2f})")
    
    # Асинхронный вызов
    print("\n⚡ Асинхронный вызов:")
    async def run_async():
        for i in range(3):
            decision = await flc.async_execute(
                my_action, 50 + i * 10,
                endpoint="/api/test",
                method="GET"
            )
            print(f"  {i+1}: {decision.action} (severity: {decision.severity:.2f})")
    
    asyncio.run(run_async())
    
    print(f"\n📊 Статистика: {flc.get_stats()}")
