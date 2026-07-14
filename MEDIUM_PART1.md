# Stop Inventing Error Responses: A 9-Digit Error Code System for Go and Python Microservices

**Part 1 of 3 — backbone series**

---

## The conversation every microservices team has eventually

It usually starts in a Slack thread at 11pm during an incident:

> "The frontend is showing a blank screen. The API is returning something but I can't tell which service is failing."
>
> "Check the logs."
>
> "Which logs? Products returns `{"error": "not found"}`, orders returns `{"message": "Order 123 does not exist", "code": 404}`, and inventory just throws a 500 with a stack trace."

Six services. Six error shapes. Nobody knows which one is the source of truth.

I have been in this conversation more times than I want to admit. So I built **backbone** — a library available in both Go and Python that gives every service the same error contract, enforced at compile time in Go and at import time in Python.

This article covers the error system. Parts 2 and 3 cover the filter specification pattern and structured logging.

---

## Why string error codes are not enough

The most common approach to error codes looks like this:

```python
raise NotFoundException("User not found", error_code="USER_NOT_FOUND")
```

```java
throw new NotFoundException("User not found", "USER_NOT_FOUND");
```

This works until you have 12 services and 200 error codes. Then:

- Nobody knows which codes already exist
- `USER_NOT_FOUND` in service A and `USER_404` in service B mean the same thing
- You cannot tell from a log entry which architectural layer the error came from
- Monitoring alerts cannot distinguish a domain rule violation from a database outage

What you actually need is a code that carries **structural information** — not just a label.

---

## The 9-digit error code format

backbone uses a simple but powerful format: `LL_NNNNNNN`

- `LL` = 2-digit layer prefix (which architectural layer owns the error)
- `NNNNNNN` = 7-digit sequence within that layer

```
11_xxxxxxx  →  Domain layer        (business rules, entities, value objects)
12_xxxxxxx  →  Application layer   (use cases, commands, queries)
13_xxxxxxx  →  Interface layer     (HTTP handlers, gRPC adapters)
14_xxxxxxx  →  Infrastructure      (databases, messaging, external APIs)
```

When you see `120000006` in a log or a Kibana alert, you immediately know:

- Layer `12` → Application layer
- Error `6` in that layer → Conflict

No grepping. No lookup table open in another tab. The code tells you where the error came from.

---

## The complete error catalogue

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

Every service in your platform uses these same codes. When `140000001` appears in any log from any service, everyone knows it is a database failure at the infrastructure layer.

---

## Implementation in Go

The Go implementation uses a typed `ErrorCode` integer so the compiler rejects invalid codes:

```go
// backbone-go/errors/codes.go

type ErrorCode int

// New returns a valid 9-digit ErrorCode for the given layer and sequence number.
// Returns 0 (invalid) if either argument is out of range — never panics.
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

// The catalogue
var (
    // Domain (11)
    DomainBusinessRuleViolation  = New(LayerDomain, 1) // 110000001
    DomainInvalidEntityState     = New(LayerDomain, 2) // 110000002
    DomainInvalidFilter          = New(LayerDomain, 5) // 110000005

    // Application (12)
    AppResourceNotFound          = New(LayerApplication, 4) // 120000004
    AppConflict                  = New(LayerApplication, 6) // 120000006

    // Interface (13)
    IfcInvalidRequestBody        = New(LayerInterface, 1) // 130000001
    IfcUnauthorized              = New(LayerInterface, 6) // 130000006

    // Infrastructure (14)
    InfraDBFailure               = New(LayerInfrastructure, 1) // 140000001
    InfraMessagingFailure        = New(LayerInfrastructure, 2) // 140000002
)
```

Using the codes in a command handler:

```go
import (
    bberrors "github.com/freakjazz/backbone-go/errors"
    "github.com/freakjazz/backbone-go/interfaces/responses"
)

func (h *CreateProductCommandHandler) Handle(ctx context.Context, cmd CreateProductCommand) (*Result, error) {
    // Validate at the application layer
    if len(cmd.Name) < 2 {
        return nil, &AppError{
            Message: "name must be at least 2 characters",
            Code:    bberrors.IfcInvalidRequestBody,
        }
    }

    // Check for conflicts
    existing, _ := h.repo.FindByName(ctx, cmd.Name)
    if existing != nil {
        return nil, &AppError{
            Message: "a product with that name already exists",
            Code:    bberrors.AppConflict,
        }
    }

    // ... create and return
}
```

In the HTTP handler (the interface layer — the only place that knows about HTTP):

