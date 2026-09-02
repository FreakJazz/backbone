import re
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple

from backbone.domain.specifications import Specification, encode_cursor, decode_cursor
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from domain.entities.product import Product
from domain.repositories.product_repository import IProductRepository, InsufficientStockError

COLUMNS = "id, name, price, category, status, description, stock, created_at, updated_at"

# Same allowlist pattern backbone's own FilterParser enforces — a field name
# must look like a plain identifier, since it gets interpolated into the
# query text (values never do; those are always %s placeholders).
_FIELD_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_OPERATOR_SQL = {
    "eq": "=", "ne": "!=", "lt": "<", "lte": "<=", "gt": ">", "gte": ">=",
    "like": "LIKE", "ilike": "ILIKE",
}

# Fields find_page_by_cursor is allowed to order and seek by. Kept separate
# from find_all's sort-field validation since every field here also needs a
# _coerce_cursor_value/_cursor_value_for case below.
_CURSOR_SORTABLE_FIELDS = {"name", "category", "status", "price", "stock", "created_at"}


class PostgresProductRepository(IProductRepository):
    """Production implementation of IProductRepository. Unlike
    MemoryProductRepository, filters are translated into a real
    parameterized SQL WHERE clause (see `_spec_to_sql`) instead of pulling
    every row into Python and filtering with `Specification.is_satisfied_by`."""

    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool

    def save(self, product: Product) -> Product:
        product.updated_at = datetime.now(timezone.utc)
        with self._pool.connection() as conn:
            conn.execute(
                f"""
                INSERT INTO products (id, name, price, category, status, description, stock, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name, price = EXCLUDED.price, category = EXCLUDED.category,
                    status = EXCLUDED.status, description = EXCLUDED.description,
                    stock = EXCLUDED.stock, updated_at = EXCLUDED.updated_at
                """,
                (product.id, product.name, product.price, product.category, product.status,
                 product.description, product.stock, product.created_at, product.updated_at),
            )
        return product

    def find_by_id(self, product_id: str) -> Optional[Product]:
        with self._pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            row = cur.execute(f"SELECT {COLUMNS} FROM products WHERE id = %s", (product_id,)).fetchone()
        return _row_to_product(row) if row else None

    def find_by_name(self, name: str) -> Optional[Product]:
        with self._pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            row = cur.execute(f"SELECT {COLUMNS} FROM products WHERE lower(name) = lower(%s)", (name,)).fetchone()
        return _row_to_product(row) if row else None

    def find_all(
        self,
        spec: Optional[Specification] = None,
        sort_field: str = "created_at",
        sort_desc: bool = True,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Product], int]:
        """Returns the page together with the total match count computed in
        the SAME query via COUNT(*) OVER() — one round trip to Postgres
        instead of a separate SELECT and COUNT(*) query. That's the
        optimization that actually matters once the table has millions of
        rows: each extra round trip costs real network + planning latency,
        while the window function reuses the same index scan Postgres
        already did for the page."""
        where_sql, params = _spec_to_sql(spec)
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)

        sort_field = sort_field if _FIELD_NAME_PATTERN.match(sort_field) else "created_at"
        direction = "DESC" if sort_desc else "ASC"

        offset = (page - 1) * page_size
        query = f"SELECT {COLUMNS}, COUNT(*) OVER() AS full_count FROM products"
        if where_sql:
            query += f" WHERE {where_sql}"
        query += f" ORDER BY {sort_field} {direction} LIMIT %s OFFSET %s"

        with self._pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            rows = cur.execute(query, params + [page_size, offset]).fetchall()

            if rows:
                return [_row_to_product(r) for r in rows], rows[0]["full_count"]

            if offset == 0:
                return [], 0  # genuinely no matches — no fallback query needed

            # Page beyond the last one: COUNT(*) OVER() has nothing to ride
            # on since zero rows came back, so fall back to a plain COUNT(*)
            # for this (rare — client asked past the end) case only.
            count_query = "SELECT COUNT(*) FROM products"
            if where_sql:
                count_query += f" WHERE {where_sql}"
            total = cur.execute(count_query, params).fetchone()["count"]
            return [], total

    def find_page_by_cursor(
        self,
        spec: Optional[Specification],
        sort_field: str,
        sort_desc: bool,
        after_cursor: Optional[str],
        limit: int,
    ) -> Tuple[List[Product], Optional[str]]:
        """Seeks directly to the row after after_cursor via a
        (sort_field, id) keyset condition instead of OFFSET — the
        difference that matters once a client pages deep into a large
        result set: OFFSET still has to scan and discard every skipped row
        no matter how large it gets, while this goes straight to the right
        place through the index.

        Fetches one row more than limit to know, for free, whether there is
        a next page — no separate COUNT or existence check needed."""
        if sort_field not in _CURSOR_SORTABLE_FIELDS:
            sort_field, sort_desc = "created_at", True
        limit = max(limit, 1)

        where_sql, params = _spec_to_sql(spec)

        if after_cursor:
            raw_value, after_id = decode_cursor(after_cursor)
            sort_value = _coerce_cursor_value(sort_field, raw_value)
            op = "<" if sort_desc else ">"
            keyset_clause = f"({sort_field}, id) {op} (%s, %s)"
            where_sql = f"({where_sql}) AND {keyset_clause}" if where_sql else keyset_clause
            params = params + [sort_value, after_id]

        direction = "DESC" if sort_desc else "ASC"
        query = f"SELECT {COLUMNS} FROM products"
        if where_sql:
            query += f" WHERE {where_sql}"
        # Tie-break by id so rows with an equal sort_field value (e.g. two
        # products at the same price) still get a total order — without
        # it, the keyset condition above could skip or repeat a tied row.
        query += f" ORDER BY {sort_field} {direction}, id {direction} LIMIT %s"

        with self._pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            rows = cur.execute(query, params + [limit + 1]).fetchall()

        next_cursor = None
        if len(rows) > limit:
            rows = rows[:limit]
            last = rows[-1]
            next_cursor = encode_cursor(_cursor_value_for(sort_field, last), last["id"])
        return [_row_to_product(r) for r in rows], next_cursor

    def delete(self, product_id: str) -> None:
        with self._pool.connection() as conn:
            conn.execute("DELETE FROM products WHERE id = %s", (product_id,))

    def exists(self, product_id: str) -> bool:
        with self._pool.connection() as conn:
            row = conn.execute("SELECT 1 FROM products WHERE id = %s", (product_id,)).fetchone()
        return row is not None

    def adjust_stock(self, product_id: str, delta: int) -> int:
        """Single UPDATE ... WHERE stock + %s >= 0 RETURNING stock — the
        check and the write happen atomically in the database, so two
        concurrent sales racing for the last unit can't both succeed."""
        with self._pool.connection() as conn:
            row = conn.execute(
                """
                UPDATE products SET stock = stock + %s, updated_at = now()
                WHERE id = %s AND stock + %s >= 0
                RETURNING stock
                """,
                (delta, product_id, delta),
            ).fetchone()
            if row is not None:
                return row[0]
            if not self.exists(product_id):
                raise ValueError("product not found")
            raise InsufficientStockError("insufficient stock")


