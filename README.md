# Backbone - Clean Architecture Framework

## 🏗️ Hexagonal/Clean Architecture with Event-Driven Microservices

Python framework designed following Clean Architecture principles and enterprise design patterns. Provides a solid and decoupled foundation for building scalable and maintainable applications with **event-driven microservices communication**.

## 📋 Table of Contents

- [Architecture](#architecture)
- [Main Features](#main-features)
- [Event-Driven Architecture](#event-driven-architecture)
- [Installation](#installation)
- [Usage Guide](#usage-guide)
- [Examples](#examples)
- [Testing](#testing)
- [Configuration](#configuration)
- [Contributing](#contributing)

## 🏛️ Architecture

### Layer Structure

```text
backbone/
├── domain/                    # 🎯 Domain Layer (Business core)
│   ├── exceptions/           # Domain exceptions (11xxxxxx)
│   ├── ports/               # Contracts for external dependencies (NEW)
│   │   ├── event_bus.py     # EventBus & EventStore contracts
│   │   └── repository.py    # Repository contracts
│   └── specifications/      # Specifications and dynamic filters
├── application/              # 🔧 Application Layer (Use cases)
│   ├── exceptions/          # Application exceptions (10xxxxxx)
│   └── event_handlers/      # Event handler decorators & registry (NEW)
├── infrastructure/          # 🛠️ Infrastructure Layer (Technical details)
│   ├── configuration/       # Configuration system with Pydantic
│   ├── exceptions/         # Infrastructure exceptions (12xxxxxx)
│   ├── logging/           # Structured logging system (JSON/ELK)
│   ├── messaging/         # Event bus adapters (NEW)
│   │   ├── kafka_adapter.py      # Apache Kafka adapter
│   │   ├── rabbitmq_adapter.py   # RabbitMQ adapter
│   │   └── redis_adapter.py      # Redis Pub/Sub adapter
│   ├── persistence/       # Persistence adapters
│   │   ├── event_store.py # Event storage implementations (NEW)
│   │   └── repositories/  # SQLAlchemy/MongoDB adapters
│   └── testing/          # Testing framework
└── interfaces/             # 🌐 Interfaces Layer (Presentation)
    ├── exceptions/         # Presentation exceptions (13xxxxxx)
    └── response_builders/  # Decoupled response builders
```

### Fundamental Principles

- **🎯 Separation of Concerns**: Each layer has a specific responsibility
- **🔄 Dependency Inversion**: Dependencies point inward (toward domain)
- **🚫 Decoupling**: Framework-agnostic, doesn't depend on FastAPI/Django/etc
- **🧪 Testable**: Design that facilitates unit testing and mocking
- **📦 Reusable**: Independent package for multiple projects
- **🔄 Event-Driven**: Microservices communication through events

## ✨ Main Features

### 🚀 **NEW: Event-Driven Microservices Architecture**

Complete event system with hexagonal architecture for microservices communication:

```python
from backbone.domain.ports import EventBus, BaseEvent
from backbone.application.event_handlers import event_handler
from backbone.infrastructure.messaging import KafkaEventBusAdapter

# Define events with standardized format
event = BaseEvent(
    event_name="UserCreated",
    source="industrial_prom",
    data={"user_id": 123, "email": "user@example.com"},
    microservice="users-service",
    functionality="create-user"
)

# Handler with automatic retry, logging, and error handling
@event_handler("UserCreated")
async def handle_user_created(event: BaseEvent):
    print(f"Processing user: {event.data['user_id']}")

# Publisher (adapter choice at infrastructure level)
event_bus = KafkaEventBusAdapter("localhost:9092")
await event_bus.publish(event)
```

**Features:**
- ✅ **Hexagonal Architecture**: Domain doesn't depend on Kafka/RabbitMQ/Redis
- ✅ **Multiple Adapters**: Kafka, RabbitMQ, Redis support
- ✅ **Automatic Retry**: Configurable exponential backoff
- ✅ **Event Validation**: Automatic format validation
- ✅ **Status Tracking**: published/failed/processed states
- ✅ **Structured Logging**: Automatic event lifecycle logging
- ✅ **Event Store**: JSON-based persistence with indexing

### 🔢 8-Digit Exception System with Error Codes

Each layer has its error code range:

```python
from backbone.domain.exceptions import DomainException
from backbone.application.exceptions import ApplicationException

# Domain exception (11xxxxxx)
raise DomainException(
    message="User age must be between 18 and 120",
    error_code="11001001",  # 11 = Domain layer
    context={"provided_age": 15}
)

# Application exception (10xxxxxx)  
raise ApplicationException(
    message="Failed to create user",
    error_code="10001001",  # 10 = Application layer
    operation="create_user"
)

# Infrastructure exception (12xxxxxx)
raise InfrastructureException(
    message="Event handler failed after 3 attempts",
    error_code="12008007", # 12 = Infrastructure layer
    operation="execute_kafka_handler"
)
```

### 🔧 Decoupled Response Builders

Builders that return dictionaries, not framework-specific objects:

```python
from backbone.interfaces.response_builders import (
    ProcessResponseBuilder,
    PaginatedResponseBuilder,
    ErrorResponseBuilder
)

# Successful response
response = ProcessResponseBuilder.success(
    data=user_dict,
    message="User created successfully",
    metadata={"operation": "create_user"}
)

# Paginated response
paginated_response = PaginatedResponseBuilder.from_repository_result(
    entities=users,
    total=total_count,
    page=0,
    page_size=20
)

# Error response
error_response = ErrorResponseBuilder.from_exception(exception)
```

### 🎯 Specification Pattern for Dynamic Filters

Advanced filtering system with operators and logical connectors:

```python
from backbone.domain.specifications import FilterParser

# Parse query parameters to specifications
filter_parser = FilterParser()
spec = filter_parser.parse_filters({
    "name__like": "john",
    "age__gte": "18",
    "status__in": "active,pending"
})

# Repository usage
users = await user_repository.find_by_specification(spec)

# Complex specifications
complex_spec = (
    FilterSpecification("age", "gte", 18)
    .and_(FilterSpecification("status", "eq", "active"))
    .or_(FilterSpecification("role", "eq", "admin"))
)
```

### 📋 Repository Pattern with Multiple Adapters

Unified contracts with implementations for different databases:

```python
from backbone.infrastructure.persistence import (
    SQLAlchemyRepository,
    MongoDBRepository
)

# SQLAlchemy
class UserRepository(SQLAlchemyRepository[User, str]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel, User)

# MongoDB  
class UserRepository(MongoDBRepository[User, str]):
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, "users", User)

# Both implement the same interface
users = await repository.find_by_specification(spec)
```

### 🗄️ Unit of Work Pattern

Transaction coordination across multiple repositories:

```python
from backbone.infrastructure.persistence import SQLAlchemyUnitOfWork

async with SQLAlchemyUnitOfWork(session) as uow:
    # Register changes
    uow.register_new(new_user)
    uow.register_dirty(updated_user)  
    uow.register_removed(deleted_user)
    
    # Atomic commit
    await uow.commit()
```

### 📊 Structured Logging for ELK Stack

JSON logging system with request context:

```python
from backbone.infrastructure.logging import LoggerFactory

logger = LoggerFactory.create_logger("user_service")

await logger.info(
    message="User created successfully",
    context={
        "user_id": user.id,
        "operation": "create_user",
        "duration_ms": 245
    }
)

# JSON Output for ELK
# {
#   "timestamp": "2024-01-15T10:30:00Z",
#   "level": "INFO", 
#   "message": "User created successfully",
#   "rid": "req_12345",
#   "trace_id": "trace_67890",
#   "context": {...}
# }
```

### 🧪 Complete Testing Framework

Test cases with Clean Architecture utilities:

```python
from backbone.infrastructure.testing import (
    BaseTestCase,
    MockRepository,
    BaseFixtureFactory
)

class UserServiceTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.mock_user_repo = self.create_mock_repository(User)
        self.user_service = UserService(self.mock_user_repo)
    
    async def test_create_user_success(self):
        # Arrange
        user_data = {"name": "John", "email": "john@example.com"}
        
        # Act
        result = await self.user_service.create_user(user_data)
        
        # Assert
        self.mock_user_repo.save.assert_called_once()
        self.assertEqual(result.name, "John")
    
    async def test_create_user_validation_error(self):
        # Test exception with specific error code
        with self.assertRaisesDomainException("11001001"):
            await self.user_service.create_user({"age": 15})
```

### ⚙️ Configuration with Pydantic Settings

Type-safe configuration system with validation:

```python
from backbone.infrastructure.configuration import config

# Type-safe configuration access
database_config = config.get_database_config()
api_config = config.get_api_config() 
logging_config = config.get_logging_config()

# Automatic validation by environment
if config.is_production:
    # Production-specific configuration
    pass
```

## 🔄 Event-Driven Architecture

### Event Format Standard

All events follow a standardized format for microservices communication:

```json
{
  "eventId": "uuid",
  "eventName": "UserCreated",
  "eventVersion": "1.0",
  "source": "industrial_prom",
  "timestamp": "2024-02-21T10:30:00Z",
  "data": {
    "user_id": 123,
    "email": "user@example.com"
  },
  "metadata": {
    "microservice": "users-service",
    "functionality": "create-user",
    "correlationId": "uuid"
  },
  "createdAt": "2024-02-21T10:30:00Z",
  "updatedAt": "2024-02-21T10:30:00Z", 
  "status": "published"
}
```

### Domain Layer - Pure Business Logic

The domain layer defines event contracts without external dependencies:

```python
from backbone.domain.ports.event_bus import EventBus, BaseEvent

# Business service remains pure
class UserService:
    def __init__(self, event_bus: EventBus):
        self._event_bus = event_bus  # Abstract contract
    
    async def create_user(self, user_data: dict):
        # Business logic
        user = User.create(user_data)
        
        # Publish domain event (no knowledge of Kafka/RabbitMQ)
        event = BaseEvent(
            event_name="UserCreated",
            source="industrial_prom",
            data={"user_id": user.id, "email": user.email},
            microservice="users-service",
            functionality="create-user"
        )
        
        await self._event_bus.publish(event)
        return user
```

### Application Layer - Event Handlers

Event handlers with automatic retry, validation, and logging:

```python
from backbone.application.event_handlers import event_handler, RetryPolicy
from backbone.domain.ports.event_bus import BaseEvent

# Configure retry policy
retry_policy = RetryPolicy(
    max_attempts=3,
    delay_seconds=1,
    exponential_backoff=True
)

@event_handler("UserCreated", retry_policy=retry_policy)
async def handle_user_created(event: BaseEvent):
    """
    Automatic features:
    - Event validation
    - Error handling with proper exceptions  
    - Configurable retry with exponential backoff
    - Structured logging (event_name, source, event_id, status)
    - Status tracking (published/failed/processed)
    """
    user_id = event.data["user_id"]
    
    # Business logic - if this fails, automatic retry
    await send_welcome_email(user_id)
    await create_user_profile(user_id)
    
    # Event automatically marked as processed on success

@event_handler("UserCreated")  # Simple handler without retry
async def update_analytics(event: BaseEvent):
    await analytics_service.increment_user_count()
```

### Infrastructure Layer - Adapters

Choose your messaging system at infrastructure level:

```python
from backbone.infrastructure.messaging import (
    KafkaEventBusAdapter,
    RabbitMQEventBusAdapter, 
    RedisEventBusAdapter
)

# Kafka for high-throughput scenarios
kafka_bus = KafkaEventBusAdapter(
    bootstrap_servers="localhost:9092",
    topic_prefix="backbone.events"
)

# RabbitMQ for complex routing
rabbitmq_bus = RabbitMQEventBusAdapter(
    connection_url="amqp://guest:guest@localhost:5672//",
    exchange_name="backbone.events"
)

# Redis for lightweight real-time events  
redis_bus = RedisEventBusAdapter(
    redis_url="redis://localhost:6379",
    channel_prefix="backbone.events"
)

# All implement the same EventBus interface
await event_bus.publish(event)  # Works with any adapter
```

### Event Handler Registry

Automatic registration of decorated handlers:

```python
from backbone.application.event_handlers import EventHandlerRegistry

# Create registry with chosen adapter
registry = EventHandlerRegistry(kafka_bus, logger)

# Register all handlers from objects
await registry.register_handlers(
    user_event_handlers,
    notification_handlers,
    analytics_handlers
)

# Or register individual functions
await registry.register_handler_functions(
    handle_user_created,
    handle_user_updated
)
```

### Event Store & Persistence

Events are automatically persisted for audit trails:

```python
from backbone.infrastructure.persistence.event_store import (
    JsonFileEventStore,
    InMemoryEventStore
)

# JSON file storage with date organization
event_store = JsonFileEventStore("./events")

# Query events by source
user_events = await event_store.get_events_by_source(
    "industrial_prom", 
    limit=100
)

# Query by event name
creation_events = await event_store.get_events_by_name(
    "UserCreated",
    limit=50
)
```

### Event Types

Three specialized event types for different scenarios:

```python
from backbone.domain.ports.event_bus import (
    DomainEvent,      # Business logic changes
    IntegrationEvent, # Cross-microservice communication  
    SystemEvent       # Infrastructure/operational events
)

# Domain event for business changes
domain_event = DomainEvent(
    event_name="UserCreated",
    aggregate_id="user_123",
    aggregate_type="User",
    source="users-service",
    data=user_data,
    microservice="users-service",
    functionality="create-user"
)

# Integration event for microservice communication
integration_event = IntegrationEvent(
    event_name="UserRegistrationCompleted", 
    source="users-service",
    target_services=["notifications", "analytics"],
    data=user_data,
    microservice="users-service",
    functionality="complete-registration"
)

# System event for operational concerns
system_event = SystemEvent(
    event_name="ServiceStarted",
    source="users-service", 
    severity="INFO",
    data={"version": "1.0.0", "environment": "production"},
    microservice="users-service",
    functionality="service-startup"
)
```

### Complete Microservice Example

```python
# Domain service (pure business logic)
class UserService:
    def __init__(self, user_repo: IRepository, event_bus: EventBus):
        self._user_repo = user_repo
        self._event_bus = event_bus
    
    async def register_user(self, user_data: dict):
        user = User.create(user_data)
        await self._user_repo.save(user)
        
        # Publish integration event
        event = IntegrationEvent(
            event_name="UserRegistered",
            source="users-service",
            target_services=["notifications", "analytics"],
            data={"user_id": user.id, "email": user.email},
            microservice="users-service", 
            functionality="register-user"
        )
        
        await self._event_bus.publish(event)

# Event handlers in other microservices
@event_handler("UserRegistered")
async def send_welcome_email(event: BaseEvent):
    user_data = event.data
    await email_service.send_welcome(user_data["email"])

@event_handler("UserRegistered") 
async def update_user_analytics(event: BaseEvent):
    await analytics.increment_metric("new_users")

# Infrastructure wiring (main.py)
async def setup_event_system():
    # Choose adapter based on environment
    if config.MESSAGE_BROKER == "kafka":
        event_bus = KafkaEventBusAdapter(config.KAFKA_SERVERS)
    elif config.MESSAGE_BROKER == "rabbitmq":
        event_bus = RabbitMQEventBusAdapter(config.RABBITMQ_URL)
    else:
        event_bus = RedisEventBusAdapter(config.REDIS_URL)
    
    # Setup event store
    event_store = JsonFileEventStore("./events")
    
    # Register handlers
    registry = EventHandlerRegistry(event_bus, logger)
    await registry.register_handlers(event_handlers)
    
    return event_bus
```

## 🚀 Installation

```bash
# Instalación básica
pip install backbone-clean-arch

# Con dependencias SQLAlchemy
pip install backbone-clean-arch[sqlalchemy]

# Con dependencias MongoDB  
pip install backbone-clean-arch[mongodb]

# Con todas las dependencias
pip install backbone-clean-arch[all]
```

## 📖 Guía de Uso

### 1. Definir Entidades de Dominio

```python
# domain/entities/user.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    id: Optional[str] = None
    name: str = ""
    email: str = ""
    age: int = 0
    created_at: Optional[datetime] = None
    is_active: bool = True
```

### 2. Crear Especificaciones de Dominio

```python
# domain/specifications/user_specifications.py
from backbone.domain.specifications import FilterSpecification

class ActiveUserSpecification(FilterSpecification):
    def __init__(self):
        super().__init__("is_active", "eq", True)

class AdultUserSpecification(FilterSpecification):
    def __init__(self):
        super().__init__("age", "gte", 18)

# Uso combinado
adult_active_users = ActiveUserSpecification().and_(AdultUserSpecification())
```

### 3. Implementar Repository

```python
# infrastructure/persistence/user_repository.py
from backbone.infrastructure.persistence import SQLAlchemyRepository
from sqlalchemy.ext.asyncio import AsyncSession

class UserRepository(SQLAlchemyRepository[User, str]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel, User)
    
    async def find_by_email(self, email: str) -> Optional[User]:
        spec = FilterSpecification("email", "eq", email)
        users = await self.find_by_specification(spec)
        return users[0] if users else None
```

### 4. Crear Caso de Uso de Aplicación

```python
# application/services/user_service.py
from backbone.application.exceptions import ApplicationException
from backbone.domain.repositories.base_repository import IRepository

class UserService:
    def __init__(self, user_repository: IRepository[User, str]):
        self._user_repository = user_repository
    
    async def create_user(self, user_data: dict) -> User:
        try:
            # Validación de dominio
            if user_data.get("age", 0) < 18:
                raise DomainException(
                    message="User must be at least 18 years old",
                    error_code="11001001"
                )
            
            # Crear entidad
            user = User(**user_data)
            
            # Guardar
            saved_user = await self._user_repository.save(user)
            
            return saved_user
            
        except Exception as e:
            raise ApplicationException(
                message="Failed to create user",
                error_code="10001001",
                operation="create_user",
                original_error=str(e)
            )
```

### 5. Crear Controlador/Handler

```python
# interfaces/api/user_controller.py  
from backbone.interfaces.response_builders import ProcessResponseBuilder
from backbone.domain.specifications import FilterParser

class UserController:
    def __init__(self, user_service: UserService):
        self._user_service = user_service
        self._filter_parser = FilterParser()
    
    async def create_user(self, request_data: dict) -> dict:
        try:
            user = await self._user_service.create_user(request_data)
            
            return ProcessResponseBuilder.success(
                data=user.__dict__,
                message="User created successfully"
            )
            
        except Exception as e:
            return ErrorResponseBuilder.from_exception(e)
    
    async def list_users(self, query_params: dict) -> dict:
        # Parse filters dinámicos
        spec = self._filter_parser.parse_filters(query_params)
        page = int(query_params.get('page', 0))
        page_size = int(query_params.get('page_size', 20))
        
        users, total = await self._user_service.get_users_paginated(
            spec, page, page_size
        )
        
        return PaginatedResponseBuilder.from_repository_result(
            users, total, page, page_size
        )
```

## 🧪 Testing

### Test Unitario

```python
# tests/unit/test_user_service.py
from backbone.infrastructure.testing import BaseTestCase, MockRepository

class UserServiceTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.mock_repo = MockRepository(User)
        self.user_service = UserService(self.mock_repo)
    
    async def test_create_adult_user_success(self):
        # Arrange
        user_data = {"name": "John", "email": "john@test.com", "age": 25}
        
        # Act
        result = await self.user_service.create_user(user_data)
        
        # Assert  
        self.assertEqual(result.name, "John")
        self.assertEqual(result.age, 25)
        saved_users = self.mock_repo.get_saved_entities()
        self.assertEqual(len(saved_users), 1)
    
    async def test_create_minor_user_raises_domain_exception(self):
        # Arrange
        user_data = {"name": "Minor", "email": "minor@test.com", "age": 15}
        
        # Act & Assert
        with self.assertRaisesDomainException("11001001"):
            await self.user_service.create_user(user_data)
```

### Test de Integración

```python
# tests/integration/test_user_repository.py
from backbone.infrastructure.testing import BaseIntegrationTestCase

class UserRepositoryIntegrationTest(BaseIntegrationTestCase):
    async def test_find_by_specification_filters_correctly(self):
        # Arrange - seed test data
        await self.seed_users([
            {"name": "John", "age": 25, "is_active": True},
            {"name": "Jane", "age": 17, "is_active": True}, 
            {"name": "Bob", "age": 30, "is_active": False}
        ])
        
        # Act - apply specification
        spec = FilterSpecification("age", "gte", 18).and_(
            FilterSpecification("is_active", "eq", True)
        )
        
        users = await self.user_repository.find_by_specification(spec)
        
        # Assert
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].name, "John")
```

## ⚙️ Configuración

### Variables de Entorno

```bash
# .env
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-here-must-be-at-least-32-chars
JWT_SECRET_KEY=your-jwt-secret-key-here-must-be-32-chars

# Database
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname

# API  
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Features
FEATURE_ADVANCED_FILTERING=true
FEATURE_METRICS_ENABLED=true
```

### Configuración Programática

```python
from backbone.infrastructure.configuration import override_config

# Override temporal para testing
test_config = override_config(
    database_url="sqlite:///:memory:",
    log_level="WARNING",
    debug=False
)
```

## 📁 Estructura de Proyecto Recomendada

```
my-app/
├── domain/
│   ├── entities/
│   │   ├── user.py
│   │   └── product.py
│   ├── specifications/
│   │   ├── user_specifications.py
│   │   └── product_specifications.py
│   └── services/
│       └── domain_services.py
├── application/
│   ├── services/
│   │   ├── user_service.py
│   │   └── product_service.py
│   └── dto/
│       ├── user_dto.py
│       └── product_dto.py
├── infrastructure/
│   ├── persistence/
│   │   ├── models/
│   │   │   ├── user_model.py
│   │   │   └── product_model.py
│   │   └── repositories/
│   │       ├── user_repository.py
│   │       └── product_repository.py
│   └── external/
│       ├── email_service.py
│       └── payment_service.py
├── interfaces/
│   ├── api/
│   │   ├── controllers/
│   │   │   ├── user_controller.py
│   │   │   └── product_controller.py
│   │   └── middleware/
│   │       └── auth_middleware.py
│   └── cli/
│       └── commands.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── main.py
└── requirements.txt
```

## 🔧 Extensiones y Personalización

### Custom Repository

```python
class CustomUserRepository(SQLAlchemyRepository[User, str]):
    async def find_active_users_by_role(self, role: str) -> List[User]:
        spec = (
            FilterSpecification("is_active", "eq", True)
            .and_(FilterSpecification("role", "eq", role))
        )
        return await self.find_by_specification(spec)
```

### Custom Exception

```python
from backbone.domain.exceptions import DomainException

class UserAlreadyExistsException(DomainException):
    def __init__(self, email: str):
        super().__init__(
            message=f"User with email {email} already exists",
            error_code="11001002",
            context={"email": email}
        )
```

### Custom Response Builder

```python
from backbone.interfaces.response_builders import BaseResponseBuilder

class CustomResponseBuilder(BaseResponseBuilder):
    @staticmethod
    def success_with_metadata(data: Any, metadata: dict) -> dict:
        return {
            "success": True,
            "data": data,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
```

## 🤝 Contribución

1. Fork el repositorio
2. Crea una branch de feature (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la branch (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

## 📞 Soporte

- 📧 Email: support@backbone-framework.com
- 🐛 Issues: [GitHub Issues](https://github.com/backbone/backbone/issues)
- 📖 Documentación: [docs.backbone-framework.com](https://docs.backbone-framework.com)

---

**Backbone Framework** - Construyendo aplicaciones limpias y escalables con Python 🐍✨

Backbone represents the structural core of a microservices ecosystem.
It centralizes technical foundations such as configuration, logging, security utilities, error handling, shared schemas, and event contracts used by FastAPI-based services.

The library is intentionally domain-agnostic and stateless.
It does not contain business logic, use cases, repositories, or service-specific integrations. Its purpose is to enforce architectural standards and reduce duplication while keeping microservices independent.
