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

## Architecture

```
backbone-go/
├── domain/
│   ├── exceptions/      # 8-digit codes (11xxxxxx domain)
│   ├── ports/           # EventBus / EventStore interfaces
│   ├── repositories/    # Repository interfaces
│   └── specifications/  # Specification + Criteria + FilterParam + ParseFilterParams
├── application/
│   └── exceptions/      # 8-digit codes (10xxxxxx application)
├── infrastructure/
│   ├── config/          # Environment config (viper)
│   ├── logging/         # Structured JSON logger (same shape as Python)
│   ├── messaging/       # InMemory / Kafka / Redis event bus
│   └── events/          # File-based event store
└── interfaces/
    └── responses/       # Response builders (no framework dependency)
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
│   ├── commands/        ← write side: XxxCommand + XxxCommandHandler
│   └── queries/         ← read side:  XxxQuery   + XxxQueryHandler
├── infrastructure/
│   ├── repositories/    ← concrete implementations
│   └── seeders/         ← data seeders (not in main.go)
└── interfaces/
    └── http/
        ├── handlers/
        │   ├── xxx_command_handler.go  ← POST PUT DELETE PATCH
        │   └── xxx_query_handler.go    ← GET (list + by id)
        └── v1/
            └── routes.go               ← versioned route registration
```

`main.go` — DI container only: infra → cmd handlers → qry handlers → HTTP adapters → routes.

---

## Quick Start

```go
package main

import (
    "github.com/freakjazz/backbone-go/infrastructure/logging"
    "github.com/freakjazz/backbone-go/interfaces/responses"
    "github.com/freakjazz/backbone-go/domain/specifications"
)

func main() {
    logger := logging.NewEnhancedLogger("my-service")

    // Scoped logger — fluent, immutable
    l := logger.
        WithLayer("application").
        WithHandler("CreateProductCommandHandler").
        WithMethod("Handle").
        WithContext(map[string]interface{}{"request_id": "abc-123"})

    l.Info("Handling command", nil)

    // Write → {"id": "uuid"}
    created := responses.ProcessResponseBuilder.Created("uuid-123")   // HTTP 201
    updated := responses.ProcessResponseBuilder.Updated("uuid-123")   // HTTP 200
    deleted := responses.ProcessResponseBuilder.Deleted("uuid-123")   // HTTP 200

    // Read single → raw object
    product := responses.SimpleObjectResponseBuilder.Found(map[string]interface{}{
        "id": "uuid-123", "name": "Laptop",
    })

    // Read list → paginated envelope
    list := responses.PaginatedResponseBuilder.Success(
        []map[string]interface{}{{"id": "1"}},
        100, 1, 10, "Products retrieved successfully",
    )

    // Error → flat contract
    notFound := responses.ErrorResponseBuilder.NotFound("Product not found")
    badReq   := responses.ErrorResponseBuilder.ValidationError("Invalid input",
        map[string]string{"name": "required"})
    _ = created; _ = updated; _ = deleted; _ = product; _ = list; _ = notFound; _ = badReq
}
```

---

## Response Contracts

### Write (create / update / delete)
```json
{"id": "uuid-123"}
```

### GET single
```json
{"id": "uuid-123", "name": "Laptop", "price": 1500.0}
```

### GET list
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

```go
import "github.com/freakjazz/backbone-go/domain/specifications"

sortField, sortDir := specifications.ParseSortBy(query.SortBy)
criteria := specifications.ParseFilterParams(query.Filters, page, pageSize, sortField, sortDir)

products, err := repo.FindByCriteria(ctx, criteria)
total,    err := repo.Count(ctx, criteria)
```

---

## Logging

```go
logger := logging.NewEnhancedLogger("my-service")

l := logger.
    WithLayer("infrastructure").
    WithHandler("ProductRepository").
    WithMethod("FindByCriteria").
    WithContext(map[string]interface{}{"request_id": "abc"})

l.Info("Query executed", map[string]interface{}{"duration_ms": 12})
l.ErrorWithCode("Not found", 12001001, nil)
l.LogQuery("SELECT * FROM products WHERE id = $1", []interface{}{"abc"}, 12, nil)
```

Log JSON (same shape as Python backbone):
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "service": "my-service",
  "component": "ProductRepository",
  "layer": "infrastructure",
  "method": "FindByCriteria",
  "message": "Query executed",
  "request_id": "abc",
  "environment": "development",
  "extra_data": {"duration_ms": 12}
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

```go
import "github.com/freakjazz/backbone-go/domain/exceptions"

err := exceptions.NewDomainException(11001001, "Name too short", nil)
```

---

## Full CRUD Example

```bash
cd examples/clean-api-go
go run main.go
# → http://localhost:8080
# → http://localhost:8080/swagger/
```

---

## Related

- [backbone (Python)](../README.md)
- [Examples comparison](../examples/README.md)
