# API Versioning Strategy with Backbone

**How to version your microservices APIs without breaking clients**

---

## Table of Contents
1. Versioning Philosophy
2. URL-Based Versioning (Recommended)
3. Backward Compatibility Strategy
4. Error Code Evolution
5. Response Schema Migration
6. Deprecation Guidelines
7. Implementation Examples

---

## 1. Versioning Philosophy

### Core Principle

**The error contract is universal. The response schema can evolve.**

```
V1 Error Response:
{
  "rid": "a8866c5e",
  "status_code": 422,
  "error_code": 120000002,
  "message": "validation failed"
}

V2 Error Response:
{
  "rid": "a8866c5e",
  "status_code": 422,
  "error_code": 120000002,
  "message": "validation failed"
}

✅ SAME - Error contract never changes
```

**But successful responses can evolve:**

```
V1 GET /api/v1/products/123:
{
  "id": "prod-123",
  "name": "Laptop",
  "price": 1500.0,
  "status": "active"
}

V2 GET /api/v2/products/123:
{
  "id": "prod-123",
  "name": "Laptop",
  "price": 1500.0,
  "status": "active",
  "category": "Electronics",        ← NEW
  "created_at": "2026-06-17T...",  ← NEW
  "updated_at": "2026-06-17T..."   ← NEW
}

✅ DIFFERENT - New fields can be added
❌ NEVER REMOVE - Old fields must stay for backward compat
```

---

## 2. URL-Based Versioning (Recommended)

### Why URL-Based?

| Strategy | Pros | Cons |
|----------|------|------|
| **URL Path** (v1, v2, v3) | Clear, explicit, easy to test | URL pollution |
| **Header** (Accept: api-v2) | Clean URLs | Less discoverable |
| **Query Param** (?version=2) | Optional fallback | Not RESTful |
| **Header + URL** | Best of both | Complexity |

**Recommendation: URL-based for clarity + optional header fallback**

### Structure

```
Production (default v1):
GET /api/v1/products
GET /api/v1/products/{id}
POST /api/v1/products
PUT /api/v1/products/{id}
DELETE /api/v1/products/{id}

New features (v2):
GET /api/v2/products
GET /api/v2/products/{id}
POST /api/v2/products
PUT /api/v2/products/{id}
DELETE /api/v2/products/{id}

Maintenance only (v1 shadow):
- No new features
- Only bug fixes and security patches
- Scheduled sunset date
```

### Version Lifecycle

```
┌─────────────┐      ┌──────────────┐      ┌────────────────┐
│ V1 - Active │ ───► │ V1 - Limited │ ───► │  V1 - Sunset   │
│ New feature │      │ Bug fixes    │      │  (3 months)    │
│ 2+ years    │      │ only         │      │  Read-only OK  │
└─────────────┘      └──────────────┘      └────────────────┘
     │ (2026)            │ (2027)                │ (2028)
     │                   │                       │
     ├───────────────┬───┴───────────────┬───────┘
     │               │                   │
     │          ┌────▼────────┐      ┌───▼──────────┐
     │          │ V2 - Beta   │  ──► │ V2 - Active  │
     │          │ Same schema │      │ New features │
     └─────────►│ + additions │      │              │
                └─────────────┘      └──────────────┘
                   (2026)              (2027)
```

---

## 3. Backward Compatibility Strategy

### The Contract

**Never remove, never rename, only add.**

```
❌ BREAKING - Removing field
Old: {"id":"1","name":"Laptop","price":1500.0,"status":"active"}
New: {"id":"1","name":"Laptop","price":1500.0}
     (removed "status") ← Breaks v1 clients

✅ SAFE - Adding field
Old: {"id":"1","name":"Laptop","price":1500.0}
New: {"id":"1","name":"Laptop","price":1500.0,"category":"Electronics"}
     (added "category") ← v1 clients ignore it

✅ SAFE - Changing default
Old: GET /products returns first 10 by default
New: GET /products returns first 20 by default
     (backward compat: add `?page_size=10` to old requests)

❌ BREAKING - Changing operator semantics
Old: price,lt,1000 means price < 1000
New: price,lt,1000 means price <= 1000
     ← Don't do this. Add new operator instead: lte
```

### Pattern: Feature Flags

For complex migrations, use feature flags to roll out gradually:

```go
// Go example
func (h *GetProductHandler) Handle(ctx context.Context, q GetProductQuery) (*Product, error) {
    product, _ := h.repo.FindByID(ctx, q.ID)

    // Feature flag: Add new fields only if client requested
    if h.config.FeatureEnabled("product.v2.schema", q.ClientID) {
        product.Metadata = h.extractMetadata(product)
    }

    return product, nil
}
```

