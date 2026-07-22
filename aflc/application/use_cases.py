"""
AFLC Application Use Cases
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4

from aflc.domain.execution import Execution
from aflc.domain.value_objects import Action, Command, Observation, Finding, RiskScore, Explanation
from aflc.domain.enums import DecisionAction, ExecutionStatus
from aflc.domain.exceptions import DomainError, InvalidStateError

from .interfaces import EventBus, ExecutionRepository


class SubmitActionUseCase:
    """
    Use Case: Submit a new action for execution.
    """

    def __init__(self, repository: ExecutionRepository, event_bus: EventBus):
        self.repository = repository
        self.event_bus = event_bus

    def execute(
        self,
        agent_id: str,
        endpoint: str,
        method: str,
        payload: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> Execution:
        action = Action(
            action_id=str(uuid4()),
            agent_id=agent_id,
            endpoint=endpoint,
            method=method,
            payload=payload,
            timestamp=datetime.utcnow()
        )

        command = Command(
            command_id=str(uuid4()),
            type="execute",
            payload={"action": action.action_id},
            timestamp=datetime.utcnow(),
            idempotency_key=idempotency_key
        )

        execution = Execution(action, command)

        self.repository.save(execution)

        for event in execution.get_events():
            self.event_bus.publish(event)

        return execution


class ProcessExecutionUseCase:
    """
    Use Case: Process an execution through its lifecycle.
    """

    def __init__(self, repository: ExecutionRepository, event_bus: EventBus):
        self.repository = repository
        self.event_bus = event_bus

    def record_observation(
        self,
        execution_id: str,
        metric: str,
        value: float
    ) -> Execution:
        """Record observation in execution."""
        execution = self.repository.find_by_id(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        observation = Observation(
            observation_id=str(uuid4()),
            metric=metric,
            value=value,
            timestamp=datetime.utcnow()
        )

        execution.record_observation(observation)
        self.repository.save(execution)

        for event in execution.get_events():
            self.event_bus.publish(event)

        return execution

    def record_finding(
        self,
        execution_id: str,
        source: str,
        score: float,
        confidence: float,
        reason: str,
        tags: List[str]
    ) -> Execution:
        """Record finding in execution."""
        execution = self.repository.find_by_id(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        finding = Finding(
            source=source,
            score=score,
            confidence=confidence,
            reason=reason,
            tags=tuple(tags)
        )

        execution.record_finding(finding)
        self.repository.save(execution)

        for event in execution.get_events():
            self.event_bus.publish(event)

        return execution

    def evaluate_risk(
        self,
        execution_id: str,
        risk_value: float,
        confidence: float,
        components: Dict[str, float]
    ) -> Execution:
        """Evaluate risk for execution."""
        execution = self.repository.find_by_id(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        risk_score = RiskScore(
            value=risk_value,
            confidence=confidence,
            components=components
        )

        execution.evaluate_risk(risk_score)
        self.repository.save(execution)

        for event in execution.get_events():
            self.event_bus.publish(event)

        return execution

    def make_decision(
        self,
        execution_id: str,
        action: str,
        reason: str,
        severity: float
    ) -> Execution:
        """Make a decision on the execution."""
        execution = self.repository.find_by_id(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        execution.make_decision(DecisionAction(action), reason, severity)
        self.repository.save(execution)

        for event in execution.get_events():
            self.event_bus.publish(event)

        return execution

    def add_explanation(
        self,
        execution_id: str,
        text: str,
        details: Dict[str, Any]
    ) -> Execution:
        """Add explanation to execution."""
        execution = self.repository.find_by_id(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        explanation = Explanation(text=text, details=details)
        execution.add_explanation(explanation)
        self.repository.save(execution)

        for event in execution.get_events():
            self.event_bus.publish(event)

        return execution

    def archive_execution(self, execution_id: str) -> Execution:
        """Archive an execution."""
        execution = self.repository.find_by_id(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        execution.store()
        execution.archive()
        self.repository.save(execution)

        for event in execution.get_events():
            self.event_bus.publish(event)

        return execution
