"""
AFLC Domain Value Objects
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Any
from datetime import datetime

from .exceptions import InvalidValueError
from .enums import Severity


@dataclass(frozen=True)
class RiskScore:
    """Immutable risk score."""
    value: float
    confidence: float
    components: Dict[str, float]

    def __post_init__(self):
        if not 0.0 <= self.value <= 1.0:
            raise InvalidValueError(f"RiskScore.value must be between 0 and 1, got {self.value}")
        if not 0.0 <= self.confidence <= 1.0:
            raise InvalidValueError(f"RiskScore.confidence must be between 0 and 1, got {self.confidence}")


@dataclass(frozen=True)
class Confidence:
    """Immutable confidence value."""
    value: float
    source: str

    def __post_init__(self):
        if not 0.0 <= self.value <= 1.0:
            raise InvalidValueError(f"Confidence.value must be between 0 and 1, got {self.value}")


@dataclass(frozen=True)
class SeverityValue:
    """Immutable severity."""
    value: float
    category: Severity

    def __post_init__(self):
        if not 0.0 <= self.value <= 1.0:
            raise InvalidValueError(f"Severity.value must be between 0 and 1, got {self.value}")


@dataclass(frozen=True)
class Finding:
    """Immutable finding from a detector."""
    source: str
    score: float
    confidence: float
    reason: str
    tags: Tuple[str, ...]

    def __post_init__(self):
        if not 0.0 <= self.score <= 1.0:
            raise InvalidValueError(f"Finding.score must be between 0 and 1, got {self.score}")
        if not 0.0 <= self.confidence <= 1.0:
            raise InvalidValueError(f"Finding.confidence must be between 0 and 1, got {self.confidence}")


@dataclass(frozen=True)
class Observation:
    """Immutable observation from an action."""
    observation_id: str
    metric: str
    value: float
    timestamp: datetime


@dataclass(frozen=True)
class Explanation:
    """Immutable explanation for a decision."""
    text: str
    details: Dict[str, Any]


@dataclass(frozen=True)
class ExecutionContext:
    """Immutable technical context of an execution."""
    trace_id: str
    span_id: str
    latency_ms: float
    error_code: int
    response_size: int
    cpu_usage: float
    memory_usage: float
    user_agent: Optional[str]
    client_ip: Optional[str]


@dataclass(frozen=True)
class Command:
    """Immutable command."""
    command_id: str
    type: str
    payload: Dict[str, Any]
    timestamp: datetime
    idempotency_key: Optional[str] = None


@dataclass(frozen=True)
class Action:
    """Immutable action."""
    action_id: str
    agent_id: str
    endpoint: str
    method: str
    payload: Dict[str, Any]
    timestamp: datetime
