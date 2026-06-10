# backbone-go

Clean Architecture kernel for Go microservices — mirrors [backbone (Python)](../README.md) exactly.

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
│   ├── exceptions/      # 8-digit exception codes (11xxxxxx domain)
│   ├── ports/           # EventBus / EventStore interfaces
│   ├── repositories/    # Repository interfaces
│   └── specifications/  # Specification + Criteria + QueryObject patterns
├── application/
│   └── exceptions/      # 8-digit exception codes (10xxxxxx application)
├── infrastructure/
│   ├── config/          # Environment-based config (viper)
│   ├── logging/         # Structured JSON logger (same shape as Python)
│   ├── messaging/       # InMemory / Kafka / Redis event bus adapters
│   └── events/          # File-based event store
└── interfaces/
    └── responses/       # Response builders (no framework dependency)
```

---

## Quick Start

```go
package main

import (
    "github.com/freakjazz/backbone-go/infrastructure/logging"
    "github.com/freakjazz/backbone-go/interfaces/responses"
    "github.com/freakjazz/backbone-go/domain/exceptions"
)

func main() {
    logger := logging.NewEnhancedLogger("my-service")

    // --- Logging ---
    logger.Info("Server starting", map[string]interface{}{"port": 8080})

    handlerLog := logger.
        WithLayer("interfaces").
        WithHandler("UserHandler").
        WithMethod("CreateUser").
        WithContext(map[string]interface{}{"request_id": "abc-123"})

    handlerLog.Info("Creating user", nil)

    // --- Exceptions ---
    err := exceptions.NewDomainException(11001001, "Name too short", nil)
    handlerLog.ErrorWithCode(err.Error(), err.Code, nil)

    // --- Response builders ---

    // POST / PUT / DELETE → {"id": "uuid"}
    created := responses.ProcessResponseBuilder.Created("uuid-123")
    updated := responses.ProcessResponseBuilder.Updated("uuid-123")
    deleted := responses.ProcessResponseBuilder.Deleted("uuid-123")

    // GET single → raw object
    product := responses.SimpleObjectResponseBuilder.Found(map[string]interface{}{
        "id": "uuid-123", "name": "Laptop",
    })

    // GET list → paginated envelope
    list := responses.PaginatedResponseBuilder.Success(
        []map[string]interface{}{{"id": "1"}, {"id": "2"}},
        100, 1, 10,
        "Products retrieved successfully",
    )

    // Errors → flat contract
    notFound  := responses.ErrorResponseBuilder.NotFound("Product not found")
    badReq    := responses.ErrorResponseBuilder.ValidationError("Invalid input", map[string]string{"name": "required"})
    serverErr := responses.ErrorResponseBuilder.InternalServerError("")
    _ = created; _ = updated; _ = deleted; _ = product; _ = list
    _ = notFound; _ = badReq; _ = serverErr
}
```

---

## Response Contracts

All contracts are identical to the Python backbone.

### Create / Update / Delete
```json
{"id": "uuid-123"}
```
HTTP status: `201` (create) or `200` (update / delete).

### GET single resource
```json
{
  "id": "uuid-123",
  "name": "Laptop",
  "price": 1500.00
}
```
Raw object — no envelope.

### GET list (paginated)
```json
{
  "meta": {
    "status": "success",
    "status_code": 200,
    "message": "Products retrieved successfully"
  },
  "items": [{"id": "1"}, {"id": "2"}],
  "pagination": {
    "total_count": 100,
    "page": 1,
    "page_size": 10,
    "total_pages": 10
  }
}
```

### Error
```json
{
  "request_id": "uuid",
  "status_code": 400,
  "message": "Validation failed",
  "code_error": "VALIDATION_ERROR",
  "field_errors": {"name": "required"}
}
```

---

## Logging

Same JSON shape as Python backbone.

```go
logger := logging.NewEnhancedLogger("my-service")

// Scoped logger (fluent, immutable)
l := logger.
    WithLayer("infrastructure").
    WithComponent("ProductRepository").
    WithMethod("FindByID").
    WithContext(map[string]interface{}{"request_id": "abc"})

l.Info("Query executed", map[string]interface{}{"duration_ms": 12})
l.ErrorWithCode("Not found", 12001001, nil)
l.LogQuery("SELECT * FROM products WHERE id = $1", []interface{}{"abc"}, 12, nil)
```

Log entry JSON:
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "service": "my-service",
  "component": "ProductRepository",
  "layer": "infrastructure",
  "method": "FindByID",
  "message": "Query executed",
  "request_id": "abc",
  "environment": "development",
  "extra_data": {"duration_ms": 12}
}
```

---

## Exception System (8 digits)

```
Layer codes:
  10xxxxxx  Application
  11xxxxxx  Domain
  12xxxxxx  Infrastructure
  13xxxxxx  Interfaces
```

```go
import "github.com/freakjazz/backbone-go/domain/exceptions"

err := exceptions.NewDomainException(
    11001001,
    "Product name must be at least 3 characters",
    map[string]interface{}{"field": "name", "value": "ab"},
)
```

---

## Specification + Criteria Pattern

```go
import "github.com/freakjazz/backbone-go/domain/specifications"

criteria := specifications.NewCriteriaBuilder().
    Where("category", "=", "Electronics").
    Where("active", "=", true).
    WhereBetween("price", 500.0, 2000.0).
    OrderByDesc("created_at").
    Paginate(1, 10).
    Build()

sql, args := criteria.GetFullSQL("SELECT * FROM products")
```

---

## Event Bus

```go
import (
    "github.com/freakjazz/backbone-go/domain/ports"
    "github.com/freakjazz/backbone-go/infrastructure/messaging"
)

bus := messaging.NewInMemoryEventBus()

bus.Subscribe(ctx, "ProductCreated", func(e *ports.BaseEvent) error {
    fmt.Println("Product created:", e.Data["id"])
    return nil
})

event := ports.NewBaseEvent("ProductCreated", "product-api", map[string]interface{}{"id": "123"}, "product-api", "create")
bus.Publish(ctx, event)
```

---

## Full CRUD Example

See [`examples/clean-api-go/`](./examples/clean-api-go/) for a complete working API:

```bash
cd examples/clean-api-go
go run main.go
```

Endpoints: `POST /api/products` · `GET /api/products` · `GET /api/products/{id}` · `PUT /api/products/{id}` · `DELETE /api/products/{id}` · `PATCH /api/products/{id}/status`

---

## Related

- [backbone (Python)](../README.md)
- [Examples](../examples/README.md)
