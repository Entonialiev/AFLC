"""
AFLC Execution Engine — основной оркестратор
"""

from typing import Optional, List, Dict, Any

from aflc.domain.execution import Execution
from aflc.domain.enums import ExecutionStatus

from .interfaces import EventBus, ExecutionRepository
from .use_cases import SubmitActionUseCase, ProcessExecutionUseCase


class ExecutionEngine:
    """
    Основной оркестратор AFLC.
    Координирует выполнение действий через Use Cases.
    """
    
    def __init__(self, repository: ExecutionRepository, event_bus: EventBus):
        self.repository = repository
        self.event_bus = event_bus
        
        self.submit_use_case = SubmitActionUseCase(repository, event_bus)
        self.process_use_case = ProcessExecutionUseCase(repository, event_bus)
    
    # --- Command Methods ---
    
    def submit_action(
        self,
        agent_id: str,
        endpoint: str,
        method: str,
        payload: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> Execution:
        """Submit a new action for execution."""
        return self.submit_use_case.execute(
            agent_id=agent_id,
            endpoint=endpoint,
            method=method,
            payload=payload,
            idempotency_key=idempotency_key
        )
    
    def start_processing(self, execution_id: str) -> Execution:
        """Start processing an execution."""
        execution = self.repository.find_by_id(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        execution.start_processing()
        self.repository.save(execution)
        return execution
    
    def complete_processing(self, execution_id: str) -> Execution:
        """Complete processing an execution."""
        execution = self.repository.find_by_id(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        execution.complete_processing()
        self.repository.save(execution)
        return execution
    
    def fail_processing(self, execution_id: str, reason: str) -> Execution:
        """Fail processing an execution."""
        execution = self.repository.find_by_id(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        execution.fail_processing(reason)
        self.repository.save(execution)
        return execution
    
    def add_observation(
        self,
        execution_id: str,
        metric: str,
        value: float
    ) -> Execution:
        """Add an observation to an execution."""
        return self.process_use_case.add_observation(
            execution_id=execution_id,
            metric=metric,
            value=value
        )
    
    def add_finding(
        self,
        execution_id: str,
        source: str,
        score: float,
        confidence: float,
        reason: str,
        tags: List[str]
    ) -> Execution:
        """Add a finding from a detector."""
        return self.process_use_case.add_finding(
            execution_id=execution_id,
            source=source,
            score=score,
            confidence=confidence,
            reason=reason,
            tags=tags
        )
    
    def complete_assessment(
        self,
        execution_id: str,
        risk_value: float,
        confidence: float,
        components: Dict[str, float]
    ) -> Execution:
        """Complete risk assessment."""
        return self.process_use_case.complete_assessment(
            execution_id=execution_id,
            risk_value=risk_value,
            confidence=confidence,
            components=components
        )
    
    def make_decision(
        self,
        execution_id: str,
        action: str,
        reason: str,
        severity: float
    ) -> Execution:
        """Make a decision on the execution."""
        return self.process_use_case.make_decision(
            execution_id=execution_id,
            action=action,
            reason=reason,
            severity=severity
        )
    
    def add_explanation(
        self,
        execution_id: str,
        text: str,
        details: Dict[str, Any]
    ) -> Execution:
        """Add explanation to execution."""
        return self.process_use_case.add_explanation(
            execution_id=execution_id,
            text=text,
            details=details
        )
    
    def archive_execution(self, execution_id: str) -> Execution:
        """Archive an execution."""
        return self.process_use_case.archive_execution(execution_id)
    
    # --- Query Methods ---
    
    def get_execution(self, execution_id: str) -> Optional[Execution]:
        """Get execution by ID."""
        return self.repository.find_by_id(execution_id)
    
    def get_executions_by_status(self, status: ExecutionStatus) -> List[Execution]:
        """Get all executions with given status."""
        return self.repository.find_by_status(status.value)
    
    def get_all_executions(self) -> List[Execution]:
        """Get all executions."""
        return self.repository.find_all()
