"""
AFLC Bootstrap — центральная точка создания и настройки приложения
"""

from typing import Optional, Dict, Any
from pathlib import Path

from .application.engine import ExecutionEngine
from .application.interfaces import EventBus, ExecutionRepository
from .infrastructure.event_bus.memory import MemoryEventBus
from .infrastructure.storage.sqlite import SQLiteStorage
from .infrastructure.repositories.execution_repository import SQLiteExecutionRepository
from .infrastructure.storage.memory import MemoryStorage


class AFLC:
    """
    Главная точка входа в AFLC.
    Создаёт и связывает все компоненты.
    """

    def __init__(
        self,
        db_path: str = "aflc.db",
        use_sqlite: bool = True,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Инициализирует AFLC с заданной конфигурацией.

        Args:
            db_path: Путь к файлу базы данных SQLite
            use_sqlite: Использовать SQLite (True) или in-memory (False)
            config: Дополнительная конфигурация
        """
        self.config = config or {}
        self.db_path = db_path
        self.use_sqlite = use_sqlite

        # Создаём компоненты
        self.event_bus = self._create_event_bus()
        self.repository = self._create_repository()
        self.storage = self._create_storage()

        # Создаём Engine
        self.engine = ExecutionEngine(
            repository=self.repository,
            event_bus=self.event_bus
        )

    def _create_event_bus(self) -> EventBus:
        """Создаёт Event Bus."""
        return MemoryEventBus()

    def _create_repository(self) -> ExecutionRepository:
        """Создаёт репозиторий."""
        if self.use_sqlite:
            return SQLiteExecutionRepository(db_path=self.db_path)
        else:
            # In-memory repository (для тестов)
            return InMemoryExecutionRepository()

    def _create_storage(self):
        """Создаёт хранилище."""
        if self.use_sqlite:
            return SQLiteStorage(db_path=self.db_path)
        else:
            return MemoryStorage()

    def get_engine(self) -> ExecutionEngine:
        """Возвращает ExecutionEngine."""
        return self.engine

    def get_event_bus(self) -> EventBus:
        """Возвращает Event Bus."""
        return self.event_bus

    def get_repository(self) -> ExecutionRepository:
        """Возвращает Repository."""
        return self.repository

    def get_storage(self):
        """Возвращает Storage."""
        return self.storage


# --- In-memory Repository (для тестов) ---

class InMemoryExecutionRepository(ExecutionRepository):
    """In-memory implementation of ExecutionRepository."""

    def __init__(self):
        self._executions: Dict[str, Execution] = {}

    def save(self, execution: Execution) -> None:
        self._executions[execution.execution_id] = execution

    def find_by_id(self, execution_id: str) -> Optional[Execution]:
        return self._executions.get(execution_id)

    def find_by_status(self, status: str) -> List[Execution]:
        return [e for e in self._executions.values() if e.status.value == status]

    def find_all(self) -> List[Execution]:
        return list(self._executions.values())


# --- Упрощённый API ---

def create_aflc(db_path: str = "aflc.db", use_sqlite: bool = True) -> AFLC:
    """
    Упрощённая функция для создания экземпляра AFLC.

    Example:
        aflc = create_aflc("my_app.db")
        engine = aflc.get_engine()
        execution = engine.submit_action(...)
    """
    return AFLC(db_path=db_path, use_sqlite=use_sqlite)
