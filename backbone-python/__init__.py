"""
Backbone - Clean Architecture Framework

Python framework following Clean Architecture/Hexagonal Architecture principles.
Provides solid and decoupled foundation for scalable and maintainable applications.

Main features:
- 🎯 Strict layer separation (Domain, Application, Infrastructure, Interfaces)
- 🔢 8-digit error code system by layer
- 🔧 Response builders decoupled from frameworks
- 🎯 Specification Pattern for dynamic filters  
- 📋 Repository Pattern with SQLAlchemy/MongoDB adapters
- 🗄️ Unit of Work Pattern for transactions
- 📊 Structured JSON logging for ELK Stack
- 🧪 Complete testing framework
- ⚙️ Configuration with Pydantic Settings
- 🔄 Event-driven architecture for microservices

Usage example:

    # Event-driven microservices
    from backbone.domain.ports import EventBus, BaseEvent
    from backbone.application.event_handlers import event_handler
    from backbone.infrastructure.messaging import KafkaEventBusAdapter
    
    # Event definition
    event = BaseEvent(
        event_name="UserCreated",
        source="industrial_prom",
        data={"user_id": 123, "email": "user@example.com"},
        microservice="users-service",
        functionality="create-user"
    )
    
    # Event handler with automatic retry
    @event_handler("UserCreated")
    async def handle_user_created(event: BaseEvent):
        print(f"Processing user: {event.data['user_id']}")
    
    # Publish event (adapter determines if Kafka/RabbitMQ/Redis)
    await event_bus.publish(event)

For more information: https://github.com/backbone/backbone
"""

# Framework version
__version__ = "1.0.0"
__author__ = "Backbone Framework Team"
__license__ = "MIT"

# === DOMAIN LAYER EXPORTS ===
from .domain.exceptions import (
    BaseKernelException,
    DomainException,
    BusinessRuleViolationException,
    InvalidEntityStateException,
    InvalidValueObjectException
)

# === EVENT SYSTEM EXPORTS ===
from .domain.ports.event_bus import (
    EventBus,
    EventStore,
    BaseEvent,
    DomainEvent,
    IntegrationEvent,
    SystemEvent,
    EventHandler
)

from .domain.repositories import (
    IRepository,
    IReadOnlyRepository,
    IUnitOfWork
)

from .domain.specifications import (
    Specification,
    FilterSpecification,
    CompositeSpecification,
    AndSpecification,
    OrSpecification,
    NotSpecification,
    EqualSpecification,
    NotEqualSpecification,
    LessThanSpecification,
    LessThanOrEqualSpecification,
    GreaterThanSpecification,
    GreaterThanOrEqualSpecification,
    LikeSpecification,
    InSpecification,
    BetweenSpecification,
    IsNullSpecification,
    IsNotNullSpecification,
    FilterParser,
    MultipleSortSpecification,
    SortSpecification,
    SortDirection
)

# === APPLICATION LAYER EXPORTS ===
from .application.exceptions import (
    ApplicationException,
    UseCaseException,
    ValidationException,
    AuthorizationException,
    ResourceNotFoundException,
    ResourceConflictException
)

# === INFRASTRUCTURE LAYER EXPORTS ===
from .infrastructure.exceptions import (
    InfrastructureException,
    DatabaseException,
    ExternalServiceException,
    ConfigurationException
)

# === INFRASTRUCTURE MESSAGING ===
from .infrastructure.messaging import (
    KafkaEventBusAdapter,
    RabbitMQEventBusAdapter,
    RedisEventBusAdapter,
    EventBusAdapterFactory
)

from .infrastructure.persistence.event_store import (
    JsonFileEventStore,
    InMemoryEventStore
)

from .infrastructure.events.base_event import (
    EventMetadata
)

# === APPLICATION EVENT HANDLERS ===
from .application.event_handlers import (
    event_handler,
    RetryPolicy,
    EventHandlerRegistry
)

from .infrastructure.logging import (
    StructuredLogger,
    ConcreteStructuredLogger,
    LoggerFactory,
    JSONFormatter,
    ConsoleFormatter,
    CompactJSONFormatter,
    FileFormatter,
    LogContext
)

from .infrastructure.configuration import (
    BaseAppConfig,
    get_config,
    load_config,
    get_feature_flags
)

from .infrastructure.testing import (
    BaseTestCase,
    BaseAsyncTestCase,
    MockRepository,
    BaseFixtureFactory,
    TestDataBuilder
)

# Persistence - exportación condicional
try:
    from .infrastructure.persistence import (
        IUnitOfWork,
        BaseUnitOfWork,
        get_available_adapters,
        is_sqlalchemy_adapter_available,
        is_mongodb_adapter_available
    )
    _persistence_available = True
except ImportError:
    _persistence_available = False

# === INTERFACES LAYER EXPORTS ===
from .interfaces.exceptions import (
    PresentationException,
    RequestValidationException,
    HttpException,
    SerializationException,
    DeserializationException
)

from .interfaces.response_builders import (
    ProcessResponseBuilder,
    SimpleObjectResponseBuilder,
    PaginatedResponseBuilder,
    ErrorResponseBuilder
)

