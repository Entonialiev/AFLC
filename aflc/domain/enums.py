"""
AFLC Domain Enums
"""

from enum import Enum


class ExecutionStatus(Enum):
    """Lifecycle states of an Execution."""
    CREATED = "created"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RISK_EVALUATED = "risk_evaluated"
    DECISION_MADE = "decision_made"
    EXPLAINED = "explained"
    STORED = "stored"
    ARCHIVED = "archived"


class DecisionAction(Enum):
    """Possible decision actions."""
    ALLOW = "allow"
    BLOCK = "block"
    RETRY = "retry"
    PAUSE = "pause"


class Severity(Enum):
    """Severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FindingSource(Enum):
    """Sources of findings."""
    RULE = "rule"
    STATISTICAL = "statistical"
    ML = "ml"
    CUSTOM = "custom"


class EventType(Enum):
    """Domain event types."""
    EXECUTION_CREATED = "execution_created"
    EXECUTION_STARTED = "execution_started"
    OBSERVATION_RECORDED = "observation_recorded"
    FINDING_CREATED = "finding_created"
    ASSESSMENT_COMPLETED = "assessment_completed"
    RISK_EVALUATED = "risk_evaluated"
    DECISION_MADE = "decision_made"
    EXPLANATION_GENERATED = "explanation_generated"
    EXECUTION_ARCHIVED = "execution_archived"
