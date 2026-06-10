# backbone

Clean Architecture kernel for Python microservices.

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

> Go port: [backbone-go](./backbone-go/README.md)

---

## Installation

```bash
# From GitHub
pip install git+https://github.com/FreakJazz/backbone.git

# Specific version
pip install git+https://github.com/FreakJazz/backbone.git@v1.0.0

# Development
git clone https://github.com/FreakJazz/backbone.git
cd backbone
pip install -e .
```

---

## Architecture

```
backbone/
├── domain/
│   ├── exceptions/      # BaseKernelException (8-digit codes)
│   ├── ports/           # EventBus / EventStore / BaseEvent
│   ├── repositories/    # IRepository / IReadOnlyRepository interfaces
│   └── specifications/  # Specification pattern
├── application/
│   └── exceptions/      # Application-layer exceptions (10xxxxxx)
├── infrastructure/
│   ├── logging/         # Structured JSON logger
│   ├── persistence/     # SQLAlchemy async adapter
│   └── messaging/       # Kafka / RabbitMQ / Redis adapters
└── interfaces/
    └── response_builders/  # Response builders (no framework dependency)
```

---

## Quick Start

```python
from backbone.infrastructure.logging import LoggerFactory
from backbone.interfaces.response_builders import (
    ProcessResponseBuilder,
    SimpleObjectResponseBuilder,
    PaginatedResponseBuilder,
    ErrorResponseBuilder,
)
from backbone.domain.exceptions import DomainException

# --- Logging ---
logger = LoggerFactory.create_logger("my-service")
logger.info("Server starting", extra_data={"port": 8080})

# Scoped logger
from backbone.infrastructure.logging import LogContext
with LogContext(request_id="abc-123", user_id="user-456"):
    logger.info("Processing request")  # request_id + user_id included automatically

# --- Exceptions ---
try:
    raise DomainException(11001001, "Product name too short")
except DomainException as e:
    logger.log_kernel_exception(e)

# --- Response builders ---

# POST / PUT / DELETE → {"id": "uuid"}
created = ProcessResponseBuilder.created("uuid-123")
updated = ProcessResponseBuilder.updated("uuid-123")
deleted = ProcessResponseBuilder.deleted("uuid-123")

# GET single → raw object (no envelope)
product = SimpleObjectResponseBuilder.found({"id": "uuid-123", "name": "Laptop"})

# GET list → paginated envelope
listing = PaginatedResponseBuilder.success(
    items=[{"id": "1"}, {"id": "2"}],
    total_count=100,
    page=1,
    page_size=10,
    message="Products retrieved successfully",
)

# Errors → flat contract
not_found  = ErrorResponseBuilder.not_found_error("Product not found")
bad_req    = ErrorResponseBuilder.validation_error("Invalid input", field_errors={"name": "required"})
server_err = ErrorResponseBuilder.internal_server_error()
```

---

## Response Contracts

### Create / Update / Delete
```json
{"id": "uuid-123"}
```

### GET single resource
```json
{
  "id": "uuid-123",
  "name": "Laptop",
  "price": 1500.00
}
```

### GET list (paginated)
```json
{
  "meta": {
    "status": "success",
    "status_code": 200,
    "message": "Products retrieved successfully"
  },
  "items": [{"id": "1"}, {"id": "2"}],
  "pagination": {
    "total_count": 100,
    "page": 1,
    "page_size": 10,
    "total_pages": 10
  }
}
```

### Error
```json
{
  "request_id": "uuid",
  "status_code": 400,
  "message": "Validation failed",
  "code_error": "VALIDATION_ERROR",
  "field_errors": {"name": "required"}
}
```

---

## Logging

```python
from backbone.infrastructure.logging import LoggerFactory, LogContext

logger = LoggerFactory.create_logger("my-service", environment="production")

# Automatic context propagation
with LogContext(request_id="abc", user_id="user-1"):
    logger.info("Handling request")
    logger.error("Something failed", exception=exc)

# Decorator
from backbone.infrastructure.logging import with_log_context

@with_log_context(operation="create_user")
def create_user(data):
    logger.info("Creating user")
```

Log entry JSON (same shape as backbone-go):
```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "level": "INFO",
  "service": "my-service",
  "component": "UserHandler",
  "layer": "interfaces",
  "message": "Handling request",
  "request_id": "abc",
  "user_id": "user-1",
  "environment": "production",
  "extra_data": {}
}
```

---

## Exception System (8 digits)

```
Layer codes:
  10xxxxxx  Application
  11xxxxxx  Domain
  12xxxxxx  Infrastructure
  13xxxxxx  Interfaces
```

```python
from backbone.domain.exceptions import DomainException, BusinessRuleViolationException
from backbone.application.exceptions import ValidationException, ResourceNotFoundException

raise DomainException(11001001, "Product name must be at least 3 characters")
raise BusinessRuleViolationException("Cannot sell inactive product")
raise ValidationException("Invalid input", field="price")
raise ResourceNotFoundException("Product", resource_id="abc-123")
```

---

## Specification Pattern

```python
from backbone.domain.specifications import Specification

class ActiveProductSpec(Specification):
    def is_satisfied_by(self, product) -> bool:
        return product.active

    def to_expression(self):
        return {"active": True}

spec = ActiveProductSpec()
filtered = [p for p in products if spec.is_satisfied_by(p)]
combined = ActiveProductSpec() & PriceRangeSpec(100, 500)
```

---

## Full CRUD Example

See [`examples/clean_api_python/`](./examples/clean_api_python/) for a FastAPI-based example with full CRUD.

---

## Related

- [backbone-go](./backbone-go/README.md)
- [Examples](./examples/README.md)
