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
  "request_id":  "uuid",
  "status_code": 404,
  "message":     "Product not found",
  "code_error":  "NOT_FOUND",
  "field_errors": { "name": "required" }
}
```

Usage:
```go
import "github.com/freakjazz/backbone-go/interfaces/responses"

responses.ProcessResponseBuilder.Created("uuid-123")
responses.SimpleObjectResponseBuilder.Found(productMap)
responses.PaginatedResponseBuilder.Success(items, 100, 1, 10, "OK")
responses.ErrorResponseBuilder.NotFound("Product not found")
responses.ErrorResponseBuilder.ValidationError("Invalid input", map[string]string{"name": "required"})
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

## Exception system — 8-digit codes

```
10xxxxxx  Application     11xxxxxx  Domain
12xxxxxx  Infrastructure  13xxxxxx  Interfaces
```

```go
import "github.com/freakjazz/backbone-go/domain/exceptions"

err := exceptions.NewDomainException(11001001, "Name too short", nil)
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
