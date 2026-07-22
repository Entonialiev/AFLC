"""
Plugin Registry для AFLC
Version: 2.1.4 (fixed deprecation warning)
"""

from typing import Dict, Type, Optional, Any, List, Callable, Tuple
from dataclasses import dataclass, field
import inspect
import logging
import sys
import warnings

from .interfaces import (
    Detector, AsyncDetector, Correlator, Policy, AsyncPolicy,
    Predictor, Memory, Explainer, HistoryBackend, Plugin
)

logger = logging.getLogger("aflc.registry")


@dataclass
class PluginMetadata:
    """Метаданные плагина для версионирования и совместимости"""
    name: str
    version: str
    min_python_version: Tuple[int, int, int] = (3, 9, 0)
    dependencies: List[str] = field(default_factory=list)
    description: str = ""
    tags: List[str] = field(default_factory=list)
    deprecated: bool = False
    deprecated_since: Optional[str] = None
    replaced_by: Optional[str] = None


@dataclass
class PluginInfo:
    name: str
    plugin_class: Type
    metadata: PluginMetadata


class PluginRegistry:
    """
    Единый реестр всех плагинов AFLC.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self._categories: Dict[str, Dict[str, PluginInfo]] = {
            "detectors": {},
            "async_detectors": {},
            "correlators": {},
            "policies": {},
            "async_policies": {},
            "predictors": {},
            "memory": {},
            "explainers": {},
            "history_backends": {},
            "risk_engines": {}
        }
        
        self._initialized_plugins: Dict[str, Plugin] = {}
        
        self._register_builtins()
    
    def _register_builtins(self):
        from .detectors import RuleDetector, StatisticalDetector
        from .correlator import Correlator as DefaultCorrelator
        from .risk import RiskEngine
        from .explainer import Explainer as DefaultExplainer
        from .history import MemoryHistory, SQLiteHistory
        from .defaults import DefaultPolicy, SimpleCorrelator
        
        self.register(
            "detectors", "rule", RuleDetector,
            metadata=PluginMetadata(
                name="rule",
                version="1.0.0",
                description="Rule-based detector (timeout, size, errors)"
            )
        )
        self.register(
            "detectors", "statistical", StatisticalDetector,
            metadata=PluginMetadata(
                name="statistical",
                version="1.0.0",
                description="EWMA-based adaptive detector"
            )
        )
        
        self.register(
            "correlators", "weighted", DefaultCorrelator,
            metadata=PluginMetadata(
                name="weighted",
                version="1.0.0",
                description="Weighted correlation"
            )
        )
        self.register(
            "correlators", "simple", SimpleCorrelator,
            metadata=PluginMetadata(
                name="simple",
                version="1.0.0",
                description="Simple max-score correlator"
            )
        )
        
        self.register(
            "policies", "default", DefaultPolicy,
            metadata=PluginMetadata(
                name="default",
                version="1.0.0",
                description="Default threshold-based policy"
            )
        )
        
        self.register(
            "risk_engines", "default", RiskEngine,
            metadata=PluginMetadata(
                name="default",
                version="1.0.0",
                description="Default risk engine"
            )
        )
        
        self.register(
            "history_backends", "memory", MemoryHistory,
            metadata=PluginMetadata(
                name="memory",
                version="1.0.0",
                description="In-memory history"
            )
        )
        self.register(
            "history_backends", "sqlite", SQLiteHistory,
            metadata=PluginMetadata(
                name="sqlite",
                version="1.0.0",
                description="SQLite history"
            )
        )
    
    def register(
        self,
        category: str,
        name: str,
        plugin_class: Type,
        metadata: Optional[PluginMetadata] = None
    ) -> None:
        if category not in self._categories:
            raise ValueError(f"Unknown category: {category}")
        
        if name in self._categories[category]:
            logger.warning(f"Overwriting plugin: {category}/{name}")
        
        if metadata:
            min_py = metadata.min_python_version
            if sys.version_info < min_py:
                raise RuntimeError(
                    f"Plugin {category}/{name} requires Python {'.'.join(map(str, min_py))}"
                )
        
        self._validate_plugin_class(plugin_class)
        
        if metadata is None:
            metadata = PluginMetadata(name=name, version="1.0.0")
        
        self._categories[category][name] = PluginInfo(
            name=name,
            plugin_class=plugin_class,
            metadata=metadata
        )
        
        logger.debug(f"Registered plugin: {category}/{name} v{metadata.version}")
    
    def _validate_plugin_class(self, plugin_class: Type) -> None:
        """
        Проверяет, что конструктор плагина совместим с системой.
        """
        # Пропускаем валидацию для классов без переопределённого __init__
        if plugin_class.__init__ is object.__init__:
            return
        
        sig = inspect.signature(plugin_class.__init__)
        params = list(sig.parameters.values())
        
        # Пропускаем self
        params = params[1:]
        
        # Если нет параметров — OK
        if not params:
            return
        
        # Если ровно один параметр
        if len(params) == 1:
            param = params[0]
            # Проверяем, что это config или **kwargs или имеет значение по умолчанию
            is_config = param.name == 'config'
            is_kwargs = param.kind == inspect.Parameter.VAR_KEYWORD
            has_default = param.default != inspect.Parameter.empty
            
            if is_config or is_kwargs or has_default:
                return
            
            raise TypeError(
                f"Plugin {plugin_class.__name__} parameter must be "
                f"`config: Optional[Dict] = None` or `**kwargs`, got `{param.name}`."
            )
        
        # Если несколько параметров, проверяем, что у всех есть дефолты
        all_have_defaults = all(p.default != inspect.Parameter.empty for p in params)
        if all_have_defaults:
            return
        
        raise TypeError(
            f"Plugin {plugin_class.__name__} has too many required parameters ({len(params)}). "
            f"Only `config: Optional[Dict] = None` or no parameters are allowed."
        )
    
    def get(self, category: str, name: str) -> Optional[PluginInfo]:
        return self._categories.get(category, {}).get(name)
    
    def create(self, category: str, name: str, config: Optional[Dict] = None) -> Optional[Any]:
        info = self.get(category, name)
        if not info:
            logger.warning(f"Plugin not found: {category}/{name}")
            return None
        
        if info.metadata.deprecated:
            logger.warning(
                f"Plugin {category}/{name} is deprecated since {info.metadata.deprecated_since}. "
                f"Use {info.metadata.replaced_by} instead."
            )
            warnings.warn(
                f"Plugin {category}/{name} is deprecated since {info.metadata.deprecated_since}. "
                f"Use {info.metadata.replaced_by} instead.",
                DeprecationWarning,
                stacklevel=2
            )
        
        try:
            sig = inspect.signature(info.plugin_class.__init__)
            params = list(sig.parameters.values())
            params = params[1:]  # пропускаем self
            
            if not params:
                instance = info.plugin_class()
            else:
                param = params[0]
                if param.name == 'config':
                    instance = info.plugin_class(config=config or {})
                elif param.kind == inspect.Parameter.VAR_KEYWORD:
                    instance = info.plugin_class(**(config or {}))
                else:
                    # Если параметр с дефолтом, передаём config как первый аргумент
                    instance = info.plugin_class(config or {})
            
            if isinstance(instance, Plugin):
                instance.initialize()
            
            return instance
            
        except Exception as e:
            logger.error(f"Failed to create plugin {category}/{name}: {e}")
            return None
    
    def list_plugins(self, category: Optional[str] = None) -> Dict[str, List[str]]:
        if category:
            if category not in self._categories:
                return {}
            return {category: list(self._categories[category].keys())}
        return {cat: list(plugins.keys()) for cat, plugins in self._categories.items()}
    
    def get_plugin_info(self, category: str, name: str) -> Optional[PluginMetadata]:
        info = self.get(category, name)
        return info.metadata if info else None
    
    def is_deprecated(self, category: str, name: str) -> bool:
        info = self.get(category, name)
        return info.metadata.deprecated if info else False
    
    # --- Удобные методы для обратной совместимости ---
    
    def register_detector(self, name: str, detector_class: Type, **kwargs):
        metadata = PluginMetadata(
            name=name,
            version=kwargs.get("version", "1.0.0"),
            description=kwargs.get("description", ""),
            tags=kwargs.get("tags", [])
        )
        self.register("detectors", name, detector_class, metadata)
    
    def register_correlator(self, name: str, correlator_class: Type, **kwargs):
        metadata = PluginMetadata(
            name=name,
            version=kwargs.get("version", "1.0.0"),
            description=kwargs.get("description", ""),
            tags=kwargs.get("tags", [])
        )
        self.register("correlators", name, correlator_class, metadata)
    
    def register_policy(self, name: str, policy_class: Type, **kwargs):
        metadata = PluginMetadata(
            name=name,
            version=kwargs.get("version", "1.0.0"),
            description=kwargs.get("description", ""),
            tags=kwargs.get("tags", [])
        )
        self.register("policies", name, policy_class, metadata)
    
    def register_memory(self, name: str, memory_class: Type, **kwargs):
        metadata = PluginMetadata(
            name=name,
            version=kwargs.get("version", "1.0.0"),
            description=kwargs.get("description", ""),
            tags=kwargs.get("tags", [])
        )
        self.register("memory", name, memory_class, metadata)
    
    def register_history_backend(self, name: str, backend_class: Type, **kwargs):
        metadata = PluginMetadata(
            name=name,
            version=kwargs.get("version", "1.0.0"),
            description=kwargs.get("description", ""),
            tags=kwargs.get("tags", [])
        )
        self.register("history_backends", name, backend_class, metadata)
    
    def register_risk_engine(self, name: str, risk_class: Type, **kwargs):
        metadata = PluginMetadata(
            name=name,
            version=kwargs.get("version", "1.0.0"),
            description=kwargs.get("description", ""),
            tags=kwargs.get("tags", [])
        )
        self.register("risk_engines", name, risk_class, metadata)
    
    def create_detector(self, name: str, config: Optional[Dict] = None):
        return self.create("detectors", name, config)
    
    def create_correlator(self, name: str, config: Optional[Dict] = None):
        return self.create("correlators", name, config)
    
    def create_policy(self, name: str, config: Optional[Dict] = None):
        return self.create("policies", name, config)
    
    def create_memory(self, name: str, config: Optional[Dict] = None):
        return self.create("memory", name, config)
    
    def create_risk_engine(self, name: str, config: Optional[Dict] = None):
        return self.create("risk_engines", name, config)
    
    def create_history_backend(self, name: str, config: Optional[Dict] = None):
        return self.create("history_backends", name, config)


# Глобальный экземпляр
registry = PluginRegistry()
