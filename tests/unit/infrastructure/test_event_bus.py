"""
Tests for Event Bus
"""

import pytest
import asyncio

from aflc.domain.events import DomainEvent
from aflc.domain.enums import EventType
from aflc.infrastructure.event_bus.memory import MemoryEventBus


class TestMemoryEventBus:
    def test_subscribe_and_publish_sync(self):
        bus = MemoryEventBus()
        called = False

        def handler(event):
            nonlocal called
            called = True

        bus.subscribe(EventType.EXECUTION_CREATED, handler=handler)
        event = DomainEvent(event_type=EventType.EXECUTION_CREATED)
        bus.publish(event)

        assert called is True

    def test_subscribe_and_publish_async(self):
        bus = MemoryEventBus()
        called = False

        async def async_handler(event):
            nonlocal called
            called = True

        bus.subscribe(EventType.EXECUTION_CREATED, async_handler=async_handler)
        event = DomainEvent(event_type=EventType.EXECUTION_CREATED)

        asyncio.run(bus.publish_async(event))
        assert called is True

    def test_multiple_handlers(self):
        bus = MemoryEventBus()
        called1 = False
        called2 = False

        def handler1(event):
            nonlocal called1
            called1 = True

        def handler2(event):
            nonlocal called2
            called2 = True

        bus.subscribe(EventType.EXECUTION_CREATED, handler=handler1)
        bus.subscribe(EventType.EXECUTION_CREATED, handler=handler2)

        event = DomainEvent(event_type=EventType.EXECUTION_CREATED)
        bus.publish(event)

        assert called1 is True
        assert called2 is True

    def test_unsubscribe(self):
        bus = MemoryEventBus()
        called = False

        def handler(event):
            nonlocal called
            called = True

        bus.subscribe(EventType.EXECUTION_CREATED, handler=handler)
        bus.unsubscribe(EventType.EXECUTION_CREATED, handler)

        event = DomainEvent(event_type=EventType.EXECUTION_CREATED)
        bus.publish(event)

        assert called is False

    def test_clear(self):
        bus = MemoryEventBus()
        called = False

        def handler(event):
            nonlocal called
            called = True

        bus.subscribe(EventType.EXECUTION_CREATED, handler=handler)
        bus.clear()

        event = DomainEvent(event_type=EventType.EXECUTION_CREATED)
        bus.publish(event)

        assert called is False

    def test_subscribe_with_string(self):
        """Test subscribing with string event type."""
        bus = MemoryEventBus()
        called = False

        def handler(event):
            nonlocal called
            called = True

        bus.subscribe("execution_created", handler=handler)
        event = DomainEvent(event_type=EventType.EXECUTION_CREATED)
        bus.publish(event)

        assert called is True
