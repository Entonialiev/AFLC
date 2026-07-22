"""
Tests for Execution Engine
"""

import pytest
from datetime import datetime
from typing import Optional, List, Dict, Any

from aflc.domain.execution import Execution
from aflc.domain.enums import ExecutionStatus, DecisionAction
from aflc.domain.events import DomainEvent
from aflc.application.engine import ExecutionEngine
from aflc.application.interfaces import EventBus, ExecutionRepository


# --- Mocks ---

class MockEventBus(EventBus):
    def __init__(self):
        self.events: List[DomainEvent] = []
    
    def publish(self, event: DomainEvent) -> None:
        self.events.append(event)
    
    async def publish_async(self, event: DomainEvent) -> None:
        self.events.append(event)


class MockRepository(ExecutionRepository):
    def __init__(self):
        self.executions: Dict[str, Execution] = {}
    
    def save(self, execution: Execution) -> None:
        self.executions[execution.execution_id] = execution
    
    def find_by_id(self, execution_id: str) -> Optional[Execution]:
        return self.executions.get(execution_id)
    
    def find_by_status(self, status: str) -> List[Execution]:
        return [e for e in self.executions.values() if e.status.value == status]


# --- Tests ---

class TestExecutionEngine:
    def setup_method(self):
        self.repository = MockRepository()
        self.event_bus = MockEventBus()
        self.engine = ExecutionEngine(self.repository, self.event_bus)
    
    def test_submit_action(self):
        execution = self.engine.submit_action(
            agent_id="agent-1",
            endpoint="/api/test",
            method="GET",
            payload={}
        )
        
        assert execution.execution_id is not None
        assert execution.status == ExecutionStatus.CREATED
        assert len(self.event_bus.events) == 1
        assert self.repository.find_by_id(execution.execution_id) is not None
    
    def test_add_observation(self):
        execution = self.engine.submit_action(
            agent_id="agent-1",
            endpoint="/api/test",
            method="GET",
            payload={}
        )
        
        execution = self.engine.add_observation(
            execution_id=execution.execution_id,
            metric="latency_ms",
            value=150.0
        )
        
        assert len(execution.observations) == 1
        assert execution.observations[0].metric == "latency_ms"
        assert execution.observations[0].value == 150.0
    
    def test_add_finding(self):
        execution = self.engine.submit_action(
            agent_id="agent-1",
            endpoint="/api/test",
            method="GET",
            payload={}
        )
        
        execution = self.engine.add_finding(
            execution_id=execution.execution_id,
            source="rule",
            score=0.8,
            confidence=0.9,
            reason="Latency anomaly",
            tags=["performance"]
        )
        
        assert len(execution.findings) == 1
        assert execution.findings[0].source == "rule"
    
    def test_full_lifecycle(self):
        # Submit
        execution = self.engine.submit_action(
            agent_id="agent-1",
            endpoint="/api/admin",
            method="DELETE",
            payload={"user": "admin"}
        )
        
        # Process
        execution = self.engine.add_observation(
            execution_id=execution.execution_id,
            metric="latency_ms",
            value=200.0
        )
        
        execution = self.engine.add_finding(
            execution_id=execution.execution_id,
            source="rule",
            score=0.7,
            confidence=0.9,
            reason="High latency",
            tags=["performance"]
        )
        
        execution = self.engine.complete_assessment(
            execution_id=execution.execution_id,
            risk_value=0.8,
            confidence=0.9,
            components={"rule": 0.7}
        )
        
        execution = self.engine.make_decision(
            execution_id=execution.execution_id,
            action="block",
            reason="High risk",
            severity=0.8
        )
        
        execution = self.engine.add_explanation(
            execution_id=execution.execution_id,
            text="Blocked due to high risk",
            details={"risk": 0.8}
        )
        
        execution = self.engine.archive_execution(execution.execution_id)
        
        assert execution.status == ExecutionStatus.ARCHIVED
