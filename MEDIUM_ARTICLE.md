# Backbone: How I Standardised Error Codes, Responses, Logs and Filters Across Go and Python Microservices

## Subtitle
A practical Clean Architecture library — identical JSON contracts in both languages, with 9-digit layer-prefixed error codes, three log formatters, and a generic filter specification pattern.

---

## The problem

When you work on a microservices platform you end up with the same conversation every few weeks:

> "Why does the products service return `{"error": "not found"}` but the orders service returns `{"detail": "Order 123 does not exist", "code": 404}`?"

Six services. Six error shapes. Six log formats. Six ways to filter lists. And every new engineer that joins the team has to read six READMEs just to understand what a 200 response looks like.

I got tired of this. So I built **backbone** — two libraries (Go and Python) that give every service the same contracts.

---

## What backbone standardises

1. **Error codes** — 9-digit codes prefixed by the originating architectural layer
2. **HTTP response contracts** — identical JSON shape regardless of framework
3. **Structured logging** — same JSON fields in Go and Python, three formatters included
4. **Filter specifications** — four generic query params, no hard-coded field names

Authentication, authorisation tokens, audit trails, database adapters — those belong to each system. backbone does one thing: make every service *speak the same language*.

---

## The error code system

The most important design decision was the error code format. Every error gets a **9-digit code**: `LL_NNNNNNN` where `LL` is the 2-digit layer prefix and `NNNNNNN` is a 7-digit sequence.

```
11_xxxxxxx  →  Domain layer
12_xxxxxxx  →  Application layer
13_xxxxxxx  →  Interface layer (HTTP)
14_xxxxxxx  →  Infrastructure layer
```

When you see error code `120000006` in a log, you immediately know it came from the Application layer, error number 6 — which is a Conflict. No guessing, no grepping.

The full catalogue:

| Code        | Layer          | Meaning                 | HTTP |
|-------------|----------------|-------------------------|------|
| `110000001` | Domain         | BusinessRuleViolation   | 422  |
| `110000002` | Domain         | InvalidEntityState      | 422  |
| `120000004` | Application    | ResourceNotFound        | 404  |
| `120000006` | Application    | Conflict                | 409  |
| `130000001` | Interface      | InvalidRequestBody      | 400  |
| `130000006` | Interface      | Unauthorized            | 401  |
| `140000001` | Infrastructure | DBFailure               | 500  |
| `140000002` | Infrastructure | MessagingFailure        | 500  |

**Go:**
```go
import bberrors "github.com/FreakJazz/backbone/backbone-go/errors"

bberrors.AppConflict.Int()              // 120000006
bberrors.IfcInvalidRequestBody.Int()    // 130000001
bberrors.InfraDBFailure.Int()           // 140000001

// Extend the catalogue for your own service:
var MyOrderLimitExceeded = bberrors.New(bberrors.LayerDomain, 1001) // 110001001
```

**Python:**
```python
from backbone.errors import ErrorCodes

ErrorCodes.APP_CONFLICT                 # 120000006
ErrorCodes.IFC_INVALID_REQUEST_BODY     # 130000001
ErrorCodes.INFRA_DB_FAILURE             # 140000001
```

---

## The response contract

Every error response has **exactly four fields** — no more, no less:

```json
{
  "rid":         "a8866c5e750643dab7cd2a8927bbcc08",
  "status_code": 409,
  "message":     "a product with that name already exists",
  "error_code":  120000006
}
```

No `field_errors`. No `data`. No `detail`. No `errors` array. The contract never changes shape — your client SDK can parse it once and never need updating.

Write operations always return just the ID:

```json
{ "id": "product-uuid-123" }
```

GET single resource returns the raw object with no envelope:

```json
{ "id": "uuid", "name": "Laptop Pro", "price": 1500.0, "status": "active" }
```

GET list returns meta, items, and pagination:

```json
{
  "meta":       { "status": "success", "status_code": 200, "message": "OK" },
  "items":      [{ "id": "1", "name": "Laptop" }],
  "pagination": { "total_count": 100, "page": 1, "page_size": 10 }
}
```

### Building responses in Go

```go
import (
    "github.com/FreakJazz/backbone/backbone-go/interfaces/responses"
    bberrors "github.com/FreakJazz/backbone/backbone-go/errors"
)

// In your HTTP handler after a use-case conflict:
e := responses.ErrorResponseBuilder.Conflict(
    "a product with that name already exists",
    responses.ErrorOpts{Code: bberrors.AppConflict.Int()})
w.Header().Set("Content-Type", "application/json")
w.WriteHeader(e.StatusCode)
json.NewEncoder(w).Encode(e)

// After creating a product:
json.NewEncoder(w).Encode(responses.ProcessResponseBuilder.Created(product.ID))
```

### Building responses in Python (Flask)

