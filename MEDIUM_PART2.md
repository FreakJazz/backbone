# One Filter Param, Any Entity: The Specification Pattern for REST List Endpoints

**Part 2 of 3 — backbone series** | [Part 1: 9-digit error codes](./MEDIUM_PART1.md)

---

## The list endpoint problem nobody talks about

Every REST API has the same list endpoint written four different ways across four services.

Service A:
```
GET /products?name=laptop&min_price=500&max_price=2000&sort=price_desc&page=1&limit=10
```

Service B:
```
GET /orders?status=pending&created_after=2026-01-01&order_by=created_at&direction=desc
```

Service C:
```
GET /users?search=john&role=admin&active=true&sortBy=lastName&sortOrder=ASC&offset=0&count=20
```

Three services. Three filter conventions. Three sort conventions. Three pagination conventions. Every time a frontend developer moves from one service to another they have to learn a new query language.

And on the backend side: every new filterable field means touching the router, the query builder, the repository, and the docs. Four files for one new column.

backbone solves this with the **Specification Pattern** — a single query language that works for every entity endpoint in every service, in both Go and Python.

---

## The idea: four generic params for everything

Instead of per-entity query params, every list endpoint in every service accepts the same four params:

| Param       | Format                             | Example                  |
|-------------|-------------------------------------|--------------------------|
| `filters`   | `field,operator,value[,condition]`  | `price,gt,500,and`       |
| `page`      | integer                             | `1`                      |
| `page_size` | integer                             | `10`                     |
| `sort_by`   | `field:direction`                   | `created_at:desc`        |
| `cursor`    | opaque token (optional, replaces `page`) | from a previous response's `page.next_cursor` |

One frontend developer. One query language. Every service.

The same URL pattern that queries products also queries orders, users, invoices, and inventory — without changing anything in the client.

---

## Supported operators

```
eq          →  field = value
ne          →  field != value
gt          →  field > value
gte         →  field >= value
lt          →  field < value
lte         →  field <= value
contains    →  field LIKE %value%
in          →  field IN (val1, val2, val3)     — values separated by |
between     →  field BETWEEN val1 AND val2     — values separated by |
is_null     →  field IS NULL
is_not_null →  field IS NOT NULL
```

Conditions (`and` / `or`) chain multiple filters.

---

## A real list endpoint URL

```
GET /api/v1/products
  ?filters=category,eq,Electronics,and
  &filters=price,between,500|2000,and
  &filters=name,contains,laptop,and
  &filters=stock,gt,0
  &page=1&page_size=10&sort_by=price:desc
```

Translation: *give me Electronics products with a price between 500 and 2000, whose name contains "laptop", that are in stock, ordered by price descending, first page of 10.*

No custom query language. No GraphQL. No OData. Just URL-encoded params that any HTTP client can build.

---

## The Specification Pattern

Before the implementation, a quick explanation of the pattern itself — because understanding it makes the code obvious.

A **Specification** is an object that answers one question: *does this entity satisfy this condition?*

```python
# Does this product cost more than 500?
spec = GreaterThanSpecification("price", 500)
spec.is_satisfied_by(product)  # True or False
```

Specifications compose with `and` / `or` / `not`:

```python
# Electronics AND price between 500 and 2000 AND in stock
spec = (EqualSpecification("category", "Electronics") &
        BetweenSpecification("price", 500, 2000) &
        GreaterThanSpecification("stock", 0))
```

A **Criteria** object wraps a specification and adds pagination and sorting — everything a repository needs to execute a query.

The parser converts URL params into this object automatically. Your repository receives a `Criteria` and translates it into SQL, MongoDB queries, or in-memory filtering — the application layer never knows which.

---

## Implementation in Go

### Parsing URL params into a Criteria

