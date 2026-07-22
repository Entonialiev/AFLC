"""
Risk Engine — оценка критичности и приоритизация аномалий
Версия: 1.0.0
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
import time

from .core import ActionContext, Detection, RiskScore


@dataclass
class RiskConfig:
    """Конфигурация оценки риска"""
    endpoint_base_risk: Dict[str, float] = None
    method_risk: Dict[str, float] = None
    user_risk: Dict[str, float] = None
    time_multipliers: Dict[str, float] = None
    
    def __post_init__(self):
        if self.endpoint_base_risk is None:
            self.endpoint_base_risk = {
                "/admin": 0.9,
                "/api/admin": 0.85,
                "/api/users": 0.5,
                "/api/public": 0.1,
                "/health": 0.05,
                "default": 0.3
            }
        
        if self.method_risk is None:
            self.method_risk = {
                "GET": 0.3,
                "POST": 0.6,
                "PUT": 0.7,
                "DELETE": 0.9,
                "PATCH": 0.6,
                "default": 0.4
            }
        
        if self.user_risk is None:
            self.user_risk = {
                "admin": 0.9,
                "moderator": 0.6,
                "user": 0.3,
                "guest": 0.1,
                "default": 0.3
            }
        
        if self.time_multipliers is None:
            self.time_multipliers = {
                "night": 1.5,   # 00:00-06:00
                "morning": 1.0,  # 06:00-12:00
                "day": 0.8,     # 12:00-18:00
                "evening": 1.2  # 18:00-00:00
            }


class RiskEngine:
    """
    Оценивает риск на основе контекста и детекции.
    
    Формула:
        risk = detection_score * endpoint_risk * method_risk * user_risk * time_multiplier
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.risk_config = RiskConfig(**self.config.get("risk_config", {}))
        self.name = "risk_engine"
    
    def evaluate(self, context: ActionContext, detection: Optional[Detection]) -> RiskScore:
        """
        Вычисляет риск для данного контекста и детекции.
        """
        # --- 1. Базовый риск от детекции ---
        detection_score = detection.score if detection else 0.0
        detection_confidence = detection.confidence if detection else 0.0
        
        # --- 2. Риск эндпоинта ---
        endpoint_risk = self._get_endpoint_risk(context.endpoint)
        
        # --- 3. Риск метода ---
        method_risk = self.risk_config.method_risk.get(
            context.method.upper(), 
            self.risk_config.method_risk["default"]
        )
        
        # --- 4. Риск пользователя ---
        user_risk = self.risk_config.user_risk.get(
            context.user_id if context.user_id else "guest",
            self.risk_config.user_risk["default"]
        )
        
        # --- 5. Временной множитель ---
        time_multiplier = self._get_time_multiplier()
        
        # --- 6. Исторический множитель ---
        history_multiplier = self._get_history_multiplier(context.history)
        
        # --- 7. Итоговый риск ---
        components = {
            "detection_score": detection_score,
            "detection_confidence": detection_confidence,
            "endpoint_risk": endpoint_risk,
            "method_risk": method_risk,
            "user_risk": user_risk,
            "time_multiplier": time_multiplier,
            "history_multiplier": history_multiplier
        }
        
        # Вычисляем итоговый риск
        # Произведение всех компонентов, но с ограничением 0-1
        risk_value = (
            detection_score * 
            endpoint_risk * 
            method_risk * 
            user_risk * 
            time_multiplier * 
            history_multiplier
        )
        risk_value = max(0.0, min(1.0, risk_value))
        
        # Confidence = среднее от confidence детекции и уверенности в контексте
        context_confidence = min(1.0, len(context.history) / 100) if context.history else 0.3
        confidence = (detection_confidence + context_confidence) / 2
        confidence = max(0.0, min(1.0, confidence))
        
        return RiskScore(
            value=risk_value,
            confidence=confidence,
            components=components
        )
    
    def _get_endpoint_risk(self, endpoint: str) -> float:
        """Определяет риск эндпоинта"""
        for pattern, risk in self.risk_config.endpoint_base_risk.items():
            if pattern in endpoint:
                return risk
        return self.risk_config.endpoint_base_risk["default"]
    
    def _get_time_multiplier(self) -> float:
        """Определяет множитель времени"""
        hour = time.localtime().tm_hour
        if 0 <= hour < 6:
            return self.risk_config.time_multipliers["night"]
        elif 6 <= hour < 12:
            return self.risk_config.time_multipliers["morning"]
        elif 12 <= hour < 18:
            return self.risk_config.time_multipliers["day"]
        else:
            return self.risk_config.time_multipliers["evening"]
    
    def _get_history_multiplier(self, history: List[Dict]) -> float:
        """Определяет множитель на основе истории"""
        if not history:
            return 1.0
        
        # Считаем количество аномалий в последних 10 действиях
        recent = history[-10:] if len(history) >= 10 else history
        anomaly_count = sum(1 for h in recent if h.get("decision") == "pause")
        
        if anomaly_count == 0:
            return 1.0
        elif anomaly_count <= 2:
            return 1.2
        elif anomaly_count <= 5:
            return 1.5
        else:
            return 2.0
    
    def get_component_breakdown(self, risk_score: RiskScore) -> str:
        """
        Возвращает человекочитаемую разбивку компонентов риска
        """
        lines = [
            "📊 Risk Breakdown:",
            f"  Detection score: {risk_score.components.get('detection_score', 0):.2f}",
            f"  Endpoint risk: {risk_score.components.get('endpoint_risk', 0):.2f}",
            f"  Method risk: {risk_score.components.get('method_risk', 0):.2f}",
            f"  User risk: {risk_score.components.get('user_risk', 0):.2f}",
            f"  Time multiplier: {risk_score.components.get('time_multiplier', 1.0):.1f}x",
            f"  History multiplier: {risk_score.components.get('history_multiplier', 1.0):.1f}x",
            f"  Confidence: {risk_score.confidence:.2f}",
            f"  → Final risk: {risk_score.value:.2f}"
        ]
        return "\n".join(lines)


# --- ПРИМЕР ИСПОЛЬЗОВАНИЯ ---
if __name__ == "__main__":
    print("📊 Risk Engine Test")
    print("=" * 40)
    
    from .core import ActionContext, Detection
    
    # Создаём Risk Engine
    risk_engine = RiskEngine()
    
    # Тестовый контекст
    context = ActionContext(
        action_id="test-001",
        endpoint="/api/admin/delete",
        method="DELETE",
        user_id="admin",
        history=[]
    )
    
    # Тестовая детекция
    detection = Detection(
        source="rule_detector",
        score=0.7,
        confidence=0.9,
        reason="Timeout anomaly"
    )
    
    # Оцениваем риск
    risk = risk_engine.evaluate(context, detection)
    
    print(f"Риск: {risk.value:.2f} (confidence: {risk.confidence:.2f})")
    print("\n" + risk_engine.get_component_breakdown(risk))
