# backbone-go

Clean Architecture + CQRS kernel for Go microservices — identical contracts to [backbone (Python)](../README.md).

![Go](https://img.shields.io/badge/go-1.21%2B-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## Installation

```bash
go get github.com/freakjazz/backbone-go
```

---

## What it provides

| Package | Purpose |
|---|---|
| `domain/specifications` | `FilterParam` · `ParseFilterParams` · `ParseSortBy` · Specification + Criteria pattern |
| `domain/exceptions` | 8-digit exception codes by layer |
| `domain/repositories` | Repository interfaces |
| `domain/ports` | `EventBus` · `EventStore` · `BaseEvent` |
| `application/exceptions` | Application-layer exceptions |
| `infrastructure/logging` | Structured JSON logger (`EnhancedLogger`) |
| `infrastructure/messaging` | InMemory · Kafka · Redis event bus |
| `infrastructure/events` | File-based event store |
| `infrastructure/config` | Environment config (viper) |
| `interfaces/responses` | HTTP response builders (no framework dependency) |

---

## Response contracts

Identical to Python backbone.

### Write — `POST` `PUT` `DELETE` `PATCH`
```json
{ "id": "uuid-123" }
```

### GET single
```json
{ "id": "uuid-123", "name": "Laptop", "price": 1500.0 }
```

### GET list
```json
{
  "meta":       { "status": "success", "status_code": 200, "message": "..." },
  "items":      [{ "id": "1" }],
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

JSON output (same shape as Python):
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "service": "my-service",
  "component": "CreateProductCommandHandler",
  "layer": "application",
  "method": "Handle",
  "message": "Product created",
  "request_id": "abc-123",
  "extra_data": { "product_id": "uuid" }
}
```

---

## Exception system — códigos de 9 dígitos

Formato: `LL_NNNNNNN` donde `LL` = prefijo de capa, `NNNNNNN` = secuencia de 7 dígitos.

```
11xxxxxxx  Domain          12xxxxxxx  Application
13xxxxxxx  Interface       14xxxxxxx  Infrastructure
```

| Código | Capa | Constante Go |
|---|---|---|
| `110000001` | Domain | `bberrors.DomainBusinessRuleViolation` |
| `110000002` | Domain | `bberrors.DomainInvalidEntityState` |
| `110000003` | Domain | `bberrors.DomainInvalidValueObject` |
| `110000004` | Domain | `bberrors.DomainAggregateInconsistency` |
| `110000005` | Domain | `bberrors.DomainInvalidFilter` |
| `120000001` | Application | `bberrors.AppUseCaseFailure` |
| `120000002` | Application | `bberrors.AppValidationFailure` |
| `120000003` | Application | `bberrors.AppAuthorizationDenied` |
| `120000004` | Application | `bberrors.AppResourceNotFound` |
| `120000005` | Application | `bberrors.AppExternalServiceFailure` |
| `120000006` | Application | `bberrors.AppConflict` |
| `130000001` | Interface | `bberrors.IfcInvalidRequestBody` |
| `130000002` | Interface | `bberrors.IfcMethodNotAllowed` |
| `130000003` | Interface | `bberrors.IfcRouteNotFound` |
| `130000004` | Interface | `bberrors.IfcMissingRequiredParam` |
| `130000005` | Interface | `bberrors.IfcInvalidFilterFormat` |
| `130000006` | Interface | `bberrors.IfcUnauthorized` |
| `130000007` | Interface | `bberrors.IfcForbidden` |
| `140000001` | Infrastructure | `bberrors.InfraDBFailure` |
| `140000002` | Infrastructure | `bberrors.InfraMessagingFailure` |
| `140000003` | Infrastructure | `bberrors.InfraCacheFailure` |
| `140000004` | Infrastructure | `bberrors.InfraExternalAPIFailure` |
| `140000005` | Infrastructure | `bberrors.InfraServiceUnavailable` |

```go
import bberrors "github.com/freakjazz/backbone-go/errors"

bberrors.DomainBusinessRuleViolation.Int()  // 110000001
bberrors.AppResourceNotFound.Int()          // 120000004
bberrors.IfcInvalidRequestBody.Int()        // 130000001
bberrors.InfraDBFailure.Int()               // 140000001
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
        ├── handlers/
        │   ├── product_command_handler.go  # POST PUT DELETE PATCH
        │   └── product_query_handler.go    # GET
        └── v1/
            └── routes.go                   # versioned route registration
```

`main.go` — DI container only. No business logic.

```go
func main() {
    // 1. Infrastructure
    repo := repositories.NewMemoryProductRepository(logger)
    seeders.NewProductSeeder(repo, logger).Run(ctx)

    // 2. Commands (write side)
    createCmd := commands.NewCreateProductCommandHandler(repo, logger)
    updateCmd := commands.NewUpdateProductCommandHandler(repo, logger)

    // 3. Queries (read side)
    getListQry  := queries.NewGetProductsQueryHandler(repo, logger)
    getByIDQry  := queries.NewGetProductByIDQueryHandler(repo, logger)

    // 4. HTTP adapters
    cmdHandler := handlers.NewProductCommandHandler(createCmd, updateCmd, ...)
    qryHandler := handlers.NewProductQueryHandler(getListQry, getByIDQry, logger)

    // 5. Routes
    mux := http.NewServeMux()
    v1.RegisterRoutes(mux, cmdHandler, qryHandler)
}
```

---

## Event bus

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

## Full example

```bash
cd examples/clean-api-go
go mod tidy
go run main.go
# → http://localhost:8080
# → http://localhost:8080/swagger/
```

---

## Related

- [backbone (Python)](../README.md)
- [Examples](../examples/README.md)
