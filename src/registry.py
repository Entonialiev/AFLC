"""
Plugin Registry для AFLC
Version: 2.0.0 (unified API)
"""

from typing import Dict, Type, Optional, Any, List, Callable
from dataclasses import dataclass, field
import inspect
import logging

from .interfaces import (
    Detector, AsyncDetector, Correlator, Policy, AsyncPolicy,
    Predictor, Memory, Explainer, HistoryBackend, Plugin
)

logger = logging.getLogger("aflc.registry")


@dataclass
class PluginInfo:
    name: str
    plugin_class: Type
    description: str = ""
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


class PluginRegistry:
    """
    Единый реестр всех плагинов AFLC.
    
    Все плагины следуют единому контракту:
    - Конструктор принимает только `config: Optional[Dict] = None`
    - Имеют методы `initialize()` и `shutdown()`
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
        
        self._plugins: Dict[str, PluginInfo] = {}
        self._categories: Dict[str, Dict[str, PluginInfo]] = {
            "detectors": {},
            "async_detectors": {},
            "correlators": {},
            "policies": {},
            "async_policies": {},
            "predictors": {},
            "memory": {},
            "explainers": {},
            "history_backends": {}
        }
        
        self._initialized_plugins: Dict[str, Plugin] = {}
        
        self._register_builtins()
    
    def _register_builtins(self):
        """Регистрирует встроенные плагины"""
        from .detectors import RuleDetector, StatisticalDetector
        from .correlator import Correlator as DefaultCorrelator
        from .risk import RiskEngine
        from .explainer import Explainer as DefaultExplainer
        from .history import MemoryHistory, SQLiteHistory
        from .defaults import DefaultPolicy, SimpleCorrelator
        
        # Детекторы
        self.register("detectors", "rule", RuleDetector, "Rule-based detector")
        self.register("detectors", "statistical", StatisticalDetector, "EWMA-based adaptive detector")
        
        # Корреляторы
        self.register("correlators", "weighted", DefaultCorrelator, "Weighted correlation")
        self.register("correlators", "simple", SimpleCorrelator, "Simple max-score correlator")
        
        # Политики
        self.register("policies", "default", DefaultPolicy, "Default policy")
        
        # Risk Engine
        self.register("risk_engines", "default", RiskEngine, "Default risk engine")
        
        # History Backends
        self.register("history_backends", "memory", MemoryHistory, "In-memory history")
        self.register("history_backends", "sqlite", SQLiteHistory, "SQLite history")
    
    def register(self, category: str, name: str, plugin_class: Type,
                 description: str = "", version: str = "1.0.0",
                 tags: List[str] = None, dependencies: List[str] = None) -> None:
        """
        Унифицированная регистрация плагина.
        
        Args:
            category: категория (detectors, policies, etc.)
            name: уникальное имя плагина
            plugin_class: класс плагина
            description: описание
            version: версия
            tags: теги
            dependencies: список зависимостей
        """
        if category not in self._categories:
            self._categories[category] = {}
        
        self._categories[category][name] = PluginInfo(
            name=name,
            plugin_class=plugin_class,
            description=description,
            version=version,
            tags=tags or [],
            dependencies=dependencies or []
        )
        
        logger.debug(f"Registered plugin: {category}/{name}")
    
    def get(self, category: str, name: str) -> Optional[PluginInfo]:
        """Возвращает информацию о плагине"""
        return self._categories.get(category, {}).get(name)
    
    def create(self, category: str, name: str, config: Optional[Dict] = None) -> Optional[Any]:
        """
        Унифицированное создание экземпляра плагина.
        
        Все плагины должны принимать `config: Optional[Dict] = None` в конструкторе.
        """
        info = self.get(category, name)
        if not info:
            logger.warning(f"Plugin not found: {category}/{name}")
            return None
        
        try:
            # Проверяем сигнатуру конструктора
            sig = inspect.signature(info.plugin_class.__init__)
            params = list(sig.parameters.keys())
            
            # Если конструктор принимает config
            if 'config' in params:
                instance = info.plugin_class(config=config or {})
            # Если конструктор принимает kwargs (старый стиль)
            elif 'kwargs' in params:
                instance = info.plugin_class(**(config or {}))
            # Если конструктор не принимает аргументов
            else:
                instance = info.plugin_class()
            
            # Вызываем initialize(), если плагин реализует Plugin
            if isinstance(instance, Plugin):
                instance.initialize()
            
            return instance
            
        except Exception as e:
            logger.error(f"Failed to create plugin {category}/{name}: {e}")
            return None
    
    def list_plugins(self, category: Optional[str] = None) -> Dict[str, List[str]]:
        """Возвращает список зарегистрированных плагинов"""
        if category:
            return {category: list(self._categories.get(category, {}).keys())}
        return {cat: list(plugins.keys()) for cat, plugins in self._categories.items()}
    
    def get_plugin_info(self, category: str, name: str) -> Optional[PluginInfo]:
        return self.get(category, name)
    
    # --- Удобные методы для обратной совместимости ---
    
    def register_detector(self, name: str, detector_class: Type, **kwargs):
        self.register("detectors", name, detector_class, **kwargs)
    
    def register_correlator(self, name: str, correlator_class: Type, **kwargs):
        self.register("correlators", name, correlator_class, **kwargs)
    
    def register_policy(self, name: str, policy_class: Type, **kwargs):
        self.register("policies", name, policy_class, **kwargs)
    
    def register_memory(self, name: str, memory_class: Type, **kwargs):
        self.register("memory", name, memory_class, **kwargs)
    
    def register_history_backend(self, name: str, backend_class: Type, **kwargs):
        self.register("history_backends", name, backend_class, **kwargs)
    
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
