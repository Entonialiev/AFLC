"""
Application Layer Interfaces
Интерфейсы для внешних зависимостей (инфраструктуры)
"""

from typing import Protocol, Optional, List, Any
from aflc.domain.execution import Execution
from aflc.domain.events import DomainEvent


class EventBus(Protocol):
    """Интерфейс шины событий"""
    
    def publish(self, event: DomainEvent) -> None:
        """Синхронная публикация события"""
        ...
    
    async def publish_async(self, event: DomainEvent) -> None:
        """Асинхронная публикация события"""
        ...


class ExecutionRepository(Protocol):
    """Интерфейс репозитория для Execution"""
    
    def save(self, execution: Execution) -> None:
        """Сохранить Execution"""
        ...
    
    def find_by_id(self, execution_id: str) -> Optional[Execution]:
        """Найти Execution по ID"""
        ...
    
    def find_by_status(self, status: str) -> List[Execution]:
        """Найти все Execution с заданным статусом"""
        ...
