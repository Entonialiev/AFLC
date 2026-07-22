"""
AFLC Interfaces
Version: 2.0.0 (with ABC)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

from .models import ActionContext, Detection, Decision, RiskScore


class Detector(ABC):
    """Синхронный детектор"""
    @abstractmethod
    def detect(self, context: ActionContext) -> Optional[Detection]:
        """Анализирует контекст и возвращает Detection или None"""
        pass


class AsyncDetector(ABC):
    """Асинхронный детектор"""
    @abstractmethod
    async def detect(self, context: ActionContext) -> Optional[Detection]:
        """Анализирует контекст и возвращает Detection или None"""
        pass


class Correlator(ABC):
    @abstractmethod
    def correlate(self, detections: List[Detection]) -> Optional[Detection]:
        """Объединяет детекции в одну"""
        pass


class Predictor(ABC):
    @abstractmethod
    def predict(self, context: ActionContext, horizon: int = 10) -> Dict[str, float]:
        """Прогнозирует будущие аномалии"""
        pass


class Policy(ABC):
    """Синхронная политика"""
    @abstractmethod
    def decide(self, context: ActionContext, detection: Optional[Detection], 
               risk: RiskScore) -> Decision:
        """Принимает решение на основе контекста, детекции и риска"""
        pass


class AsyncPolicy(ABC):
    """Асинхронная политика"""
    @abstractmethod
    async def decide(self, context: ActionContext, detection: Optional[Detection], 
                     risk: RiskScore) -> Decision:
        """Принимает решение на основе контекста, детекции и риска"""
        pass


class Explainer(ABC):
    @abstractmethod
    def explain(self, context: ActionContext, detection: Optional[Detection],
                decision: Decision, risk: Optional[RiskScore]) -> str:
        """Генерирует человекочитаемое объяснение"""
        pass


class Memory(ABC):
    @abstractmethod
    def store(self, context: ActionContext, detection: Optional[Detection],
              decision: Decision, risk: RiskScore) -> None:
        """Сохраняет запись в память"""
        pass


class HistoryBackend(ABC):
    """Бэкенд для хранения истории"""
    @abstractmethod
    def add(self, record: Dict[str, Any]) -> None:
        """Добавляет запись"""
        pass
    
    @abstractmethod
    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Возвращает последние записи"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Очищает историю"""
        pass


class Plugin(ABC):
    """Базовый класс для всех плагинов AFLC"""
    
    @abstractmethod
    def initialize(self) -> None:
        """Инициализация плагина (вызывается при регистрации)"""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Завершение работы плагина (вызывается при удалении)"""
        pass
