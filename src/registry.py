"""
Plugin Registry для AFLC
"""

from typing import Dict, Type, Any
from .core import Detector, Correlator, Policy, Predictor, Memory


class PluginRegistry:
    """Реестр плагинов AFLC"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.detectors = {}
            cls._instance.correlators = {}
            cls._instance.policies = {}
            cls._instance.predictors = {}
            cls._instance.memory_backends = {}
        return cls._instance
    
    def register_detector(self, name: str, detector_class: Type[Detector]):
        self.detectors[name] = detector_class
    
    def get_detector(self, name: str) -> Type[Detector]:
        return self.detectors.get(name)
    
    # Аналогично для других типов