```go
import "github.com/FreakJazz/backbone/backbone-go/domain/specifications"

func (h *GetProductsQueryHandler) Handle(ctx context.Context, q GetProductsQuery) (*GetProductsResult, error) {
    // Parse sort_by: "price:desc" → ("price", "desc")
    sortField, sortDir := specifications.ParseSortBy(q.SortBy)

    // Parse filters: ["category,eq,Electronics,and", "price,between,500|2000"] → *Criteria
    criteria := specifications.ParseFilterParams(
        q.Filters,
        q.Page,
        q.PageSize,
        sortField,
        sortDir,
    )

    // One call, one round trip: FindByCriteria returns the page AND the
    // total match count together. Earlier drafts of this repository split
    // that into FindByCriteria + a separate Count(ctx, criteria) call —
    // two queries where one does. A production repository (see "What the
    // repository does with a Criteria" below) rides the total on the same
    // query via SQL's COUNT(*) OVER(), so the split version wasn't just
    // more verbose, it was strictly slower for no benefit.
    products, total, err := h.repo.FindByCriteria(ctx, criteria)
    if err != nil {
        return nil, err
    }

    return &GetProductsResult{Products: products, Total: total}, nil
}
```

### Building criteria manually for domain logic

```go
import "github.com/FreakJazz/backbone/backbone-go/domain/specifications"

// Business rule: find all active premium products for restock alert
criteria := specifications.NewCriteriaBuilder().
    Where("status", "=", "active").
    Where("tier", "=", "premium").
    Where("stock", "<", 10).
    OrderByAsc("stock").
    Paginate(1, 100).
    Build()

products, total, _ := repo.FindByCriteria(ctx, criteria)
```

### Receiving params in the HTTP handler

```go
func (h *ProductQueryHandler) GetProducts(w http.ResponseWriter, r *http.Request) {
    page, _     := strconv.Atoi(r.URL.Query().Get("page"))
    pageSize, _ := strconv.Atoi(r.URL.Query().Get("page_size"))

    if page < 1     { page = 1 }
    if pageSize < 1 { pageSize = 10 }

    query := GetProductsQuery{
        Filters:  r.URL.Query()["filters"],   // []string — repeated param
        SortBy:   r.URL.Query().Get("sort_by"),
        Page:     page,
        PageSize: pageSize,
    }

    result, err := h.getProductsHandler.Handle(r.Context(), query)
    if err != nil {
        e := responses.ErrorResponseBuilder.InternalServerError(err.Error())
        json.NewEncoder(w).Encode(e)
        return
    }

    json.NewEncoder(w).Encode(
        responses.PaginatedResponseBuilder.Success(
            result.Products, result.Total, page, pageSize, "Products retrieved successfully"))
}
```

---

## Implementation in Python

### Parsing URL params into a specification

```python
from backbone import FilterParser, SortDirection
from backbone.domain.specifications.sort_specification import SortParser

class GetProductsQueryHandler:
    def handle(self, query):
        # Parse filters: ["category,eq,Electronics,and", "price,between,500|2000"]
        parser = FilterParser()
        spec = parser.parse_filters(query.filters)

        # Parse sort: "price,desc" → SortSpecification
        sort = SortParser().parse_sort(query.sort_by or "created_at,desc")

        # One call, one round trip: find_by_criteria returns the page AND
        # the total match count together — not a separate .count(spec)
        # call. A production repository rides the total on the same query
        # via SQL's COUNT(*) OVER() (see "What the repository does with a
        # Criteria" below), so splitting this into two calls wouldn't just
        # be more verbose, it would be strictly slower for no benefit.
        products, total = self._repo.find_by_criteria(spec, sort, query.page, query.page_size)

        return GetProductsResult(products=products, total=total)
```

### Building specifications manually for domain logic

```python
from backbone import (
    EqualSpecification,
    BetweenSpecification,
    GreaterThanSpecification,
    LikeSpecification,
)

# Business rule: find active premium products low on stock
spec = (EqualSpecification("status", "active") &
        EqualSpecification("tier", "premium") &
        GreaterThanSpecification("stock", 0) &
        BetweenSpecification("price", 500, 2000))

products, total = repo.find_by_criteria(spec, page=1, page_size=100)
```

### Parsing from a dictionary (Django-style)

```python
# From query params dict directly — useful with Flask/FastAPI
spec = FilterParser().parse_filters({
    "category":    "Electronics",
    "price__gte":  "500",
    "price__lte":  "2000",
    "name__like":  "laptop",
    "stock__gt":   "0",
})
```

### Receiving params in the Flask route