# === PUBLIC API ===
__all__ = [
    # Version info
    "__version__",
    "__author__", 
    "__license__",
    
    # Domain Layer - Events
    "EventBus",
    "EventStore",
    "BaseEvent",
    "DomainEvent",
    "IntegrationEvent",
    "SystemEvent",
    "EventHandler",
    "EventMetadata",
    
    # Domain Layer - Core
    "BaseKernelException",
    "DomainException",
    "BusinessRuleViolationException",
    "InvalidEntityStateException", 
    "InvalidValueObjectException",
    "IRepository",
    "IReadOnlyRepository",
    "IUnitOfWork",
    "Specification",
    "FilterSpecification",
    "CompositeSpecification", 
    "AndSpecification",
    "OrSpecification",
    "NotSpecification",
    "EqualSpecification",
    "NotEqualSpecification",
    "LessThanSpecification",
    "LessThanOrEqualSpecification",
    "GreaterThanSpecification",
    "GreaterThanOrEqualSpecification",
    "LikeSpecification",
    "InSpecification",
    "BetweenSpecification",
    "IsNullSpecification",
    "IsNotNullSpecification",
    "FilterParser",
    "MultipleSortSpecification",
    "SortSpecification",
    "SortDirection",
    
    # Application Layer
    "ApplicationException",
    "UseCaseException",
    "ValidationException", 
    "AuthorizationException",
    "ResourceNotFoundException",
    "ResourceConflictException",
    "event_handler",
    "RetryPolicy",
    "EventHandlerRegistry",
    
    # Infrastructure Layer - Core
    "InfrastructureException", 
    "DatabaseException",
    "ExternalServiceException",
    "ConfigurationException",
    "StructuredLogger",
    "ConcreteStructuredLogger",
    "LoggerFactory",
    "JSONFormatter",
    "ConsoleFormatter",
    "CompactJSONFormatter",
    "FileFormatter",
    "LogContext",
    "BaseAppConfig",
    "get_config",
    "load_config",
    "get_feature_flags",
    "BaseTestCase",
    "BaseAsyncTestCase", 
    "MockRepository",
    "BaseFixtureFactory",
    "TestDataBuilder",
    
    # Infrastructure Layer - Messaging
    "KafkaEventBusAdapter",
    "RabbitMQEventBusAdapter",
    "RedisEventBusAdapter",
    "EventBusAdapterFactory",
    "JsonFileEventStore",
    "InMemoryEventStore",
    
    # Interfaces Layer
    "PresentationException",
    "RequestValidationException",
    "HttpException",
    "SerializationException", 
    "DeserializationException",
    "ProcessResponseBuilder",
    "SimpleObjectResponseBuilder",
    "PaginatedResponseBuilder", 
    "ErrorResponseBuilder"
]

# Agregar persistence exports si está disponible
if _persistence_available:
    __all__.extend([
        "IUnitOfWork",
        "BaseUnitOfWork", 
        "get_available_adapters",
        "is_sqlalchemy_adapter_available",
        "is_mongodb_adapter_available"
    ])

# === UTILITY FUNCTIONS ===

def get_version() -> str:
    """Retorna versión del framework."""
    return __version__

def get_available_features() -> dict:
    """
    Retorna características disponibles del framework.
    
    Returns:
        Diccionario con features disponibles
    """
    features = {
        "domain_layer": True,
        "application_layer": True,
        "infrastructure_layer": True,
        "interfaces_layer": True,
        "exceptions_system": True,
        "specifications": True,
        "response_builders": True,
        "structured_logging": True,
        "configuration_system": True,
        "testing_framework": True,
        "persistence_layer": _persistence_available
    }
    
    if _persistence_available:
        from .infrastructure.persistence import get_available_adapters
        adapters = get_available_adapters()
        features.update({
            "sqlalchemy_adapter": "sqlalchemy" in adapters,
            "mongodb_adapter": "mongodb" in adapters
        })
    
    return features

def print_banner():
    """Imprime banner informativo del framework."""
    banner = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    🏗️  BACKBONE - CLEAN ARCHITECTURE FRAMEWORK                              ║
║                                                                              ║
║    Version: {__version__:<10} | License: {__license__:<10} | Python 3.8+     ║
║                                                                              ║
║    🎯 Clean Architecture & Hexagonal Architecture                           ║
║    🔢 8-digit error codes by layer                                          ║
║    🔧 Framework-agnostic response builders                                  ║
║    🎯 Dynamic filtering with Specification Pattern                          ║
║    📋 Repository Pattern with multiple adapters                             ║
║    🗄️ Unit of Work Pattern for transactions                                 ║
║    📊 Structured JSON logging for ELK Stack                                 ║
║    🧪 Complete testing framework                                            ║
║    ⚙️ Type-safe configuration with Pydantic                                 ║
║    🗄️ Persistence layer with multiple adapters                              ║
║    📖 Docs: https://docs.backbone-framework.com                             ║
║    🐛 Issues: https://github.com/backbone/backbone/issues                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """.strip()
    
    print(banner)