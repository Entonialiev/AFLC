"""
RuleDetector — детектор на основе жёстких и статистических правил
"""

from typing import Optional, Dict, List
import numpy as np

from ..core import ActionContext, Detection


class RuleDetector:
    """Детектор на основе правил"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.timeout_limit_ms = self.config.get("timeout_limit_ms", 2000)
        self.size_limit_bytes = self.config.get("size_limit_bytes", 1_000_000)
        self.name = "rule_detector"
        
        # История для статистики
        self.history: Dict[str, List[float]] = {
            "response_time": [],
            "response_size": [],
            "error_codes": []
        }
    
    def detect(self, context: ActionContext) -> Optional[Detection]:
        # Добавляем в историю
        self.history["response_time"].append(context.latency_ms)
        self.history["response_size"].append(context.response_size)
        self.history["error_codes"].append(context.error_code)
        
        # Ограничиваем историю
        max_history = self.config.get("max_history", 1000)
        for key in self.history:
            if len(self.history[key]) > max_history:
                self.history[key] = self.history[key][-max_history:]
        
        # Проверяем правила
        if context.latency_ms > self.timeout_limit_ms:
            score = min(1.0, (context.latency_ms - self.timeout_limit_ms) / 3000)
            return Detection(
                source=self.name,
                score=score,
                confidence=0.9,
                reason=f"Timeout: {context.latency_ms:.0f}ms > {self.timeout_limit_ms}ms",
                tags=["timeout", "performance"]
            )
        
        if context.response_size > self.size_limit_bytes:
            return Detection(
                source=self.name,
                score=0.9,
                confidence=0.9,
                reason=f"Response size: {context.response_size} bytes > {self.size_limit_bytes}",
                tags=["size", "security"]
            )
        
        if context.error_code != 0:
            return Detection(
                source=self.name,
                score=1.0,
                confidence=1.0,
                reason=f"Error: HTTP {context.error_code}",
                tags=["error", "security"]
            )
        
        return None
