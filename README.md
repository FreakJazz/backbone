# backbone

Clean Architecture + CQRS kernel for Python microservices.

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

> Go port: [backbone-go](./backbone-go/README.md) — identical contracts and architecture.

---

## Installation

```bash
pip install git+https://github.com/FreakJazz/backbone.git

# specific version
pip install git+https://github.com/FreakJazz/backbone.git@v1.0.0
```

---

## What it provides

| Module | Purpose |
|---|---|
| `domain.specifications` | `FilterParser` · `SortParser` · `Specification` pattern |
| `domain.exceptions` | 8-digit exception codes by layer |
| `domain.repositories` | `IRepository` / `IReadOnlyRepository` interfaces |
| `domain.ports` | `EventBus` · `EventStore` · `BaseEvent` |
| `application.exceptions` | Application-layer exceptions |
| `infrastructure.logging` | Structured JSON logger with context propagation |
| `infrastructure.persistence` | SQLAlchemy async adapter |
| `infrastructure.messaging` | Kafka / RabbitMQ / Redis adapters |
| `interfaces.response_builders` | HTTP response builders (no framework dependency) |

---

## Response contracts

All contracts are identical between Python and Go.

### Write operations — `POST` `PUT` `DELETE` `PATCH`
```json
{ "id": "uuid-123" }
```

### GET single resource
```json
{ "id": "uuid-123", "name": "Laptop", "price": 1500.0 }
```
Raw object — no envelope.

### GET list
```json
{
  "meta":       { "status": "success", "status_code": 200, "message": "..." },
  "items":      [{ "id": "1" }, { "id": "2" }],
  "pagination": { "total_count": 100, "page": 1, "page_size": 10 }
}
```

### Error
```json
{
  "request_id":  "uuid",
  "status_code": 404,
  "message":     "Product not found",
  "code_error":  "NOT_FOUND",
  "field_errors": { "name": "required" }
}
```

Usage:
```python
from backbone.interfaces.response_builders import (
    ProcessResponseBuilder,
    SimpleObjectResponseBuilder,
    PaginatedResponseBuilder,
    ErrorResponseBuilder,
)

ProcessResponseBuilder.created("uuid-123")          # {"id": "uuid-123"}
SimpleObjectResponseBuilder.found(product.to_dict()) # raw object
PaginatedResponseBuilder.success(items, 100, 1, 10, "OK")
ErrorResponseBuilder.not_found_error("Product not found")
ErrorResponseBuilder.validation_error("Invalid input", {"name": "required"})
```

---

## Dynamic filters

4 generic query params — no hard-coded fields:

| Param | Format | Example |
|---|---|---|
| `filters` | repeated `field,operator,value[,condition]` | `filters=price,gt,500,and` |
| `page` | integer | `page=1` |
| `page_size` | integer | `page_size=10` |
| `sort_by` | `field:direction` | `sort_by=price:desc` |

Supported operators: `eq` `ne` `gt` `gte` `lt` `lte` `contains` `in` `between` `is_null` `is_not_null`

```python
from backbone.domain.specifications import FilterParser, SortParser

spec  = FilterParser().parse_filters(["category,eq,Electronics,and", "price,gt,500"])
sorts = SortParser().parse_sort("price,desc").to_sort_criteria()

products = repo.find_by_criteria(filters=spec, sorts=sorts, page=1, page_size=10)
```

---

## Logging

```python
from backbone.infrastructure.logging import LoggerFactory, LogContext, with_log_context

logger = LoggerFactory.create_logger("my-service", environment="production")

# Automatic context propagation
with LogContext(request_id="abc-123", user_id="user-1"):
    logger.info("Processing", extra_data={"action": "create"})
    logger.error("Failed", exception=exc, error_code=10001001)

@with_log_context(operation="create_product")
def create(data): ...
```

JSON output:
```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "level": "INFO",
  "service": "my-service",
  "layer": "application",
  "message": "Processing",
  "request_id": "abc-123",
  "user_id": "user-1",
  "extra_data": { "action": "create" }
}
```

---

## Exception system — 8-digit codes

```
10xxxxxx  Application     11xxxxxx  Domain
12xxxxxx  Infrastructure  13xxxxxx  Interfaces
```

```python
from backbone.domain.exceptions import DomainException, BusinessRuleViolationException
from backbone.application.exceptions import ValidationException, ResourceNotFoundException

raise DomainException(11001001, "Name must be at least 3 characters")
raise ValidationException("Invalid price", field="price")
raise ResourceNotFoundException("Product", resource_id="abc-123")
```

---

## Project structure — Clean Architecture + CQRS

```
your_service/
├── domain/
│   ├── entities/
│   ├── repositories/          # interfaces
│   └── specifications/        # domain-specific specs
├── application/
│   ├── commands/              # write side: XxxCommand + XxxCommandHandler
│   └── queries/               # read side:  XxxQuery   + XxxQueryHandler
├── infrastructure/
│   ├── repositories/          # concrete implementations
│   └── seeders/               # data seeders
└── interfaces/
    └── http/
        ├── commands/          # HTTP adapter per command  (POST PUT DELETE PATCH)
        ├── queries/           # HTTP adapter per query    (GET)
        └── v1/
            └── routes.py      # versioned route registration
```

`main.py` — DI container only. No business logic.

---

## Full example

See [`examples/clean_api_python/`](./examples/clean_api_python/) — complete product CRUD API with Flask + Flask-RESTX.

```bash
cd examples/clean_api_python
pip install flask flask-restx
python main.py
# → http://localhost:5000/docs
```

---

## Related

- [backbone-go](./backbone-go/README.md)
- [Examples](./examples/README.md)