```python
from backbone import FilterParser, ErrorResponseBuilder, PaginatedResponseBuilder
from backbone.domain.specifications.sort_specification import SortParser
from backbone.errors import ErrorCodes

@bp.route("/products", methods=["GET"])
def get_products():
    try:
        filters  = request.args.getlist("filters")
        sort_by  = request.args.get("sort_by", "created_at,desc")
        page     = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))

        query  = GetProductsQuery(filters=filters, sort_by=sort_by, page=page, page_size=page_size)
        result = handler.handle(query)

        return jsonify(PaginatedResponseBuilder.success(
            items=result.products, total_count=result.total,
            page=page, page_size=page_size,
            message="Products retrieved successfully")), 200

    except Exception as e:
        err = ErrorResponseBuilder.internal_server_error(str(e))
        return jsonify(err), 500
```

---

## Validating which fields are filterable

You do not want users filtering on internal fields like `password_hash` or `internal_notes`. backbone provides field validation:

**Go — validate in the query handler:**
```go
allowed := map[string]bool{
    "name": true, "price": true, "category": true, "status": true,
}

for _, f := range q.Filters {
    field := strings.SplitN(f, ",", 2)[0]
    if !allowed[field] {
        e := responses.ErrorResponseBuilder.ValidationError(
            fmt.Sprintf("filter on field '%s' is not allowed", field),
            responses.ErrorOpts{Code: bberrors.IfcInvalidFilterFormat.Int()})
        json.NewEncoder(w).Encode(e)
        return
    }
}
```

**Python — validate in the parser:**
```python
allowed_fields = ["name", "price", "category", "status", "stock"]

parser = FilterParser()
for filter_str in query.filters:
    field = filter_str.split(",")[0].strip()
    parser.validate_filter_field(field, allowed_fields)
    # raises InvalidValueObjectException if field not in list

spec = parser.parse_filters(query.filters)
```

---

## What the repository does with a Criteria

The repository is the only layer that knows about the database. It receives the `Criteria` object and translates it — without the application layer knowing how. Two real implementations, same call from the application layer:

**In-memory repository (testing / demo)** — evaluates the specification against each entity in process, via reflection:

```go
func (r *MemoryProductRepository) FindByCriteria(ctx context.Context, c *specifications.Criteria) ([]*Product, int, error) {
    var filtered []*Product
    for _, p := range r.products {
        if c.Specification == nil || c.Specification.IsSatisfiedBy(p) {
            filtered = append(filtered, p)
        }
    }
    // sort filtered by c.Sorts...
    total := len(filtered)
    page := paginate(filtered, c.Offset, c.Limit)
    return page, total, nil
}
```

**Postgres repository (production)** — `Criteria.GetFullSQL(...)` already builds a real parameterized `WHERE`/`ORDER BY`/`LIMIT` clause from the same specification, no reflection involved. The one addition worth making yourself: ride the total count on the *same* query with `COUNT(*) OVER()`, instead of running the SELECT and then a separate `COUNT(*)` — that's the difference between one round trip and two, and it's the round trips that cost real latency as the table grows, not the SQL generation itself:

```go
func (r *PostgresProductRepository) FindByCriteria(ctx context.Context, c *specifications.Criteria) ([]*Product, int, error) {
    query, args := c.GetFullSQL("SELECT id, name, price, category, status, stock, COUNT(*) OVER() AS full_count FROM products")
    query = rebindPlaceholders(query) // backbone-go's Specification.ToSQL emits "?" — pgx needs "$1, $2, ..."

    rows, err := r.pool.Query(ctx, query, args...)
    // scan rows into products, read full_count off the first row...
}
```

The application layer calls `repo.FindByCriteria(ctx, criteria)` in both cases — same call, different implementation, same `(products, total, error)` return shape. That is the whole point of the Repository Pattern — and why the total count is part of that one call instead of a second method entirely: the interface itself should make the fast shape the only shape.

---

## Deep paging: when OFFSET stops being enough

`page`/`page_size` above is `LIMIT`/`OFFSET` under the hood — simple, gives you a `total_count`, and it's the right default. But `OFFSET` has a cost that grows with the offset: to return page 5,000, Postgres still has to scan and discard the 49,990 rows before it. Whether you fetch the count in one round trip or two, that scan happens regardless.

For infinite-scroll feeds, activity logs, or any list a client pages deep into, backbone offers keyset ("cursor") pagination as an alternative — not a replacement, a different tool for a different access pattern:

