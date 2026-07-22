"""
Event Bus for AFLC
Позволяет компонентам обмениваться событиями без прямой связанности
"""

from dataclasses import dataclass
from typing import Dict, List, Callable, Any, Optional
import asyncio


@dataclass
class Event:
    """Базовое событие"""
    name: str
    data: Dict[str, Any]


class EventBus:
    """
    Шина событий для слабосвязанной архитектуры.
    
    Пример:
        bus = EventBus()
        
        @bus.subscribe("user_logged_in")
        def on_login(event: Event):
            print(f"User {event.data['user']} logged in")
        
        bus.publish(Event("user_logged_in", {"user": "admin"}))
    """
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_name: str):
        """
        Декоратор для подписки на события.
        
        Usage:
            @event_bus.subscribe("action_started")
            def handler(event: Event):
                print(event.data)
        """
        def wrapper(func: Callable):
            if event_name not in self._listeners:
                self._listeners[event_name] = []
            self._listeners[event_name].append(func)
            return func
        return wrapper
    
    def add_listener(self, event_name: str, listener: Callable):
        """Добавляет слушатель события"""
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(listener)
    
    def remove_listener(self, event_name: str, listener: Callable):
        """Удаляет слушатель события"""
        if event_name in self._listeners:
            self._listeners[event_name] = [l for l in self._listeners[event_name] if l != listener]
    
    def publish(self, event: Event) -> None:
        """Синхронная публикация события"""
        for listener in self._listeners.get(event.name, []):
            try:
                listener(event)
            except Exception as e:
                print(f"Event listener error: {e}")
    
    async def publish_async(self, event: Event) -> None:
        """Асинхронная публикация события"""
        for listener in self._listeners.get(event.name, []):
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event)
                else:
                    listener(event)
            except Exception as e:
                print(f"Async event listener error: {e}")
    
    def clear(self):
        """Очищает все подписки"""
        self._listeners.clear()


# --- ПРИМЕР ---
if __name__ == "__main__":
    bus = EventBus()
    
    @bus.subscribe("test_event")
    def test_handler(event: Event):
        print(f"Handled: {event.data}")
    
    bus.publish(Event("test_event", {"message": "Hello"}))
