"""
AFLC Domain Events
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any
from datetime import datetime
from uuid import uuid4

from .value_objects import Finding, Observation, Explanation, Action, RiskScore
from .enums import DecisionAction, EventType


@dataclass(frozen=True)
class DomainEvent:
    """Base domain event."""
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: EventType = field(default=EventType.EXECUTION_CREATED)
    execution_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class ExecutionCreated(DomainEvent):
    """Execution has been created."""
    command_id: str = ""
    action: Action = field(default_factory=lambda: None)

    def __post_init__(self):
        if not self.command_id:
            raise ValueError("command_id is required")
        if self.action is None:
            raise ValueError("action is required")
        object.__setattr__(self, "event_type", EventType.EXECUTION_CREATED)


@dataclass(frozen=True)
class ExecutionStarted(DomainEvent):
    """Execution has been started (transitioned to RUNNING)."""

    def __post_init__(self):
        object.__setattr__(self, "event_type", EventType.EXECUTION_STARTED)


@dataclass(frozen=True)
class ObservationRecorded(DomainEvent):
    """Observation has been recorded."""
    observation: Observation = field(default_factory=lambda: None)

    def __post_init__(self):
        if self.observation is None:
            raise ValueError("observation is required")
        object.__setattr__(self, "event_type", EventType.OBSERVATION_RECORDED)


@dataclass(frozen=True)
class FindingCreated(DomainEvent):
    """Finding has been created."""
    finding: Finding = field(default_factory=lambda: None)

    def __post_init__(self):
        if self.finding is None:
            raise ValueError("finding is required")
        object.__setattr__(self, "event_type", EventType.FINDING_CREATED)


@dataclass(frozen=True)
class AssessmentCompleted(DomainEvent):
    """Assessment has been completed (DEPRECATED - use RiskEvaluated)."""
    findings: List[Finding] = field(default_factory=list)
    risk_score: Any = field(default_factory=lambda: None)

    def __post_init__(self):
        if self.risk_score is None:
            raise ValueError("risk_score is required")
        object.__setattr__(self, "event_type", EventType.ASSESSMENT_COMPLETED)


@dataclass(frozen=True)
class RiskEvaluated(DomainEvent):
    """Risk has been evaluated."""
    risk_score: RiskScore = field(default_factory=lambda: None)
    components: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.risk_score is None:
            raise ValueError("risk_score is required")
        object.__setattr__(self, "event_type", EventType.RISK_EVALUATED)


@dataclass(frozen=True)
class DecisionMade(DomainEvent):
    """Decision has been made."""
    action: DecisionAction = field(default=DecisionAction.ALLOW)
    reason: str = ""
    severity: float = 0.0

    def __post_init__(self):
        if not self.reason:
            raise ValueError("reason is required")
        if not 0.0 <= self.severity <= 1.0:
            raise ValueError("severity must be between 0 and 1")
        object.__setattr__(self, "event_type", EventType.DECISION_MADE)


@dataclass(frozen=True)
class ExplanationGenerated(DomainEvent):
    """Explanation has been generated."""
    explanation: Explanation = field(default_factory=lambda: None)

    def __post_init__(self):
        if self.explanation is None:
            raise ValueError("explanation is required")
        object.__setattr__(self, "event_type", EventType.EXPLANATION_GENERATED)


@dataclass(frozen=True)
class ExecutionArchived(DomainEvent):
    """Execution has been archived."""

    def __post_init__(self):
        object.__setattr__(self, "event_type", EventType.EXECUTION_ARCHIVED)
