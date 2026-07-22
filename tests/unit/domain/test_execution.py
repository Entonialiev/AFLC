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
    ExecutionCreated, ExecutionStarted, ObservationRecorded,
    FindingCreated, AssessmentCompleted, RiskEvaluated, DecisionMade,
    ExplanationGenerated, ExecutionArchived
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

    def test_start_execution(self):
        execution = Execution(self.action, self.command)
        execution.submit()
        execution.start()

        assert execution.status == ExecutionStatus.RUNNING
        assert isinstance(execution.events[-1], ExecutionStarted)

    def test_start_fails_if_not_submitted(self):
        execution = Execution(self.action, self.command)
        # start() without submit() should raise InvalidTransitionError
        with pytest.raises(InvalidTransitionError):
            execution.start()

    def test_complete_processing(self):
        execution = Execution(self.action, self.command)
        execution.submit()
        execution.start()
        execution.complete_processing()

        assert execution.status == ExecutionStatus.COMPLETED

    def test_fail_processing(self):
        execution = Execution(self.action, self.command)
        execution.submit()
        execution.start()
        execution.fail_processing("test error")

        assert execution.status == ExecutionStatus.FAILED

    def test_record_observation(self):
        execution = Execution(self.action, self.command)
        execution.submit()
        execution.start()

        obs = Observation(
            observation_id="obs-1",
            metric="latency_ms",
            value=150.0,
            timestamp=datetime.utcnow()
        )
        execution.record_observation(obs)

        assert len(execution.observations) == 1
        assert isinstance(execution.events[-1], ObservationRecorded)

    def test_record_finding(self):
        execution = Execution(self.action, self.command)
        execution.submit()
        execution.start()

        finding = Finding(
            source="rule",
            score=0.8,
            confidence=0.9,
            reason="Latency anomaly",
            tags=("performance",)
        )
        execution.record_finding(finding)

        assert len(execution.findings) == 1
        assert isinstance(execution.events[-1], FindingCreated)

    def test_cannot_record_observation_if_not_running(self):
        execution = Execution(self.action, self.command)
        obs = Observation(
            observation_id="obs-1",
            metric="latency_ms",
            value=150.0,
            timestamp=datetime.utcnow()
        )
        with pytest.raises(InvalidStateError):
            execution.record_observation(obs)

    def test_evaluate_risk(self):
        execution = Execution(self.action, self.command)
        execution.submit()
        execution.start()
        execution.complete_processing()

        risk = RiskScore(value=0.7, confidence=0.9, components={"rule": 0.6})
        execution.evaluate_risk(risk)

        assert execution.status == ExecutionStatus.RISK_EVALUATED
        assert execution.risk_score == risk
        assert isinstance(execution.events[-1], RiskEvaluated)

    def test_make_decision(self):
        execution = Execution(self.action, self.command)
        execution.submit()
        execution.start()
        execution.complete_processing()

        risk = RiskScore(value=0.7, confidence=0.9, components={"rule": 0.6})
        execution.evaluate_risk(risk)

        execution.make_decision(DecisionAction.BLOCK, "High risk", 0.7)

        assert execution.status == ExecutionStatus.DECISION_MADE
        assert execution.decision["action"] == DecisionAction.BLOCK
        assert isinstance(execution.events[-1], DecisionMade)

    def test_add_explanation(self):
        execution = Execution(self.action, self.command)
        execution.submit()
        execution.start()
        execution.complete_processing()

        risk = RiskScore(value=0.7, confidence=0.9, components={"rule": 0.6})
        execution.evaluate_risk(risk)
        execution.make_decision(DecisionAction.BLOCK, "High risk", 0.7)

        explanation = Explanation(text="Blocked due to high risk", details={})
        execution.add_explanation(explanation)

        assert execution.status == ExecutionStatus.EXPLAINED
        assert execution.explanation == explanation
        assert isinstance(execution.events[-1], ExplanationGenerated)

    def test_store_and_archive(self):
        execution = Execution(self.action, self.command)
        execution.submit()
        execution.start()
        execution.complete_processing()

        risk = RiskScore(value=0.7, confidence=0.9, components={"rule": 0.6})
        execution.evaluate_risk(risk)
        execution.make_decision(DecisionAction.BLOCK, "High risk", 0.7)
        explanation = Explanation(text="Blocked due to high risk", details={})
        execution.add_explanation(explanation)

        execution.store()
        execution.archive()

        assert execution.status == ExecutionStatus.ARCHIVED
        assert isinstance(execution.events[-1], ExecutionArchived)

    def test_get_events_clears_events(self):
        execution = Execution(self.action, self.command)
        events = execution.get_events()

        assert len(events) == 1
        assert len(execution.events) == 0

    def test_is_terminal(self):
        execution = Execution(self.action, self.command)
        assert execution.is_terminal() is False

        execution.submit()
        execution.start()
        execution.fail_processing("error")
        assert execution.is_terminal() is True
