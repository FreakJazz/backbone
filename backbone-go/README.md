# backbone-go

> Lightweight Go library for standardising **error codes, HTTP responses, structured logs, and filter specifications** across microservices following Clean Architecture.

![Go](https://img.shields.io/badge/go-1.21%2B-00ADD8?logo=go)
![Version](https://img.shields.io/badge/version-v0.1.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-beta-orange)

---

## The problem it solves

In a microservices ecosystem every team invents its own error shape, log format, and filter syntax. After six services you have six different conventions. backbone-go gives every service the same contracts so that monitoring dashboards, API gateways, and client SDKs never have to guess the shape of a response.

---

## Installation

```bash
go get github.com/freakjazz/backbone-go@v0.1.0
```

**Requirements:** Go 1.21+

---

## Project structure

```
backbone-go/
├── domain/
│   ├── exceptions/          # domain exception types
│   ├── ports/               # EventBus, EventStore interfaces
│   ├── repositories/        # IRepository, IReadOnlyRepository interfaces
│   └── specifications/      # Specification + Criteria + FilterParser
├── application/
│   └── exceptions/          # application exception types
├── errors/
│   └── codes.go             # 9-digit error code catalogue
├── infrastructure/
│   ├── config/              # viper-based configuration
│   ├── events/              # file-based event store
│   ├── logging/             # StructuredLogger + JSONFormatter / ConsoleFormatter
│   └── messaging/           # InMemory / Kafka / RabbitMQ / Redis adapters
├── interfaces/
│   └── responses/           # ProcessResponseBuilder, ErrorResponseBuilder, ...
└── tests/                   # mirror of source tree, one test per package
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

```go
import bberrors "github.com/freakjazz/backbone-go/errors"

// Domain
bberrors.DomainBusinessRuleViolation.Int()  // 110000001
bberrors.DomainInvalidEntityState.Int()     // 110000002
bberrors.DomainInvalidFilter.Int()          // 110000005

// Application
bberrors.AppResourceNotFound.Int()          // 120000004
bberrors.AppConflict.Int()                  // 120000006

// Interface
bberrors.IfcInvalidRequestBody.Int()        // 130000001
bberrors.IfcRouteNotFound.Int()             // 130000003
bberrors.IfcUnauthorized.Int()              // 130000006

// Infrastructure
bberrors.InfraDBFailure.Int()               // 140000001
bberrors.InfraMessagingFailure.Int()        // 140000002
```

Extend the catalogue for your own service without touching backbone:

```go
var MyCustomDomainError = bberrors.New(bberrors.LayerDomain, 1001) // 110001001
```

---

## Response builders

All responses follow a strict contract — **no surprise fields**.

### Error response — always `{rid, status_code, message, error_code}`

```go
import (
    "github.com/freakjazz/backbone-go/interfaces/responses"
    bberrors "github.com/freakjazz/backbone-go/errors"
)

// 400 Bad Request
e := responses.ErrorResponseBuilder.ValidationError("name must be at least 2 characters",
    responses.ErrorOpts{Code: bberrors.IfcInvalidRequestBody.Int()})
// {"rid":"a8b3...","status_code":400,"message":"name must be at least 2 characters","error_code":130000001}

// 404 Not Found
e = responses.ErrorResponseBuilder.NotFound("product not found",
    responses.ErrorOpts{Code: bberrors.AppResourceNotFound.Int()})
// {"rid":"...","status_code":404,"message":"product not found","error_code":120000004}

// 409 Conflict
e = responses.ErrorResponseBuilder.Conflict("a product with that name already exists",
    responses.ErrorOpts{Code: bberrors.AppConflict.Int()})
// {"rid":"...","status_code":409,"message":"a product with that name already exists","error_code":120000006}

// 401 / 403 / 500
e = responses.ErrorResponseBuilder.Unauthorized("token expired")
e = responses.ErrorResponseBuilder.Forbidden("insufficient permissions")
e = responses.ErrorResponseBuilder.InternalError("unexpected failure")
```

### Success responses

```go
// POST / PUT / DELETE / PATCH
created := responses.ProcessResponseBuilder.Created("product-uuid-123")
// {"id":"product-uuid-123"}

updated := responses.ProcessResponseBuilder.Updated("product-uuid-123")
// {"id":"product-uuid-123"}

// GET single — raw object, no envelope
product := responses.SimpleObjectResponseBuilder.Found(productMap)
// {"id":"uuid","name":"Laptop Pro","price":1500.0}

// GET list
list := responses.PaginatedResponseBuilder.Found(items, meta, pagination)
// {"meta":{...},"items":[...],"pagination":{...}}
```

---

## Structured logging

Three formatters ship out of the box — swap without touching your log calls.

```go
import "github.com/freakjazz/backbone-go/infrastructure/logging"

// Production default: JSON lines for ELK / Loki / CloudWatch
logger := logging.NewLogger("products-service")

// Development: coloured, human-readable
logger.SetFormatter(logging.NewConsoleFormatter())
// 2026-06-16 10:23:45 [INFO    ] products-service > ProductHandler | product created  {"product_id":"123"}

// High-throughput: compact JSON, fewer bytes per line
logger.SetFormatter(&logging.CompactJSONFormatter{})
// {"ts":"2026-06-16T10:23:45Z","level":"INFO","service":"products-service","msg":"product created"}

// Scoped context — propagates to all child log calls
scoped := logger.WithContext(map[string]interface{}{
    "request_id": rid,
    "user_id":    userID,
})
scoped.Info("product created", map[string]interface{}{"product_id": "123"})
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

> The JSON shape is **identical** to backbone-python — both services feed the same ELK index without remapping.

---

## Filter specifications

Four generic query params — no hard-coded field names in your router.

| Param       | Format                             | Example           |
|-------------|------------------------------------|-------------------|
| `filters`   | `field,operator,value[,condition]` | `price,gt,500,and`|
| `page`      | integer                            | `1`               |
| `page_size` | integer                            | `20`              |
| `sort_by`   | `field:direction`                  | `created_at:desc` |

Supported operators: `eq` `ne` `gt` `gte` `lt` `lte` `contains` `in` `between` `is_null` `is_not_null`

```go
import "github.com/freakjazz/backbone-go/domain/specifications"

sortField, sortDir := specifications.ParseSortBy(r.URL.Query().Get("sort_by"))
criteria := specifications.ParseFilterParams(
    r.URL.Query()["filters"],
    page, pageSize, sortField, sortDir,
)

products, _ := repo.FindByCriteria(ctx, criteria)
total, _    := repo.Count(ctx, criteria)
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

## Event bus

```go
import (
    "github.com/freakjazz/backbone-go/domain/ports"
    "github.com/freakjazz/backbone-go/infrastructure/messaging"
)

bus := messaging.NewInMemoryEventBus()

bus.Subscribe(ctx, "ProductCreated", func(e *ports.BaseEvent) error {
    fmt.Println("received:", e.Data["product_id"])
    return nil
})

event := ports.NewBaseEvent("ProductCreated", "products-service",
    map[string]interface{}{"product_id": "uuid-123"}, "products-service", "create-product")
bus.Publish(ctx, event)
```

---

## Clean Architecture example

```
examples/go/clean-api-go/
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
    ├── handlers/           # ProductCommandHandler, ProductQueryHandler
    └── v1/routes.go        # route registration
```

```bash
cd examples/go/clean-api-go
go mod tidy && swag init && go run main.go
# http://localhost:8005/docs/index.html
```

---

## Running tests

```bash
go test ./...
```

All 8 packages pass: `tests`, `tests/application/exceptions`, `tests/domain/exceptions`, `tests/domain/ports`, `tests/domain/specifications`, `tests/infrastructure/logging`, `tests/infrastructure/messaging`, `tests/interfaces/responses`.

---

## Companion library

[backbone-python](../backbone-python/README.md) — identical JSON contracts, Python implementation.

---

## Version

`v0.1.0` — public beta. API stabilises at `v1.0.0`.

## License

MIT © [FreakJazz](https://github.com/FreakJazz)