```python
from backbone import ErrorResponseBuilder, ProcessResponseBuilder
from backbone.errors import ErrorCodes

# In your Flask route after a conflict:
e = ErrorResponseBuilder.conflict(
    "a product with that name already exists",
    error_code=ErrorCodes.APP_CONFLICT)
return jsonify(e), e["status_code"]

# After creating:
result = ProcessResponseBuilder.created(product.id)
return jsonify(result), 201
```

---

## Application exceptions

The cleanest pattern: your use case raises a backbone exception, and your HTTP handler catches it and maps it to the right builder. The handler becomes a thin adapter.

```python
# application/commands/create_product.py
from backbone import ResourceConflictException
from backbone.errors import ErrorCodes

class CreateProductCommandHandler:
    def handle(self, command):
        existing = self._repo.find_by_name(command.name)
        if existing:
            raise ResourceConflictException(
                message="a product with that name already exists",
                resource_type="Product",
                conflict_field="name",
                conflict_value=command.name,
                code=ErrorCodes.APP_CONFLICT,
            )
        # ... create product
```

```python
# interfaces/http/commands/create_product.py  (Flask)
from backbone import ErrorResponseBuilder, ResourceConflictException

@bp.route("/products", methods=["POST"])
def create_product():
    try:
        result = handler.handle(command)
        return jsonify(ProcessResponseBuilder.created(result.id)), 201
    except ResourceConflictException as e:
        err = ErrorResponseBuilder.conflict(e.message, error_code=e.code)
        return jsonify(err), 409
```

Same pattern in Go:

```go
// application/commands/create_product.go
func (h *CreateProductCommandHandler) Handle(ctx context.Context, cmd CreateProductCommand) (*CreateProductResult, error) {
    existing, _ := h.repo.FindByName(ctx, cmd.Name)
    if existing != nil {
        return nil, &AppError{
            Message: "a product with that name already exists",
            Code:    bberrors.AppConflict,
        }
    }
    // ... create product
}

// interfaces/http/handlers/product_command_handler.go
func (h *ProductCommandHandler) CreateProduct(w http.ResponseWriter, r *http.Request) {
    result, err := h.createCmd.Handle(ctx, cmd)
    if err != nil {
        e := responses.ErrorResponseBuilder.Conflict(err.Error(),
            responses.ErrorOpts{Code: bberrors.AppConflict.Int()})
        json.NewEncoder(w).Encode(e)
        return
    }
    json.NewEncoder(w).Encode(responses.ProcessResponseBuilder.Created(result.ID))
}
```

---

## Structured logging

The hardest part of distributed systems debugging is correlating logs across services. backbone solves this by making every service emit the same JSON shape.

```json
{
  "timestamp":  "2026-06-16T10:23:45Z",
  "level":      "INFO",
  "service":    "products-service",
  "component":  "ProductCommandHandler",
  "layer":      "interface",
  "message":    "product created",
  "request_id": "a8866c5e750643dab7cd2a8927bbcc08",
  "extra_data": { "product_id": "uuid-123" }
}
```

When every service emits this shape, a single ELK index can hold all your logs. Kibana queries work the same across services.

Three formatters ship out of the box:

**Go:**
```go
import "github.com/FreakJazz/backbone/backbone-go/infrastructure/logging"

logger := logging.NewLogger("products-service")

// Production (default): compact JSON lines for log aggregators
logger.SetFormatter(&logging.JSONFormatter{})

// Development: coloured, human-readable
logger.SetFormatter(logging.NewConsoleFormatter())
// → 2026-06-16 10:23:45 [INFO    ] products-service > Handler | product created

// High-throughput: minimal JSON
logger.SetFormatter(&logging.CompactJSONFormatter{})
// → {"ts":"2026-06-16T10:23:45Z","level":"INFO","service":"products-service","msg":"product created"}

// Attach context to every subsequent call
scoped := logger.WithContext(map[string]interface{}{
    "request_id": rid,
    "user_id":    userID,
})
scoped.Info("product created", map[string]interface{}{"product_id": id})
```

**Python:**
```python
from backbone import LoggerFactory, JSONFormatter, ConsoleFormatter, CompactJSONFormatter

factory = LoggerFactory("products-service")

# Production
logger = factory.get_logger("ProductCommandHandler", formatter=JSONFormatter())

# Development
logger = factory.get_logger("ProductCommandHandler", formatter=ConsoleFormatter())

# High-throughput
logger = factory.get_logger("ProductCommandHandler", formatter=CompactJSONFormatter())

logger.info("product created", extra_data={"product_id": id}, request_id=rid)
```

---

## Filter specifications

Generic list endpoints are the most painful part of a REST API. If you add a new filterable field you have to change the router, the query builder, and the docs. backbone solves this with four generic params that work for any entity.

```
GET /api/v1/products
  ?filters=category,eq,Electronics,and
  &filters=price,between,500|2000
  &filters=name,contains,laptop
  &page=1&page_size=10&sort_by=price:desc
```

