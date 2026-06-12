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
  "error_code":  130000001,
  "message":     "name is required",
  "rid":         "a8866c5e750643dab7cd2a8927bbcc08",
  "status_code": 400
}
```

`field_errors` aparece solo en errores de validación con detalle por campo:
```json
{
  "error_code":  130000001,
  "message":     "invalid request body",
  "rid":         "a8866c5e750643dab7cd2a8927bbcc08",
  "status_code": 400,
  "field_errors": { "name": "required", "price": "must be greater than 0" }
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `error_code` | int (9 dígitos) | Código estructurado por capa — siempre presente |
| `message` | string | Mensaje legible |
| `rid` | string | Request ID de traza (auto-generado si no viene del middleware) |
| `status_code` | int | HTTP status code |
| `field_errors` | object | Solo en errores de validación — omitido si no aplica |

Usage:
```python
from backbone.interfaces.response_builders import (
    ProcessResponseBuilder,
    SimpleObjectResponseBuilder,
    PaginatedResponseBuilder,
    ErrorResponseBuilder,
)
from backbone.errors import ErrorCodes

ProcessResponseBuilder.created("uuid-123")           # {"id": "uuid-123"}
SimpleObjectResponseBuilder.found(product.to_dict()) # raw object
PaginatedResponseBuilder.success(items, 100, 1, 10, "OK")
ErrorResponseBuilder.not_found("Product not found")
ErrorResponseBuilder.validation_error(
    "invalid request body",
    error_code=ErrorCodes.IFC_INVALID_REQUEST_BODY,
    field_errors={"name": "required"},
)
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

## Exception system — códigos de 9 dígitos

Formato: `LL_NNNNNNN` donde `LL` = prefijo de capa, `NNNNNNN` = secuencia de 7 dígitos.

```
11xxxxxxx  Domain          12xxxxxxx  Application
13xxxxxxx  Interface       14xxxxxxx  Infrastructure
```

| Código | Capa | Nombre |
|---|---|---|
| `110000001` | Domain | BusinessRuleViolation |
| `110000002` | Domain | InvalidEntityState |
| `110000003` | Domain | InvalidValueObject |
| `110000004` | Domain | AggregateInconsistency |
| `110000005` | Domain | InvalidFilter |
| `120000001` | Application | UseCaseFailure |
| `120000002` | Application | ValidationFailure |
| `120000003` | Application | AuthorizationDenied |
| `120000004` | Application | ResourceNotFound |
| `120000005` | Application | ExternalServiceFailure |
| `120000006` | Application | Conflict |
| `130000001` | Interface | InvalidRequestBody |
| `130000002` | Interface | MethodNotAllowed |
| `130000003` | Interface | RouteNotFound |
| `130000004` | Interface | MissingRequiredParam |
| `130000005` | Interface | InvalidFilterFormat |
| `130000006` | Interface | Unauthorized |
| `130000007` | Interface | Forbidden |
| `140000001` | Infrastructure | DBFailure |
| `140000002` | Infrastructure | MessagingFailure |
| `140000003` | Infrastructure | CacheFailure |
| `140000004` | Infrastructure | ExternalAPIFailure |
| `140000005` | Infrastructure | ServiceUnavailable |

```python
from backbone.errors import ErrorCodes

ErrorCodes.DOMAIN_BUSINESS_RULE_VIOLATION  # 110000001
ErrorCodes.APP_RESOURCE_NOT_FOUND          # 120000004
ErrorCodes.IFC_INVALID_REQUEST_BODY        # 130000001
ErrorCodes.INFRA_DB_FAILURE                # 140000001

# Usar en el error builder
ErrorResponseBuilder.validation_error("msg", error_code=ErrorCodes.IFC_INVALID_REQUEST_BODY)
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