```go
func (h *ProductCommandHandler) CreateProduct(w http.ResponseWriter, r *http.Request) {
    result, err := h.createCmd.Handle(r.Context(), cmd)
    if err != nil {
        appErr := err.(*AppError)
        var e responses.ErrorResponse

        switch appErr.Code {
        case bberrors.AppConflict:
            e = responses.ErrorResponseBuilder.Conflict(appErr.Message,
                responses.ErrorOpts{Code: appErr.Code.Int()})
        case bberrors.IfcInvalidRequestBody:
            e = responses.ErrorResponseBuilder.ValidationError(appErr.Message,
                responses.ErrorOpts{Code: appErr.Code.Int()})
        default:
            e = responses.ErrorResponseBuilder.InternalError(appErr.Message)
        }

        w.Header().Set("Content-Type", "application/json")
        w.WriteHeader(e.StatusCode)
        json.NewEncoder(w).Encode(e)
        return
    }

    w.WriteHeader(http.StatusCreated)
    json.NewEncoder(w).Encode(responses.ProcessResponseBuilder.Created(result.ID))
}
```

---

## Implementation in Python

The Python version uses a class with integer constants — same values, same meaning:

```python
# backbone-python/errors/__init__.py

class ErrorCodes:
    """Error code catalogue — aligned with backbone-go."""

    # Domain (11)
    DOMAIN_BUSINESS_RULE_VIOLATION  = 110000001
    DOMAIN_INVALID_ENTITY_STATE     = 110000002
    DOMAIN_INVALID_VALUE_OBJECT     = 110000003
    DOMAIN_AGGREGATE_INCONSISTENCY  = 110000004
    DOMAIN_INVALID_FILTER           = 110000005

    # Application (12)
    APP_USE_CASE_FAILURE            = 120000001
    APP_VALIDATION_FAILURE          = 120000002
    APP_AUTHORIZATION_DENIED        = 120000003
    APP_RESOURCE_NOT_FOUND          = 120000004
    APP_EXTERNAL_SERVICE_FAILURE    = 120000005
    APP_CONFLICT                    = 120000006

    # Interface (13)
    IFC_INVALID_REQUEST_BODY        = 130000001
    IFC_METHOD_NOT_ALLOWED          = 130000002
    IFC_ROUTE_NOT_FOUND             = 130000003
    IFC_MISSING_REQUIRED_PARAM      = 130000004
    IFC_INVALID_FILTER_FORMAT       = 130000005
    IFC_UNAUTHORIZED                = 130000006
    IFC_FORBIDDEN                   = 130000007

    # Infrastructure (14)
    INFRA_DB_FAILURE                = 140000001
    INFRA_MESSAGING_FAILURE         = 140000002
    INFRA_CACHE_FAILURE             = 140000003
    INFRA_EXTERNAL_API_FAILURE      = 140000004
    INFRA_SERVICE_UNAVAILABLE       = 140000005

    @staticmethod
    def layer(code: int) -> int:
        return code // 10_000_000

    @staticmethod
    def layer_name(code: int) -> str:
        return {11: "domain", 12: "application",
                13: "interface", 14: "infrastructure"}.get(
            ErrorCodes.layer(code), "unknown")
```

Using the codes in a command handler:

```python
from backbone import ResourceConflictException, ValidationException
from backbone.errors import ErrorCodes

class CreateProductCommandHandler:
    def handle(self, command):
        # Validate
        if len(command.name) < 2:
            raise ValidationException(
                message="name must be at least 2 characters",
                code=ErrorCodes.IFC_INVALID_REQUEST_BODY,
            )

        # Check for conflicts
        existing = self._repo.find_by_name(command.name)
        if existing:
            raise ResourceConflictException(
                message="a product with that name already exists",
                resource_type="Product",
                conflict_field="name",
                conflict_value=command.name,
                code=ErrorCodes.APP_CONFLICT,
            )

        # ... create and return
```

In the Flask route (interface layer):

```python
from backbone import ErrorResponseBuilder, ProcessResponseBuilder
from backbone import ResourceConflictException, ValidationException

@bp.route("/products", methods=["POST"])
def create_product():
    try:
        result = handler.handle(command)
        return jsonify(ProcessResponseBuilder.created(result.id)), 201

    except ValidationException as e:
        err = ErrorResponseBuilder.validation_error(e.message, error_code=e.code)
        return jsonify(err), 400

    except ResourceConflictException as e:
        err = ErrorResponseBuilder.conflict(e.message, error_code=e.code)
        return jsonify(err), 409
```

---

## The error response contract

The error response shape is fixed. Always exactly four fields:

```json
{
  "rid":         "a8866c5e750643dab7cd2a8927bbcc08",
  "status_code": 409,
  "message":     "a product with that name already exists",
  "error_code":  120000006
}
```

`rid` is a **request ID** — the thread that connects everything that happened during a single HTTP request, across every service that touched it.

