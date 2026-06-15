# backbone

Clean Architecture + CQRS kernel — available in Python and Go.

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Go](https://img.shields.io/badge/go-1.21%2B-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

Both implementations share identical response contracts, exception codes, filter operators, and log shapes.

| | Python | Go |
|---|---|---|
| Folder | [`backbone-python/`](./backbone-python/README.md) | [`backbone-go/`](./backbone-go/README.md) |
| Install | `pip install git+https://github.com/FreakJazz/backbone.git` | `go get github.com/freakjazz/backbone-go` |
| Example | [`examples/python/clean_api_python/`](./examples/python/clean_api_python/) | [`examples/go/clean-api-go/`](./examples/go/clean-api-go/README.md) |

---

## Installation

**Python**
```bash
pip install git+https://github.com/FreakJazz/backbone.git

# specific version
pip install git+https://github.com/FreakJazz/backbone.git@v1.0.0
```

**Go**
```bash
go get github.com/freakjazz/backbone-go
```

---

## What it provides

| Module / Package | Python | Go | Purpose |
|---|---|---|---|
| `domain/specifications` | `backbone.domain.specifications` | `domain/specifications` | `FilterParser` · `SortParser` · Specification + Criteria pattern |
| `domain/exceptions` | `backbone.domain.exceptions` | `domain/exceptions` | 9-digit exception codes by layer |
| `domain/repositories` | `backbone.domain.repositories` | `domain/repositories` | `IRepository` / `IReadOnlyRepository` interfaces |
| `domain/ports` | `backbone.domain.ports` | `domain/ports` | `EventBus` · `EventStore` · `BaseEvent` |
| `application/exceptions` | `backbone.application.exceptions` | `application/exceptions` | Application-layer exceptions |
| `infrastructure/logging` | `backbone.infrastructure.logging` | `infrastructure/logging` | Structured JSON logger with context propagation |
| `infrastructure/persistence` | `backbone.infrastructure.persistence` | — | SQLAlchemy async adapter |
| `infrastructure/messaging` | `backbone.infrastructure.messaging` | `infrastructure/messaging` | Kafka / RabbitMQ / Redis / InMemory adapters |
| `infrastructure/events` | — | `infrastructure/events` | File-based event store |
| `infrastructure/config` | — | `infrastructure/config` | Environment config (viper) |
| `interfaces/responses` | `backbone.interfaces.response_builders` | `interfaces/responses` | HTTP response builders (no framework dependency) |

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

**Python usage:**
```python
from backbone.interfaces.response_builders import (
    ProcessResponseBuilder,
    SimpleObjectResponseBuilder,
    PaginatedResponseBuilder,
    ErrorResponseBuilder,
)
from backbone.errors import ErrorCodes

ProcessResponseBuilder.created("uuid-123")
SimpleObjectResponseBuilder.found(product.to_dict())
PaginatedResponseBuilder.success(items, 100, 1, 10, "OK")
ErrorResponseBuilder.not_found("Product not found")
ErrorResponseBuilder.validation_error(
    "invalid request body",
    error_code=ErrorCodes.IFC_INVALID_REQUEST_BODY,
    field_errors={"name": "required"},
)
```

**Go usage:**
```go
import (
    "github.com/freakjazz/backbone-go/interfaces/responses"
    bberrors "github.com/freakjazz/backbone-go/errors"
)

responses.ProcessResponseBuilder.Created("uuid-123")
responses.SimpleObjectResponseBuilder.Found(productMap)
responses.PaginatedResponseBuilder.Success(items, 100, 1, 10, "OK")
responses.ErrorResponseBuilder.NotFound("Product not found")
responses.ErrorResponseBuilder.ValidationError("invalid request body",
    responses.ErrorOpts{
        FieldErrors: map[string]string{"name": "required"},
    },
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

**Python:**
```python
from backbone.domain.specifications import FilterParser, SortParser

spec  = FilterParser().parse_filters(["category,eq,Electronics,and", "price,gt,500"])
sorts = SortParser().parse_sort("price,desc").to_sort_criteria()

products = repo.find_by_criteria(filters=spec, sorts=sorts, page=1, page_size=10)
```

**Go:**
```go
import "github.com/freakjazz/backbone-go/domain/specifications"

sortField, sortDir := specifications.ParseSortBy("price:desc")
criteria := specifications.ParseFilterParams(
    []string{"category,eq,Electronics,and", "price,gt,500"},
    1, 10, sortField, sortDir,
)

products, _ := repo.FindByCriteria(ctx, criteria)
total, _    := repo.Count(ctx, criteria)
```

URL example:
```
GET /api/v1/products
  ?filters=category,eq,Electronics,and
  &filters=price,between,500|2000
  &filters=name,contains,laptop
  &page=1&page_size=10&sort_by=price:desc
```

---

## Logging

Both implementations emit the same JSON log shape.

**Python:**
```python
from backbone.infrastructure.logging import LoggerFactory, LogContext, with_log_context

logger = LoggerFactory.create_logger("my-service", environment="production")

with LogContext(request_id="abc-123", user_id="user-1"):
    logger.info("Processing", extra_data={"action": "create"})
    logger.error("Failed", exception=exc, error_code=10001001)

@with_log_context(operation="create_product")
def create(data): ...
```

**Go:**
```go
import "github.com/freakjazz/backbone-go/infrastructure/logging"

logger := logging.NewEnhancedLogger("my-service")

l := logger.
    WithLayer("application").
    WithHandler("CreateProductCommandHandler").
    WithMethod("Handle").
    WithContext(map[string]interface{}{"request_id": "abc-123"})

l.Info("Product created", map[string]interface{}{"product_id": "uuid"})
l.ErrorWithCode("Validation failed", 10001001, nil)
l.LogQuery("SELECT * FROM products WHERE id = $1", args, 12, nil)
```

JSON output (same shape in both):
```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "level": "INFO",
  "service": "my-service",
  "layer": "application",
  "component": "CreateProductCommandHandler",
  "method": "Handle",
  "message": "Processing",
  "request_id": "abc-123",
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

### Catálogo de códigos

| Código | Capa | Nombre | HTTP |
|---|---|---|---|
| `110000001` | Domain | BusinessRuleViolation | 422 |
| `110000002` | Domain | InvalidEntityState | 422 |
| `110000003` | Domain | InvalidValueObject | 422 |
| `110000004` | Domain | AggregateInconsistency | 409 |
| `110000005` | Domain | InvalidFilter | 400 |
| `120000001` | Application | UseCaseFailure | 500 |
| `120000002` | Application | ValidationFailure | 400 |
| `120000003` | Application | AuthorizationDenied | 403 |
| `120000004` | Application | ResourceNotFound | 404 |
| `120000005` | Application | ExternalServiceFailure | 502 |
| `120000006` | Application | Conflict | 409 |
| `130000001` | Interface | InvalidRequestBody | 400 |
| `130000002` | Interface | MethodNotAllowed | 405 |
| `130000003` | Interface | RouteNotFound | 404 |
| `130000004` | Interface | MissingRequiredParam | 400 |
| `130000005` | Interface | InvalidFilterFormat | 400 |
| `130000006` | Interface | Unauthorized | 401 |
| `130000007` | Interface | Forbidden | 403 |
| `140000001` | Infrastructure | DBFailure | 500 |
| `140000002` | Infrastructure | MessagingFailure | 500 |
| `140000003` | Infrastructure | CacheFailure | 500 |
| `140000004` | Infrastructure | ExternalAPIFailure | 502 |
| `140000005` | Infrastructure | ServiceUnavailable | 503 |

**Python:**
```python
from backbone.errors import ErrorCodes

# Referencia directa al catálogo
ErrorCodes.DOMAIN_BUSINESS_RULE_VIOLATION  # 110000001
ErrorCodes.APP_RESOURCE_NOT_FOUND          # 120000004
ErrorCodes.IFC_INVALID_REQUEST_BODY        # 130000001
ErrorCodes.INFRA_DB_FAILURE                # 140000001
```

**Go:**
```go
import bberrors "github.com/freakjazz/backbone-go/errors"

bberrors.DomainBusinessRuleViolation.Int()  // 110000001
bberrors.AppResourceNotFound.Int()          // 120000004
bberrors.IfcInvalidRequestBody.Int()        // 130000001
bberrors.InfraDBFailure.Int()               // 140000001
```

---

## Project structure — Clean Architecture + CQRS

Both implementations follow the same layered layout:

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
        ├── commands/          # HTTP adapter per command  (POST PUT DELETE PATCH)  [Python: commands/]
        ├── queries/           # HTTP adapter per query    (GET)                    [Python: queries/]
        └── v1/
            └── routes.*       # versioned route registration
```

`main.py` / `main.go` — DI container only. No business logic.

**Go DI container example:**
```go
func main() {
    repo := repositories.NewMemoryProductRepository(logger)
    seeders.NewProductSeeder(repo, logger).Run(ctx)

    createCmd := commands.NewCreateProductCommandHandler(repo, logger)
    updateCmd := commands.NewUpdateProductCommandHandler(repo, logger)

    getListQry  := queries.NewGetProductsQueryHandler(repo, logger)
    getByIDQry  := queries.NewGetProductByIDQueryHandler(repo, logger)

    cmdHandler := handlers.NewProductCommandHandler(createCmd, updateCmd, ...)
    qryHandler := handlers.NewProductQueryHandler(getListQry, getByIDQry, logger)

    mux := http.NewServeMux()
    v1.RegisterRoutes(mux, cmdHandler, qryHandler)
}
```

---

## Event bus (Go)

```go
import (
    "github.com/freakjazz/backbone-go/domain/ports"
    "github.com/freakjazz/backbone-go/infrastructure/messaging"
)

bus := messaging.NewInMemoryEventBus()

bus.Subscribe(ctx, "ProductCreated", func(e *ports.BaseEvent) error {
    fmt.Println(e.Data["id"])
    return nil
})

event := ports.NewBaseEvent("ProductCreated", "product-api",
    map[string]interface{}{"id": "uuid-123"}, "product-api", "create")
bus.Publish(ctx, event)
```

---

## Run examples

```bash
# Python
cd examples/python/clean_api_python
pip install flask flask-restx
python main.py          # → http://localhost:5000/docs

# Go
cd examples/go/clean-api-go
go mod tidy
swag init               # genera docs Swagger
go run main.go          # → http://localhost:8005/docs/index.html
```

---

## Related

- [backbone-python — detailed docs](./backbone-python/README.md)
- [backbone-go — detailed docs](./backbone-go/README.md)
