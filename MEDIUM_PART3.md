# Same Logs, Different Languages: Structured Logging Across Go and Python Microservices

**Part 3 of 3 — backbone series** | [Part 1: 9-digit error codes](./MEDIUM_PART1.md) · [Part 2: filter specifications](./MEDIUM_PART2.md)

---

## The log aggregation problem

You have ten microservices. Five are in Go, five are in Python. When an incident hits at 11pm and you open Kibana, you see this:

```
[products-go]    {"timestamp":"2026-06-17T23:41:02Z","level":"ERROR","msg":"conflict"}
[orders-python]  2026-06-17 23:41:02 ERROR orders - Order creation failed - user_id=42
[inventory-go]   {"time":"2026-06-17T23:41:02","severity":"error","message":"stock low"}
[payments-python] {"lvl":"ERR","svc":"payments","rid":"a8b3","text":"charge failed"}
```

Four services. Four log shapes. Four different field names for the same concepts — `msg`, `message`, `text`. Four different timestamp formats. Four different level names — `ERROR`, `error`, `ERR`.

You cannot build a single Kibana dashboard for all of them. You cannot write one alert rule that fires on errors from any service. You cannot correlate a request across services by `request_id` if every service calls it something different.

backbone fixes this by making every service — regardless of language — emit the exact same JSON shape.

---

## The unified log entry shape

Every backbone logger produces this:

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

Same field names. Same timestamp format (RFC3339 UTC). Same level values (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). Go service and Python service — one Kibana index, one dashboard, one alert rule.

---

## Three formatters, one log call

The formatter is a strategy — you swap it without changing any log call in your code. The same `logger.Info(...)` line produces different output depending on which formatter is active.

backbone ships three formatters in both languages:

| Formatter | Output | Use case |
|---|---|---|
| `JSONFormatter` | Full JSON, one line per entry | ELK / Loki / CloudWatch (default) |
| `ConsoleFormatter` | Coloured, human-readable | Local development |
| `CompactJSONFormatter` | Minimal JSON, short keys | High-throughput production |

---

## Go implementation

### Creating a logger

```go
import "github.com/freakjazz/backbone-go/infrastructure/logging"

// Production default — full JSON for ELK
logger := logging.NewLogger("orders-service")

// Development — coloured console
logger.SetFormatter(logging.NewConsoleFormatter())

// High-throughput — compact JSON
logger.SetFormatter(&logging.CompactJSONFormatter{})
```

### Basic log calls

```go
// Simple info log
logger.Info("order created", map[string]interface{}{
    "order_id": order.ID,
    "total":    order.Total,
})

// Warning
logger.Warning("low stock detected", map[string]interface{}{
    "product_id": product.ID,
    "stock":      product.Stock,
})

// Error with structured error code (links to Part 1)
logger.Error("payment failed", map[string]interface{}{
    "order_id":   order.ID,
    "error_code": bberrors.InfraExternalAPIFailure.Int(), // 140000004
})
```

### Enhanced logger — scope to a layer and component

The `EnhancedLogger` adds fluent methods to bind a logger to a specific layer, component, and method. Every log call from that logger automatically includes those fields.

```go
import "github.com/freakjazz/backbone-go/infrastructure/logging"

// Create once per handler — all logs from this instance carry layer, component, method
logger := logging.NewEnhancedLogger("orders-service").
    WithLayer("application").
    WithComponent("CreateOrderCommandHandler").
    WithMethod("Handle")

logger.Info("processing order", map[string]interface{}{"order_id": "ord-123"})
// {"level":"INFO","layer":"application","component":"CreateOrderCommandHandler","method":"Handle","message":"processing order",...}

// Error with error code and automatic stack trace
logger.ErrorWithCode("charge failed", bberrors.InfraExternalAPIFailure.Int(), map[string]interface{}{
    "order_id": "ord-123",
})
// {"level":"ERROR","error":{"type":"Error","message":"charge failed","code":140000004,"stack_trace":"..."},...}

// Log a SQL query with duration — infrastructure layer standard
logger.LogQuery(
    "SELECT * FROM orders WHERE user_id = $1",
    []interface{}{userID},
    12, // duration in ms
    nil,
)
// {"level":"DEBUG","query":{"sql":"SELECT * FROM orders WHERE user_id = $1","duration_ms":12},...}
```

### Scoped context — the rid flows through everything

This is the connection to Part 1. The `rid` from the error response is the same value that appears in every log line for that request.

```go
// Middleware injects rid at the start of every request
rid := r.Header.Get("X-Request-ID")
if rid == "" {
    rid = uuid.New().String()
}

// Scope the logger — every log call in this request carries rid and user_id
scoped := logger.WithContext(map[string]interface{}{
    "request_id": rid,
    "user_id":    userID,
})

// Now pass scoped to your handlers — rid travels through every layer
result, err := createOrderHandler.Handle(ctx, cmd)
if err != nil {
    scoped.ErrorWithCode("order creation failed",
        bberrors.AppConflict.Int(),
        map[string]interface{}{"order_id": cmd.OrderID})

    // Error response also carries rid — user can give you this value
    e := responses.ErrorResponseBuilder.Conflict(err.Error(),
        responses.ErrorOpts{
            RID:  rid,
            Code: bberrors.AppConflict.Int(),
        })
    json.NewEncoder(w).Encode(e)
}
```

---

## Python implementation

### Creating a logger

