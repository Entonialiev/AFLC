"""
Plugin Registry для AFLC
Позволяет регистрировать и получать плагины (детекторы, политики, корреляторы и т.д.)
Версия: 1.0.0
"""

from typing import Dict, Type, Optional, Any, Callable, List
from dataclasses import dataclass, field

from .core import Detector, Correlator, Policy, Predictor, Memory, Explainer


@dataclass
class PluginInfo:
    """Информация о зарегистрированном плагине"""
    name: str
    plugin_class: Type
    description: str = ""
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)


class PluginRegistry:
    """
    Реестр плагинов AFLC.
    
    Позволяет регистрировать и получать плагины различных типов:
    - Detector
    - Correlator
    - Policy
    - Predictor
    - Memory
    - Explainer
    
    Пример:
        registry = PluginRegistry()
        registry.register_detector("my_detector", MyDetector, description="Custom detector")
        
        detector_class = registry.get_detector("my_detector")
        detector = detector_class()
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
        
        self._detectors: Dict[str, PluginInfo] = {}
        self._correlators: Dict[str, PluginInfo] = {}
        self._policies: Dict[str, PluginInfo] = {}
        self._predictors: Dict[str, PluginInfo] = {}
        self._memory_backends: Dict[str, PluginInfo] = {}
        self._explainers: Dict[str, PluginInfo] = {}
        
        # Автоматически регистрируем встроенные плагины
        self._register_builtins()
    
    def _register_builtins(self):
        """Регистрирует встроенные плагины AFLC"""
        from .detectors import RuleDetector, StatisticalDetector
        from .correlator import Correlator
        from .core import DefaultPolicy, SimpleCorrelator
        from .risk import RiskEngine
        from .explainer import Explainer
        from .memory import Memory
        
        # Детекторы
        self.register_detector("rule", RuleDetector, "Rule-based detector (timeout, size, errors)")
        self.register_detector("statistical", StatisticalDetector, "EWMA-based adaptive detector")
        
        # Корреляторы
        self.register_correlator("weighted", Correlator, "Weighted correlation of detector results")
        self.register_correlator("simple", SimpleCorrelator, "Simple max-score correlator")
        
        # Политики
        self.register_policy("default", DefaultPolicy, "Default policy with threshold-based decisions")
        
        # Memory
        self.register_memory("default", Memory, "In-memory storage with JSON persistence")
    
    # --- Регистрация ---
    
    def register_detector(self, name: str, detector_class: Type[Detector], 
                          description: str = "", version: str = "1.0.0", 
                          tags: List[str] = None) -> None:
        """Регистрирует детектор"""
        self._detectors[name] = PluginInfo(name, detector_class, description, version, tags or [])
    
    def register_correlator(self, name: str, correlator_class: Type[Correlator],
                           description: str = "", version: str = "1.0.0",
                           tags: List[str] = None) -> None:
        """Регистрирует коррелятор"""
        self._correlators[name] = PluginInfo(name, correlator_class, description, version, tags or [])
    
    def register_policy(self, name: str, policy_class: Type[Policy],
                       description: str = "", version: str = "1.0.0",
                       tags: List[str] = None) -> None:
        """Регистрирует политику"""
        self._policies[name] = PluginInfo(name, policy_class, description, version, tags or [])
    
    def register_predictor(self, name: str, predictor_class: Type[Predictor],
                          description: str = "", version: str = "1.0.0",
                          tags: List[str] = None) -> None:
        """Регистрирует предиктор"""
        self._predictors[name] = PluginInfo(name, predictor_class, description, version, tags or [])
    
    def register_memory(self, name: str, memory_class: Type[Memory],
                       description: str = "", version: str = "1.0.0",
                       tags: List[str] = None) -> None:
        """Регистрирует бэкенд памяти"""
        self._memory_backends[name] = PluginInfo(name, memory_class, description, version, tags or [])
    
    def register_explainer(self, name: str, explainer_class: Type[Explainer],
                          description: str = "", version: str = "1.0.0",
                          tags: List[str] = None) -> None:
        """Регистрирует объяснитель"""
        self._explainers[name] = PluginInfo(name, explainer_class, description, version, tags or [])
    
    # --- Получение ---
    
    def get_detector(self, name: str) -> Optional[Type[Detector]]:
        """Возвращает класс детектора по имени"""
        info = self._detectors.get(name)
        return info.plugin_class if info else None
    
    def get_correlator(self, name: str) -> Optional[Type[Correlator]]:
        """Возвращает класс коррелятора по имени"""
        info = self._correlators.get(name)
        return info.plugin_class if info else None
    
    def get_policy(self, name: str) -> Optional[Type[Policy]]:
        """Возвращает класс политики по имени"""
        info = self._policies.get(name)
        return info.plugin_class if info else None
    
    def get_predictor(self, name: str) -> Optional[Type[Predictor]]:
        """Возвращает класс предиктора по имени"""
        info = self._predictors.get(name)
        return info.plugin_class if info else None
    
    def get_memory(self, name: str) -> Optional[Type[Memory]]:
        """Возвращает класс бэкенда памяти по имени"""
        info = self._memory_backends.get(name)
        return info.plugin_class if info else None
    
    def get_explainer(self, name: str) -> Optional[Type[Explainer]]:
        """Возвращает класс объяснителя по имени"""
        info = self._explainers.get(name)
        return info.plugin_class if info else None
    
    # --- Списки ---
    
    def list_detectors(self) -> List[str]:
        """Возвращает список имён зарегистрированных детекторов"""
        return list(self._detectors.keys())
    
    def list_correlators(self) -> List[str]:
        """Возвращает список имён зарегистрированных корреляторов"""
        return list(self._correlators.keys())
    
    def list_policies(self) -> List[str]:
        """Возвращает список имён зарегистрированных политик"""
        return list(self._policies.keys())
    
    def list_memory_backends(self) -> List[str]:
        """Возвращает список имён зарегистрированных бэкендов памяти"""
        return list(self._memory_backends.keys())
    
    def list_all(self) -> Dict[str, Dict[str, PluginInfo]]:
        """Возвращает все зарегистрированные плагины по категориям"""
        return {
            "detectors": self._detectors,
            "correlators": self._correlators,
            "policies": self._policies,
            "predictors": self._predictors,
            "memory": self._memory_backends,
            "explainers": self._explainers
        }
    
    # --- Создание экземпляров ---
    
    def create_detector(self, name: str, config: Optional[Dict] = None) -> Optional[Detector]:
        """Создаёт экземпляр детектора по имени"""
        detector_class = self.get_detector(name)
        if detector_class:
            return detector_class(config or {})
        return None
    
    def create_correlator(self, name: str, config: Optional[Dict] = None) -> Optional[Correlator]:
        """Создаёт экземпляр коррелятора по имени"""
        correlator_class = self.get_correlator(name)
        if correlator_class:
            return correlator_class(config or {})
        return None
    
    def create_policy(self, name: str, config: Optional[Dict] = None) -> Optional[Policy]:
        """Создаёт экземпляр политики по имени"""
        policy_class = self.get_policy(name)
        if policy_class:
            return policy_class(config or {})
        return None
    
    def create_memory(self, name: str, config: Optional[Dict] = None) -> Optional[Memory]:
        """Создаёт экземпляр памяти по имени"""
        memory_class = self.get_memory(name)
        if memory_class:
            return memory_class(**(config or {}))
        return None


# --- Глобальный экземпляр ---
registry = PluginRegistry()


# --- УДОБНЫЕ ФУНКЦИИ ДЛЯ ВНЕШНЕГО ИСПОЛЬЗОВАНИЯ ---

def register_plugin(plugin_type: str, name: str, plugin_class: Type, **kwargs) -> None:
    """
    Упрощённая функция для регистрации плагина.
    
    Args:
        plugin_type: "detector", "correlator", "policy", "predictor", "memory", "explainer"
        name: имя плагина
        plugin_class: класс плагина
        **kwargs: дополнительные параметры (description, version, tags)
    """
    if plugin_type == "detector":
        registry.register_detector(name, plugin_class, **kwargs)
    elif plugin_type == "correlator":
        registry.register_correlator(name, plugin_class, **kwargs)
    elif plugin_type == "policy":
        registry.register_policy(name, plugin_class, **kwargs)
    elif plugin_type == "predictor":
        registry.register_predictor(name, plugin_class, **kwargs)
    elif plugin_type == "memory":
        registry.register_memory(name, plugin_class, **kwargs)
    elif plugin_type == "explainer":
        registry.register_explainer(name, plugin_class, **kwargs)
    else:
        raise ValueError(f"Unknown plugin type: {plugin_type}")


# --- ПРИМЕР ---
if __name__ == "__main__":
    print("🔌 Plugin Registry Demo")
    print("=" * 40)
    
    # Получаем глобальный реестр
    reg = PluginRegistry()
    
    # Список зарегистрированных детекторов
    print("\n📋 Зарегистрированные детекторы:")
    for name in reg.list_detectors():
        info = reg._detectors[name]
        print(f"  - {name}: {info.description} (v{info.version})")
    
    # Создаём детектор по имени
    print("\n🔧 Создаём детектор 'rule':")
    detector = reg.create_detector("rule", {"timeout_limit_ms": 3000})
    print(f"  {detector.__class__.__name__} создан с параметрами: {detector.config}")
    
    # Список всех плагинов
    print("\n📦 Все зарегистрированные плагины:")
    all_plugins = reg.list_all()
    for category, plugins in all_plugins.items():
        print(f"  {category}: {', '.join(plugins.keys())}")
