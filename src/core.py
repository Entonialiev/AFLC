"""
AFLC - Adaptive Feedback Loop Core
Version: 0.7.3 (final circular import fix)
"""

from typing import Dict, List, Optional, Any, Callable, Union
import time
import asyncio
import logging

from .models import ActionContext, Detection, Decision, RiskScore
from .interfaces import (
    Detector, AsyncDetector, Correlator, Predictor,
    Policy, AsyncPolicy, Explainer, Memory
)
from .events import EventBus, Event
from .registry import registry
from .exceptions import AFLCError, PipelineError, ConfigurationError

logger = logging.getLogger("aflc")


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
        flc.register_history_backend(SQLiteHistory())
        
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
        self.history_backend: Optional['HistoryBackend'] = None
        
        self.action_counter = 0
        self.last_decision: Optional[Decision] = None
        
        self._setup_default_event_handlers()
    
    def _setup_default_event_handlers(self):
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
        import yaml
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return cls.from_config_dict(data)
        except Exception as e:
            raise ConfigurationError(f"Failed to load config from {config_path}: {e}") from e
    
    @classmethod
    def from_config_dict(cls, data: Dict[str, Any]) -> 'AdaptiveFeedbackLoopCore':
        from .history import MemoryHistory, SQLiteHistory
        
        agent_id = data.get("agent_id", "default-agent")
        flc = cls(agent_id=agent_id, config=data)
        
        for name, detector_config in data.get("detectors", {}).items():
            if not detector_config.get("enabled", True):
                continue
            detector = registry.create_detector(name, detector_config.get("params", {}))
            if detector:
                flc.register_detector(detector)
                logger.info(f"Registered detector: {name}")
            else:
                logger.warning(f"Detector not found in registry: {name}")
        
        correlator_name = data.get("correlator", {}).get("type", "weighted")
        correlator = registry.create_correlator(correlator_name, data.get("correlator", {}))
        if correlator:
            flc.register_correlator(correlator)
        
        risk_engine = registry.create_risk_engine(data.get("risk", {}))
        if risk_engine:
            flc.register_risk_engine(risk_engine)
        
        policy_name = data.get("policy", {}).get("type", "default")
        policy = registry.create_policy(policy_name, data.get("policy", {}))
        if policy:
            flc.register_policy(policy)
        
        memory_config = data.get("memory", {})
        memory = registry.create_memory(memory_config.get("type", "default"), memory_config)
        if memory:
            flc.register_memory(memory)
        
        history_config = data.get("history", {})
        history_type = history_config.get("type", "memory")
        history_params = history_config.get("params", {})
        
        if history_type == "sqlite":
            flc.register_history_backend(SQLiteHistory(**history_params))
        else:
            flc.register_history_backend(MemoryHistory(**history_params))
        
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
    
    def register_history_backend(self, backend: 'HistoryBackend') -> 'AdaptiveFeedbackLoopCore':
        self.history_backend = backend
        return self
    
    def _build_pipeline(self):
        from .pipeline import Pipeline
        return Pipeline(self)
    
    def _prepare_action(self, action_func: Callable, *args, **kwargs) -> ActionContext:
        self.action_counter += 1
        action_id = f"{self.agent_id}-{self.action_counter:04d}"
        
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
        
        return ActionContext(
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
            history=[]
        )
    
    def _finalize(self, result_context: ActionContext) -> Decision:
        decision = getattr(result_context, '_decision', None)
        if decision is None:
            raise PipelineError("Pipeline did not produce a decision")
        
        self.last_decision = decision
        
        if self.history_backend:
            self.history_backend.add({
                "action_id": result_context.action_id,
                "timestamp": result_context.timestamp,
                "endpoint": result_context.endpoint,
                "method": result_context.method,
                "latency_ms": result_context.latency_ms,
                "error_code": result_context.error_code,
                "decision": decision.action,
                "severity": decision.severity,
                "risk_score": decision.risk_score,
                "metadata": {"payload": result_context.payload, "user_id": result_context.user_id}
            })
        
        return decision
    
    def execute(self, action_func: Callable, *args, **kwargs) -> Decision:
        context = self._prepare_action(action_func, *args, **kwargs)
        result_context = self._build_pipeline().execute(context)
        return self._finalize(result_context)
    
    async def async_execute(self, action_func: Callable, *args, **kwargs) -> Decision:
        context = self._prepare_action(action_func, *args, **kwargs)
        result_context = await self._build_pipeline().execute_async(context)
        return self._finalize(result_context)
    
    def reset(self):
        self.action_counter = 0
        self.last_decision = None
        if self.history_backend:
            self.history_backend.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        stats = {
            "agent_id": self.agent_id,
            "actions": self.action_counter,
            "detectors": [d.__class__.__name__ for d in self.detectors],
            "has_correlator": self.correlator is not None,
            "has_risk_engine": self.risk_engine is not None,
            "has_policy": self.policy is not None,
            "has_explainer": self.explainer is not None,
            "has_memory": self.memory is not None,
            "has_history_backend": self.history_backend is not None,
            "last_decision": self.last_decision.action if self.last_decision else None
        }
        if self.history_backend:
            stats["history"] = self.history_backend.get_stats()
        return stats


if __name__ == "__main__":
    print("🔁 AFLC v0.7.3 — Circular Import Fixed")
    print("=" * 50)
    
    flc = AdaptiveFeedbackLoopCore(agent_id="demo-agent")
    
    # Регистрируем через реестр
    policy = registry.create_policy("default")
    correlator = registry.create_correlator("simple")
    
    if policy:
        flc.register_policy(policy)
    if correlator:
        flc.register_correlator(correlator)
    
    from .history import MemoryHistory
    flc.register_history_backend(MemoryHistory(max_size=100))
    
    def my_action(delay_ms=100):
        import time
        time.sleep(delay_ms / 1000.0)
        return {"status": "ok"}
    
    print("\n🔄 Выполнение действий:")
    for i in range(3):
        decision = flc.execute(my_action, 50 + i * 10, endpoint="/api/test", method="GET")
        print(f"  {i+1}: {decision.action} (severity: {decision.severity:.2f})")
    
    print(f"\n📊 Статистика: {flc.get_stats()}")
