"""
Pytest configuration for benchmarks
"""

import pytest
import tempfile
import os

from src.registry import PluginRegistry


@pytest.fixture
def registry():
    """Создаёт свежий экземпляр Registry для каждого бенчмарка"""
    return PluginRegistry()


@pytest.fixture
def temp_db_path():
    """Создаёт временный путь для SQLite бенчмарков"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def sample_context():
    """Создаёт тестовый контекст для бенчмарков"""
    from src.models import ActionContext
    return ActionContext(
        action_id="benchmark",
        endpoint="/api/test",
        method="GET",
        latency_ms=500,
        error_code=0,
        response_size=1024,
        user_id="bench_user"
    )
