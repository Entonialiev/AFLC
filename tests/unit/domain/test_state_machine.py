"""
Unit tests for Execution State Machine
"""

import pytest

from aflc.domain.enums import ExecutionStatus
from aflc.domain.execution import ExecutionStateMachine
from aflc.domain.exceptions import InvalidTransitionError


class TestExecutionStateMachine:
    def test_valid_transitions(self):
        # CREATED → PENDING
        assert ExecutionStateMachine.validate_transition(
            ExecutionStatus.CREATED, ExecutionStatus.PENDING
        ) is True

        # PENDING → RUNNING
        assert ExecutionStateMachine.validate_transition(
            ExecutionStatus.PENDING, ExecutionStatus.RUNNING
        ) is True

        # RUNNING → COMPLETED
        assert ExecutionStateMachine.validate_transition(
            ExecutionStatus.RUNNING, ExecutionStatus.COMPLETED
        ) is True

        # RUNNING → FAILED
        assert ExecutionStateMachine.validate_transition(
            ExecutionStatus.RUNNING, ExecutionStatus.FAILED
        ) is True

        # COMPLETED → RISK_EVALUATED
        assert ExecutionStateMachine.validate_transition(
            ExecutionStatus.COMPLETED, ExecutionStatus.RISK_EVALUATED
        ) is True

        # RISK_EVALUATED → DECISION_MADE
        assert ExecutionStateMachine.validate_transition(
            ExecutionStatus.RISK_EVALUATED, ExecutionStatus.DECISION_MADE
        ) is True

        # DECISION_MADE → EXPLAINED
        assert ExecutionStateMachine.validate_transition(
            ExecutionStatus.DECISION_MADE, ExecutionStatus.EXPLAINED
        ) is True

        # EXPLAINED → STORED
        assert ExecutionStateMachine.validate_transition(
            ExecutionStatus.EXPLAINED, ExecutionStatus.STORED
        ) is True

        # STORED → ARCHIVED
        assert ExecutionStateMachine.validate_transition(
            ExecutionStatus.STORED, ExecutionStatus.ARCHIVED
        ) is True

    def test_invalid_transitions(self):
        # CREATED → RUNNING (skip PENDING)
        assert ExecutionStateMachine.validate_transition(
            ExecutionStatus.CREATED, ExecutionStatus.RUNNING
        ) is False

        # FAILED → anything
        assert ExecutionStateMachine.validate_transition(
            ExecutionStatus.FAILED, ExecutionStatus.COMPLETED
        ) is False

        # ARCHIVED → anything
        assert ExecutionStateMachine.validate_transition(
            ExecutionStatus.ARCHIVED, ExecutionStatus.STORED
        ) is False

    def test_transition_performs_valid_change(self):
        result = ExecutionStateMachine.transition(
            ExecutionStatus.CREATED, ExecutionStatus.PENDING
        )
        assert result == ExecutionStatus.PENDING

    def test_transition_raises_on_invalid(self):
        with pytest.raises(InvalidTransitionError):
            ExecutionStateMachine.transition(
                ExecutionStatus.CREATED, ExecutionStatus.RUNNING
            )
