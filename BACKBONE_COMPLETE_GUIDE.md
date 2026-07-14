# Backbone: The Complete Microservices Standardization Framework for Go & Python

**Unified error handling, filtering patterns, structured logging, and testing strategies for distributed systems**

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [Quick Start (5 minutes)](#quick-start-5-minutes)
- [Part 1: Error Handling System](#part-1-error-handling-system)
  - 1.1 The 9-Digit Error Code Format
  - 1.2 Error Response Contract
  - 1.3 Input Validation Integration
  - 1.4 Implementation in Go & Python
- [Part 2: Unified Query & Filtering](#part-2-unified-query--filtering)
  - 2.1 The Specification Pattern
  - 2.2 Implementation in Go & Python
  - 2.3 Repository Pattern
- [Part 3: Structured Logging](#part-3-structured-logging)
  - 3.1 Unified Log Schema
  - 3.2 Three Formatters
  - 3.3 RID Propagation
  - 3.4 Implementation in Go & Python
- [Testing Strategy](#testing-strategy)
- [API Versioning](#api-versioning)
- [Database Agnosticity](#database-agnosticity)
- [Production Checklist](#production-checklist)
- [FAQ & Glossary](#faq--glossary)

---

## Executive Summary

When you build microservices, you solve the same problems six times:

1. **Error handling** — Every service returns errors differently
2. **Query filtering** — Every service implements pagination differently  
3. **Logging** — Every service emits logs in a different format
4. **Testing** — Every service has a different testing strategy
5. **Versioning** — Every service breaks clients differently
6. **Database choice** — Every service is locked to one database

**backbone solves all of these with a single framework available in Go and Python.**

Every service uses the same error codes, the same query operators, the same log shape, and the same response contracts. Your frontend doesn't need to learn six APIs. Your operations team doesn't need six alert rules. Your database choice doesn't lock your architecture.

This document explains how.

---

## Quick Start (5 minutes)

### Install

```bash
# Go
go get github.com/freakjazz/backbone-go@v0.1.0

# Python
pip install backbone-python==0.1.0
```

### Basic Error Response

Every error has exactly four fields:

```json
{
  "rid":         "a8866c5e750643dab7cd2a8927bbcc08",
  "status_code": 409,
  "error_code":  120000006,
  "message":     "a product with that name already exists"
}
```

**Go:**
```go
import (
    bberrors "github.com/freakjazz/backbone-go/errors"
    "github.com/freakjazz/backbone-go/interfaces/responses"
)

e := responses.ErrorResponseBuilder.Conflict("already exists",
    responses.ErrorOpts{Code: bberrors.AppConflict.Int()})
w.Header().Set("Content-Type", "application/json")
json.NewEncoder(w).Encode(e)
```

**Python:**
```python
from backbone import ErrorResponseBuilder
from backbone.errors import ErrorCodes

err = ErrorResponseBuilder.conflict(
    "already exists",
    error_code=ErrorCodes.APP_CONFLICT)
return jsonify(err), 409
```

### Basic Query Filtering

Every list endpoint accepts the same four params:

```
GET /api/v1/products
  ?filters=category,eq,Electronics,and
  &filters=price,between,500|2000
  &page=1&page_size=10&sort_by=price:desc
```

### Basic Logging

Every log is the same JSON shape:

```json
{
  "timestamp":  "2026-06-17T10:23:45Z",
  "level":      "INFO",
  "service":    "products-service",
  "component":  "ProductCommandHandler",
  "message":    "product created",
  "request_id": "a8866c5e750643dab7cd2a8927bbcc08",
  "extra_data": {"product_id": "uuid-123"}
}
```

---

# PART 1: Error Handling System

## 1.1 The 9-Digit Error Code Format

### The Problem With String Codes

```python
raise NotFoundException("User not found", error_code="USER_NOT_FOUND")
```

This works until you have 12 services and 200 error codes:

- Nobody knows which codes already exist
- `USER_NOT_FOUND` in service A and `USER_404` in service B mean the same thing
- You cannot tell from a log which architectural layer the error came from
- Monitoring alerts cannot distinguish a domain rule violation from a database outage

### The Solution: Layer-Prefixed Codes

backbone uses a simple but powerful format: `LL_NNNNNNN`

- `LL` = 2-digit **layer prefix** (which architectural layer owns the error)
- `NNNNNNN` = 7-digit **sequence** within that layer

```
11_xxxxxxx  →  Domain layer        (business rules, entities, value objects)
12_xxxxxxx  →  Application layer   (use cases, commands, queries)
13_xxxxxxx  →  Interface layer     (HTTP handlers, gRPC adapters)
14_xxxxxxx  →  Infrastructure      (databases, messaging, external APIs)
```

When you see `120000006` in a log or Kibana alert, you immediately know:

- Layer `12` → Application layer
- Error `6` in that layer → Conflict

No grepping. No lookup table. **The code tells you where the error came from.**

### Complete Error Catalogue

| Code        | Layer          | Name                    | HTTP |
|-------------|----------------|-------------------------|------|
| `110000001` | Domain         | BusinessRuleViolation   | 422  |
| `110000002` | Domain         | InvalidEntityState      | 422  |
| `110000003` | Domain         | InvalidValueObject      | 422  |
| `110000004` | Domain         | AggregateInconsistency  | 409  |
| `110000005` | Domain         | InvalidFilter           | 400  |
| `120000001` | Application    | UseCaseFailure          | 500  |
| `120000002` | Application    | ValidationFailure       | 400  |
| `120000003` | Application    | AuthorizationDenied     | 403  |
| `120000004` | Application    | ResourceNotFound        | 404  |
| `120000005` | Application    | ExternalServiceFailure  | 502  |
| `120000006` | Application    | Conflict                | 409  |
| `130000001` | Interface      | InvalidRequestBody      | 400  |
| `130000002` | Interface      | MethodNotAllowed        | 405  |
| `130000003` | Interface      | RouteNotFound           | 404  |
| `130000004` | Interface      | MissingRequiredParam    | 400  |
| `130000005` | Interface      | InvalidFilterFormat     | 400  |
| `130000006` | Interface      | Unauthorized            | 401  |
| `130000007` | Interface      | Forbidden               | 403  |
| `140000001` | Infrastructure | DBFailure               | 500  |
| `140000002` | Infrastructure | MessagingFailure        | 500  |
| `140000003` | Infrastructure | CacheFailure            | 500  |
| `140000004` | Infrastructure | ExternalAPIFailure      | 502  |
| `140000005` | Infrastructure | ServiceUnavailable      | 503  |

## 1.2 Error Response Contract

The error response shape is **fixed. Always exactly four fields.**

```json
{
  "rid":         "a8866c5e750643dab7cd2a8927bbcc08",
  "status_code": 409,
  "error_code":  120000006,
  "message":     "a product with that name already exists"
}
```

**No `field_errors`. No `data` wrapper. No `detail`. No `errors` array.**

The contract never changes shape regardless of which service returns it or which language it is written in.

### What is RID?

`rid` is a **request ID** — the thread that connects everything that happened during a single HTTP request, across every service that touched it.

Example: A user clicks "Buy" and your frontend calls the orders service, which calls inventory, which calls payments. If payments fails, you have four separate services. Without a shared `rid`, you cannot correlate them:

```
[orders-service]     INFO  creating order          rid=a8866c5e  product_id=123
[inventory-service]  INFO  reserving stock         rid=a8866c5e  product_id=123
[payments-service]   ERROR charge failed           rid=a8866c5e  reason="card declined"
[orders-service]     ERROR order creation failed   rid=a8866c5e  error_code=120000005
```

**One query in Kibana — `rid: a8866c5e` — and you see the entire journey.**

### Success Response Contracts

Error is not the only contract backbone enforces.

**Write operations** return just the ID:
```json
{ "id": "product-uuid-123" }
```

**GET single resource** returns the raw object with no envelope:
```json
{ "id": "uuid", "name": "Laptop Pro", "price": 1500.0, "status": "active" }
```

**GET list** returns meta, items, and pagination:
```json
{
  "meta":       { "status": "success", "status_code": 200, "message": "OK" },
  "items":      [{ "id": "1", "name": "Laptop" }],
  "pagination": { "total_count": 100, "page": 1, "page_size": 10 }
}
```

## 1.3 Input Validation Integration

Validation errors use the same contract:

```json
{
  "rid":         "a8866c5e750643dab7cd2a8927bbcc08",
  "status_code": 400,
  "error_code":  130000001,
  "message":     "invalid request body",
  "extra_data":  {
    "failed_fields": {
      "name":  "must be 2-50 characters",
      "email": "invalid email format",
      "price": "must be greater than 0"
    }
  }
}
```

Error code `130000001` = `IFC_INVALID_REQUEST_BODY`.

### Go: Validation Example

```go
type CreateProductRequest struct {
    Name     string  `json:"name"`
    Price    float64 `json:"price"`
    Category string  `json:"category"`
}

func (r *CreateProductRequest) Validate() map[string]string {
    failed := make(map[string]string)

    if len(r.Name) < 2 || len(r.Name) > 50 {
        failed["name"] = "must be 2-50 characters"
    }
    if r.Price <= 0 {
        failed["price"] = "must be greater than 0"
    }

    return failed
}

func (h *ProductHandler) CreateProduct(w http.ResponseWriter, r *http.Request) {
    var req CreateProductRequest
    json.NewDecoder(r.Body).Decode(&req)

    if failed := req.Validate(); len(failed) > 0 {
        e := responses.ErrorResponseBuilder.InvalidRequestBody(
            "validation failed",
            responses.ErrorOpts{
                Code: bberrors.IfcInvalidRequestBody.Int(),
                ExtraData: map[string]interface{}{
                    "failed_fields": failed,
                },
            },
        )
        json.NewEncoder(w).Encode(e)
        return
    }

    // Validation passed
    json.NewEncoder(w).Encode(responses.ProcessResponseBuilder.Created(result.ID))
}
```

### Python: Validation Example

```python
class CreateProductRequest:
    def __init__(self, data: dict):
        self.name = data.get("name", "").strip()
        self.price = data.get("price")
        self.category = data.get("category", "").strip()

    def validate(self) -> Dict[str, str]:
        failed = {}
        if len(self.name) < 2 or len(self.name) > 50:
            failed["name"] = "must be 2-50 characters"
        if not isinstance(self.price, (int, float)) or self.price <= 0:
            failed["price"] = "must be greater than 0"
        return failed

@bp.route("", methods=["POST"])
def create_product():
    data = request.get_json()
    req = CreateProductRequest(data)
    
    if failed := req.validate():
        err = ErrorResponseBuilder.invalid_request_body(
            "validation failed",
            error_code=ErrorCodes.IFC_INVALID_REQUEST_BODY,
            extra_data={"failed_fields": failed}
        )
        return jsonify(err), 400

    return jsonify(ProcessResponseBuilder.created(result.id)), 201
```

## 1.4 Implementation in Go & Python

### Go: Using Error Codes

```go
import bberrors "github.com/freakjazz/backbone-go/errors"

type ErrorCode int

// New returns a valid 9-digit ErrorCode
func New(layer, number int) ErrorCode {
    if layer < 11 || layer > 19 {
        return 0
    }
    if number < 1 || number > 9_999_999 {
        return 0
    }
    return ErrorCode(layer*10_000_000 + number)
}

// Layer prefixes
const (
    LayerDomain         = 11
    LayerApplication    = 12
    LayerInterface      = 13
    LayerInfrastructure = 14
)

// Error codes
var (
    DomainBusinessRuleViolation = New(LayerDomain, 1)        // 110000001
    AppConflict                 = New(LayerApplication, 6)   // 120000006
    IfcInvalidRequestBody       = New(LayerInterface, 1)     // 130000001
    InfraDBFailure              = New(LayerInfrastructure, 1) // 140000001
)
```

### Python: Using Error Codes

```python
from backbone.errors import ErrorCodes

class ErrorCodes:
    # Domain (11)
    DOMAIN_BUSINESS_RULE_VIOLATION  = 110000001
    
    # Application (12)
    APP_CONFLICT                    = 120000006
    
    # Interface (13)
    IFC_INVALID_REQUEST_BODY        = 130000001
    
    # Infrastructure (14)
    INFRA_DB_FAILURE                = 140000001

    @staticmethod
    def layer(code: int) -> int:
        return code // 10_000_000
```

---

# PART 2: Unified Query & Filtering

## 2.1 The Specification Pattern

### The List Endpoint Problem

Every REST API has list endpoints written differently:

```
Service A: GET /products?name=laptop&min_price=500&max_price=2000&sort=price_desc
Service B: GET /orders?status=pending&created_after=2026-01-01&order_by=created_at
Service C: GET /users?search=john&role=admin&sortBy=lastName&offset=0&count=20
```

Three services. Three filter conventions. Three sort conventions. Three pagination conventions.

Every time a frontend developer moves from one service to another, they learn a new query language.

### The Solution: Four Generic Params

Instead of per-entity query params, **every list endpoint in every service accepts the same four params:**

| Param       | Format                             | Example              |
|-------------|-------------------------------------|----------------------|
| `filters`   | `field,operator,value[,condition]` | `price,gt,500,and`   |
| `page`      | integer                             | `1`                  |
| `page_size` | integer                             | `10`                 |
| `sort_by`   | `field:direction`                   | `created_at:desc`    |

### Supported Operators

```
eq          →  field = value
ne          →  field != value
gt          →  field > value
gte         →  field >= value
lt          →  field < value
lte         →  field <= value
contains    →  field LIKE %value%
in          →  field IN (val1, val2)     — values separated by |
between     →  field BETWEEN val1 AND val2 — values separated by |
is_null     →  field IS NULL
is_not_null →  field IS NOT NULL
```

### A Real URL Example

```
GET /api/v1/products
  ?filters=category,eq,Electronics,and
  &filters=price,between,500|2000,and
  &filters=name,contains,laptop
  &page=1&page_size=10&sort_by=price:desc
```

Translation: *Electronics products with price between 500-2000 and name containing "laptop", sorted by price descending, first page of 10.*

## 2.2 Implementation in Go & Python

### Go: Query Handler

```go
func (h *GetProductsQueryHandler) Handle(ctx context.Context, q GetProductsQuery) (*GetProductsResult, error) {
    // Parse sort_by: "price:desc" → ("price", "desc")
    sortField, sortDir := specifications.ParseSortBy(q.SortBy)

    // Parse filters: ["category,eq,Electronics,and", "price,between,500|2000"] → *Criteria
    criteria := specifications.ParseFilterParams(
        q.Filters,
        q.Page,
        q.PageSize,
        sortField,
        sortDir,
    )

    products, err := h.repo.FindByCriteria(ctx, criteria)
    total, err := h.repo.Count(ctx, criteria)

    return &GetProductsResult{Products: products, Total: total}, nil
}
```

### Go: HTTP Handler

```go
func (h *ProductQueryHandler) GetProducts(w http.ResponseWriter, r *http.Request) {
    page, _     := strconv.Atoi(r.URL.Query().Get("page"))
    pageSize, _ := strconv.Atoi(r.URL.Query().Get("page_size"))

    if page < 1     { page = 1 }
    if pageSize < 1 { pageSize = 10 }

    query := GetProductsQuery{
        Filters:  r.URL.Query()["filters"],
        SortBy:   r.URL.Query().Get("sort_by"),
        Page:     page,
        PageSize: pageSize,
    }

    result, err := h.handler.Handle(r.Context(), query)
    if err != nil {
        json.NewEncoder(w).Encode(responses.ErrorResponseBuilder.InternalError(err.Error()))
        return
    }

    json.NewEncoder(w).Encode(
        responses.PaginatedResponseBuilder.Found(result.Products, result.Meta, result.Pagination))
}
```

### Python: Query Handler

```python
class GetProductsQueryHandler:
    def handle(self, query: GetProductsQuery) -> GetProductsResult:
        parser = FilterParser()
        spec = parser.parse_filters(query.filters)

        sort = SortParser().parse_sort(query.sort_by or "created_at:desc")

        products = self.repo.find_by_criteria(spec, sort, query.page, query.page_size)
        total = self.repo.count(spec)

        return GetProductsResult(products=products, total=total)
```

### Python: Flask Route

```python
@bp.route("/products", methods=["GET"])
def get_products():
    filters  = request.args.getlist("filters")
    sort_by  = request.args.get("sort_by", "created_at:desc")
    page     = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 10))

    query  = GetProductsQuery(filters=filters, sort_by=sort_by, page=page, page_size=page_size)
    result = handler.handle(query)

    return jsonify(PaginatedResponseBuilder.found(
        result.products, result.meta, result.pagination)), 200
```

## 2.3 Repository Pattern

### The Interface (Universal)

Both Go and Python use the same repository contract:

**Go:**
```go
type ProductRepository interface {
    FindByID(ctx context.Context, id string) (*Product, error)
    FindByCriteria(ctx context.Context, c *specifications.Criteria) ([]*Product, error)
    Count(ctx context.Context, c *specifications.Criteria) (int, error)
    Create(ctx context.Context, p *Product) error
    Update(ctx context.Context, p *Product) error
    Delete(ctx context.Context, id string) error
}
```

**Python:**
```python
class ProductRepository(ABC):
    @abstractmethod
    def find_by_id(self, product_id: str) -> Optional[Product]:
        pass

    @abstractmethod
    def find_by_criteria(self, criteria: Criteria) -> List[Product]:
        pass

    @abstractmethod
    def count(self, criteria: Criteria) -> int:
        pass

    @abstractmethod
    def create(self, product: Product) -> None:
        pass
```

**Key insight:** The application layer never knows if the repository uses PostgreSQL, MongoDB, DynamoDB, or an in-memory array. Only the implementations know.

---

# PART 3: Structured Logging

## 3.1 Unified Log Schema

Every backbone logger produces this JSON shape:

```json
{
  "timestamp":   "2026-06-17T23:41:02Z",
  "level":       "ERROR",
  "service":     "orders-service",
  "component":   "CreateOrderCommandHandler",
  "layer":       "application",
  "method":      "handle",
  "message":     "order creation failed",
  "request_id":  "a8866c5e750643dab7cd2a8927bbcc08",
  "trace_id":    "4bf92f3577b34da6a3ce929d0e0e4736",
  "user_id":     "user-42",
  "environment": "production",
  "extra_data":  { "order_id": "ord-123", "total": 1500.0 },
  "error": {
    "type":        "ResourceConflictException",
    "message":     "order creation failed",
    "code":        120000006,
    "stack_trace": "..."
  }
}
```

**Same field names. Same timestamp format (RFC3339 UTC). Same level values.**

Go service and Python service — one Kibana index, one dashboard, one alert rule.

## 3.2 Three Formatters

The formatter is a strategy — you swap it without changing any log call in your code.

| Formatter | Output | Use Case |
|---|---|---|
| `JSONFormatter` | Full JSON, one line per entry | ELK / Loki / CloudWatch (production) |
| `ConsoleFormatter` | Coloured, human-readable | Local development |
| `CompactJSONFormatter` | Minimal JSON, short keys | High-throughput production |

### Same Log Call, Different Output

```python
logger.info("order created", extra_data={"order_id": "ord-123"}, request_id="a8866c5e")
```

**JSONFormatter (production):**
```json
{"timestamp": "2026-06-17T23:41:02Z", "level": "INFO", "service": "orders-service", "message": "order created", "request_id": "a8866c5e", "extra_data": {"order_id": "ord-123"}}
```

**ConsoleFormatter (development):**
```
[23:41:02.441] INFO     | orders-service.CreateOrderCommandHandler | a8866c5e | order created | order_id=ord-123
```

**CompactJSONFormatter (high-throughput):**
```json
{"ts":"2026-06-17T23:41:02Z","lvl":"INFO","msg":"order created","rid":"a8866c5e","svc":"orders-service","extra":{"order_id":"ord-123"}}
```

## 3.3 RID Propagation

The `rid` from the error response is the exact string that appears in every log line for that request.

```
[orders-service]     INFO  creating order          rid=a8866c5e  product_id=123
[inventory-service]  INFO  reserving stock         rid=a8866c5e  product_id=123
[payments-service]   ERROR charge failed           rid=a8866c5e  reason="card declined"
[orders-service]     ERROR order creation failed   rid=a8866c5e  error_code=120000006
```

**One query in Kibana — `rid:"a8866c5e"` — and you see the entire distributed request trace without an APM tool.**

## 3.4 Implementation in Go & Python

### Go: Create Enhanced Logger

```go
import "github.com/freakjazz/backbone-go/infrastructure/logging"

logger := logging.NewEnhancedLogger("orders-service").
    WithLayer("application").
    WithComponent("CreateOrderCommandHandler").
    WithMethod("Handle")

logger.Info("processing order", map[string]interface{}{"order_id": "ord-123"})
```

### Go: Scoped Context

```go
// Middleware injects rid at start of request
rid := r.Header.Get("X-Request-ID")
if rid == "" {
    rid = uuid.New().String()
}

// Scope the logger — every call carries rid
scoped := logger.WithContext(map[string]interface{}{
    "request_id": rid,
    "user_id":    userID,
})

// Pass scoped to handlers — rid travels everywhere
result, err := createOrderHandler.Handle(ctx, cmd)
if err != nil {
    scoped.ErrorWithCode("order creation failed",
        bberrors.AppConflict.Int(),
        map[string]interface{}{"order_id": cmd.OrderID})

    // Error response also carries rid
    e := responses.ErrorResponseBuilder.Conflict(err.Error(),
        responses.ErrorOpts{
            RID:  rid,
            Code: bberrors.AppConflict.Int(),
        })
    json.NewEncoder(w).Encode(e)
}
```

### Python: Create Logger

```python
from backbone import LoggerFactory, ConsoleFormatter

logger = LoggerFactory.create_logger(
    "orders-service",
    environment="development",  # Auto-selects ConsoleFormatter
    component="CreateOrderCommandHandler",
    layer="application",
)
```

### Python: LogContext (Thread-Local Storage)

```python
from backbone import LogContext

# In middleware — set once per request
@app.before_request
def inject_context():
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    LogContext.set("request_id", rid)
    LogContext.set("user_id", getattr(g, "user_id", None))

# In any handler — logger picks up rid automatically
class CreateOrderCommandHandler:
    def handle(self, command):
        self.logger.info("creating order", extra_data={"order_id": command.order_id})
        # request_id is automatically included from LogContext
```

---

# Testing Strategy

## Mock Repositories (No Database)

backbone enforces the Repository interface, making testing trivial:

### Go: In-Memory Repository

```go
type MockProductRepository struct {
    products map[string]*domain.Product
    mu       sync.RWMutex
}

func (r *MockProductRepository) FindByCriteria(ctx context.Context, c *specifications.Criteria) ([]*domain.Product, error) {
    r.mu.RLock()
    defer r.mu.RUnlock()

    var results []*domain.Product
    for _, p := range r.products {
        if r.matchesSpecification(p, c.Specification) {
            results = append(results, p)
        }
    }
    return results, nil
}

func (r *MockProductRepository) Seed(products ...*domain.Product) {
    r.mu.Lock()
    defer r.mu.Unlock()
    for _, p := range products {
        r.products[p.ID] = p
    }
}
```

### Go: Test Example

```go
func TestCreateProductCommandHandler_WhenConflict_ReturnsConflictError(t *testing.T) {
    repo := infrastructure.NewMockProductRepository()
    
    // Pre-populate with existing product
    repo.Seed(&domain.Product{ID: "p1", Name: "Laptop", Price: 999.0})

    handler := commands.NewCreateProductCommandHandler(repo)

    // Act
    result, err := handler.Handle(context.Background(), cmd)

    // Assert: validate error code
    appErr := err.(*commands.AppError)
    if appErr.Code != bberrors.AppConflict.Int() {
        t.Errorf("expected error code %d, got %d", bberrors.AppConflict.Int(), appErr.Code)
    }
}
```

### Python: In-Memory Repository

```python
class MockProductRepository:
    def __init__(self):
        self.products: Dict[str, Product] = {}
        self._lock = RLock()

    def find_by_criteria(self, criteria: Criteria) -> List[Product]:
        with self._lock:
            results = list(self.products.values())
            if criteria.specification:
                results = [p for p in results if self._matches_specification(p, criteria.specification)]
            return results

    def seed(self, *products: Product) -> None:
        with self._lock:
            for product in products:
                self.products[product.id] = product
```

### Python: Test Example

```python
def test_when_conflict_returns_conflict_error():
    repo = MockProductRepository()
    repo.seed(Product(id="p1", name="Laptop", price=999.0))
    
    handler = CreateProductCommandHandler(repo)
    
    with pytest.raises(ResourceConflictException) as exc_info:
        handler.handle(cmd)
    
    assert exc_info.value.code == ErrorCodes.APP_CONFLICT  # 120000006
```

---

# API Versioning

## Core Principle

**The error contract is universal. The response schema can evolve.**

Error responses never change:
```
v1: {"rid":"a8866c5e","status_code":409,"error_code":120000006,"message":"..."}
v2: {"rid":"a8866c5e","status_code":409,"error_code":120000006,"message":"..."}

✅ IDENTICAL
```

But success responses can evolve:
```
v1: {"id":"1","name":"Laptop","price":1500.0}
v2: {"id":"1","name":"Laptop","price":1500.0,"category":"Electronics","created_at":"..."}

✅ DIFFERENT - New fields only
```

## Versioning Strategy

Use **URL-based versioning**:

```
Production (default v1):
GET /api/v1/products
GET /api/v1/products/{id}

New features (v2):
GET /api/v2/products
GET /api/v2/products/{id}
```

## Version Lifecycle

```
┌─────────────┐      ┌──────────────┐      ┌────────────────┐
│ V1 - Active │ ───► │ V1 - Limited │ ───► │  V1 - Sunset   │
│ New feature │      │ Bug fixes    │      │  (3 months)    │
│ 2+ years    │      │ only         │      │  Read-only OK  │
└─────────────┘      └──────────────┘      └────────────────┘
     │ (2026)            │ (2027)                │ (2028)
```

## Error Codes Never Change

Once an error code is in production, it is **immutable**:

```
v1: 120000006 = APP_CONFLICT
v2: 120000006 = APP_CONFLICT (same meaning, might trigger for more cases)

❌ NEVER redefine: 120000006 = SOMETHING_ELSE
```

When you need a new error category, **add a new code**:

```go
var (
    AppConflict        = New(LayerApplication, 6)  // 120000006
    AppRateLimitExceeded = New(LayerApplication, 7) // 120000007 (NEW)
)
```

## Response Schema Evolution

New fields should be `null` first, then populated:

```
Release 2026-06:
{"id":"prod-123","name":"Laptop","price":1500.0}

Release 2026-09 (introduce null):
{"id":"prod-123","name":"Laptop","price":1500.0,"category":null}

Release 2026-12 (populate):
{"id":"prod-123","name":"Laptop","price":1500.0,"category":"Electronics"}
```

This ensures old clients that crash on unexpected fields won't crash on `null`.

---

# Database Agnosticity

## Repository Pattern: One Interface, Many Implementations

```
┌──────────────────────────────┐
│   Application Layer          │
│   (Business Logic)           │
└──────────────────┬───────────┘
                   │
        ┌──────────▼──────────┐
        │ Repository Interface│
        │ FindByCriteria()    │
        └──────────┬──────────┘
                   │
    ┌──────────────┼──────────────┬──────────────┐
    │              │              │              │
┌───▼──┐   ┌──────▼────┐  ┌──────▼────┐  ┌──────▼────┐
│SQL   │   │  NoSQL    │  │ Key-Value │  │  Cloud    │
│Postgres
│   │  MongoDB  │  │DynamoDB   │  │Firestore  │
└──────┘   └───────────┘  └───────────┘  └───────────┘
```

## Switching Databases

Because the interface is enforced, switching is **one line**:

```go
func ProvideProductRepository(cfg *Config) domain.ProductRepository {
    switch cfg.Database.Type {
    case "postgres":
        return infrastructure.NewPostgresProductRepository(...)
    case "mongodb":
        return infrastructure.NewMongoProductRepository(...)
    case "dynamodb":
        return infrastructure.NewDynamoProductRepository(...)
    case "memory":
        return infrastructure.NewMockProductRepository()
    }
}
```

## Supported Databases

- ✅ **PostgreSQL** — With SQLC (Go) and SQLAlchemy (Python)
- ✅ **MongoDB** — With mongo-driver (Go) and PyMongo (Python)
- ✅ **DynamoDB** — With AWS SDK (Go & Python)
- ✅ **Firestore** — Google Cloud (Python)
- ✅ **In-Memory** — For testing

All implementations use the same `Criteria` object for queries.

---

# Production Checklist

Before deploying backbone to production:

## Infrastructure Setup
- [ ] ELK / Loki configured to ingest logs
- [ ] Kibana index pattern created for backbone logs
- [ ] Elasticsearch / Loki retention policy set
- [ ] API Gateway configured (CORS, rate limiting at boundary)

## Error Handling
- [ ] All error codes from catalogue are in use
- [ ] No custom error codes added (use layer prefix + sequence)
- [ ] Error responses tested end-to-end
- [ ] RID injection middleware deployed

## Logging
- [ ] Formatter selected for environment (JSON for prod)
- [ ] LogContext injected in middleware
- [ ] All handlers emit logs to appropriate levels
- [ ] Timestamps verified in UTC RFC3339

## Querying
- [ ] Allowed filter fields validated
- [ ] Specification parser tested with edge cases
- [ ] Pagination tested (offset, limits)
- [ ] Sorting tested both directions
- [ ] Database indexes created for common filters

## Testing
- [ ] Mock repositories used in unit tests
- [ ] Error codes asserted, not just messages
- [ ] RID propagation tested end-to-end
- [ ] Specification tests cover all operators
- [ ] Integration tests use real database once

## Versioning
- [ ] Version routes registered (/api/v1, /api/v2)
- [ ] Deprecation timeline documented
- [ ] Migration guide published
- [ ] Backward compatibility verified

## Monitoring & Alerts
- [ ] Alert for `error_code: 14*` (infrastructure failures)
- [ ] Alert for `error_code: 12*` (application failures)
- [ ] Alert for `error_code: 13*` spike (interface issues)
- [ ] Dashboard created showing errors by layer
- [ ] RID search available in Kibana

---

# FAQ & Glossary

## FAQ

**Q: Why layer prefixes instead of semantic codes like "USER_NOT_FOUND"?**

A: Layer prefixes tell you WHERE the error happened, not just WHAT happened. If every layer can return "not found", you need to know which layer failed. The code `120000004` (App layer) is architecturally different from `130000003` (Interface layer).

**Q: Can I use my own error codes?**

A: No. Reuse the existing catalogue. If you need a service-specific code, use higher sequence numbers in your layer: `110001001` (Domain, sequence 1001) will never conflict with backbone's 1-99 range.

**Q: Does backbone force me to use a specific framework?**

A: No. backbone is framework-agnostic. Use it with gin, echo, fastapi, flask, whatever. The repository interface is the only requirement.

**Q: What if my database doesn't support Criteria queries?**

A: Implement the repository interface to translate Criteria into your database's native query language. The application layer never knows.

**Q: How do I test without a database?**

A: Use MockProductRepository. It's in-memory and implements the same interface. Your application layer can't tell the difference.

**Q: When should I add a new version?**

A: Only when you need to change response schema. New error codes don't require versioning. New fields can be added as `null` in v1. Only break when necessary (rare).

## Glossary

| Term | Definition |
|------|-----------|
| **RID** | Request ID — unique identifier tying all logs for one HTTP request across all services |
| **Criteria** | Object containing filters, sorting, and pagination for a database query |
| **Specification** | Object answering "does this entity satisfy this condition?" — composes with AND/OR |
| **Repository Pattern** | Interface for data access — application layer doesn't know which database |
| **Layer Prefix** | First 2 digits of error code indicating which architectural layer owns it (11-14) |
| **Formatter** | Strategy for log output (JSON, console, compact) — swappable at runtime |

---

## Install

```bash
# Go
go get github.com/freakjazz/backbone-go@v0.1.0

# Python
pip install backbone-python==0.1.0
```

Source and examples: [github.com/FreakJazz/backbone](https://github.com/FreakJazz/backbone)

---

## What is Next

backbone v0.1.0 is production-ready. Future versions planned:

- ✅ v0.2.0: GraphQL support
- ✅ v0.3.0: OpenTelemetry trace propagation
- ✅ v0.4.0: Middleware helpers for all frameworks
- ✅ v1.0.0: Stable API, breaking changes freeze

---

*If this saved you from six error formats, six query languages, and six log shapes, hit the clap button.*
