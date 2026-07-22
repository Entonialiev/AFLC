"""
In-memory Event Bus implementation
"""

import asyncio
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
import logging

from aflc.domain.events import DomainEvent


logger = logging.getLogger(__name__)


@dataclass
class Subscription:
    """Subscription to an event."""
    event_type: str
    handler: Callable[[DomainEvent], Any]
    async_handler: Optional[Callable[[DomainEvent], Any]] = None


class MemoryEventBus:
    """
    In-memory event bus implementation.
    Supports both sync and async handlers.
    """

    def __init__(self):
        self._subscriptions: Dict[str, List[Subscription]] = {}

    def subscribe(
        self,
        event_type: str,
        handler: Optional[Callable[[DomainEvent], Any]] = None,
        async_handler: Optional[Callable[[DomainEvent], Any]] = None
    ) -> None:
        """Subscribe to an event type."""
        if not handler and not async_handler:
            raise ValueError("Either handler or async_handler must be provided")

        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []

        self._subscriptions[event_type].append(
            Subscription(
                event_type=event_type,
                handler=handler,
                async_handler=async_handler
            )
        )

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._subscriptions:
            self._subscriptions[event_type] = [
                s for s in self._subscriptions[event_type]
                if s.handler != handler and s.async_handler != handler
            ]

    def publish(self, event: DomainEvent) -> None:
        """Publish an event synchronously."""
        if event.event_type.value not in self._subscriptions:
            return

        for subscription in self._subscriptions[event.event_type.value]:
            try:
                if subscription.handler:
                    subscription.handler(event)
                elif subscription.async_handler:
                    # If only async handler is available, we can't call it synchronously
                    logger.warning(
                        f"Async handler for {event.event_type.value} cannot be called synchronously"
                    )
            except Exception as e:
                logger.error(f"Error in event handler: {e}")

    async def publish_async(self, event: DomainEvent) -> None:
        """Publish an event asynchronously."""
        if event.event_type.value not in self._subscriptions:
            return

        tasks = []
        for subscription in self._subscriptions[event.event_type.value]:
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
