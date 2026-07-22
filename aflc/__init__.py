"""
AFLC — Agent Foundation & Lifecycle Control Platform
"""

__version__ = "2.0.0-alpha1"

# Основные экспорты для пользователей
from .domain import (
    Execution,
    ExecutionStatus,
    DecisionAction,
    EventType,
    DomainError,
    InvalidStateError,
    InvalidTransitionError,
    Action,
    Command,
    Observation,
    Finding,
    RiskScore,
    Explanation,
)

__all__ = [
    "Execution",
    "ExecutionStatus",
    "DecisionAction",
    "EventType",
    "DomainError",
    "InvalidStateError",
    "InvalidTransitionError",
    "Action",
    "Command",
    "Observation",
    "Finding",
    "RiskScore",
    "Explanation",
]
