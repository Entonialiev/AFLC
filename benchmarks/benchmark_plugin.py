"""
Plugin Lifecycle Benchmark
"""

import pytest

from src.interfaces import Plugin
from src.registry import PluginRegistry


class LifecyclePlugin(Plugin):
    """Тестовый плагин с жизненным циклом"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self._initialized = False
    
    def initialize(self):
        self._initialized = True
    
    def shutdown(self):
        self._initialized = False


class HeavyLifecyclePlugin(Plugin):
    """Тестовый плагин с тяжёлым жизненным циклом"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self._initialized = False
    
    def initialize(self):
        # Симулируем тяжёлую инициализацию
        import time
        time.sleep(0.001)  # 1ms
        self._initialized = True
    
    def shutdown(self):
        import time
        time.sleep(0.001)
        self._initialized = False


def test_plugin_create_simple(benchmark):
    """Измеряет скорость создания простого плагина"""
    registry = PluginRegistry()
    registry.register("detectors", "lifecycle", LifecyclePlugin)
    
    result = benchmark(
        registry.create,
        "detectors",
        "lifecycle"
    )
    
    assert result is not None


def test_plugin_create_with_config(benchmark):
    """Измеряет скорость создания плагина с конфигурацией"""
    registry = PluginRegistry()
    registry.register("detectors", "lifecycle", LifecyclePlugin)
    
    result = benchmark(
        registry.create,
        "detectors",
        "lifecycle",
        {"test": True, "value": 42}
    )
    
    assert result is not None
    assert result.config.get("test") is True


def test_plugin_lifecycle_heavy(benchmark):
    """Измеряет скорость жизненного цикла тяжёлого плагина"""
    registry = PluginRegistry()
    registry.register("detectors", "heavy", HeavyLifecyclePlugin)
    
    plugin = benchmark(
        registry.create,
        "detectors",
        "heavy"
    )
    
    assert plugin is not None
    assert plugin._initialized is True
    
    plugin.shutdown()


def test_plugin_lookup(benchmark):
    """Измеряет скорость поиска плагина в Registry"""
    registry = PluginRegistry()
    registry.register("detectors", "lifecycle", LifecyclePlugin)
    
    result = benchmark(
        registry.get,
        "detectors",
        "lifecycle"
    )
    
    assert result is not None


def test_plugin_metadata_access(benchmark):
    """Измеряет скорость доступа к метаданным"""
    from src.registry import PluginMetadata
    
    registry = PluginRegistry()
    metadata = PluginMetadata(name="test", version="1.0.0")
    registry.register("detectors", "with_meta", LifecyclePlugin, metadata)
    
    result = benchmark(
        registry.get_plugin_info,
        "detectors",
        "with_meta"
    )
    
    assert result is not None
    assert result.version == "1.0.0"


def test_plugin_deprecated_check(benchmark):
    """Измеряет скорость проверки депрекации"""
    from src.registry import PluginMetadata
    
    registry = PluginRegistry()
    metadata = PluginMetadata(
        name="old",
        version="1.0.0",
        deprecated=True,
        deprecated_since="2.0.0",
        replaced_by="new"
    )
    registry.register("detectors", "old", LifecyclePlugin, metadata)
    
    # Создаём с депрекацией
    result = benchmark(
        registry.create,
        "detectors",
        "old"
    )
    
    assert result is not None
