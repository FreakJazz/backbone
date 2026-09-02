# clean-api-go

Product CRUD + sales/stock-movement transactions using **backbone-go** —
Clean Architecture + CQRS with `net/http`, backed by real **PostgreSQL**
(product catalog) and **MongoDB** (append-only transaction logs).

| Concern                           | Store      | Why                                                                   |
|------------------------------------|------------|------------------------------------------------------------------------|
| Product catalog (`stock` counter)  | PostgreSQL | Relational, needs atomic check-and-update guards, strong consistency  |
| Sales log                          | MongoDB    | Append-only event stream, one document per sale, never updated        |
| Stock movements log                | MongoDB    | Append-only event stream (`IN` / `OUT` / `ADJUSTMENT`)                |

---

## Setup

```bash
# 1. Start Postgres + Mongo (+ Adminer + Mongo Express UIs)
docker compose -f ../../docker-compose.yml up -d

# 2. Configure
cp .env.example .env

# 3. Run
go mod tidy
swag init          # regenerate Swagger docs (only needed after annotation changes)
go run main.go
```

Server runs on **http://localhost:8005** (see `.env.example` to change it).

| URL | Description |
|-----|-------------|
| http://localhost:8005/docs/index.html | **Swagger UI** |
| http://localhost:8005/api/v1/products | REST API |

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/products` | List with filters, pagination, sorting — see **Pagination** below |
| `POST` | `/api/v1/products` | Create product (`name`, `price`, `category`, `description`, `stock`) |
| `GET` | `/api/v1/products/{id}` | Get by ID |
| `PUT` | `/api/v1/products/{id}` | Update (partial) |
| `DELETE` | `/api/v1/products/{id}` | Delete |
| `PATCH` | `/api/v1/products/{id}/status` | Change status |
| `POST` | `/api/v1/sales` | Register a sale — decrements stock (Postgres) + logs sale (Mongo) |
| `GET` | `/api/v1/sales?product_id=...` | List sales, optionally filtered by product |
| `POST` | `/api/v1/stock-movements` | Register `IN`/`OUT`/`ADJUSTMENT` — adjusts stock (Postgres) + logs movement (Mongo) |
| `GET` | `/api/v1/stock-movements?product_id=...` | List stock movements, optionally filtered by product |

---

## Filters

Filters are passed as **repeated query params** — one per condition:

```
GET /api/v1/products
  ?filters=category,eq,Electronics,and
  &filters=price,gt,500
  &page=1
  &page_size=10
  &sort_by=price:desc
```

Format per token: `field,operator,value[,condition]`

| Operator | Description |
|----------|-------------|
| `eq` | equals |
| `ne` | not equals |
| `gt` / `gte` | greater than / or equal |
| `lt` / `lte` | less than / or equal |
| `contains` | substring match (backbone automatically wraps with `%...%`) |
| `in` | value in list (comma-separated) |
| `between` | range `min\|max` |
| `is_null` / `is_not_null` | null checks |

> **Note on `contains`**: Pass the value **without `%` symbols** — the backbone automatically wraps it for substring matching across all persistence layers (in-memory, SQL, MongoDB). Example: `filters=name,contains,laptop` ✓ (NOT `%laptop%`)

Condition (`and` / `or`) joins this filter with the next one. Omit on the last filter.

---

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
GET /api/v1/products?cursor=eyJ2IjoxOTkuOTksImlkIjoiLi4uIn0&page_size=10&sort_by=price:desc
```

```json
{ "meta": {...}, "items": [...], "page": { "next_cursor": "eyJ2Ijo...", "has_more": true } }
```

The cursor is opaque — treat it as a black box, always pass back exactly
what the previous response gave you. It's implemented by
`backbone-go`'s `specifications.EncodeCursor`/`DecodeCursor`
(base64 of `{"v": <sort field's value>, "id": <row id>}`), which is what
made this cheap to add: the library already had everything needed except
the token itself.

---

## Request / Response examples

### Create product
```bash
POST /api/v1/products
Content-Type: application/json

{ "name": "Laptop Pro", "price": 999.99, "category": "Electronics", "description": "..." }
```
```json
{ "id": "uuid-123" }
```

### List with filters
```bash
GET /api/v1/products?filters=category,eq,Electronics,and&filters=price,gt,500&sort_by=price:desc
```
```json
{
  "meta":       { "status": "success", "status_code": 200, "message": "Products retrieved successfully" },
  "items":      [{ "id": "1", "name": "Laptop Pro", "price": 1500, "category": "Electronics", "status": "active" }],
  "pagination": { "total_count": 2, "page": 1, "page_size": 10 }
}
```

