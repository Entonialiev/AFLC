"""
Plugin Registry для AFLC
"""

from typing import Dict, Type, Optional, Any, List
from dataclasses import dataclass, field

from .core import Detector, AsyncDetector, Correlator, Policy, AsyncPolicy, Predictor, Memory, Explainer


@dataclass
class PluginInfo:
    name: str
    plugin_class: Type
    description: str = ""
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)


class PluginRegistry:
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
        
        self._detectors: Dict[str, PluginInfo] = {}
        self._correlators: Dict[str, PluginInfo] = {}
        self._policies: Dict[str, PluginInfo] = {}
        self._predictors: Dict[str, PluginInfo] = {}
        self._memory_backends: Dict[str, PluginInfo] = {}
        self._explainers: Dict[str, PluginInfo] = {}
        self._risk_engines: Dict[str, PluginInfo] = {}
        
        self._register_builtins()
    
    def _register_builtins(self):
        from .detectors import RuleDetector, StatisticalDetector
        from .correlator import Correlator
        from .core import DefaultPolicy, SimpleCorrelator
        from .risk import RiskEngine
        from .explainer import Explainer
        from .memory import Memory
        
        self.register_detector("rule", RuleDetector, "Rule-based detector")
        self.register_detector("statistical", StatisticalDetector, "EWMA-based adaptive detector")
        
        self.register_correlator("weighted", Correlator, "Weighted correlation")
        self.register_correlator("simple", SimpleCorrelator, "Simple max-score correlator")
        
        self.register_policy("default", DefaultPolicy, "Default policy")
        
        self.register_risk_engine("default", RiskEngine, "Default risk engine")
        
        self.register_memory("default", Memory, "In-memory storage with JSON")
    
    # --- Регистрация ---
    
    def register_detector(self, name: str, detector_class: Type, description: str = "", version: str = "1.0.0", tags: List[str] = None):
        self._detectors[name] = PluginInfo(name, detector_class, description, version, tags or [])
    
    def register_correlator(self, name: str, correlator_class: Type, description: str = "", version: str = "1.0.0", tags: List[str] = None):
        self._correlators[name] = PluginInfo(name, correlator_class, description, version, tags or [])
    
    def register_policy(self, name: str, policy_class: Type, description: str = "", version: str = "1.0.0", tags: List[str] = None):
        self._policies[name] = PluginInfo(name, policy_class, description, version, tags or [])
    
    def register_predictor(self, name: str, predictor_class: Type, description: str = "", version: str = "1.0.0", tags: List[str] = None):
        self._predictors[name] = PluginInfo(name, predictor_class, description, version, tags or [])
    
    def register_memory(self, name: str, memory_class: Type, description: str = "", version: str = "1.0.0", tags: List[str] = None):
        self._memory_backends[name] = PluginInfo(name, memory_class, description, version, tags or [])
    
    def register_explainer(self, name: str, explainer_class: Type, description: str = "", version: str = "1.0.0", tags: List[str] = None):
        self._explainers[name] = PluginInfo(name, explainer_class, description, version, tags or [])
    
    def register_risk_engine(self, name: str, risk_class: Type, description: str = "", version: str = "1.0.0", tags: List[str] = None):
        self._risk_engines[name] = PluginInfo(name, risk_class, description, version, tags or [])
    
    # --- Получение ---
    
    def get_detector(self, name: str) -> Optional[Type]:
        return self._detectors.get(name).plugin_class if name in self._detectors else None
    
    def get_correlator(self, name: str) -> Optional[Type]:
        return self._correlators.get(name).plugin_class if name in self._correlators else None
    
    def get_policy(self, name: str) -> Optional[Type]:
        return self._policies.get(name).plugin_class if name in self._policies else None
    
    def get_predictor(self, name: str) -> Optional[Type]:
        return self._predictors.get(name).plugin_class if name in self._predictors else None
    
    def get_memory(self, name: str) -> Optional[Type]:
        return self._memory_backends.get(name).plugin_class if name in self._memory_backends else None
    
    def get_explainer(self, name: str) -> Optional[Type]:
        return self._explainers.get(name).plugin_class if name in self._explainers else None
    
    def get_risk_engine(self, name: str) -> Optional[Type]:
        return self._risk_engines.get(name).plugin_class if name in self._risk_engines else None
    
    # --- Создание ---
    
    def create_detector(self, name: str, config: Optional[Dict] = None) -> Optional[Any]:
        cls = self.get_detector(name)
        return cls(config or {}) if cls else None
    
    def create_correlator(self, name: str, config: Optional[Dict] = None) -> Optional[Any]:
        cls = self.get_correlator(name)
        return cls(config or {}) if cls else None
    
    def create_policy(self, name: str, config: Optional[Dict] = None) -> Optional[Any]:
        cls = self.get_policy(name)
        return cls(config or {}) if cls else None
    
    def create_memory(self, name: str, config: Optional[Dict] = None) -> Optional[Any]:
        cls = self.get_memory(name)
        return cls(**(config or {})) if cls else None
    
    def create_risk_engine(self, name: str, config: Optional[Dict] = None) -> Optional[Any]:
        cls = self.get_risk_engine(name)
        return cls(config or {}) if cls else None
    
    def list_detectors(self) -> List[str]:
        return list(self._detectors.keys())


# Глобальный экземпляр
registry = PluginRegistry()