```python
# Python example
def handle(self, query: GetProductQuery) -> Product:
    product = self.repo.find_by_id(query.id)

    # Feature flag: Add new fields only if client requested
    if self.config.is_feature_enabled("product.v2.schema", query.client_id):
        product.metadata = self._extract_metadata(product)

    return product
```

---

## 4. Error Code Evolution

### Error Codes NEVER Change

**Once an error code is in production, it is immutable.**

```
v1 (2026):
120000001 = APP_USE_CASE_FAILURE (500 - Internal Server Error)
120000002 = APP_VALIDATION_FAILURE (422 - Unprocessable Entity)
120000003 = APP_AUTHORIZATION_DENIED (403 - Forbidden)
120000004 = APP_RESOURCE_NOT_FOUND (404 - Not Found)
120000005 = APP_EXTERNAL_SERVICE_FAILURE (502 - Bad Gateway)
120000006 = APP_CONFLICT (409 - Conflict)

v2 (2027):
← Add new codes if needed
120000007 = APP_RATE_LIMIT_EXCEEDED (429 - Too Many Requests)
120000008 = APP_PAYMENT_FAILED (400 - Bad Request)

← But NEVER redefine existing codes
120000001 = ✅ Still means APP_USE_CASE_FAILURE
120000002 = ✅ Still means APP_VALIDATION_FAILURE
```

### Adding New Error Codes

When you need a new error category, **add** a new code:

```go
// Go
const (
    // Existing (never change)
    AppConflict = New(LayerApplication, 6) // 120000006

    // New in v2
    AppRateLimitExceeded = New(LayerApplication, 7) // 120000007
    AppPaymentFailed = New(LayerApplication, 8)     // 120000008
)
```

```python
# Python
class ErrorCodes:
    # Existing
    APP_CONFLICT = 120000006

    # New in v2
    APP_RATE_LIMIT_EXCEEDED = 120000007
    APP_PAYMENT_FAILED = 120000008
```

### Version-Specific Behavior

You can change **what triggers** an error code, but not the code itself:

```
v1: Duplicate product name → APP_CONFLICT (409)

v2: Duplicate product name → APP_CONFLICT (409)   ← Same code!
    OR Duplicate SKU        → APP_CONFLICT (409)   ← But triggers for more cases

✅ Both v1 and v2 clients understand: status 409 = conflict
```

---

## 5. Response Schema Migration

### Forward-Declare New Fields (Null-Tolerant)

Release new fields as `null` for several releases first:

```
Release 2026-06-01 (v1):
{
  "id": "prod-123",
  "name": "Laptop",
  "price": 1500.0
}

Release 2026-09-01 (v1.5 - introduces fields):
{
  "id": "prod-123",
  "name": "Laptop",
  "price": 1500.0,
  "category": null,         ← NEW field, null for now
  "supplier_id": null       ← NEW field, null for now
}

Release 2026-12-01 (v2 - populates fields):
{
  "id": "prod-123",
  "name": "Laptop",
  "price": 1500.0,
  "category": "Electronics",    ← NOW populated
  "supplier_id": "supplier-42"  ← NOW populated
}
```

**Why?** Clients that crash on unexpected fields will NOT crash on `null` values. You can safely add fields without breaking old clients.

### Deprecated Fields

If you must retire a field (rare):

```
v1:
{
  "id": "prod-123",
  "name": "Laptop",
  "status": "active",           ← OLD field
  "status_new": "in_stock"      ← NEW field, same meaning
}

v2:
{
  "id": "prod-123",
  "name": "Laptop",
  "status": "active",           ← STILL HERE (backward compat)
  "status_new": "in_stock"      ← Still both for migration period
}

v3:
{
  "id": "prod-123",
  "name": "Laptop",
  "status_new": "in_stock"      ← OLD field finally removed
}
```

---

## 6. Deprecation Guidelines

### Public Deprecation Timeline

For v1 → v2 migration:

```
2026-06-01: V2 released
            - New features in v2
            - v1 still 100% supported

2026-12-01: V1 enters maintenance mode (6 months after v2)
            - No new features for v1
            - Bug fixes and security patches only
            - Clients get warning: "v1 will sunset in 6 months"

2027-06-01: V1 sunset date
            - New connections: API Gateway rejects v1
            - Existing connections: Continue to work
            - Message: "v1 has reached EOL, please upgrade to v2"

2027-09-01: V1 removal
            - API Gateway no longer routes v1
            - Force all clients to v2
```

