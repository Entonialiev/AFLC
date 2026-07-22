"""
AFLC Registry Benchmarks
"""

import pytest

from src.registry import PluginRegistry
from src.interfaces import Plugin


class DummyPlugin:
    """Тестовый плагин без зависимостей"""
    def __init__(self, config=None):
        self.config = config or {}


class LifecyclePlugin(Plugin):
    """Тестовый плагин с жизненным циклом"""
    def __init__(self, config=None):
        self.config = config or {}
        self._initialized = False
    
    def initialize(self):
        self._initialized = True
    
    def shutdown(self):
        self._initialized = False


def test_registry_register_speed(benchmark, registry):
    """Измеряет скорость регистрации плагина"""
    
    def register():
        registry.register("detectors", "dummy", DummyPlugin)
    
    benchmark(register)


def test_registry_create_speed(benchmark, registry):
    """Измеряет скорость создания экземпляра плагина"""
    registry.register("detectors", "dummy", DummyPlugin)
    
    result = benchmark(
        registry.create,
        "detectors",
        "dummy",
        {"test": True}
    )
    
    assert result is not None
    assert result.config.get("test") is True


def test_registry_lookup_speed(benchmark, registry):
    """Измеряет скорость поиска плагина"""
    registry.register("detectors", "dummy", DummyPlugin)
    
    result = benchmark(
        registry.get,
        "detectors",
        "dummy"
    )
    
    assert result is not None


def test_registry_create_with_lifecycle(benchmark, registry):
    """Измеряет скорость создания плагина с жизненным циклом"""
    registry.register("detectors", "lifecycle", LifecyclePlugin)
    
    plugin = benchmark(
        registry.create,
        "detectors",
        "lifecycle"
    )
    
    assert plugin is not None
    assert plugin._initialized is True
    plugin.shutdown()


def test_registry_metadata_overhead(benchmark, registry):
    """Измеряет оверхед метаданных при создании"""
    from src.registry import PluginMetadata
    
    metadata = PluginMetadata(
        name="test",
        version="2.0.0",
        description="Test plugin with metadata",
        tags=["test", "benchmark"]
    )
    
    registry.register("detectors", "with_meta", DummyPlugin, metadata)
    
    result = benchmark(
        registry.create,
        "detectors",
        "with_meta"
    )
    
    assert result is not None