```
GET /api/v1/products?cursor=&page_size=20&sort_by=price:desc
```

```json
{
  "meta":  { "status": "success", "status_code": 200, "message": "Products retrieved successfully" },
  "items": [ { "id": "1", "price": 1999.0 }, ... ],
  "page":  { "next_cursor": "eyJ2IjoxOTk5LjAsImlkIjoiMSJ9", "has_more": true }
}
```

Pass `page.next_cursor` back as `cursor` to get the next page. No `total_count`, no `page` number — a keyset window can't produce a total without the very `COUNT` query this pattern exists to avoid, and there's no such thing as "page number 47" when you're seeking by position, not counting rows. That's a real trade-off, not an oversight: pick offset when you need a total or random-access page jumps, cursor when you're paging forward through a large or growing set.

**Go:**
```go
import "github.com/FreakJazz/backbone/backbone-go/domain/specifications"

// Encode a cursor from the last row of a page — sortValue is whatever that
// row's sort field held, id is the row's unique id (the tiebreaker for
// when the sort field repeats, e.g. two products at the same price).
token, _ := specifications.EncodeCursor(lastProduct.Price, lastProduct.ID)

// Decode it back on the next request
sortValue, id, err := specifications.DecodeCursor(r.URL.Query().Get("cursor"))
```

**Python:**
```python
from backbone.domain.specifications import encode_cursor, decode_cursor

token = encode_cursor(last_product.price, last_product.id)
sort_value, id_ = decode_cursor(request.args.get("cursor"))
```

The token is opaque JSON-in-base64 (`{"v": ..., "id": ...}`) — the same wire format in both languages, but treat it as a black box regardless: it's not signed, not meant to be constructed by hand, just passed back verbatim. Decoding it gives you the raw sort value (a float, string, or bool from JSON) — converting that into the column's real type (a `float64` for price, a parsed `time.Time` for a timestamp field) is the repository's job, the same way it already owns turning a `Specification` into real SQL. The cursor package can't know your schema; the repository that queries it does.

Building the actual keyset query is one extra `WHERE` fragment alongside whatever the `Specification` already produced:

```go
// desc sort: strictly-less-than; asc sort: strictly-greater-than.
// The id tiebreak matters: without it, two rows tied on price could get
// skipped or repeated across pages.
where += " AND (price, id) < (?, ?)"
args = append(args, sortValue, id)

query := "SELECT ... FROM products WHERE " + where +
    " ORDER BY price DESC, id DESC LIMIT " + strconv.Itoa(limit+1) // +1 to know if there's a next page for free
```

---

## Combining with the error contract from Part 1

When a filter is malformed, backbone raises a typed exception that maps to a consistent error response:

```
GET /products?filters=price,unknown_op,500
```

```json
{
  "rid":         "c3f2...",
  "status_code": 400,
  "message":     "filter on field 'price': unsupported operator 'unknown_op'",
  "error_code":  130000005
}
```

Error code `130000005` = `IFC_INVALID_FILTER_FORMAT`. The monitoring alert fires for the Interface layer. The frontend parses the same four-field shape it always parses. No special case handling anywhere.

---

## Install

Tagged and pushed for real — `backbone-go/v0.2.0` and `backbone-python/v0.2.0`. Neither is on pkg.go.dev / PyPI yet, so both install straight from the GitHub tag:

```bash
# Go — note @v0.2.0, not @backbone-go/v0.2.0: the module path already
# contains the backbone-go/ prefix the tag itself needs
go get github.com/FreakJazz/backbone/backbone-go@v0.2.0

# Python — a plain HTTPS tarball URL, not git+https://, so installing it
# needs no `git` binary on the host or in a Docker image
pip install "backbone @ https://github.com/FreakJazz/backbone/archive/refs/tags/backbone-python/v0.2.0.tar.gz#subdirectory=backbone-python"
```

Source and full examples: [github.com/FreakJazz/backbone](https://github.com/FreakJazz/backbone)

---

## What is next

**Part 3** covers structured logging — the same JSON log shape across Go and Python services, with three formatters (JSON for production, coloured console for development, compact for high-throughput), and how the `rid` from Part 1 flows through every log line automatically.

---

*If your list endpoints finally speak the same language, hit the clap button.*
