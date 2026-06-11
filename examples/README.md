# Examples

Full CRUD product API in both languages — same contracts, same architecture.

| | Python | Go |
|---|---|---|
| Path | `examples/clean_api_python/` | `backbone-go/examples/clean-api-go/` |
| Framework | Flask + Flask-RESTX | net/http (stdlib) |
| Docs | `http://localhost:5000/docs` | `http://localhost:8080/swagger/` |
| Run | `python main.py` | `go run main.go` |

---

## Endpoints

| Method | Path | Description | Response |
|---|---|---|---|
| `POST` | `/api/v1/products` | Create product | `{"id": "uuid"}` |
| `GET` | `/api/v1/products` | List + filters + pagination | paginated envelope |
| `GET` | `/api/v1/products/{id}` | Get single product | raw object |
| `PUT` | `/api/v1/products/{id}` | Update product | `{"id": "uuid"}` |
| `DELETE` | `/api/v1/products/{id}` | Delete product | `{"id": "uuid"}` |
| `PATCH` | `/api/v1/products/{id}/status` | Activate / deactivate | `{"id": "uuid"}` |
| `GET` | `/health` | Health check | `{"status": "healthy"}` |

---

## curl examples

```bash
BASE=http://localhost:8080/api/v1   # Go   (Python: port 5000)

# Create
curl -X POST $BASE/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Laptop Dell XPS","description":"16GB RAM","price":1500,"category":"Electronics","stock":50}'
# → {"id": "uuid-generated"}

# List with filters
curl "$BASE/products?filters=category,eq,Electronics,and&filters=price,gt,500&page=1&page_size=10&sort_by=price:desc"

# Get by ID
curl $BASE/products/1

# Update
curl -X PUT $BASE/products/1 \
  -H "Content-Type: application/json" \
  -d '{"price":1400,"stock":45}'
# → {"id": "1"}

# Delete
curl -X DELETE $BASE/products/1
# → {"id": "1"}

# Change status
curl -X PATCH $BASE/products/2/status \
  -H "Content-Type: application/json" \
  -d '{"active": false}'
# → {"id": "2"}
```

---

## Filter operators

| Operator | SQL equivalent | Example |
|---|---|---|
| `eq` | `=` | `filters=category,eq,Electronics` |
| `ne` | `!=` | `filters=active,ne,false` |
| `gt` | `>` | `filters=price,gt,500` |
| `gte` | `>=` | `filters=price,gte,500` |
| `lt` | `<` | `filters=stock,lt,10` |
| `lte` | `<=` | `filters=price,lte,2000` |
| `contains` | `LIKE %x%` | `filters=name,contains,laptop` |
| `in` | `IN (a\|b\|c)` | `filters=category,in,Electronics\|Furniture` |
| `between` | `BETWEEN a AND b` | `filters=price,between,100\|2000` |
| `is_null` | `IS NULL` | `filters=description,is_null` |
| `is_not_null` | `IS NOT NULL` | `filters=description,is_not_null` |

Multiple filters combine with `and` / `or` via the `condition` field (default `and`).

---

## Architecture

Both examples follow the same Clean Architecture + CQRS structure:

```
application/
  commands/     CreateProduct · UpdateProduct · DeleteProduct · ChangeProductStatus
  queries/      GetProducts · GetProductByID

infrastructure/
  repositories/ MemoryProductRepository (swap for DB in production)
  seeders/      ProductSeeder

interfaces/http/
  commands/     HTTP adapter per command  (POST PUT DELETE PATCH)
  queries/      HTTP adapter per query    (GET)
  v1/           routes (versioned)
```

`main.py` / `main.go` — DI container only. No business logic.

---

## Running

**Python:**
```bash
cd examples/clean_api_python
pip install flask flask-restx
python main.py
```

**Go:**
```bash
cd backbone-go/examples/clean-api-go
go mod tidy
go run main.go
```
