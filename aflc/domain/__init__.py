"""
AFLC Domain — независимое доменное ядро.
Не зависит от внешних библиотек.
"""

from .exceptions import (
    DomainError,
    InvalidActionError,
    InvalidTransitionError,
    InvalidStateError,
    InvalidValueError,
    AggregateNotFoundError,
    RuleViolationError,
    ImmutableError,
)

from .enums import (
    ExecutionStatus,
    DecisionAction,
    Severity,
    FindingSource,
    EventType,
)

from .value_objects import (
    RiskScore,
    Confidence,
    SeverityValue,
    Finding,
    Observation,
    Explanation,
    ExecutionContext,
    Command,
    Action,
)

from .events import (
    DomainEvent,
    ExecutionCreated,
    ExecutionStarted,
    ObservationRecorded,
    FindingCreated,
    AssessmentCompleted,
    RiskEvaluated,
    DecisionMade,
    ExplanationGenerated,
    ExecutionArchived,
)

from .execution import Execution, ExecutionStateMachine

__all__ = [
    # Exceptions
    "DomainError",
    "InvalidActionError",
    "InvalidTransitionError",
    "InvalidStateError",
    "InvalidValueError",
    "AggregateNotFoundError",
    "RuleViolationError",
    "ImmutableError",
    # Enums
    "ExecutionStatus",
    "DecisionAction",
    "Severity",
    "FindingSource",
    "EventType",
    # Value Objects
    "RiskScore",
    "Confidence",
    "SeverityValue",
    "Finding",
    "Observation",
    "Explanation",
    "ExecutionContext",
    "Command",
    "Action",
    # Events
    "DomainEvent",
    "ExecutionCreated",
    "ExecutionStarted",
    "ObservationRecorded",
    "FindingCreated",
    "AssessmentCompleted",
    "RiskEvaluated",
    "DecisionMade",
    "ExplanationGenerated",
    "ExecutionArchived",
    # Aggregate
    "Execution",
    "ExecutionStateMachine",
]
