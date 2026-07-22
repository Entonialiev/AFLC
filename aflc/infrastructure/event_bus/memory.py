"""
In-memory Event Bus implementation
"""

import asyncio
from typing import Dict, List, Callable, Any, Optional, Union
from dataclasses import dataclass
import logging

from aflc.domain.events import DomainEvent
from aflc.domain.enums import EventType


logger = logging.getLogger(__name__)


@dataclass
class Subscription:
    """Subscription to an event."""
    event_type: Union[str, EventType]
    handler: Optional[Callable[[DomainEvent], Any]] = None
    async_handler: Optional[Callable[[DomainEvent], Any]] = None


class MemoryEventBus:
    """
    In-memory event bus implementation.
    Supports both sync and async handlers.
    """

    def __init__(self):
        self._subscriptions: Dict[str, List[Subscription]] = {}

    def _get_key(self, event_type: Union[str, EventType]) -> str:
        """Convert event type to string key."""
        if isinstance(event_type, EventType):
            return event_type.value
        return event_type

    def subscribe(
        self,
        event_type: Union[str, EventType],
        handler: Optional[Callable[[DomainEvent], Any]] = None,
        async_handler: Optional[Callable[[DomainEvent], Any]] = None
    ) -> None:
        """Subscribe to an event type."""
        if not handler and not async_handler:
            raise ValueError("Either handler or async_handler must be provided")

        key = self._get_key(event_type)
        if key not in self._subscriptions:
            self._subscriptions[key] = []

        self._subscriptions[key].append(
            Subscription(
                event_type=event_type,
                handler=handler,
                async_handler=async_handler
            )
        )

    def unsubscribe(self, event_type: Union[str, EventType], handler: Callable) -> None:
        """Unsubscribe from an event type."""
        key = self._get_key(event_type)
        if key in self._subscriptions:
            self._subscriptions[key] = [
                s for s in self._subscriptions[key]
                if s.handler != handler and s.async_handler != handler
            ]

    def publish(self, event: DomainEvent) -> None:
        """Publish an event synchronously."""
        key = self._get_key(event.event_type)
        if key not in self._subscriptions:
            return

        for subscription in self._subscriptions[key]:
            try:
                if subscription.handler:
                    subscription.handler(event)
                elif subscription.async_handler:
                    # If only async handler is available, we can't call it synchronously
                    logger.warning(
                        f"Async handler for {key} cannot be called synchronously"
                    )
            except Exception as e:
                logger.error(f"Error in event handler: {e}")

    async def publish_async(self, event: DomainEvent) -> None:
        """Publish an event asynchronously."""
        key = self._get_key(event.event_type)
        if key not in self._subscriptions:
            return

        tasks = []
        for subscription in self._subscriptions[key]:
            if subscription.async_handler:
                tasks.append(subscription.async_handler(event))
            elif subscription.handler:
                # Run sync handler in executor
                loop = asyncio.get_event_loop()
                tasks.append(
                    loop.run_in_executor(None, subscription.handler, event)
                )

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def clear(self) -> None:
        """Clear all subscriptions."""
        self._subscriptions.clear()
