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
import "github.com/freakjazz/backbone-go/domain/specifications"

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

    products, err := h.repo.FindByCriteria(ctx, criteria)
    if err != nil {
        return nil, err
    }

    total, err := h.repo.Count(ctx, criteria)
    if err != nil {
        return nil, err
    }

    return &GetProductsResult{Products: products, Total: total}, nil
}
```

### Building criteria manually for domain logic

```go
import "github.com/freakjazz/backbone-go/domain/specifications"

// Business rule: find all active premium products for restock alert
criteria := specifications.NewCriteriaBuilder().
    Where("status", "=", "active").
    Where("tier", "=", "premium").
    Where("stock", "<", 10).
    OrderByAsc("stock").
    Paginate(1, 100).
    Build()

products, _ := repo.FindByCriteria(ctx, criteria)
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
        e := responses.ErrorResponseBuilder.InternalError(err.Error())
        json.NewEncoder(w).Encode(e)
        return
    }

    json.NewEncoder(w).Encode(
        responses.PaginatedResponseBuilder.Found(result.Products, result.Meta, result.Pagination))
}
```

---

## Implementation in Python

### Parsing URL params into a specification

```python
from backbone import FilterParser, SortParser, SortDirection

class GetProductsQueryHandler:
    def handle(self, query):
        # Parse filters: ["category,eq,Electronics,and", "price,between,500|2000"]
        parser = FilterParser()
        spec = parser.parse_filters(query.filters)

        # Parse sort: "price,desc" → SortSpecification
        sort = SortParser().parse_sort(query.sort_by or "created_at,desc")

        products = self._repo.find_by_criteria(spec, sort, query.page, query.page_size)
        total    = self._repo.count(spec)

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

products = repo.find_by_criteria(spec, page=1, page_size=100)
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
from backbone import FilterParser, SortParser, ErrorResponseBuilder, PaginatedResponseBuilder
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

        return jsonify(PaginatedResponseBuilder.found(
            result.products, result.meta, result.pagination)), 200

    except Exception as e:
        err = ErrorResponseBuilder.internal_error(str(e))
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

The repository is the only layer that knows about the database. It receives the `Criteria` object and translates it — without the application layer knowing how.

**In-memory repository (testing / demo):**
```go
func (r *MemoryProductRepository) FindByCriteria(ctx context.Context, c *specifications.Criteria) ([]*Product, error) {
    var results []*Product
    for _, p := range r.products {
        if r.matchesCriteria(p, c) {
            results = append(results, p)
        }
    }
    // apply sort, pagination...
    return results, nil
}
```

**SQL repository (production):**
```go
func (r *SQLProductRepository) FindByCriteria(ctx context.Context, c *specifications.Criteria) ([]*Product, error) {
    qb := specifications.NewQueryBuilder("products")
    qb.ApplyCriteria(c)
    sql, args := qb.Build()
    // execute sql with args...
}
```

The application layer calls `repo.FindByCriteria(ctx, criteria)` in both cases — same call, different implementation. That is the whole point of the Repository Pattern.

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

```bash
# Go
go get github.com/freakjazz/backbone-go@v0.1.0

# Python
pip install backbone-python==0.1.0
```

Source and full examples: [github.com/FreakJazz/backbone](https://github.com/FreakJazz/backbone)

---

## What is next

**Part 3** covers structured logging — the same JSON log shape across Go and Python services, with three formatters (JSON for production, coloured console for development, compact for high-throughput), and how the `rid` from Part 1 flows through every log line automatically.

---

*If your list endpoints finally speak the same language, hit the clap button.*
