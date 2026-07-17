# Filter Usage Guide — Backbone

## Quick Reference

### How `contains` (LIKE) Works

The `contains` operator automatically wraps your search value with `%...%` for substring matching across all persistence layers (in-memory, SQL, MongoDB). **You don't need to do it manually.**

| Don't ❌ | Do ✅ |
|---------|------|
| `filters=name,contains,%laptop%` | `filters=name,contains,laptop` |
| `filters=email,contains,%@gmail%` | `filters=email,contains,@gmail` |
| `filters=description,contains,%wireless%` | `filters=description,contains,wireless` |

### Why?

The backbone specification layer handles wrapping internally:

**Go:**
```go
// In backbone-go/domain/specifications/specification.go
func NewLikeSpecification(field, pattern string) *LikeSpecification {
    // Automatically wraps pattern with % unless already wrapped
    if !strings.HasPrefix(pattern, "%") {
        pattern = "%" + pattern
    }
    if !strings.HasSuffix(pattern, "%") {
        pattern = pattern + "%"
    }
    return &LikeSpecification{field: field, pattern: pattern}
}
```

**Python:**
```python
# In backbone-python/domain/specifications/filter_specification.py
class LikeSpecification(FilterSpecification):
    def __init__(self, field: str, value: str):
        # Wrap pattern with % unless already wrapped
        wrapped_value = value
        if not value.startswith("%"):
            wrapped_value = "%" + wrapped_value
        if not wrapped_value.endswith("%"):
            wrapped_value = wrapped_value + "%"
        super().__init__(field, "like", wrapped_value)
```

This ensures:
- ✅ Consistent behavior across all adapters (SQLAlchemy, MongoDB, in-memory)
- ✅ No code duplication in consuming applications
- ✅ Single source of truth in the backbone

---

## Complete Filter Examples

### Go Example
```bash
GET /api/v1/products
  ?filters=category,eq,Electronics,and
  &filters=price,gt,500,and
  &filters=name,contains,laptop
  &page=1&page_size=10&sort_by=price:desc
```

**Response:** Electronics products over $500 with "laptop" in the name.

### Python Example
```python
filters = [
    "category,eq,Electronics,and",
    "price,gt,500,and",
    "name,contains,laptop"
]
spec = FilterParser().parse_filters(filters)
products = repository.find(spec, page=1, page_size=10)
```

---

## All Operators

| Operator | Format | Example | Result |
|----------|--------|---------|--------|
| `eq` | `field,eq,value` | `status,eq,active` | status = 'active' |
| `ne` | `field,ne,value` | `status,ne,deleted` | status != 'deleted' |
| `gt` | `field,gt,value` | `price,gt,100` | price > 100 |
| `gte` | `field,gte,value` | `age,gte,18` | age >= 18 |
| `lt` | `field,lt,value` | `price,lt,1000` | price < 1000 |
| `lte` | `field,lte,value` | `remaining,lte,5` | remaining <= 5 |
| `contains` | `field,contains,text` | `name,contains,john` | name LIKE '%john%' |
| `in` | `field,in,val1\|val2\|val3` | `status,in,active\|pending` | status IN ('active', 'pending') |
| `between` | `field,between,min\|max` | `price,between,50\|500` | price BETWEEN 50 AND 500 |
| `is_null` | `field,is_null` | `deleted_at,is_null` | deleted_at IS NULL |
| `is_not_null` | `field,is_not_null` | `updated_at,is_not_null` | updated_at IS NOT NULL |

---

## Logical Connectors

Join filters with `and` or `or`:

```
filter1,value1,and
filter2,value2,or
filter3,value3
     ↑
  (no connector on last filter)
```

**Example:**
```bash
?filters=status,eq,active,and
&filters=type,ne,draft,or
&filters=created_at,is_not_null
```

Evaluates as: `(status='active' AND type!='draft') OR created_at IS NOT NULL`

---

## Implementation in Your Application

### Go
```go
package application

func (h *GetProductsHandler) Handle(ctx context.Context, filters []string) {
    // No manual wrapping needed — backbone handles it
    criteria := specifications.ParseFilterParams(
        filters,
        page, pageSize,
        sortField, sortDir,
    )
    products, _ := h.repo.FindByCriteria(ctx, criteria)
}
```

### Python
```python
from backbone import FilterParser

class GetProductsHandler:
    def handle(self, filters: list):
        # No manual wrapping needed — backbone handles it
        spec = FilterParser().parse_filters(filters)
        products, total = self.repo.find_all(spec=spec, page=page)
```

---

## Key Takeaway

✨ **Pass clean filter values to backbone. It handles the rest.**

- Don't wrap `contains` with `%`
- Don't escape special characters (backbone handles it)
- Don't think about SQL/MongoDB differences (backbone abstracts them)
- Just pass the raw value and let the specification layer work
