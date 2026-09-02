# clean_api_python

Product CRUD + sales/stock-movement transactions using **backbone** —
Clean Architecture + CQRS with Flask, backed by real **PostgreSQL**
(product catalog) and **MongoDB** (append-only transaction logs).

| Concern                           | Store      | Why                                                                   |
|------------------------------------|------------|------------------------------------------------------------------------|
| Product catalog (`stock` counter)  | PostgreSQL | Relational, needs atomic check-and-update guards, strong consistency  |
| Sales log                          | MongoDB    | Append-only event stream, one document per sale, never updated        |
| Stock movements log                | MongoDB    | Append-only event stream (`IN` / `OUT` / `ADJUSTMENT`)                |

## Setup

```bash
# 1. Start Postgres + Mongo (+ Adminer + Mongo Express UIs)
docker compose -f ../docker-compose.yml up -d

# 2. Configure
cd clean_api_python
cp .env.example .env

# 3. Install & run
python -m venv .venv
.venv/Scripts/activate   # (or: source .venv/bin/activate on Linux/macOS)
pip install -r requirements.txt
python main.py
# → http://localhost:5000/docs
```

`backbone` is installed for real from GitHub via pip (see `requirements.txt`)
— no sys.path/sys.modules shim needed.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/products?filters=...&page=1&page_size=10&sort_by=price:desc` | Paginated list — see **Pagination** below |
| `POST` | `/api/v1/products` | `{"name","price","category","description","stock"}` |
| `GET` | `/api/v1/products/{id}` | Get by ID |
| `PUT` | `/api/v1/products/{id}` | Update (partial) |
| `DELETE` | `/api/v1/products/{id}` | Delete |
| `PATCH` | `/api/v1/products/{id}/status` | `{"status": "active|inactive|discontinued"}` |
| `POST` | `/api/v1/sales` | `{"product_id","quantity"}` — decrements stock (Postgres) + logs sale (Mongo) |
| `GET` | `/api/v1/sales?product_id=...` | List sales, optionally filtered by product |
| `POST` | `/api/v1/stock-movements` | `{"product_id","type":"IN\|OUT\|ADJUSTMENT","quantity","reason"}` |
| `GET` | `/api/v1/stock-movements?product_id=...` | List stock movements, optionally filtered |

## Filter Operators

| Operator | Description |
|----------|-------------|
| `eq` | equals |
| `ne` | not equals |
| `gt` / `gte` | greater than / or equal |
| `lt` / `lte` | less than / or equal |
| `like` | substring match (backbone automatically wraps with `%...%`) |
| `in` | value in list (pipe-separated: `val1\|val2`) |
| `between` | range (pipe-separated: `min\|max`) |
| `is_null` / `is_not_null` | null checks |

> **Note on `like`**: Pass the value **without `%` symbols** — backbone wraps it for you. Example: `filters=name,like,laptop` ✓

## Pagination

Two mutually exclusive modes on `GET /api/v1/products` — `cursor`, when
present, wins and `page` is ignored:

**Offset** (default) — `?page=1&page_size=10`. Familiar, gives a
`total_count`, but `OFFSET` cost grows with how deep you page: Postgres
still scans and discards every skipped row no matter how large the offset
gets.

```json
{ "meta": {...}, "items": [...], "pagination": { "total_count": 42, "page": 3, "page_size": 10 } }
```

**Cursor (keyset)** — `?cursor=<token>&page_size=10`. Pass `cursor=` (empty)
to start; take `page.next_cursor` from the response and pass it back to get
the next page. No `total_count`/`page` — a keyset window can't produce one
without an extra `COUNT` query, which would defeat the point. Recommended
for deep paging: Postgres seeks directly via the `(sort_field, id)` index
ordering regardless of how far into the result set you are.

```bash
GET /api/v1/products?cursor=&page_size=10&sort_by=price:desc
GET /api/v1/products?cursor=eyJ2IjogMTk5Ljk5LCAiaWQiOiAiLi4uIn0&page_size=10&sort_by=price:desc
```

```json
{ "meta": {...}, "items": [...], "page": { "next_cursor": "eyJ2Ijog...", "has_more": true } }
```

The cursor is opaque — treat it as a black box, always pass back exactly
what the previous response gave you. It's implemented by
`backbone.domain.specifications.encode_cursor`/`decode_cursor`
(base64 of `{"v": <sort field's value>, "id": <row id>}`) — same wire
format as backbone-go's `EncodeCursor`/`DecodeCursor`, since contracts
match backbone Python and Go exactly everywhere else in this library.

## Performance

Applied, verified against real Postgres+Mongo:

- **One round trip, not two, for every list endpoint.** `find_all` used to
  run a `SELECT` and a separate `COUNT(*)` query; it now rides the total
  count on the same query via Postgres's `COUNT(*) OVER()`. The Mongo
  repositories (`sales`, `stock_movements`) use a single `$facet`
  aggregation (`data` + `totalCount` branches from one `$match`) instead of
  `count_documents()` + `find()`. This is what actually matters as a
  table/collection grows — every avoided round trip is real network +
  planner latency.
  - Edge case handled correctly: `COUNT(*) OVER()` returns nothing when a
    requested page is past the last row, so `find_all` falls back to one
    plain `COUNT(*)` *only* in that (rare) case — `$facet`'s `totalCount`
    branch has no such problem, since it's independent of `data`'s
    `$skip`/`$limit`.
- **Indexes match the actual query shapes**: `category`, `status`, a unique
  index on `lower(name)`, and `created_at DESC` (the default sort field —
  an unindexed `ORDER BY` becomes a full sort once the table is large).
  Mongo's `(product_id, created_at)` compound index covers both the
  `$match` and the `$sort` in one pass.
- **Connection pool tuned to avoid cold starts**: `min_size=2` on the
  psycopg pool so a request right after idle doesn't pay for a fresh
  connection handshake.
- **`debug=True` was hardcoded** in the original in-memory version of this
  example — not just a style nit: the Werkzeug debugger it enables lets a
  remote client execute arbitrary Python via the traceback page if this
  ever gets exposed off localhost, and it adds real per-request overhead
  (reloader stat-checks, verbose tracebacks). Now driven by `FLASK_DEBUG`,
  off by default.

### Where backbone helps vs. where it doesn't

- **Helps**: `Specification.to_expression()` returns a generic
  `{field, operator, value}` / `{operator: AND|OR|NOT, ...}` tree designed
  for exactly this — `_expr_to_sql` in `postgres_product_repository.py`
  walks it into a real parameterized SQL WHERE clause. `MemoryProductRepository`
  is the other adapter for the same tree, evaluating it with
  `is_satisfied_by` — that reflection-ish path never runs in the
  Postgres-backed request path.
- **Added**: keyset pagination didn't exist anywhere in backbone —
  `find_all` only ever took `page`/`page_size`. `encode_cursor`/`decode_cursor`
  (opaque `base64({"v": ..., "id": ...})` tokens) is the new, generic
  building block; `CursorPaginatedResponseBuilder` is the matching response
  envelope. Both are intentionally minimal — the library doesn't try to
  build SQL for you here, because it can't know a column's real type (see
  `_coerce_cursor_value` in `postgres_product_repository.py`); that
  schema-aware part correctly stays in the repository that owns the schema,
  the same separation backbone already used for `Specification.to_expression()`
  vs. the repository's `_expr_to_sql`.
- **A real structural limit, still true**: OFFSET pagination itself (the
  default mode, `?page=&page_size=`) still degrades at very large offsets —
  Postgres has to scan and discard every skipped row no matter how the
  round trips are batched. That's exactly why cursor pagination exists now
  as the alternative for deep paging, rather than something to "fix" about
  OFFSET — the two modes serve different needs (total counts vs. no
  degradation), not one obsoleting the other.

For curl examples of the error-response shape, see the [Go example's README](../go/clean-api-go/README.md#request--response-examples).
