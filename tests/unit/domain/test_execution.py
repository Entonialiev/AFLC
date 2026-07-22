"""
Unit tests for Execution Aggregate Root
"""

import pytest
from datetime import datetime

from aflc.domain.execution import Execution
from aflc.domain.value_objects import (
    Action, Command, Observation, Finding, RiskScore, Explanation
)
from aflc.domain.enums import ExecutionStatus, DecisionAction, Severity
from aflc.domain.events import (
    ExecutionCreated, ObservationAdded, FindingProduced,
    AssessmentCompleted, DecisionMade, ExplanationGenerated,
    ExecutionArchived
)
from aflc.domain.exceptions import InvalidStateError, InvalidTransitionError


class TestExecution:
    def setup_method(self):
        now = datetime.utcnow()
        self.action = Action(
            action_id="action-1",
            agent_id="agent-1",
            endpoint="/api/test",
            method="GET",
            payload={},
            timestamp=now
        )
        self.command = Command(
            command_id="cmd-1",
            type="execute",
            payload={},
            timestamp=now
        )

    def test_create_execution(self):
        execution = Execution(self.action, self.command)

        assert execution.execution_id is not None
        assert execution.status == ExecutionStatus.CREATED
        assert len(execution.events) == 1
        assert isinstance(execution.events[0], ExecutionCreated)

    def test_submit_execution(self):
        execution = Execution(self.action, self.command)
        execution.submit()

        assert execution.status == ExecutionStatus.PENDING

    def test_start_processing(self):
        execution = Execution(self.action, self.command)
        execution.submit()
        execution.start_processing()

        assert execution.status == ExecutionStatus.RUNNING

    def test_complete_processing(self):
        execution = Execution(self.action, self.command)
        execution.submit()
        execution.start_processing()
        execution.complete_processing()

        assert execution.status == ExecutionStatus.COMPLETED

    def test_fail_processing(self):
        execution = Execution(self.action, self.command)
        execution.submit()
        execution.start_processing()
        execution.fail_processing("test error")

        assert execution.status == ExecutionStatus.FAILED

    def test_complete_assessment(self):
        execution = Execution(self.action, self.command)
        execution.submit()
        execution.start_processing()
        execution.complete_processing()

        risk = RiskScore(value=0.7, confidence=0.9, components={"rule": 0.6})
        execution.complete_assessment(risk)

        assert execution.status == ExecutionStatus.RISK_EVALUATED
        assert execution.risk_score == risk
        assert isinstance(execution.events[-1], AssessmentCompleted)

    def test_make_decision(self):
        execution = Execution(self.action, self.command)
        execution.submit()
        execution.start_processing()
        execution.complete_processing()

        risk = RiskScore(value=0.7, confidence=0.9, components={"rule": 0.6})
        execution.complete_assessment(risk)

        execution.make_decision(DecisionAction.BLOCK, "High risk", 0.7)

        assert execution.status == ExecutionStatus.DECISION_MADE
        assert execution.decision["action"] == DecisionAction.BLOCK
        assert isinstance(execution.events[-1], DecisionMade)

    def test_add_explanation(self):
        execution = Execution(self.action, self.command)
        execution.submit()
        execution.start_processing()
        execution.complete_processing()

        risk = RiskScore(value=0.7, confidence=0.9, components={"rule": 0.6})
        execution.complete_assessment(risk)
        execution.make_decision(DecisionAction.BLOCK, "High risk", 0.7)

        explanation = Explanation(text="Blocked due to high risk", details={})
        execution.add_explanation(explanation)

        assert execution.status == ExecutionStatus.EXPLAINED
        assert execution.explanation == explanation
        assert isinstance(execution.events[-1], ExplanationGenerated)

    def test_archive(self):
        execution = Execution(self.action, self.command)
        execution.submit()
        execution.start_processing()
        execution.complete_processing()

        risk = RiskScore(value=0.7, confidence=0.9, components={"rule": 0.6})
        execution.complete_assessment(risk)
        execution.make_decision(DecisionAction.BLOCK, "High risk", 0.7)
        explanation = Explanation(text="Blocked due to high risk", details={})
        execution.add_explanation(explanation)

        execution.store()  # Добавляем промежуточный шаг
        execution.archive()

        assert execution.status == ExecutionStatus.ARCHIVED
        assert isinstance(execution.events[-1], ExecutionArchived)

    def test_add_observation(self):
        execution = Execution(self.action, self.command)
        execution.submit()
        execution.start_processing()

        obs = Observation(
            observation_id="obs-1",
            metric="latency_ms",
            value=150.0,
            timestamp=datetime.utcnow()
        )
        execution.add_observation(obs)

        assert len(execution.observations) == 1
        assert isinstance(execution.events[-1], ObservationAdded)

    def test_add_finding(self):
        execution = Execution(self.action, self.command)
        execution.submit()
        execution.start_processing()

        finding = Finding(
            source="rule",
            score=0.8,
            confidence=0.9,
            reason="Latency anomaly",
            tags=("performance",)
        )
        execution.add_finding(finding)

        assert len(execution.findings) == 1
        assert isinstance(execution.events[-1], FindingProduced)

    def test_cannot_add_observation_in_wrong_state(self):
        execution = Execution(self.action, self.command)
        # CREATED state

        obs = Observation(
            observation_id="obs-1",
            metric="latency_ms",
            value=150.0,
            timestamp=datetime.utcnow()
        )
        with pytest.raises(InvalidStateError):
            execution.add_observation(obs)

    def test_cannot_make_decision_in_wrong_state(self):
        execution = Execution(self.action, self.command)
        execution.submit()
        execution.start_processing()
        execution.complete_processing()

        # Not in RISK_EVALUATED state
        with pytest.raises(InvalidStateError):
            execution.make_decision(DecisionAction.BLOCK, "test", 0.5)

    def test_get_events_clears_events(self):
        execution = Execution(self.action, self.command)
        events = execution.get_events()

        assert len(events) == 1
        assert len(execution.events) == 0

    def test_is_terminal(self):
        execution = Execution(self.action, self.command)
        assert execution.is_terminal() is False

        execution.submit()
        execution.start_processing()
        execution.fail_processing("error")
        assert execution.is_terminal() is True