### Documentation

In your API docs, clearly state:

```markdown
## Versioning

### Current Versions
| Version | Status | Sunset Date | Support |
|---------|--------|-------------|---------|
| v1      | Maintenance | 2027-06-01 | Bug fixes only |
| v2      | Active | (ongoing) | New features |

### Upgrading from v1 to v2
1. Review schema changes: [migration guide]
2. Update error handling: error codes are identical
3. Add new fields to your parsers: [new fields list]
4. Test in staging: [test script]
5. Deploy: No downtime required
```

---

## 7. Implementation Examples

### Go: Version-Aware Router

```go
package interfaces

import (
    "github.com/gorilla/mux"
    "your-app/interfaces/http/handlers/v1"
    "your-app/interfaces/http/handlers/v2"
)

func RegisterRoutes(router *mux.Router) {
    // V1 routes (maintenance mode)
    v1Routes := router.PathPrefix("/api/v1").Subrouter()
    v1Routes.HandleFunc("/products", v1.GetProductsHandler).Methods("GET")
    v1Routes.HandleFunc("/products/{id}", v1.GetProductHandler).Methods("GET")
    v1Routes.HandleFunc("/products", v1.CreateProductHandler).Methods("POST")

    // V2 routes (active development)
    v2Routes := router.PathPrefix("/api/v2").Subrouter()
    v2Routes.HandleFunc("/products", v2.GetProductsHandler).Methods("GET")
    v2Routes.HandleFunc("/products/{id}", v2.GetProductHandler).Methods("GET")
    v2Routes.HandleFunc("/products", v2.CreateProductHandler).Methods("POST")
    v2Routes.HandleFunc("/products/{id}/variants", v2.GetVariantsHandler).Methods("GET") // V2 only
}
```

### Go: Version-Specific Handler

```go
package handlers

import (
    "encoding/json"
    "net/http"
    "your-app/application/queries"
    "your-app/interfaces/responses"
)

// V1 Handler - returns minimal schema
func (h *GetProductHandlerV1) Handle(w http.ResponseWriter, r *http.Request) {
    result, err := h.handler.Handle(r.Context(), query)
    if err != nil {
        json.NewEncoder(w).Encode(buildErrorResponse(err))
        return
    }

    // V1 schema: only basic fields
    response := map[string]interface{}{
        "id":    result.Product.ID,
        "name":  result.Product.Name,
        "price": result.Product.Price,
    }
    json.NewEncoder(w).Encode(response)
}

// V2 Handler - returns extended schema
func (h *GetProductHandlerV2) Handle(w http.ResponseWriter, r *http.Request) {
    result, err := h.handler.Handle(r.Context(), query)
    if err != nil {
        json.NewEncoder(w).Encode(buildErrorResponse(err))
        return
    }

    // V2 schema: includes new fields
    response := map[string]interface{}{
        "id":         result.Product.ID,
        "name":       result.Product.Name,
        "price":      result.Product.Price,
        "category":   result.Product.Category,        // NEW
        "created_at": result.Product.CreatedAt,       // NEW
        "updated_at": result.Product.UpdatedAt,       // NEW
    }
    json.NewEncoder(w).Encode(response)
}
```

### Python: Version-Aware Blueprint

```python
from flask import Blueprint, request, jsonify
from your_app.application.queries import GetProductQueryHandler
from your_app.infrastructure import ProductRepository

def create_products_api_v1(repo: ProductRepository):
    bp = Blueprint("products_v1", __name__, url_prefix="/api/v1/products")

    handler = GetProductQueryHandler(repo)

    @bp.route("/<product_id>", methods=["GET"])
    def get_product(product_id):
        result = handler.handle(GetProductQuery(id=product_id))

        # V1 schema: minimal
        return jsonify({
            "id": result.product.id,
            "name": result.product.name,
            "price": result.product.price,
        }), 200

    return bp

def create_products_api_v2(repo: ProductRepository):
    bp = Blueprint("products_v2", __name__, url_prefix="/api/v2/products")

    handler = GetProductQueryHandler(repo)

    @bp.route("/<product_id>", methods=["GET"])
    def get_product(product_id):
        result = handler.handle(GetProductQuery(id=product_id))

        # V2 schema: extended
        return jsonify({
            "id": result.product.id,
            "name": result.product.name,
            "price": result.product.price,
            "category": result.product.category,           # NEW
            "created_at": result.product.created_at.isoformat(),  # NEW
            "updated_at": result.product.updated_at.isoformat(),  # NEW
        }), 200

    return bp

# Register both versions
def create_app():
    app = Flask(__name__)
    repo = ProductRepository()

    # V1
    app.register_blueprint(create_products_api_v1(repo))

    # V2
    app.register_blueprint(create_products_api_v2(repo))

    return app
```