```python
from backbone import LoggerFactory, JSONFormatter, ConsoleFormatter, CompactJSONFormatter

# Development — coloured console (auto-detected when ENVIRONMENT=development)
logger = LoggerFactory.create_logger("orders-service")

# Explicit environment
logger = LoggerFactory.create_logger("orders-service", environment="production")

# With component and layer
logger = LoggerFactory.create_logger(
    service_name="orders-service",
    environment="production",
    component="CreateOrderCommandHandler",
    layer="application",
)
```

### Basic log calls

```python
# Info
logger.info("order created",
    extra_data={"order_id": order.id, "total": order.total},
    request_id=rid)

# Warning
logger.warning("low stock detected",
    extra_data={"product_id": product.id, "stock": product.stock})

# Error with exception and error code
try:
    result = payment_gateway.charge(order)
except PaymentGatewayError as e:
    logger.error("payment failed",
        exception=e,
        error_code=ErrorCodes.INFRA_EXTERNAL_API_FAILURE,
        extra_data={"order_id": order.id})
```

### Environment-based automatic configuration

`LoggerFactory` reads `ENVIRONMENT` from your environment variables and configures the right formatter automatically:

```python
# ENVIRONMENT=development → ConsoleFormatter (coloured, DEBUG level)
# ENVIRONMENT=staging     → JSONFormatter to stdout + FileFormatter to logs/errors.log
# ENVIRONMENT=production  → CompactJSONFormatter to stdout + stderr for errors
logger = LoggerFactory.create_logger("orders-service")
```

No configuration in code. Set `ENVIRONMENT` in your Docker / Kubernetes manifest and get the right formatter.

### LogContext — request scope without passing logger everywhere

Python's `LogContext` uses thread-local storage to propagate the `rid` and `user_id` without threading them through every function signature.

```python
from backbone import LogContext

# In your Flask middleware — set once per request
@app.before_request
def inject_request_context():
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    LogContext.set("request_id", rid)
    LogContext.set("user_id", getattr(g, "user_id", None))

# In any handler, repository, or service — logger picks up rid automatically
class CreateOrderCommandHandler:
    def handle(self, command):
        self.logger.info("creating order", extra_data={"order_id": command.order_id})
        # request_id is automatically included from LogContext — no parameter needed
```

### Context manager for scoped logging

```python
from backbone import LogContext

with LogContext(request_id=rid, user_id=user.id, operation="checkout"):
    # Every log call inside this block includes request_id, user_id, operation
    logger.info("order validated", extra_data={"items": len(order.items)})
    payment_result = payment_service.charge(order)
    logger.info("payment completed", extra_data={"transaction_id": payment_result.id})
```

---

## What each formatter output looks like

Same log call:
```python
logger.info("order created", extra_data={"order_id": "ord-123", "total": 1500.0}, request_id="a8866c5e")
```

**JSONFormatter** (production, ELK):
```json
{"timestamp": "2026-06-17T23:41:02Z", "level": "INFO", "service": "orders-service", "component": "CreateOrderCommandHandler", "layer": "application", "message": "order created", "request_id": "a8866c5e", "extra_data": {"order_id": "ord-123", "total": 1500.0}}
```

**ConsoleFormatter** (development):
```
[23:41:02.441] INFO     | orders-service.CreateOrderCommandHandler | a8866c5e | order created | order_id=ord-123 total=1500.0
```

**CompactJSONFormatter** (high-throughput):
```json
{"ts":"2026-06-17T23:41:02Z","lvl":"INFO","msg":"order created","rid":"a8866c5e","svc":"orders-service","comp":"CreateOrderCommandHandler","layer":"application","extra":{"order_id":"ord-123","total":1500.0}}
```

Three formats. Zero changes to the log call. One line in your startup config.

---

## Putting it all together: the full request journey

This is how the three parts of the series connect in a single HTTP request.

```
1. Request arrives at the interface layer
   → middleware generates rid = "a8866c5e"
   → scoped logger and error builder both receive rid

2. Interface layer calls the application layer
   → logger.info("processing request", request_id="a8866c5e")
   → application raises ResourceConflictException(code=120000006)

3. Interface layer catches the exception
   → logger.error("conflict", error_code=120000006, request_id="a8866c5e")
   → error builder returns {"rid":"a8866c5e","status_code":409,"error_code":120000006,...}

4. Client receives the error response
   → sees rid = "a8866c5e" in the JSON body
   → pastes it into Kibana search: rid:"a8866c5e"
   → finds every log line from every service that touched this request
```

The `rid` is the thread. The unified log shape is what makes that thread queryable.

---

## One ELK index for all services

Once every service emits the same field names, you configure one Logstash pipeline:

```yaml
filter {
  json { source => "message" }
  date { match => ["timestamp", "ISO8601"] target => "@timestamp" }
}
```

And one Kibana index pattern: `microservices-*`

Every service feeds the same index. One dashboard for all errors. One alert rule: `level:ERROR AND error.code:14*` fires when any service has an infrastructure failure. `level:ERROR AND error.code:12*` fires for application layer failures.

You could build this alerting without backbone — but you would have to maintain a field mapping for every service. With backbone you write it once.

---

## Install

```bash
# Go
go get github.com/freakjazz/backbone-go@v0.1.0

# Python
pip install backbone-python==0.1.0
```

Source and full examples: [github.com/FreakJazz/backbone](https://github.com/FreakJazz/backbone)

---

## The backbone series

- **[Part 1](./MEDIUM_PART1.md)** — 9-digit error codes by architectural layer + the `rid` for distributed tracing
- **[Part 2](./MEDIUM_PART2.md)** — the Specification Pattern for generic list endpoints
- **Part 3** ← you are here — unified structured logging across Go and Python

---

*If your Kibana search `rid:"a8866c5e"` finally returns results from every service, hit the clap button.*
