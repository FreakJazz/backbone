# backbone

> Clean Architecture kernel for Go and Python microservices — standardised error codes, HTTP response contracts, structured logs, and filter specifications.

![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python)
![Go](https://img.shields.io/badge/go-1.21%2B-00ADD8?logo=go)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-beta-orange)

Both implementations share **identical JSON contracts** — the same error shape, the same log fields, the same filter operators — so your Go and Python services are interoperable out of the box.

---

## Libraries

| | Python | Go |
|---|---|---|
| Folder | [`backbone-python/`](./backbone-python/README.md) | [`backbone-go/`](./backbone-go/README.md) |
| Install | `pip install backbone-python==0.1.0` | `go get github.com/freakjazz/backbone-go@v0.1.0` |
| Tests | 94 passed | 8 packages, all green |
| Example | [`examples/python/clean_api_python/`](./examples/python/clean_api_python/) | [`examples/go/clean-api-go/`](./examples/go/clean-api-go/) |

---

## What it provides

| Feature | Python | Go |
|---|---|---|
| 9-digit error code catalogue | `backbone.errors.ErrorCodes` | `backbone-go/errors` |
| Response builders | `backbone.interfaces.response_builders` | `backbone-go/interfaces/responses` |
| Structured logging (JSON / Console / Compact) | `backbone.infrastructure.logging` | `backbone-go/infrastructure/logging` |
| Specification + Filter + Sort pattern | `backbone.domain.specifications` | `backbone-go/domain/specifications` |
| Domain / Application exceptions | `backbone.domain.exceptions` + `backbone.application.exceptions` | `backbone-go/domain/exceptions` + `application/exceptions` |
| EventBus + EventStore | `backbone.infrastructure.messaging` | `backbone-go/infrastructure/messaging` |
| Repository interfaces | `backbone.domain.repositories` | `backbone-go/domain/repositories` |
| Testing utilities | `backbone.infrastructure.testing` | — |
| Pydantic-based config | `backbone.infrastructure.configuration` | — |
| Viper-based config | — | `backbone-go/infrastructure/config` |

---

## Response contracts

Contracts are **identical in both languages**.

### Write operations (POST / PUT / DELETE / PATCH)

```json
{ "id": "uuid-123" }
```

### GET single resource

```json
{ "id": "uuid-123", "name": "Laptop Pro", "price": 1500.0, "status": "active" }
```

Raw object — no envelope.

### GET list

```json
{
  "meta":       { "status": "success", "status_code": 200, "message": "OK" },
  "items":      [{ "id": "1", "name": "Laptop" }, { "id": "2", "name": "Mouse" }],
  "pagination": { "total_count": 100, "page": 1, "page_size": 10 }
}
```

### Error — always `{rid, status_code, message, error_code}`

```json
{
  "rid":         "a8866c5e750643dab7cd2a8927bbcc08",
  "status_code": 409,
  "message":     "a product with that name already exists",
  "error_code":  120000006
}
```

No `field_errors`, no `data` wrapper, no extra keys — the contract never changes shape.

---

## Error codes

Format: `LL_NNNNNNN` (9 digits). `LL` = layer prefix, `NNNNNNN` = sequence.

| Code        | Layer          | Name                        | HTTP |
|-------------|----------------|-----------------------------|------|
| `110000001` | Domain         | BusinessRuleViolation       | 422  |
| `110000002` | Domain         | InvalidEntityState          | 422  |
| `110000003` | Domain         | InvalidValueObject          | 422  |
| `110000004` | Domain         | AggregateInconsistency      | 409  |
| `110000005` | Domain         | InvalidFilter               | 400  |
| `120000001` | Application    | UseCaseFailure              | 500  |
| `120000002` | Application    | ValidationFailure           | 400  |
| `120000003` | Application    | AuthorizationDenied         | 403  |
| `120000004` | Application    | ResourceNotFound            | 404  |
| `120000005` | Application    | ExternalServiceFailure      | 502  |
| `120000006` | Application    | Conflict                    | 409  |
| `130000001` | Interface      | InvalidRequestBody          | 400  |
| `130000002` | Interface      | MethodNotAllowed            | 405  |
| `130000003` | Interface      | RouteNotFound               | 404  |
| `130000004` | Interface      | MissingRequiredParam        | 400  |
| `130000005` | Interface      | InvalidFilterFormat         | 400  |
| `130000006` | Interface      | Unauthorized                | 401  |
| `130000007` | Interface      | Forbidden                   | 403  |
| `140000001` | Infrastructure | DBFailure                   | 500  |
| `140000002` | Infrastructure | MessagingFailure            | 500  |
| `140000003` | Infrastructure | CacheFailure                | 500  |
| `140000004` | Infrastructure | ExternalAPIFailure          | 502  |
| `140000005` | Infrastructure | ServiceUnavailable          | 503  |

**Python:**
```python
from backbone.errors import ErrorCodes
ErrorCodes.APP_CONFLICT                 # 120000006
ErrorCodes.IFC_INVALID_REQUEST_BODY     # 130000001
ErrorCodes.INFRA_DB_FAILURE             # 140000001
```

**Go:**
```go
import bberrors "github.com/freakjazz/backbone-go/errors"
bberrors.AppConflict.Int()              // 120000006
bberrors.IfcInvalidRequestBody.Int()    // 130000001
bberrors.InfraDBFailure.Int()           // 140000001
```

---

## Response builders

**Python:**
```python
from backbone import (
    ErrorResponseBuilder, ProcessResponseBuilder,
    SimpleObjectResponseBuilder, PaginatedResponseBuilder,
)
from backbone.errors import ErrorCodes

# Errors
ErrorResponseBuilder.validation_error("name is required",
    error_code=ErrorCodes.IFC_INVALID_REQUEST_BODY)
ErrorResponseBuilder.not_found("product not found",
    error_code=ErrorCodes.APP_RESOURCE_NOT_FOUND)
ErrorResponseBuilder.conflict("already exists",
    error_code=ErrorCodes.APP_CONFLICT)

# Success
ProcessResponseBuilder.created("uuid-123")
SimpleObjectResponseBuilder.found(product.to_dict())
PaginatedResponseBuilder.found(items, meta, pagination)
```

**Go:**
```go
import (
    "github.com/freakjazz/backbone-go/interfaces/responses"
    bberrors "github.com/freakjazz/backbone-go/errors"
)

// Errors
responses.ErrorResponseBuilder.ValidationError("name is required",
    responses.ErrorOpts{Code: bberrors.IfcInvalidRequestBody.Int()})
responses.ErrorResponseBuilder.NotFound("product not found",
    responses.ErrorOpts{Code: bberrors.AppResourceNotFound.Int()})
responses.ErrorResponseBuilder.Conflict("already exists",
    responses.ErrorOpts{Code: bberrors.AppConflict.Int()})

// Success
responses.ProcessResponseBuilder.Created("uuid-123")
responses.SimpleObjectResponseBuilder.Found(productMap)
responses.PaginatedResponseBuilder.Found(items, meta, pagination)
```

---

## Logging

Both implementations emit the same JSON shape.

**Python:**
```python
from backbone import LoggerFactory, JSONFormatter, ConsoleFormatter

logger = LoggerFactory("my-service").get_logger("Handler", formatter=JSONFormatter())
logger.info("processing request", extra_data={"order_id": "123"}, request_id=rid)
```

**Go:**
```go
import "github.com/freakjazz/backbone-go/infrastructure/logging"

logger := logging.NewLogger("my-service")
logger.SetFormatter(logging.NewConsoleFormatter()) // dev
// logger.SetFormatter(&logging.JSONFormatter{})  // prod (default)

scoped := logger.WithContext(map[string]interface{}{"request_id": rid})
scoped.Info("processing request", map[string]interface{}{"order_id": "123"})
```

JSON output (identical in both):

```json
{
  "timestamp":  "2026-06-16T10:23:45Z",
  "level":      "INFO",
  "service":    "my-service",
  "component":  "Handler",
  "message":    "processing request",
  "request_id": "abc-123",
  "extra_data": { "order_id": "123" }
}
```

---

## Dynamic filters

Four generic query params — no hard-coded field names in your router.

```
GET /api/v1/products
  ?filters=category,eq,Electronics,and
  &filters=price,between,500|2000
  &filters=name,contains,laptop
  &page=1&page_size=10&sort_by=price:desc
```

Supported operators: `eq` `ne` `gt` `gte` `lt` `lte` `contains` `in` `between` `is_null` `is_not_null`

**Python:**
```python
from backbone import FilterParser, SortSpecification

criteria = FilterParser(allowed_fields=["name","price","category"]).parse(
    request.args.getlist("filters"))
products = repo.find_by_criteria(criteria, page=1, page_size=10)
```

**Go:**
```go
import "github.com/freakjazz/backbone-go/domain/specifications"

sortField, sortDir := specifications.ParseSortBy(r.URL.Query().Get("sort_by"))
criteria := specifications.ParseFilterParams(r.URL.Query()["filters"], page, pageSize, sortField, sortDir)
products, _ := repo.FindByCriteria(ctx, criteria)
```

---

## Clean Architecture layout

Both examples follow the same layered structure:

```
your-service/
├── domain/
│   ├── entities/           # core business objects
│   ├── repositories/       # interfaces (no implementation)
│   └── specifications/     # domain-specific filters
├── application/
│   ├── commands/           # write side — XxxCommandHandler
│   └── queries/            # read side  — XxxQueryHandler
├── infrastructure/
│   ├── repositories/       # concrete DB / memory implementations
│   └── seeders/            # test data
└── interfaces/http/
    ├── handlers/           # thin HTTP adapters — call application layer
    └── v1/routes.*         # versioned route registration
```

`main.py` / `main.go` — dependency injection only, zero business logic.

---

## Run examples

```bash
# Python (Flask + flask-restx)
cd examples/python/clean_api_python
pip install flask flask-restx
python main.py
# http://localhost:5000/docs

# Go (net/http + swagger)
cd examples/go/clean-api-go
go mod tidy && swag init && go run main.go
# http://localhost:8005/docs/index.html
```

---

## Detailed docs

- [backbone-python — full reference](./backbone-python/README.md)
- [backbone-go — full reference](./backbone-go/README.md)

---

## License

MIT © [FreakJazz](https://github.com/FreakJazz)