### Python: Conditional Fields with Feature Flags

```python
from your_app import config

class GetProductHandlerV2:
    def handle(self, query: GetProductQuery) -> GetProductResult:
        product = self.repo.find_by_id(query.id)

        # Conditionally add new fields based on feature flag
        if config.is_feature_enabled("product.show_supplier", query.client_id):
            product.supplier_id = self._get_supplier_id(product.id)

        if config.is_feature_enabled("product.show_inventory", query.client_id):
            product.inventory = self._get_inventory(product.id)

        return GetProductResult(product=product)

# In response builder
def format_product(product, version="v2"):
    response = {
        "id": product.id,
        "name": product.name,
        "price": product.price,
    }

    if version >= "v2":
        response["category"] = product.category
        response["created_at"] = product.created_at.isoformat()
        response["updated_at"] = product.updated_at.isoformat()

    if hasattr(product, 'supplier_id'):
        response["supplier_id"] = product.supplier_id

    if hasattr(product, 'inventory'):
        response["inventory"] = product.inventory

    return response
```

---

## Testing Version Compatibility

### Go: Test Both Versions

```go
func TestGetProduct_V1_Schema(t *testing.T) {
    // Test v1 still works
    repo := NewMockProductRepository()
    repo.Seed(activeProductFixture())

    handler := handlers.NewGetProductHandlerV1(repo)
    response := handler.Handle(testContext(), GetProductQuery{ID: "prod-1"})

    // V1 should only have these fields
    if response["id"] == "" || response["name"] == "" || response["price"] == 0 {
        t.Error("v1 missing required fields")
    }

    // V1 should NOT have these fields
    if _, hasCategory := response["category"]; hasCategory {
        t.Error("v1 should not have category field")
    }
}

func TestGetProduct_V2_Schema(t *testing.T) {
    // Test v2 has new fields
    repo := NewMockProductRepository()
    repo.Seed(activeProductFixture())

    handler := handlers.NewGetProductHandlerV2(repo)
    response := handler.Handle(testContext(), GetProductQuery{ID: "prod-1"})

    // V2 should have all v1 fields
    if response["id"] == "" || response["name"] == "" {
        t.Error("v2 missing v1 fields")
    }

    // V2 should have new fields
    if _, hasCategory := response["category"]; !hasCategory {
        t.Error("v2 should have category field")
    }
    if _, hasCreatedAt := response["created_at"]; !hasCreatedAt {
        t.Error("v2 should have created_at field")
    }
}
```

### Python: Test Both Versions

```python
def test_get_product_v1_schema():
    # Test v1 schema
    repo = MockProductRepository()
    repo.seed(active_product_fixture())

    handler = GetProductHandlerV1(repo)
    response = handler.handle(GetProductQuery(id="prod-1"))

    # V1 required fields
    assert "id" in response
    assert "name" in response
    assert "price" in response

    # V1 should NOT have v2 fields
    assert "category" not in response
    assert "created_at" not in response

def test_get_product_v2_schema():
    # Test v2 schema
    repo = MockProductRepository()
    repo.seed(active_product_fixture())

    handler = GetProductHandlerV2(repo)
    response = handler.handle(GetProductQuery(id="prod-1"))

    # V2 includes v1 fields
    assert "id" in response
    assert "name" in response
    assert "price" in response

    # V2 includes new fields
    assert "category" in response
    assert "created_at" in response
    assert "updated_at" in response
```

---

## Summary

| Principle | Rule |
|-----------|------|
| **Error Contract** | Never changes. Universal across all versions. |
| **New Fields** | Add as `null` first, populate later. Never remove. |
| **New Error Codes** | Add with higher sequence numbers. Never redefine. |
| **Operators** | Never change semantics. Add new operators instead. |
| **Version Lifecycle** | Active (2+ years) → Maintenance (1 year) → Sunset (EOL) |
| **URL Versioning** | Use path prefix: `/api/v1/`, `/api/v2/` |
| **Testing** | Test both versions simultaneously. Assert schema differences. |
| **Documentation** | Publish migration guides and deprecation timeline. |

---

*Next: Database Agnosticity section*
