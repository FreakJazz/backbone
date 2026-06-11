"""
Events Module - Complete event handling system for microservices
"""
from .base_event import (
    BaseEvent,
    EventMetadata,
    DomainEvent,
    IntegrationEvent,
    SystemEvent
)
from .event_store import (
    IEventStore,
    JsonFileEventStore,
    InMemoryEventStore
)
from .event_bus import (
    IEventPublisher,
    IEventSubscriber,
    EventBusWithAdapters,
    InMemoryEventBus,  # Legacy alias
    EventBusFactory,
    EventHandler,
    event_handler,
    EventHandlerRegistry
)
from .event_adapters import (
    RabbitMQEventAdapter,
    RedisEventAdapter,
    EventAdapterFactory
)

__all__ = [
    # Base events
    "BaseEvent",
    "EventMetadata",
    "DomainEvent",
    "IntegrationEvent",
    "SystemEvent",
    
    # Event storage
    "IEventStore",
    "JsonFileEventStore",
    "InMemoryEventStore",
    
    # Event bus
    "IEventPublisher",
    "IEventSubscriber",
    "EventBusWithAdapters",
    "InMemoryEventBus",
    "EventBusFactory",
    "EventHandler",
    "event_handler",
    "EventHandlerRegistry",
    
    # External adapters
    "RabbitMQEventAdapter",
    "RedisEventAdapter",
    "EventAdapterFactory"
]