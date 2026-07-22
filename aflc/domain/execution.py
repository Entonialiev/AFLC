"""
AFLC Domain Aggregate Root: Execution
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from datetime import datetime
from uuid import uuid4

from .enums import ExecutionStatus, DecisionAction, Severity
from .value_objects import (
    Action, Command, Observation, Finding, RiskScore,
    Explanation, ExecutionContext, Confidence, SeverityValue
)
from .events import (
    DomainEvent, ExecutionCreated, ExecutionStarted, ObservationRecorded,
    FindingCreated, AssessmentCompleted, RiskEvaluated, DecisionMade,
    ExplanationGenerated, ExecutionArchived
)
from .exceptions import InvalidStateError, InvalidTransitionError, InvalidActionError


class ExecutionStateMachine:
    """State machine for Execution lifecycle."""

    _transitions = {
        ExecutionStatus.CREATED: {ExecutionStatus.PENDING},
        ExecutionStatus.PENDING: {ExecutionStatus.RUNNING},
        ExecutionStatus.RUNNING: {ExecutionStatus.COMPLETED, ExecutionStatus.FAILED},
        ExecutionStatus.COMPLETED: {ExecutionStatus.RISK_EVALUATED},
        ExecutionStatus.FAILED: set(),
        ExecutionStatus.RISK_EVALUATED: {ExecutionStatus.DECISION_MADE},
        ExecutionStatus.DECISION_MADE: {ExecutionStatus.EXPLAINED},
        ExecutionStatus.EXPLAINED: {ExecutionStatus.STORED},
        ExecutionStatus.STORED: {ExecutionStatus.ARCHIVED},
        ExecutionStatus.ARCHIVED: set(),
    }

    @classmethod
    def validate_transition(cls, current: ExecutionStatus, target: ExecutionStatus) -> bool:
        """Check if transition is valid."""
        if current == target:
            return True
        return target in cls._transitions.get(current, set())

    @classmethod
    def transition(cls, current: ExecutionStatus, target: ExecutionStatus) -> ExecutionStatus:
        """Perform transition if valid."""
        if not cls.validate_transition(current, target):
            raise InvalidTransitionError(
                f"Cannot transition from {current.value} to {target.value}"
            )
        return target


@dataclass
class Execution:
    """
    Aggregate Root for Action Execution.
    All state changes go through this aggregate.
    """

    execution_id: str
    action: Action
    command: Command
    status: ExecutionStatus
    observations: List[Observation]
    findings: List[Finding]
    risk_score: Optional[RiskScore]
    decision: Optional[Dict[str, Any]]
    explanation: Optional[Explanation]
    context: Optional[ExecutionContext]
    events: List[DomainEvent]
    created_at: datetime
    updated_at: datetime

    def __init__(self, action: Action, command: Command):
        self.execution_id = str(uuid4())
        self.action = action
        self.command = command
        self.status = ExecutionStatus.CREATED
        self.observations = []
        self.findings = []
        self.risk_score = None
        self.decision = None
        self.explanation = None
        self.context = None
        self.events = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        self.events.append(
            ExecutionCreated(
                execution_id=self.execution_id,
                command_id=command.command_id,
                action=action
            )
        )

    # --- Lifecycle Methods ---

    def submit(self) -> None:
        """Submit execution for processing (CREATED -> PENDING)."""
        self._transition_to(ExecutionStatus.PENDING)

    def start(self) -> None:
        """Start execution (PENDING -> RUNNING)."""
        self._transition_to(ExecutionStatus.RUNNING)
        self._add_event(ExecutionStarted(execution_id=self.execution_id))

    def complete_processing(self) -> None:
        """Complete processing execution (RUNNING -> COMPLETED)."""
        self._transition_to(ExecutionStatus.COMPLETED)

    def fail_processing(self, reason: str) -> None:
        """Fail processing execution (RUNNING -> FAILED)."""
        self._transition_to(ExecutionStatus.FAILED)

    def record_observation(self, observation: Observation) -> None:
        """Add observation to execution."""
        if self.status != ExecutionStatus.RUNNING:
            raise InvalidStateError(f"Cannot add observation in state {self.status.value}")
        self.observations.append(observation)
        self.updated_at = datetime.utcnow()
        self._add_event(ObservationRecorded(
            execution_id=self.execution_id,
            observation=observation
        ))

    def record_finding(self, finding: Finding) -> None:
        """Add finding from a detector."""
        if self.status != ExecutionStatus.RUNNING:
            raise InvalidStateError(f"Cannot add finding in state {self.status.value}")
        self.findings.append(finding)
        self.updated_at = datetime.utcnow()
        self._add_event(FindingCreated(
            execution_id=self.execution_id,
            finding=finding
        ))

    def evaluate_risk(self, risk_score: RiskScore) -> None:
        """Evaluate risk for the execution."""
        if self.status != ExecutionStatus.COMPLETED:
            raise InvalidStateError(f"Cannot evaluate risk in state {self.status.value}")
        self.risk_score = risk_score
        self._transition_to(ExecutionStatus.RISK_EVALUATED)
        self._add_event(RiskEvaluated(
            execution_id=self.execution_id,
            risk_score=risk_score,
            components=risk_score.components
        ))

    def make_decision(self, action: DecisionAction, reason: str, severity: float) -> None:
        """Make a decision."""
        if self.status != ExecutionStatus.RISK_EVALUATED:
            raise InvalidStateError(f"Cannot make decision in state {self.status.value}")
        self.decision = {"action": action, "reason": reason, "severity": severity}
        self._transition_to(ExecutionStatus.DECISION_MADE)
        self._add_event(DecisionMade(
            execution_id=self.execution_id,
            action=action,
            reason=reason,
            severity=severity
        ))

    def add_explanation(self, explanation: Explanation) -> None:
        """Add explanation to execution."""
        if self.status != ExecutionStatus.DECISION_MADE:
            raise InvalidStateError(f"Cannot add explanation in state {self.status.value}")
        self.explanation = explanation
        self._transition_to(ExecutionStatus.EXPLAINED)
        self._add_event(ExplanationGenerated(
            execution_id=self.execution_id,
            explanation=explanation
        ))

    def store(self) -> None:
        """Store execution (EXPLAINED -> STORED)."""
        self._transition_to(ExecutionStatus.STORED)

    def archive(self) -> None:
        """Archive execution (STORED -> ARCHIVED)."""
        self._transition_to(ExecutionStatus.ARCHIVED)
        self._add_event(ExecutionArchived(execution_id=self.execution_id))

    # --- Private Methods ---

    def _transition_to(self, target: ExecutionStatus) -> None:
        """Transition to target state."""
        new_status = ExecutionStateMachine.transition(self.status, target)
        self.status = new_status
        self.updated_at = datetime.utcnow()

    def _add_event(self, event: DomainEvent) -> None:
        """Add domain event."""
        self.events.append(event)
        self.updated_at = datetime.utcnow()

    # --- Query Methods ---

    def is_terminal(self) -> bool:
        """Check if execution is in a terminal state."""
        return self.status in [ExecutionStatus.FAILED, ExecutionStatus.ARCHIVED]

    def get_events(self) -> List[DomainEvent]:
        """Get and clear domain events."""
        events = self.events.copy()
        self.events.clear()
        return events
