# backbone

Clean Architecture + CQRS kernel for Python microservices.

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

> Go port: [backbone-go](./backbone-go/README.md) — identical contracts, same architecture.

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
│   ├── exceptions/        # BaseKernelException (8-digit codes: 11xxxxxx)
│   ├── ports/             # EventBus / EventStore / BaseEvent
│   ├── repositories/      # IRepository / IReadOnlyRepository interfaces
│   └── specifications/    # Specification + FilterParser + SortParser
├── application/
│   └── exceptions/        # Application exceptions (10xxxxxx)
├── infrastructure/
│   ├── logging/           # Structured JSON logger (same shape as backbone-go)
│   ├── persistence/       # SQLAlchemy async adapter
│   └── messaging/         # Kafka / RabbitMQ / Redis adapters
└── interfaces/
    └── response_builders/ # Response builders (no framework dependency)
```

---

## CQRS Project Structure

```
your_service/
├── domain/
│   ├── entities/
│   ├── repositories/
│   └── specifications/
├── application/
│   ├── commands/          ← write side: CreateXxxCommand + XxxCommandHandler
│   └── queries/           ← read side:  GetXxxQuery     + XxxQueryHandler
├── infrastructure/
│   ├── repositories/      ← concrete implementations
│   └── seeders/           ← data seeders (not in main.py)
└── interfaces/
    └── http/
        ├── handlers/
        │   ├── xxx_command_handler.py   ← POST PUT DELETE PATCH
        │   └── xxx_query_handler.py     ← GET (list + by id)
        └── v1/
            └── routes.py                ← versioned route registration
```

`main.py` — DI container only: wires infra → command handlers → query handlers → HTTP adapters → routes.

---

## Quick Start

```python
from backbone.infrastructure.logging import LoggerFactory, LogContext
from backbone.interfaces.response_builders import (
    ProcessResponseBuilder,
    SimpleObjectResponseBuilder,
    PaginatedResponseBuilder,
    ErrorResponseBuilder,
)
from backbone.domain.specifications import FilterParser, SortParser

logger = LoggerFactory.create_logger("my-service")

# Automatic context propagation in all logs inside the block
with LogContext(request_id="abc-123", user_id="user-1"):
    logger.info("Processing request")
```

---

## Response Contracts

### Write operations (create / update / delete)
```json
{"id": "uuid-123"}
```
HTTP: `201` create · `200` update / delete

### GET single resource
```json
{"id": "uuid-123", "name": "Laptop", "price": 1500.0}
```
Raw object — no envelope.

### GET list (paginated)
```json
{
  "meta":       {"status": "success", "status_code": 200, "message": "Products retrieved successfully"},
  "items":      [{"id": "1"}, {"id": "2"}],
  "pagination": {"total_count": 100, "page": 1, "page_size": 10}
}
```

### Error
```json
{
  "request_id":  "uuid",
  "status_code": 404,
  "message":     "Product not found",
  "code_error":  "NOT_FOUND",
  "field_errors": {"name": "required"}
}
```

---

## Dynamic Filters (Specification Pattern)

Query params — 4 generic parameters:

| Param | Description |
|---|---|
| `filters` | Repeated. Format: `field,operator,value[,condition]` |
| `page` | Page number (default `1`) |
| `page_size` | Items per page (default `10`) |
| `sort_by` | `field:direction` — e.g. `price:desc` |

```
GET /api/v1/products
  ?filters=category,eq,Electronics,and
  &filters=price,gt,500,and
  &filters=stock,gt,0
  &page=1&page_size=10&sort_by=price:desc
```

| Operator | Meaning | Example |
|---|---|---|
| `eq` | = | `name,eq,Laptop` |
| `ne` | != | `active,ne,false` |
| `gt` | > | `price,gt,500` |
| `gte` | >= | `price,gte,500` |
| `lt` | < | `stock,lt,10` |
| `lte` | <= | `price,lte,2000` |
| `contains` | LIKE %x% | `name,contains,laptop` |
| `in` | IN (a\|b\|c) | `category,in,Electronics\|Furniture` |
| `between` | BETWEEN a AND b | `price,between,100\|2000` |
| `is_null` | IS NULL | `description,is_null` |
| `is_not_null` | IS NOT NULL | `description,is_not_null` |

Using it in a query handler:

```python
from backbone.domain.specifications import FilterParser, SortParser

spec   = FilterParser().parse_filters(query.filters)   # → Specification
sorts  = SortParser().parse_sort("price,desc").to_sort_criteria()  # → [("price","desc")]

products = repo.find_by_criteria(filters=spec, sorts=sorts, page=1, page_size=10)
```

---

## Logging

```python
from backbone.infrastructure.logging import LoggerFactory, LogContext, with_log_context

logger = LoggerFactory.create_logger("my-service", environment="production")

# Scoped via context manager
with LogContext(request_id="abc", user_id="user-1"):
    logger.info("Processing", extra_data={"action": "create"})
    logger.error("Failed", exception=exc, error_code=10001001)

# Scoped via decorator
@with_log_context(operation="create_product")
def create(data):
    logger.info("Creating product")
```

Log JSON (same shape as backbone-go):
```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "level": "INFO",
  "service": "my-service",
  "component": "CreateProductCommandHandler",
  "layer": "application",
  "message": "Product created",
  "request_id": "abc",
  "user_id": "user-1",
  "environment": "production",
  "extra_data": {"product_id": "uuid"}
}
```

---

## Exception System (8 digits)

```
10xxxxxx  Application
11xxxxxx  Domain
12xxxxxx  Infrastructure
13xxxxxx  Interfaces
```

```python
from backbone.domain.exceptions import DomainException, BusinessRuleViolationException
from backbone.application.exceptions import ValidationException, ResourceNotFoundException

raise DomainException(11001001, "Name too short")
raise ValidationException("Invalid input", field="price")
raise ResourceNotFoundException("Product", resource_id="abc-123")
```

---

## Full CRUD Example

See [`examples/clean_api_python/`](./examples/clean_api_python/).

```bash
cd examples/clean_api_python
pip install flask flask-restx
python main.py
# → http://localhost:5000/docs
```

---

## Related

- [backbone-go](./backbone-go/README.md)
- [Examples comparison](./examples/README.md)
