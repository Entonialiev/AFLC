"""
AFLC Data Models
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import time


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
