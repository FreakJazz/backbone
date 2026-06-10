# Examples

Complete CRUD API examples for both backbone variants.

| | Python | Go |
|---|---|---|
| Framework | FastAPI | net/http (stdlib) |
| Path | `examples/clean_api_python/` | `backbone-go/examples/clean-api-go/` |
| Run | `uvicorn main:app --reload` | `go run main.go` |
| Port | 8000 | 8080 |

---

## Endpoints

Both examples expose identical contracts:

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/products` | Create → `{"id": "uuid"}` |
| `GET` | `/api/products` | List + filters + pagination |
| `GET` | `/api/products/{id}` | Single product (raw object) |
| `PUT` | `/api/products/{id}` | Update → `{"id": "uuid"}` |
| `DELETE` | `/api/products/{id}` | Delete → `{"id": "uuid"}` |
| `PATCH` | `/api/products/{id}/status` | Activate / deactivate → `{"id": "uuid"}` |
| `GET` | `/health` | Health check |

---

## Request / Response Examples

### POST /api/products
```bash
curl -X POST http://localhost:8080/api/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Laptop Dell XPS","description":"High performance","price":1500,"category":"Electronics","stock":50}'
```
```json
{"id": "uuid-generated-123"}
```

### GET /api/products (with filters)
```bash
curl "http://localhost:8080/api/products?category=Electronics&min_price=500&max_price=2000&in_stock=true&page=1&page_size=10"
```
```json
{
  "meta": {
    "status": "success",
    "status_code": 200,
    "message": "Products retrieved successfully"
  },
  "items": [
    {"id": "1", "name": "Laptop Dell XPS", "price": 1500.0, "category": "Electronics", "stock": 50, "active": true}
  ],
  "pagination": {
    "total_count": 1,
    "page": 1,
    "page_size": 10,
    "total_pages": 1
  }
}
```

### GET /api/products/{id}
```bash
curl http://localhost:8080/api/products/1
```
```json
{
  "id": "1",
  "name": "Laptop Dell XPS",
  "description": "High performance",
  "price": 1500.0,
  "category": "Electronics",
  "stock": 50,
  "active": true,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### PUT /api/products/{id}
```bash
curl -X PUT http://localhost:8080/api/products/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Laptop Dell XPS 15 Updated","price":1400}'
```
```json
{"id": "1"}
```

### DELETE /api/products/{id}
```bash
curl -X DELETE http://localhost:8080/api/products/1
```
```json
{"id": "1"}
```

### PATCH /api/products/{id}/status
```bash
curl -X PATCH http://localhost:8080/api/products/1/status \
  -H "Content-Type: application/json" \
  -d '{"active": false}'
```
```json
{"id": "1"}
```

### Error response
```json
{
  "request_id": "uuid",
  "status_code": 404,
  "message": "Product not found",
  "code_error": "NOT_FOUND"
}
```

---

## Query Filters (GET /api/products)

| Param | Type | Description |
|---|---|---|
| `category` | string | Filter by category |
| `min_price` | float | Minimum price |
| `max_price` | float | Maximum price |
| `in_stock` | bool | Only in-stock items |
| `active` | bool | Active only (default `true`) |
| `name` | string | Name pattern search |
| `page` | int | Page number (default `1`) |
| `page_size` | int | Items per page (default `10`) |
| `sort_by` | string | Field to sort by |
| `sort_order` | string | `asc` or `desc` |

---

## Architecture Layers

```
domain/
  entities/        Product entity with domain validation
  repositories/    ProductRepository interface
  specifications/  Active, Category, PriceRange, InStock specs

application/
  usecases/        CreateProduct  GetProducts  GetProductByID
                   UpdateProduct  DeleteProduct  ChangeProductStatus

infrastructure/
  repositories/    In-memory (swap for SQLAlchemy / GORM in production)

interfaces/
  http/handlers/   ProductHandler — delegates to use cases
  http/middleware/  Logging middleware — injects request_id
```

---

## Log Output

Structured JSON — same shape in Python and Go:

```json
{"timestamp":"2024-01-01T12:00:00Z","level":"INFO","service":"product-api","component":"HTTPMiddleware","layer":"interfaces","method":"LoggingMiddleware","message":"Incoming HTTP request","request_id":"abc-123","extra_data":{"method":"POST","path":"/api/products"}}
{"timestamp":"2024-01-01T12:00:00Z","level":"INFO","service":"product-api","component":"ProductHandler","layer":"interfaces","method":"CreateProduct","message":"Product created","request_id":"abc-123","extra_data":{"product_id":"uuid-generated"}}
{"timestamp":"2024-01-01T12:00:00Z","level":"DEBUG","service":"product-api","component":"MemoryProductRepository","layer":"infrastructure","method":"Create","message":"Product created","extra_data":{"product_id":"uuid","duration_ms":0}}
```

---

## Running

**Go:**
```bash
cd backbone-go/examples/clean-api-go
go run main.go
# → http://localhost:8080
```

**Python:**
```bash
cd examples/clean_api_python
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# → http://localhost:8000
```
