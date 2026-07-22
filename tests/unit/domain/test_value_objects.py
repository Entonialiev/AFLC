"""
Unit tests for Domain Value Objects
"""

import pytest
from datetime import datetime

from aflc.domain.value_objects import (
    RiskScore, Confidence, SeverityValue, Finding,
    Observation, Explanation, ExecutionContext, Command, Action
)
from aflc.domain.enums import Severity
from aflc.domain.exceptions import InvalidValueError


class TestRiskScore:
    def test_valid_risk_score(self):
        risk = RiskScore(value=0.7, confidence=0.9, components={"rule": 0.6})
        assert risk.value == 0.7
        assert risk.confidence == 0.9
        assert risk.components["rule"] == 0.6

    def test_invalid_value_raises(self):
        with pytest.raises(InvalidValueError):
            RiskScore(value=1.5, confidence=0.9, components={})

    def test_invalid_confidence_raises(self):
        with pytest.raises(InvalidValueError):
            RiskScore(value=0.5, confidence=1.5, components={})


class TestConfidence:
    def test_valid_confidence(self):
        conf = Confidence(value=0.8, source="detector")
        assert conf.value == 0.8
        assert conf.source == "detector"

    def test_invalid_confidence_raises(self):
        with pytest.raises(InvalidValueError):
            Confidence(value=1.5, source="test")


class TestSeverityValue:
    def test_valid_severity(self):
        sev = SeverityValue(value=0.7, category=Severity.HIGH)
        assert sev.value == 0.7
        assert sev.category == Severity.HIGH

    def test_invalid_severity_raises(self):
        with pytest.raises(InvalidValueError):
            SeverityValue(value=1.5, category=Severity.MEDIUM)


class TestFinding:
    def test_valid_finding(self):
        finding = Finding(
            source="rule",
            score=0.8,
            confidence=0.9,
            reason="Latency anomaly",
            tags=("performance",)
        )
        assert finding.score == 0.8
        assert finding.tags == ("performance",)

    def test_invalid_score_raises(self):
        with pytest.raises(InvalidValueError):
            Finding(
                source="rule",
                score=1.5,
                confidence=0.9,
                reason="test",
                tags=()
            )


class TestObservation:
    def test_observation_creation(self):
        now = datetime.utcnow()
        obs = Observation(
            observation_id="obs-1",
            metric="latency_ms",
            value=150.0,
            timestamp=now
        )
        assert obs.observation_id == "obs-1"
        assert obs.value == 150.0


class TestExplanation:
    def test_explanation_creation(self):
        exp = Explanation(
            text="Decision was made due to high risk",
            details={"risk": 0.8}
        )
        assert exp.text == "Decision was made due to high risk"
        assert exp.details["risk"] == 0.8


class TestExecutionContext:
    def test_context_creation(self):
        ctx = ExecutionContext(
            trace_id="trace-1",
            span_id="span-1",
            latency_ms=100.0,
            error_code=0,
            response_size=1024,
            cpu_usage=0.5,
            memory_usage=0.6,
            user_agent="test",
            client_ip="127.0.0.1"
        )
        assert ctx.trace_id == "trace-1"
        assert ctx.latency_ms == 100.0


class TestCommand:
    def test_command_creation(self):
        now = datetime.utcnow()
        cmd = Command(
            command_id="cmd-1",
            type="execute",
            payload={"action": "test"},
            timestamp=now,
            idempotency_key="key-1"
        )
        assert cmd.command_id == "cmd-1"
        assert cmd.type == "execute"


class TestAction:
    def test_action_creation(self):
        now = datetime.utcnow()
        action = Action(
            action_id="action-1",
            agent_id="agent-1",
            endpoint="/api/test",
            method="GET",
            payload={"param": "value"},
            timestamp=now
        )
        assert action.action_id == "action-1"
        assert action.agent_id == "agent-1"
        assert action.endpoint == "/api/test"
