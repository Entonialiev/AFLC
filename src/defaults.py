"""
Default implementations for AFLC
Version: 2.0.0 (unified config)
"""

from typing import List, Optional, Dict
from .models import ActionContext, Detection, Decision, RiskScore
from .interfaces import Policy, Correlator


class DefaultPolicy(Policy):
    """Политика по умолчанию"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.threshold = self.config.get("pause_threshold", 0.3)
    
    def decide(self, context: ActionContext, detection: Optional[Detection],
               risk: RiskScore) -> Decision:
        if detection and detection.score > self.threshold:
            return Decision(
                action="pause",
                reason=detection.reason,
                severity=detection.score,
                confidence=detection.confidence,
                risk_score=risk.value,
                explanation=f"Anomaly detected by {detection.source} (threshold: {self.threshold})"
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
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def correlate(self, detections: List[Detection]) -> Optional[Detection]:
        if not detections:
            return None
        return max(detections, key=lambda x: x.score)
