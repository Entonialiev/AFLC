"""
Default implementations for AFLC
Version: 1.0.0
"""

from typing import List, Optional
from .models import ActionContext, Detection, Decision, RiskScore
from .interfaces import Policy, Correlator


class DefaultPolicy(Policy):
    """Политика по умолчанию"""
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
        return max(detections, key=lambda x: x.score)
