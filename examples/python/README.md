# Example — backbone-python

Full CRUD product API with Clean Architecture + CQRS.

## Run

```bash
cd clean_api_python
pip install flask flask-restx
python main.py
# → http://localhost:5000/docs
```

## Endpoints

| Method | Path | Response |
|---|---|---|
| `POST` | `/api/v1/products` | `{"id": "uuid"}` |
| `GET` | `/api/v1/products?filters=...&page=1&page_size=10&sort_by=price:desc` | paginated |
| `GET` | `/api/v1/products/{id}` | raw object |
| `PUT` | `/api/v1/products/{id}` | `{"id": "uuid"}` |
| `DELETE` | `/api/v1/products/{id}` | `{"id": "uuid"}` |
| `PATCH` | `/api/v1/products/{id}/status` | `{"id": "uuid"}` |

For curl examples and filter operators see the [root README](../../README.md).

## Filter Operators

| Operator | Description |
|----------|-------------|
| `eq` | equals |
| `ne` | not equals |
| `gt` / `gte` | greater than / or equal |
| `lt` / `lte` | less than / or equal |
| `contains` | substring match (backbone automatically wraps with `%...%`) |
| `in` | value in list (pipe-separated: `val1\|val2`) |
| `between` | range (pipe-separated: `min\|max`) |
| `is_null` / `is_not_null` | null checks |

> **Note on `contains`**: Pass the value **without `%` symbols** — the backbone automatically wraps it for substring matching. Example: `filters=name,contains,laptop` ✓
