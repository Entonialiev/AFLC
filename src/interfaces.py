"""
AFLC Interfaces
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any
from .models import ActionContext, Detection, Decision, RiskScore


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
