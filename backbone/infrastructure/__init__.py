"""
Infrastructure Layer - External dependencies and adapters
"""
# Configuration
from .configuration import get_config

# Logging
from .logging.structured_logger import StructuredLogger

# Event System
from .messaging import (
    KafkaEventBusAdapter,
    RabbitMQEventBusAdapter,
    RedisEventBusAdapter,
    EventBusAdapterFactory
)
from .persistence.event_store import JsonFileEventStore, InMemoryEventStore

# Testing
from .testing import BaseTestCase, MockRepository

__all__ = [
    # Configuration
    "get_config",
    
    # Logging
    "StructuredLogger",
    
    # Event System
    "KafkaEventBusAdapter",
    "RabbitMQEventBusAdapter", 
    "RedisEventBusAdapter",
    "EventBusAdapterFactory",
    "JsonFileEventStore",
    "InMemoryEventStore",
    
    # Testing
    "BaseTestCase",
    "MockRepository"
]