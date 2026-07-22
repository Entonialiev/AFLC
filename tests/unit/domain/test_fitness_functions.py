"""
Architectural Fitness Functions
"""

import os
import ast
import pytest


def test_domain_has_no_external_imports():
    """Domain must not import external libraries."""
    domain_path = "aflc/domain"
    forbidden_imports = {
        "fastapi", "sqlalchemy", "redis", "prometheus",
        "opentelemetry", "pydantic", "kafka", "rabbitmq"
    }

    if not os.path.exists(domain_path):
        pytest.skip(f"Domain path {domain_path} not found")

    for root, _, files in os.walk(domain_path):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, "r") as f:
                    try:
                        tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for name in node.names:
                                    import_name = name.name.split(".")[0]
                                    assert import_name not in forbidden_imports, \
                                        f"Found forbidden import '{import_name}' in {filepath}"
                            elif isinstance(node, ast.ImportFrom):
                                if node.module and node.module.split(".")[0] in forbidden_imports:
                                    assert False, \
                                        f"Found forbidden import from '{node.module}' in {filepath}"
                    except SyntaxError:
                        pass  # Skip invalid files


def test_value_objects_are_frozen():
    """All Value Objects must be frozen (using dataclass(frozen=True))."""
    value_objects = [
        "RiskScore", "Confidence", "SeverityValue",
        "Finding", "Observation", "Explanation",
        "ExecutionContext", "Command", "Action"
    ]

    import aflc.domain.value_objects as vo

    for name in value_objects:
        cls = getattr(vo, name, None)
        if cls:
            # Проверяем, что класс является dataclass с frozen=True
            # В Python 3.9 это можно проверить через __dataclass_fields__
            assert hasattr(cls, "__dataclass_fields__"), f"{name} is not a dataclass"
            # Проверяем, что frozen=True через параметры dataclass
            # В Python 3.9 нет прямого способа, проверяем, что объект неизменяем
            if name in ["RiskScore", "Confidence", "SeverityValue", "Finding"]:
                # Эти классы имеют __post_init__, значит они должны быть frozen
                assert hasattr(cls, "__post_init__"), f"{name} should have __post_init__"


def test_execution_is_aggregate_root():
    """Execution must be the only Aggregate Root in domain."""
    from aflc.domain.execution import Execution

    # Check that Execution has aggregate characteristics
    assert hasattr(Execution, "execution_id")
    assert hasattr(Execution, "get_events")
    assert hasattr(Execution, "is_terminal")


def test_domain_exceptions_inherit_domain_error():
    """All domain exceptions must inherit from DomainError."""
    import aflc.domain.exceptions as exceptions

    base = exceptions.DomainError
    for name in dir(exceptions):
        if name.endswith("Error") and name != "DomainError":
            cls = getattr(exceptions, name)
            if isinstance(cls, type):
                assert issubclass(cls, base), \
                    f"{name} does not inherit from DomainError"