Here is why it matters. A user clicks "Buy" and your frontend calls the orders service. The orders service calls the inventory service. Inventory calls the payments service. Payments fails. Without a shared `rid`, you have four separate log entries with no link between them. You know *something* failed, but you cannot reconstruct the chain.

With `rid` the picture is different:

```
[orders-service]     INFO  creating order          rid=a8866c5e  product_id=123
[inventory-service]  INFO  reserving stock         rid=a8866c5e  product_id=123
[payments-service]   ERROR charge failed           rid=a8866c5e  reason="card declined"
[orders-service]     ERROR order creation failed   rid=a8866c5e  error_code=120000005
```

One query in Kibana — `rid: a8866c5e` — and you see the entire journey: which services ran, in which order, and exactly where it broke. That `a8866c5e` in the error response the frontend received is the same value in every log line across every service.

backbone generates the `rid` automatically if your middleware does not inject one. If you already propagate a correlation ID (from an `X-Request-ID` header for example), you pass it to the builder:

**Go:**
```go
rid := r.Header.Get("X-Request-ID")
e := responses.ErrorResponseBuilder.Conflict("already exists",
    responses.ErrorOpts{
        RID:  rid,
        Code: bberrors.AppConflict.Int(),
    })
// {"rid":"a8866c5e...","status_code":409,"message":"already exists","error_code":120000006}
```

**Python:**
```python
rid = request.headers.get("X-Request-ID")
e = ErrorResponseBuilder.conflict(
    "already exists",
    rid=rid,
    error_code=ErrorCodes.APP_CONFLICT)
# {"rid":"a8866c5e...","status_code":409,"message":"already exists","error_code":120000006}
```

The `rid` the user sees in the error response is the exact string to paste into your log aggregator to reconstruct the full request trace — no APM tool required.

No `field_errors`. No `data` wrapper. No `detail`. No `errors` array. The contract never changes shape regardless of which service returns it or which language it is written in.

---

## Success response contracts

Error is not the only contract backbone enforces. Write operations always return just the ID:

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

**Go builders:**
```go
// Write operations
responses.ProcessResponseBuilder.Created("uuid-123")
responses.ProcessResponseBuilder.Updated("uuid-123")
responses.ProcessResponseBuilder.Deleted("uuid-123")

// Read operations
responses.SimpleObjectResponseBuilder.Found(productMap)
responses.PaginatedResponseBuilder.Found(items, meta, pagination)
```

**Python builders:**
```python
# Write operations
ProcessResponseBuilder.created("uuid-123")
ProcessResponseBuilder.updated("uuid-123")
ProcessResponseBuilder.deleted("uuid-123")

# Read operations
SimpleObjectResponseBuilder.found(product_dict)
PaginatedResponseBuilder.found(items, meta, pagination)
```

---

## Extending the catalogue for your service

backbone codes start at sequence `1` in each layer. Your service can define its own without conflict — just use higher sequence numbers or a different starting range:

**Go:**
```go
import bberrors "github.com/freakjazz/backbone-go/errors"

// Your service-specific codes — will never clash with backbone's 1-99 range
var (
    OrderLimitExceeded    = bberrors.New(bberrors.LayerDomain,      1001) // 110001001
    PaymentGatewayTimeout = bberrors.New(bberrors.LayerInfrastructure, 1001) // 140001001
)
```

**Python:**
```python
from backbone.errors import ErrorCodes

class MyServiceErrorCodes(ErrorCodes):
    ORDER_LIMIT_EXCEEDED     = 110001001
    PAYMENT_GATEWAY_TIMEOUT  = 140001001
```

---

## Real-world impact

When every service in your platform uses this system:

**During an incident:** error code `140000001` in any log from any service immediately tells you it is a database failure at infrastructure — no need to read the message or check the service name.

**In monitoring:** you can build alerts grouped by layer prefix. A spike in `12xxxxxxx` codes means application logic is failing. A spike in `14xxxxxxx` means your infrastructure is under stress. Different teams own different prefixes.

**For frontend teams:** the error contract never changes shape. Parse it once in your API client and it works for every service forever.

**For API documentation:** one error table in your OpenAPI spec covers every service. No per-service error format to document.

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

## What is next

**Part 2** covers the filter specification pattern — four generic query params that work for any entity endpoint without hard-coding field names in your router:

```
GET /api/v1/products
  ?filters=category,eq,Electronics,and
  &filters=price,between,500|2000
  &sort_by=price:desc&page=1&page_size=10
```

**Part 3** covers structured logging — the same JSON log shape across Go and Python services, with three formatters (JSON for production, coloured console for development, compact for high-throughput).

---

*If this saved you from a 11pm Slack thread, hit the clap button.*
