"""
Explainer — человекочитаемое объяснение решений
Версия: 1.0.0
"""

from typing import Dict, Optional, List
from datetime import datetime

from .core import ActionContext, Detection, Decision, RiskScore


class Explainer:
    """
    Генерирует человекочитаемые объяснения решений.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.name = "explainer"
    
    def explain(self, context: ActionContext, detection: Optional[Detection],
                decision: Decision, risk: Optional[RiskScore]) -> str:
        """
        Генерирует полное объяснение решения.
        """
        lines = []
        
        # --- Заголовок ---
        if decision.action == "pause":
            lines.append("⛔ **Действие ОСТАНОВЛЕНО**")
        elif decision.action == "continue":
            lines.append("✅ **Действие ПРОДОЛЖЕНО**")
        elif decision.action == "block":
            lines.append("🚫 **Действие ЗАБЛОКИРОВАНО**")
        else:
            lines.append(f"ℹ️ **Решение: {decision.action.upper()}**")
        
        lines.append("")
        
        # --- Основная причина ---
        lines.append(f"📌 **Причина:** {decision.reason}")
        
        if detection:
            lines.append(f"  Детектор: {detection.source}")
            lines.append(f"  Score: {detection.score:.2f}")
            lines.append(f"  Confidence: {detection.confidence:.2f}")
        lines.append("")
        
        # --- Контекст выполнения ---
        lines.append("📊 **Контекст выполнения:**")
        lines.append(f"  Эндпоинт: {context.endpoint}")
        lines.append(f"  Метод: {context.method}")
        lines.append(f"  Задержка: {context.latency_ms:.0f} мс")
        if context.response_size:
            lines.append(f"  Размер ответа: {context.response_size} байт")
        if context.error_code:
            lines.append(f"  Код ошибки: HTTP {context.error_code}")
        if context.user_id:
            lines.append(f"  Пользователь: {context.user_id}")
        lines.append("")
        
        # --- Риск ---
        if risk:
            lines.append("⚠️ **Оценка риска:**")
            lines.append(f"  Итоговый риск: {risk.value:.2f}")
            lines.append(f"  Уверенность: {risk.confidence:.2f}")
            
            if risk.components:
                lines.append("  Компоненты:")
                for key, value in risk.components.items():
                    if key != "detection_score" and value > 0:
                        lines.append(f"    • {key}: {value:.2f}")
            lines.append("")
        
        # --- Время и история ---
        lines.append("⏱️ **Временной контекст:**")
        now = datetime.now()
        lines.append(f"  Время: {now.strftime('%H:%M:%S')}")
        lines.append(f"  Дата: {now.strftime('%d.%m.%Y')}")
        
        if context.history:
            recent = context.history[-5:] if len(context.history) >= 5 else context.history
            anomalies = sum(1 for h in recent if h.get("decision") == "pause")
            if anomalies > 0:
                lines.append(f"  📈 Аномалий в последних 5 действиях: {anomalies}")
        lines.append("")
        
        # --- Рекомендации ---
        recommendations = self._generate_recommendations(context, detection, decision)
        if recommendations:
            lines.append("💡 **Рекомендация:**")
            lines.append(f"  {recommendations}")
        
        return "\n".join(lines)
    
    def short_explain(self, decision: Decision) -> str:
        """
        Краткое объяснение (одна строка).
        """
        if decision.action == "continue":
            return f"✅ Продолжено: {decision.reason}"
        elif decision.action == "pause":
            return f"⛔ Остановлено: {decision.reason}"
        elif decision.action == "block":
            return f"🚫 Заблокировано: {decision.reason}"
        else:
            return f"ℹ️ {decision.action}: {decision.reason}"
    
    def _generate_recommendations(self, context: ActionContext, 
                                  detection: Optional[Detection],
                                  decision: Decision) -> Optional[str]:
        """
        Генерирует рекомендации на основе контекста.
        """
        if decision.action == "continue":
            return None
        
        recommendations = []
        
        if detection and detection.tags:
            if "timeout" in detection.tags or "performance" in detection.tags:
                recommendations.append("Проверьте нагрузку на API и время ответа")
            
            if "security" in detection.tags or "error" in detection.tags:
                recommendations.append("Проверьте логи на предмет несанкционированного доступа")
            
            if "size" in detection.tags:
                recommendations.append("Проверьте размер ответа — возможна утечка данных")
        
        if context.endpoint.startswith("/admin") or context.endpoint.startswith("/api/admin"):
            recommendations.append("Критический эндпоинт — требуется немедленная проверка")
        
        if context.error_code >= 500:
            recommendations.append("Ошибка сервера — проверьте логи приложения")
        
        if recommendations:
            return " | ".join(recommendations)
        
        return "Проверьте конфигурацию и повторите запрос"
    
    def explain_detection(self, detection: Detection) -> str:
        """
        Объясняет только результат детекции.
        """
        lines = [
            f"🔍 **Детекция от {detection.source}**",
            f"  Score: {detection.score:.2f}",
            f"  Confidence: {detection.confidence:.2f}",
            f"  Причина: {detection.reason}",
            f"  Теги: {', '.join(detection.tags) if detection.tags else 'нет'}"
        ]
        return "\n".join(lines)
    
    def explain_risk(self, risk: RiskScore) -> str:
        """
        Объясняет оценку риска.
        """
        lines = [
            "⚠️ **Оценка риска:**",
            f"  Значение: {risk.value:.2f}",
            f"  Уверенность: {risk.confidence:.2f}"
        ]
        if risk.components:
            lines.append("  Компоненты:")
            for key, value in risk.components.items():
                if value > 0:
                    lines.append(f"    • {key}: {value:.2f}")
        return "\n".join(lines)


# --- ПРИМЕР ИСПОЛЬЗОВАНИЯ ---
if __name__ == "__main__":
    print("📖 Explainer Test")
    print("=" * 40)
    
    from .core import ActionContext, Detection, Decision
    
    explainer = Explainer()
    
    context = ActionContext(
        action_id="test-001",
        endpoint="/api/admin/delete",
        method="DELETE",
        latency_ms=3245,
        error_code=0,
        response_size=1024,
        user_id="admin"
    )
    
    detection = Detection(
        source="statistical_detector",
        score=0.79,
        confidence=0.92,
        reason="Latency anomaly: 3245ms (baseline: 105±12ms, z=4.5σ)",
        tags=["statistical", "timeout", "performance"]
    )
    
    decision = Decision(
        action="pause",
        reason=detection.reason,
        severity=0.79,
        confidence=0.92,
        risk_score=0.85,
        explanation="Anomaly detected by statistical_detector"
    )
    
    risk = RiskScore(
        value=0.85,
        confidence=0.92,
        components={
            "detection_score": 0.79,
            "endpoint_risk": 0.9,
            "method_risk": 0.9,
            "user_risk": 0.9,
            "time_multiplier": 1.5,
            "history_multiplier": 1.2
        }
    )
    
    print(explainer.explain(context, detection, decision, risk))