Supported operators: `eq` `ne` `gt` `gte` `lt` `lte` `contains` `in` `between` `is_null` `is_not_null`

`page`/`page_size` above is offset pagination — the default, and it gives
you a `total_count`. For deep paging into a large or growing list, pass
`cursor=<token>` instead (from a previous response's `page.next_cursor`):
Postgres seeks directly via the sort index instead of scanning and
discarding every skipped row the way `OFFSET` has to. The two modes are
mutually exclusive and serve different needs, not one replacing the other
— full write-up in [Part 2](./MEDIUM_PART2.md#deep-paging-when-offset-stops-being-enough).

**Go:**
```go
import "github.com/FreakJazz/backbone/backbone-go/domain/specifications"

// In your query handler:
sortField, sortDir := specifications.ParseSortBy(r.URL.Query().Get("sort_by"))
criteria := specifications.ParseFilterParams(
    r.URL.Query()["filters"],
    page, pageSize, sortField, sortDir,
)

// One call, one round trip — FindByCriteria returns the page and the total
// match count together (a production repository rides the total on the
// same query via SQL's COUNT(*) OVER(), so a separate Count(ctx, criteria)
// call would just be a second, avoidable round trip).
products, total, _ := repo.FindByCriteria(ctx, criteria)
```

**Python:**
```python
from backbone import FilterParser, SortSpecification

parser = FilterParser(allowed_fields=["name", "price", "category", "status"])
criteria = parser.parse(request.args.getlist("filters"))
sort     = SortSpecification.parse(request.args.get("sort_by", "created_at:desc"))

products, total = repo.find_by_criteria(criteria, sort, page=1, page_size=20)
```

You can also compose specifications manually for domain logic:

```python
from backbone import EqualSpecification, BetweenSpecification, LikeSpecification

spec = (EqualSpecification("category", "Electronics") &
        BetweenSpecification("price", 500, 2000) &
        LikeSpecification("name", "laptop"))
```

---

## Clean Architecture layout

Both examples follow this layout. The key rule: **the application layer never imports from the interface layer**. backbone exception types are the shared vocabulary.

```
your-service/
├── domain/
│   ├── entities/           # core business objects — no framework imports
│   ├── repositories/       # interfaces only (no DB code here)
│   └── specifications/     # domain-specific filter specs
├── application/
│   ├── commands/           # write side: CreateProduct, UpdateProduct, ...
│   └── queries/            # read side:  GetProducts, GetProductByID
├── infrastructure/
│   ├── database/           # connection pools + schema/index bootstrap (Postgres, Mongo)
│   ├── repositories/       # concrete implementations — Postgres/Mongo in production,
│   │                       # an in-memory fake kept around for the test suite only
│   └── seeders/            # demo data
└── interfaces/http/
    ├── handlers/           # thin HTTP adapters — map HTTP → command/query
    └── v1/routes.*         # versioned route registration
```

`main.py` / `main.go` is the only file with knowledge of all layers — it wires the dependency graph and starts the server. Zero business logic there.

---

## Try it

Both examples run against real PostgreSQL (product catalog) and MongoDB
(sales/stock-movement transaction logs) — not an in-memory stand-in — via a
shared `docker-compose.yml`:

```bash
# 1. Start Postgres + Mongo (shared by both examples)
cd examples
docker compose up -d

# 2a. Go example — Swagger UI included
cd go/clean-api-go
cp .env.example .env
go mod tidy && swag init && go run main.go
# http://localhost:8005/docs/index.html

# 2b. Python example — flask-restx UI included
cd examples/python/clean_api_python
cp .env.example .env
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt && python main.py
# http://localhost:5000/docs
```

Both examples implement the same product CRUD (create, update, change
status, delete, get by ID, get list with filters) *plus* sales and
stock-movement endpoints that decrement/adjust `stock` in Postgres and log
the event in Mongo, and the same two pagination modes on the list endpoint
— offset (`page`/`page_size`) and keyset (`cursor`). Run both and compare
the JSON responses: they are identical.

---

## Install

Not yet published to pkg.go.dev / PyPI — install straight from source until `v0.1.0` is tagged:

```bash
# Go
go get github.com/FreakJazz/backbone/backbone-go@main

# Python
pip install "backbone @ git+https://github.com/FreakJazz/backbone.git#subdirectory=backbone-python"
```

Source: [github.com/FreakJazz/backbone](https://github.com/FreakJazz/backbone)

---

## What is next

backbone `v0.1.0` is a public beta. Before `v1.0.0` I plan to:

- SQLAlchemy async adapter for backbone-python
- OpenTelemetry trace propagation in both loggers
- Middleware helpers (rid injection, error mapping) for gin, echo, Flask, FastAPI
- Published to PyPI and pkg.go.dev

Feedback and contributions welcome — open an issue or a PR.

---

*If this saved you from writing the same error handler for the sixth time, hit the clap button.*