def _row_to_product(row: dict) -> Product:
    return Product(
        id=row["id"], name=row["name"], price=row["price"], category=row["category"],
        status=row["status"], description=row["description"], stock=row["stock"],
        created_at=row["created_at"], updated_at=row["updated_at"],
    )


def _coerce_cursor_value(sort_field: str, value: Any) -> Any:
    """Converts a cursor's decoded JSON value (a float for any number,
    otherwise a string) into the Python type psycopg needs to bind against
    sort_field's real column type. This is exactly the same kind of
    caller-knows-the-schema conversion FilterParser values already go
    through (raw query-string text -> int/float/str) before reaching a
    Specification — the generic cursor module can't know column types, so
    the repository that does is where this belongs."""
    if sort_field == "price":
        return float(value)
    if sort_field == "stock":
        return int(value)
    if sort_field == "created_at":
        return datetime.fromisoformat(value)
    return str(value)  # name, category, status


def _cursor_value_for(sort_field: str, row: dict) -> Any:
    """Extracts sort_field's value from a result row, for encoding the
    token that identifies that row's position for the next page."""
    value = row[sort_field]
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _spec_to_sql(spec: Optional[Specification]) -> Tuple[str, List[Any]]:
    """Walks the generic {field, operator, value} / {operator: AND|OR|NOT, ...}
    tree that Specification.to_expression() produces and compiles it into a
    real parameterized SQL fragment. This is exactly the adapter-specific
    translation the base class's docstring calls for — MemoryProductRepository
    is the other adapter, evaluating the same tree with `is_satisfied_by`."""
    if spec is None:
        return "", []
    return _expr_to_sql(spec.to_expression())


def _expr_to_sql(expr: dict) -> Tuple[str, List[Any]]:
    op = expr["operator"]

    if op == "AND":
        left_sql, left_params = _expr_to_sql(expr["left"])
        right_sql, right_params = _expr_to_sql(expr["right"])
        return f"({left_sql} AND {right_sql})", left_params + right_params
    if op == "OR":
        left_sql, left_params = _expr_to_sql(expr["left"])
        right_sql, right_params = _expr_to_sql(expr["right"])
        return f"({left_sql} OR {right_sql})", left_params + right_params
    if op == "NOT":
        inner_sql, inner_params = _expr_to_sql(expr["spec"])
        return f"NOT ({inner_sql})", inner_params

    field = expr["field"]
    if not _FIELD_NAME_PATTERN.match(field):
        return "FALSE", []  # unsafe identifier — degrade to always-false, like backbone-go does

    value = expr["value"]

    if op == "in":
        placeholders = ", ".join(["%s"] * len(value))
        return f"{field} IN ({placeholders})", list(value)
    if op == "between":
        return f"{field} BETWEEN %s AND %s", [value[0], value[1]]
    if op == "is_null":
        return f"{field} IS NULL", []
    if op == "is_not_null":
        return f"{field} IS NOT NULL", []

    sql_op = _OPERATOR_SQL.get(op, "=")
    return f"{field} {sql_op} %s", [value]
