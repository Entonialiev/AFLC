"""
AFLC Domain Events
"""

from dataclasses import dataclass
from typing import List, Optional, Any
from datetime import datetime
from uuid import uuid4

from .value_objects import Finding, Observation, Explanation, Action
from .enums import DecisionAction, EventType


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """Base domain event."""
    event_id: str
    event_type: EventType
    execution_id: str
    timestamp: datetime

    @staticmethod
    def new_id() -> str:
        return str(uuid4())


@dataclass(frozen=True, slots=True)
class ExecutionCreated(DomainEvent):
    """Execution has been created."""
    command_id: str
    action: Action

    def __init__(
        self,
        execution_id: str,
        command_id: str,
        action: Action,
        event_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        super().__init__(
            event_id=event_id or DomainEvent.new_id(),
            event_type=EventType.EXECUTION_CREATED,
            execution_id=execution_id,
            timestamp=timestamp or datetime.utcnow()
        )
        object.__setattr__(self, "command_id", command_id)
        object.__setattr__(self, "action", action)


@dataclass(frozen=True, slots=True)
class ObservationAdded(DomainEvent):
    """Observation has been added to execution."""
    observation: Observation

    def __init__(
        self,
        execution_id: str,
        observation: Observation,
        event_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        super().__init__(
            event_id=event_id or DomainEvent.new_id(),
            event_type=EventType.OBSERVATION_ADDED,
            execution_id=execution_id,
            timestamp=timestamp or datetime.utcnow()
        )
        object.__setattr__(self, "observation", observation)


@dataclass(frozen=True, slots=True)
class FindingProduced(DomainEvent):
    """Finding has been produced."""
    finding: Finding

    def __init__(
        self,
        execution_id: str,
        finding: Finding,
        event_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        super().__init__(
            event_id=event_id or DomainEvent.new_id(),
            event_type=EventType.FINDING_PRODUCED,
            execution_id=execution_id,
            timestamp=timestamp or datetime.utcnow()
        )
        object.__setattr__(self, "finding", finding)


@dataclass(frozen=True, slots=True)
class AssessmentCompleted(DomainEvent):
    """Assessment has been completed."""
    findings: List[Finding]
    risk_score: Any  # RiskScore

    def __init__(
        self,
        execution_id: str,
        findings: List[Finding],
        risk_score: Any,
        event_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        super().__init__(
            event_id=event_id or DomainEvent.new_id(),
            event_type=EventType.ASSESSMENT_COMPLETED,
            execution_id=execution_id,
            timestamp=timestamp or datetime.utcnow()
        )
        object.__setattr__(self, "findings", findings)
        object.__setattr__(self, "risk_score", risk_score)


@dataclass(frozen=True, slots=True)
class DecisionMade(DomainEvent):
    """Decision has been made."""
    action: DecisionAction
    reason: str
    severity: float

    def __init__(
        self,
        execution_id: str,
        action: DecisionAction,
        reason: str,
        severity: float,
        event_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        super().__init__(
            event_id=event_id or DomainEvent.new_id(),
            event_type=EventType.DECISION_MADE,
            execution_id=execution_id,
            timestamp=timestamp or datetime.utcnow()
        )
        object.__setattr__(self, "action", action)
        object.__setattr__(self, "reason", reason)
        object.__setattr__(self, "severity", severity)


@dataclass(frozen=True, slots=True)
class ExplanationGenerated(DomainEvent):
    """Explanation has been generated."""
    explanation: Explanation

    def __init__(
        self,
        execution_id: str,
        explanation: Explanation,
        event_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        super().__init__(
            event_id=event_id or DomainEvent.new_id(),
            event_type=EventType.EXPLANATION_GENERATED,
            execution_id=execution_id,
            timestamp=timestamp or datetime.utcnow()
        )
        object.__setattr__(self, "explanation", explanation)


@dataclass(frozen=True, slots=True)
class ExecutionArchived(DomainEvent):
    """Execution has been archived."""

    def __init__(
        self,
        execution_id: str,
        event_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        super().__init__(
            event_id=event_id or DomainEvent.new_id(),
            event_type=EventType.EXECUTION_ARCHIVED,
            execution_id=execution_id,
            timestamp=timestamp or datetime.utcnow()
        )
