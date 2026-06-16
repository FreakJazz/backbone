# backbone-python

> Python library for standardising **error codes, HTTP responses, structured logs, and filter specifications** across microservices following Clean Architecture / Hexagonal Architecture.

![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python)
![Version](https://img.shields.io/badge/version-0.1.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-beta-orange)

> Designed to pair with [backbone-go](../backbone-go/README.md) — both libraries emit **identical JSON contracts**.

---

## The problem it solves

In a microservices ecosystem every team invents its own error shape, log format, and filter syntax. After six services you have six different conventions. backbone-python gives every service the same contracts so that monitoring dashboards, API gateways, and client SDKs never have to guess the shape of a response.

---

## Installation

```bash
pip install backbone-python==0.1.0
```

From source (development):

```bash
git clone https://github.com/FreakJazz/backbone.git
cd backbone/backbone-python
pip install -e .
```

**Requirements:** Python 3.11+, pydantic >= 2.0

---

## Project structure

```
backbone-python/
├── domain/
│   ├── exceptions/          # domain exception types
│   ├── ports/               # EventBus, EventStore interfaces
│   ├── repositories/        # IRepository, IReadOnlyRepository interfaces
│   └── specifications/      # Specification + Criteria + FilterParser + SortParser
├── application/
│   ├── event_handlers/      # @event_handler decorator, RetryPolicy
│   └── exceptions/          # ValidationException, ResourceNotFoundException, ...
├── errors/
│   └── __init__.py          # ErrorCodes catalogue (9-digit codes by layer)
├── infrastructure/
│   ├── configuration/       # BaseAppConfig (Pydantic Settings)
│   ├── events/              # BaseEvent, DomainEvent, IntegrationEvent, SystemEvent
│   ├── logging/             # StructuredLogger + JSONFormatter / ConsoleFormatter
│   ├── messaging/           # InMemory / Kafka / RabbitMQ / Redis adapters
│   ├── persistence/         # InMemoryEventStore, JsonFileEventStore
│   └── testing/             # BaseTestCase, MockRepository, TestDataBuilder
├── interfaces/
│   ├── exceptions/          # PresentationException, HttpException, ...
│   └── response_builders/   # ProcessResponseBuilder, ErrorResponseBuilder, ...
└── tests/                   # 94 tests covering all layers
```

---

## Error codes

Every error carries a **9-digit code** prefixed by the originating layer — `LL_NNNNNNN`.

| Prefix | Layer          | Example     |
|--------|----------------|-------------|
| `11`   | Domain         | `110000001` |
| `12`   | Application    | `120000006` |
| `13`   | Interface      | `130000001` |
| `14`   | Infrastructure | `140000001` |

```python
from backbone.errors import ErrorCodes

# Domain
ErrorCodes.DOMAIN_BUSINESS_RULE_VIOLATION   # 110000001
ErrorCodes.DOMAIN_INVALID_ENTITY_STATE      # 110000002
ErrorCodes.DOMAIN_INVALID_FILTER            # 110000005

# Application
ErrorCodes.APP_RESOURCE_NOT_FOUND           # 120000004
ErrorCodes.APP_CONFLICT                     # 120000006

# Interface
ErrorCodes.IFC_INVALID_REQUEST_BODY         # 130000001
ErrorCodes.IFC_ROUTE_NOT_FOUND              # 130000003
ErrorCodes.IFC_UNAUTHORIZED                 # 130000006

# Infrastructure
ErrorCodes.INFRA_DB_FAILURE                 # 140000001
ErrorCodes.INFRA_MESSAGING_FAILURE          # 140000002
```

---

## Response builders

All responses follow a strict contract — **no surprise fields**.

### Error response — always `{rid, status_code, message, error_code}`

```python
from backbone import ErrorResponseBuilder
from backbone.errors import ErrorCodes

# 400 Bad Request
e = ErrorResponseBuilder.validation_error(
    "name must be at least 2 characters",
    error_code=ErrorCodes.IFC_INVALID_REQUEST_BODY)
# {"rid":"a8b3...","status_code":400,"message":"name must be at least 2 characters","error_code":130000001}

# 404 Not Found
e = ErrorResponseBuilder.not_found(
    "product not found",
    error_code=ErrorCodes.APP_RESOURCE_NOT_FOUND)
# {"rid":"...","status_code":404,"message":"product not found","error_code":120000004}

# 409 Conflict
e = ErrorResponseBuilder.conflict(
    "a product with that name already exists",
    error_code=ErrorCodes.APP_CONFLICT)
# {"rid":"...","status_code":409,"message":"a product with that name already exists","error_code":120000006}

# 401 / 403 / 500
e = ErrorResponseBuilder.unauthorized("token expired")
e = ErrorResponseBuilder.forbidden("insufficient permissions")
e = ErrorResponseBuilder.internal_error("unexpected failure")
```

### Success responses

```python
from backbone import ProcessResponseBuilder, SimpleObjectResponseBuilder, PaginatedResponseBuilder

# POST / PUT / DELETE / PATCH
created = ProcessResponseBuilder.created("product-uuid-123")
# {"id": "product-uuid-123"}

updated = ProcessResponseBuilder.updated("product-uuid-123")
# {"id": "product-uuid-123"}

# GET single — raw object, no envelope
product = SimpleObjectResponseBuilder.found(product_dict)
# {"id": "uuid", "name": "Laptop Pro", "price": 1500.0}

# GET list
listing = PaginatedResponseBuilder.found(items, meta, pagination)
# {"meta": {...}, "items": [...], "pagination": {...}}
```

---

## Application exceptions

Raise backbone exceptions in your use cases — the interface layer maps them to the right HTTP status automatically.

```python
from backbone import (
    ValidationException,
    ResourceNotFoundException,
    ResourceConflictException,
    AuthorizationException,
)
from backbone.errors import ErrorCodes

# In a command handler
raise ValidationException(
    message="name must be at least 2 characters",
    validation_errors=[{"field": "name", "error": "too short"}],
    code=ErrorCodes.IFC_INVALID_REQUEST_BODY,
)

raise ResourceNotFoundException(
    message="product not found",
    resource_type="Product",
    code=ErrorCodes.APP_RESOURCE_NOT_FOUND,
)

raise ResourceConflictException(
    message="a product with that name already exists",
    resource_type="Product",
    conflict_field="name",
    conflict_value=name,
    code=ErrorCodes.APP_CONFLICT,
)
```

---

## Structured logging

Three formatters ship out of the box — swap without touching your log calls.

```python
from backbone import LoggerFactory, JSONFormatter, ConsoleFormatter, CompactJSONFormatter

factory = LoggerFactory("products-service")

# Production default: JSON lines for ELK / Loki / CloudWatch
logger = factory.get_logger("ProductHandler", formatter=JSONFormatter())
logger.info("product created", extra_data={"product_id": "123"}, request_id=rid)

# Development: coloured, human-readable
logger = factory.get_logger("ProductHandler", formatter=ConsoleFormatter())
# 2026-06-16 10:23:45 [INFO] products-service > ProductHandler | product created

# High-throughput: compact JSON, fewer bytes per line
logger = factory.get_logger("ProductHandler", formatter=CompactJSONFormatter())
# {"ts":"2026-06-16T10:23:45Z","level":"INFO","service":"products-service","msg":"product created"}
```

Full JSON entry (JSONFormatter — default):

```json
{
  "timestamp":  "2026-06-16T10:23:45Z",
  "level":      "INFO",
  "service":    "products-service",
  "component":  "ProductHandler",
  "layer":      "interface",
  "message":    "product created",
  "request_id": "abc-123",
  "extra_data": { "product_id": "123" }
}
```

> The JSON shape is **identical** to backbone-go — both services feed the same ELK index without remapping.

---

## Filter specifications

Four generic query params — no hard-coded field names in your router.

| Param       | Format                             | Example            |
|-------------|------------------------------------|--------------------|
| `filters`   | `field,operator,value[,condition]` | `price,gt,500,and` |
| `page`      | integer                            | `1`                |
| `page_size` | integer                            | `20`               |
| `sort_by`   | `field:direction`                  | `created_at:desc`  |

Supported operators: `eq` `ne` `gt` `gte` `lt` `lte` `contains` `in` `between` `is_null` `is_not_null`

```python
from backbone import FilterParser, SortSpecification

# Build from Flask / FastAPI request params
parser = FilterParser(allowed_fields=["name", "price", "category", "status"])
criteria = parser.parse(request.args.getlist("filters"))
sort     = SortSpecification.parse(request.args.get("sort_by", "created_at:desc"))

products = repo.find_by_criteria(criteria, sort, page=1, page_size=20)

# Or build manually
from backbone import EqualSpecification, GreaterThanOrEqualSpecification

spec = EqualSpecification("category", "Electronics") & \
       GreaterThanOrEqualSpecification("price", 500)
```

Example URL:

```
GET /api/v1/products
  ?filters=category,eq,Electronics,and
  &filters=price,between,500|2000
  &filters=name,contains,laptop
  &page=1&page_size=10&sort_by=price:desc
```

---

## Event-driven microservices

```python
from backbone import DomainEvent, IntegrationEvent, InMemoryEventStore

# Define and publish a domain event
event = DomainEvent(
    event_name="ProductCreated",
    source="products-service",
    data={"product_id": "123", "name": "Laptop Pro"},
    microservice="products-service",
    functionality="create-product",
    aggregate_id="product-123",
    aggregate_version=1,
)

store = InMemoryEventStore()
await store.save(event)

# Integration event — notifies other services
notification = IntegrationEvent(
    event_name="ProductCreated",
    source="products-service",
    data={"product_id": "123"},
    target_services=["inventory", "analytics"],
    microservice="products-service",
    functionality="create-product",
)
```

---

## Clean Architecture example

```
examples/python/clean_api_python/
├── domain/
│   ├── entities/           # Product entity
│   ├── repositories/       # IProductRepository interface
│   └── specifications/     # ProductSpecification
├── application/
│   ├── commands/           # CreateProduct, UpdateProduct, ChangeStatus, DeleteProduct
│   └── queries/            # GetProducts, GetProductByID
├── infrastructure/
│   ├── repositories/       # in-memory implementation
│   └── seeders/            # test data
└── interfaces/http/
    ├── commands/           # Flask route handlers for write operations
    └── queries/            # Flask route handlers for read operations
```

```bash
cd examples/python/clean_api_python
pip install flask flask-restx
python main.py
# http://localhost:5000/docs
```

---

## Running tests

```bash
cd backbone-python
pytest
# 94 passed in ~7s
```

---

## Companion library

[backbone-go](../backbone-go/README.md) — identical JSON contracts, Go implementation.

---

## Version

`0.1.0` — public beta. API stabilises at `1.0.0`.

## License

MIT © [FreakJazz](https://github.com/FreakJazz)