### Validation error
```json
{
  "rid":         "afdef44d-2f09-49d8-a847-89e0c56d8ce4",
  "status_code": 400,
  "message":     "name must be at least 2 characters",
  "error_code":  130000001,
  "field_errors": { "name": "min length 2" }
}
```

### Conflict — duplicate name
```json
{
  "rid":         "3bc6ef65-e2f9-4737-a94d-d43da58258d1",
  "status_code": 409,
  "message":     "a product with that name already exists",
  "error_code":  120000006,
  "field_errors": { "name": "already exists" }
}
```

---

## Business rules

- `name` — required, min 2 characters, **unique (case-insensitive)**
- `price` — required, must be > 0
- `category` — required
- `status` — `active` | `inactive` | `discontinued` (default: `active`)
- Updating a product with the **same name** is allowed (no false conflict)

---

## Error codes

| Code | Layer | Meaning | HTTP |
|------|-------|---------|------|
| `120000002` | Application | ValidationFailure | 400 |
| `120000004` | Application | ResourceNotFound | 404 |
| `120000006` | Application | Conflict (duplicate) | 409 |
| `130000001` | Interface | InvalidRequestBody | 400 |
| `140000001` | Infrastructure | DBFailure | 500 |

Full catalog → [backbone root README](../../../README.md#exception-system--códigos-de-9-dígitos)

---

## Performance

Applied, verified against real Postgres+Mongo (not just "should be faster in theory"):

- **One round trip, not two, for every list endpoint.** `products`, `sales`
  and `stock-movements` all used to run a `SELECT` and a separate `COUNT`
  query. `FindByCriteria` now rides the total count on the same query via
  Postgres's `COUNT(*) OVER()`; the Mongo repositories use a single `$facet`
  aggregation (`data` + `totalCount` branches from one `$match`). This is
  the optimization that matters as a table/collection grows — every avoided
  round trip is real network + planner latency, not just CPU.
  - Edge case handled correctly: `COUNT(*) OVER()` returns nothing when a
    requested page is past the last row, so `FindByCriteria` falls back to
    one plain `COUNT(*)` *only* in that (rare) case — `$facet`'s `totalCount`
    branch doesn't have this problem since it's independent of `data`'s
    `$skip`/`$limit`.
- **Indexes match the actual query shapes**: `category`, `status`, a unique
  index on `lower(name)`, and — easy to forget — `created_at DESC`, since
  that's the default sort field and an unindexed `ORDER BY` becomes a full
  sort once the table is large. Mongo's `(product_id, created_at)` compound
  index covers both the `$match` and the `$sort` in one pass.
- **Removed a real per-request allocation**: every command/query handler
  used to call `logger.WithMethod("Handle")` *inside* `Handle()` — a call
  that clones the logger struct and its context map on every single
  request, for a method name that never varies. Moved to construction time
  (alongside `WithLayer`/`WithComponent`, which were already there) across
  all ten handlers; `Handle()` now just reads a field.
- **Connection pools tuned to avoid cold starts**: `MinConns = 2` on the
  pgx pool so a request right after idle doesn't pay for a fresh TCP+TLS
  handshake.

### Where backbone-go helps vs. where it doesn't

Two things flagged here as backbone-go limitations were fixed in the
library itself (not worked around in the example) once it became clear
fixing them was small and correct — see `backbone-go/interfaces/responses/response_builders.go`
and `backbone-go/domain/specifications/cursor.go`:

- **Fixed**: `PaginatedResponseBuilder.Success` and `SimpleObjectResponseBuilder.Found`
  used to be hard-typed to `map[string]interface{}`, forcing every response
  to build a map (and pay `encoding/json`'s key-sorting on it) even when the
  caller already had a tagged struct. Both now accept `any` — Go has no
  generic methods, so this was the fix, not a generic signature — and
  `get_products.go`/`get_sales.go`/`get_stock_movements.go`/`get_product_by_id.go`
  were updated to pass `[]*entities.Product` etc. straight through instead
  of flattening them first (`Product.ToMap()` is gone — nothing calls it
  anymore).
- **Added**: keyset pagination didn't exist anywhere in backbone-go —
  `Criteria` only ever exposed `Limit`/`Offset`. `specifications.EncodeCursor`/`DecodeCursor`
  (opaque `base64({"v": ..., "id": ...})` tokens) is the new, generic
  building block; `CursorPaginatedResponseBuilder` is the matching response
  envelope. Both are intentionally minimal — the library doesn't try to
  build SQL for you here, because it can't know a column's real type (see
  `coerceCursorValue` in `postgres_product_repository.go`); that
  schema-aware part correctly stays in the repository that owns the schema,
  the same separation backbone-go already used for `Specification.ToSQL()`
  vs. the repository's `rebindPlaceholders`.
- **Helps, unchanged**: `Criteria.GetFullSQL(...)` and `Specification.ToSQL()`
  are what make the single-round-trip `COUNT(*) OVER()` query (and the
  keyset query's filter half) possible at all — the library already emits a
  real parameterized WHERE clause, so there was no reflection-based
  filtering to remove from the Postgres path (unlike `MemoryProductRepository`,
  which does use `IsSatisfiedBy` reflection, but that's a test fake, never
  in the request path).
- **A real structural limit, still true**: OFFSET pagination itself (the
  default mode, `?page=&page_size=`) still degrades at very large offsets —
  Postgres has to scan and discard every skipped row no matter how the
  round trips are batched. That's exactly why cursor pagination exists now
  as the alternative for deep paging, rather than something to "fix" about
  OFFSET — the two modes serve different needs (total counts vs. no
  degradation), not one obsoleting the other.

## What's actually "real" here

- **`infrastructure/repositories/postgres_product_repository.go`** translates
  `backbone-go`'s `Criteria` (built from `?filters=field,op,value`) into a
  real parameterized SQL query via `Criteria.GetFullSQL(...)`, rebinding the
  library's `?` placeholders to Postgres's `$1, $2, ...`.
- **`AdjustStock`** is a single `UPDATE ... WHERE stock + $1 >= 0 RETURNING
  stock` statement — the check and the write happen atomically in the
  database, so two concurrent sales racing for the last unit can't both
  succeed.
- **`RegisterSaleCommandHandler`** / **`RegisterStockMovementCommandHandler`**
  each touch two databases for one business action (decrement/adjust stock
  in Postgres, then append a document in Mongo). This is **not** a
  distributed transaction — if the Mongo write fails after the Postgres
  update commits, the handler returns an error but does **not** roll stock
  back; it logs the inconsistency instead. A production system would close
  that gap with an outbox table + reconciliation job.
- **`MemoryProductRepository`** is kept as a fast, dependency-free fake for
  the unit tests under `tests/application/` — it is not wired into
  `main.go`; `PostgresProductRepository` is.
- Schema is created with an idempotent `CREATE TABLE IF NOT EXISTS` in
  `infrastructure/database/postgres.go` for a one-command demo. A real
  service should own its schema with a versioned migration tool
  (golang-migrate, atlas, goose, ...) instead.

---

## Project structure

```
clean-api-go/
├── domain/
│   ├── entities/          # Product, Sale, StockMovement
│   ├── repositories/      # IProductRepository (+AdjustStock) · ISaleRepository · IStockMovementRepository
│   └── specifications/    # BuildCriteria (filters → *Criteria)
├── application/
│   ├── commands/          # Create · Update · Delete · ChangeStatus · RegisterSale · RegisterStockMovement
│   └── queries/           # GetProducts · GetProductByID · GetSales · GetStockMovements
├── infrastructure/
│   ├── database/          # Postgres pool + migration, Mongo client + indexes
│   ├── repositories/      # PostgresProductRepository · MongoSaleRepository · MongoStockMovementRepository
│   │                      # + MemoryProductRepository (test fake only)
│   └── seeders/           # ProductSeeder
├── interfaces/
│   └── http/
│       ├── handlers/      # ProductCommandHandler · ProductQueryHandler · SaleHandler · StockMovementHandler
│       └── v1/            # RegisterRoutes
├── tests/
│   └── application/
│       ├── commands/      # create · update tests (against MemoryProductRepository)
│       └── queries/       # list · detail tests
├── docs/                  # Generated by swag init
├── .env.example
├── go.mod
└── main.go                # DI container only
```

Shared `docker-compose.yml` (Postgres + Mongo + Adminer + Mongo Express) at
`../../docker-compose.yml` — used by both `clean-api-go` and
`clean_api_python`.

## Known caveat inherited from backbone-go

`contains`/`like` filters compile to `LIKE` (case-sensitive in Postgres by
default). Use `ILIKE` at the database level if you need case-insensitive
search — the library doesn't emit it yet.

---

## Run tests

```bash
go test ./tests/... -v
```
