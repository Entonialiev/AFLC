"""
AFLC - Adaptive Feedback Loop Core
Industrial-grade framework for AI agent self-correction
Version: 0.1.0 (Architectural foundation)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import time
import json


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
    source: str  # "rule", "statistical", "isolation_forest", "llm"
    score: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0
    reason: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Decision:
    """Решение, принятое Policy Engine"""
    action: str  # "continue", "pause", "block", "retry", "rollback"
    reason: str
    severity: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0
    risk_score: float  # 0.0 - 1.0
    explanation: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskScore:
    """Оценка риска"""
    value: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0
    components: Dict[str, float] = field(default_factory=dict)  # {"endpoint": 0.8, "user": 0.3}


# --- ИНТЕРФЕЙСЫ (ПРОТОКОЛЫ) ---

class Detector:
    """Базовый интерфейс для всех детекторов"""
    
    def detect(self, context: ActionContext) -> Optional[Detection]:
        """Анализирует контекст и возвращает Detection или None"""
        raise NotImplementedError


class Correlator:
    """Объединяет результаты нескольких детекторов"""
    
    def correlate(self, detections: List[Detection]) -> Optional[Detection]:
        """Строит единый Detection из списка"""
        raise NotImplementedError


class Predictor:
    """Прогнозирует будущие аномалии"""
    
    def predict(self, context: ActionContext, horizon: int = 10) -> Dict[str, float]:
        """Возвращает вероятности аномалий на следующем шаге"""
        raise NotImplementedError


class Policy:
    """Движок принятия решений"""
    
    def decide(self, context: ActionContext, detection: Optional[Detection], 
               risk: RiskScore) -> Decision:
        """Принимает решение на основе контекста, детекции и риска"""
        raise NotImplementedError


# --- ГЛАВНЫЙ ОРКЕСТРАТОР ---

class AdaptiveFeedbackLoopCore:
    """
    Главный класс AFLC. Оркестрирует все компоненты.
    
    Usage:
        flc = AdaptiveFeedbackLoopCore(agent_id="my-agent")
        flc.register_detector(RuleDetector())
        flc.register_policy(DefaultPolicy())
        
        decision = flc.execute(my_action, endpoint="/api/users", method="GET")
        if decision.action == "pause":
            print("Anomaly detected! Stopping chain.")
    """
    
    def __init__(self, agent_id: str, config: Optional[Dict] = None):
        self.agent_id = agent_id
        self.config = config or {}
        
        # Компоненты (будут заполняться через регистрацию)
        self.detectors: List[Detector] = []
        self.correlator: Optional[Correlator] = None
        self.predictor: Optional[Predictor] = None
        self.policy: Optional[Policy] = None
        
        # Состояние
        self.action_counter = 0
        self.history: List[Dict] = []
        self.last_decision: Optional[Decision] = None
    
    def register_detector(self, detector: Detector) -> 'AdaptiveFeedbackLoopCore':
        """Добавляет детектор в конвейер"""
        self.detectors.append(detector)
        return self
    
    def register_correlator(self, correlator: Correlator) -> 'AdaptiveFeedbackLoopCore':
        """Устанавливает коррелятор"""
        self.correlator = correlator
        return self
    
    def register_predictor(self, predictor: Predictor) -> 'AdaptiveFeedbackLoopCore':
        """Устанавливает предиктор"""
        self.predictor = predictor
        return self
    
    def register_policy(self, policy: Policy) -> 'AdaptiveFeedbackLoopCore':
        """Устанавливает движок политик"""
        self.policy = policy
        return self
    
    def execute(self, action_func: Callable, *args, **kwargs) -> Decision:
        """
        Выполняет действие с полным контролем AFLC
        
        Args:
            action_func: функция, которая выполняет действие
            endpoint: str (обязательно) — эндпоинт
            method: str (обязательно) — метод
            payload: Optional[Dict] — полезная нагрузка
            user_id: Optional[str] — идентификатор пользователя
            
        Returns:
            Decision — решение, принятое системой
        """
        self.action_counter += 1
        action_id = f"{self.agent_id}-{self.action_counter:04d}"
        
        # --- 1. Выполняем действие и собираем контекст ---
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
        
        # Создаём контекст
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
        
        # --- 2. Прогоняем через все детекторы ---
        detections = []
        for detector in self.detectors:
            detection = detector.detect(context)
            if detection:
                detections.append(detection)
        
        # --- 3. Коррелируем результаты ---
        final_detection = None
        if self.correlator and detections:
            final_detection = self.correlator.correlate(detections)
        elif detections:
            final_detection = detections[0]  # Если коррелятора нет, берём первый
        
        # --- 4. Прогнозируем ---
        if self.predictor:
            predictions = self.predictor.predict(context)
        else:
            predictions = {}
        
        # --- 5. Оцениваем риск ---
        risk = RiskScore(value=0.0, confidence=0.0)
        if final_detection:
            risk = RiskScore(
                value=final_detection.score,
                confidence=final_detection.confidence,
                components={"detection_score": final_detection.score}
            )
            if context.endpoint.startswith("/admin") or context.endpoint.startswith("/api/admin"):
                risk.value = min(1.0, risk.value * 1.5)
                risk.components["endpoint_criticality"] = 0.8
        
        # --- 6. Принимаем решение ---
        if self.policy:
            decision = self.policy.decide(context, final_detection, risk)
        else:
            # Дефолтная политика
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
        
        # --- 7. Сохраняем в историю ---
        self.history.append({
            "action_id": action_id,
            "endpoint": context.endpoint,
            "method": context.method,
            "latency_ms": latency_ms,
            "decision": decision.action,
            "severity": decision.severity,
            "risk_score": decision.risk_score
        })
        self.last_decision = decision
        
        return decision


# --- ВСПОМОГАТЕЛЬНЫЕ КЛАССЫ ---

class DefaultPolicy(Policy):
    """Простая политика по умолчанию"""
    
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
    """Простой коррелятор: берёт максимальный score"""
    
    def correlate(self, detections: List[Detection]) -> Optional[Detection]:
        if not detections:
            return None
        # Берём детекцию с максимальным score
        best = max(detections, key=lambda x: x.score)
        return best


# --- ПРИМЕР ИСПОЛЬЗОВАНИЯ ---

if __name__ == "__main__":
    print("🔁 AFLC v0.1.0 — Architectural Foundation")
    print("=" * 50)
    
    # Создаём экземпляр
    flc = AdaptiveFeedbackLoopCore(agent_id="demo-agent")
    
    # Регистрируем компоненты
    flc.register_policy(DefaultPolicy())
    
    # Определяем действие
    def my_action():
        import time
        time.sleep(0.1)
        return {"status": "ok"}
    
    # Выполняем
    decision = flc.execute(
        my_action,
        endpoint="/api/v1/users",
        method="GET"
    )
    
    print(f"Decision: {decision.action}")
    print(f"Reason: {decision.reason}")
    print(f"Severity: {decision.severity:.2f}")
    print(f"Risk score: {decision.risk_score:.2f}")
