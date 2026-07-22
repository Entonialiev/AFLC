"""
Plugin SDK Tests
"""

import pytest
import sys
from typing import Optional, Dict

from src.registry import PluginRegistry, PluginMetadata
from src.interfaces import Plugin


def test_register_with_metadata():

    registry = PluginRegistry()

    class TestPlugin:
        pass

    metadata = PluginMetadata(
        name="test",
        version="2.0.0",
        min_python_version=(3, 10, 0),
        description="Test plugin"
    )

    if sys.version_info >= (3, 10, 0):
        registry.register("detectors", "test", TestPlugin, metadata)
        info = registry.get("detectors", "test")
        assert info.metadata.version == "2.0.0"
    else:
        with pytest.raises(RuntimeError):
            registry.register("detectors", "test", TestPlugin, metadata)


def test_plugin_validation_fails_with_too_many_params():

    registry = PluginRegistry()

    class BadPlugin:
        def __init__(self, a, b, c):
            pass

    with pytest.raises(TypeError):
        registry.register("detectors", "bad", BadPlugin)


def test_plugin_validation_passes_with_config():

    registry = PluginRegistry()

    class GoodPlugin:
        def __init__(self, config: Optional[Dict] = None):
            pass

    registry.register("detectors", "good", GoodPlugin)
    assert registry.get("detectors", "good") is not None


def test_plugin_validation_passes_with_kwargs():

    registry = PluginRegistry()

    class KwargsPlugin:
        def __init__(self, **kwargs):
            pass

    registry.register("detectors", "kwargs", KwargsPlugin)
    assert registry.get("detectors", "kwargs") is not None


def test_deprecation_warning():

    registry = PluginRegistry()

    class OldPlugin:
        pass

    metadata = PluginMetadata(
        name="old",
        version="1.0.0",
        deprecated=True,
        deprecated_since="2.0.0",
        replaced_by="new_plugin"
    )

    registry.register("detectors", "old", OldPlugin, metadata)

    import logging
    with pytest.warns(UserWarning):
        registry.create("detectors", "old")


def test_risk_engines_category_exists():

    registry = PluginRegistry()

    assert "risk_engines" in registry._categories


def test_backward_compatible_register_risk_engine():

    registry = PluginRegistry()

    from src.risk import RiskEngine

    registry.register_risk_engine("default", RiskEngine)

    engine = registry.create_risk_engine("default")

    from src.risk import RiskEngine
    assert isinstance(engine, RiskEngine)
