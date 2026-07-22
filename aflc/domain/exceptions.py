"""
AFLC Domain Exceptions
"""


class DomainError(Exception):
    """Base exception for all domain errors."""
    pass


class InvalidActionError(DomainError):
    """Raised when an action is invalid."""
    pass


class InvalidTransitionError(DomainError):
    """Raised when a state transition is invalid."""
    pass


class InvalidStateError(DomainError):
    """Raised when an operation is performed in an invalid state."""
    pass


class InvalidValueError(DomainError):
    """Raised when a value object is invalid."""
    pass


class AggregateNotFoundError(DomainError):
    """Raised when an aggregate is not found."""
    pass


class RuleViolationError(DomainError):
    """Raised when a policy rule is violated."""
    pass


class ImmutableError(DomainError):
    """Raised when trying to mutate an immutable object."""
    pass
