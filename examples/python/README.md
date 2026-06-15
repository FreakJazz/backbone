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
