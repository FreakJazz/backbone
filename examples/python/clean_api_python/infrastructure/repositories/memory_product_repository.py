from datetime import datetime
from typing import Dict, List, Optional, Tuple

from backbone.domain.specifications import Specification, encode_cursor, decode_cursor

from domain.entities.product import Product
from domain.repositories.product_repository import IProductRepository, InsufficientStockError


class MemoryProductRepository(IProductRepository):
    """Fast, dependency-free fake of IProductRepository. Kept for quick
    experimentation without any infrastructure running; production wiring in
    main.py uses PostgresProductRepository instead."""

    def __init__(self) -> None:
        self._store: Dict[str, Product] = {}

    def save(self, product: Product) -> Product:
        self._store[product.id] = product
        return product

    def find_by_id(self, product_id: str) -> Optional[Product]:
        return self._store.get(product_id)

    def find_all(
        self,
        spec: Optional[Specification] = None,
        sort_field: str = "name",
        sort_desc: bool = False,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Product], int]:
        products = list(self._store.values())

        # Filtrado usando Specification.is_satisfied_by sobre el dict del producto
        if spec is not None:
            products = [p for p in products if spec.is_satisfied_by(p)]

        # Ordenamiento
        products.sort(
            key=lambda p: getattr(p, sort_field, ""),
            reverse=sort_desc,
        )

        total = len(products)
        start = (page - 1) * page_size
        return products[start: start + page_size], total

    def find_by_name(self, name: str) -> Optional[Product]:
        lower = name.strip().lower()
        for p in self._store.values():
            if p.name.lower() == lower:
                return p
        return None

    def delete(self, product_id: str) -> None:
        self._store.pop(product_id, None)

    def exists(self, product_id: str) -> bool:
        return product_id in self._store

    def adjust_stock(self, product_id: str, delta: int) -> int:
        product = self._store.get(product_id)
        if product is None:
            raise ValueError("product not found")
        if product.stock + delta < 0:
            raise InsufficientStockError("insufficient stock")
        product.stock += delta
        return product.stock

    def find_page_by_cursor(
        self,
        spec: Optional[Specification],
        sort_field: str,
        sort_desc: bool,
        after_cursor: Optional[str],
        limit: int,
    ) -> Tuple[List[Product], Optional[str]]:
        """Mirrors PostgresProductRepository's keyset contract using the
        same full filter+sort pass find_all already does, then finds
        after_cursor's row by id and slices the next `limit` items after it
        — an O(n) scan here, since the fake has no index to seek with, but
        the contract callers see (same ordering, same tiebreak-by-id, same
        next-cursor semantics) is identical to the real Postgres
        implementation."""
        products = list(self._store.values())
        if spec is not None:
            products = [p for p in products if spec.is_satisfied_by(p)]

        products.sort(key=lambda p: (getattr(p, sort_field, ""), p.id), reverse=sort_desc)

        start = 0
        if after_cursor:
            _, after_id = decode_cursor(after_cursor)
            for i, p in enumerate(products):
                if p.id == after_id:
                    start = i + 1
                    break
            else:
                return [], None

        if start >= len(products):
            return [], None

        end = start + limit
        has_more = end < len(products)
        page = products[start:end]

        next_cursor = None
        if has_more and page:
            last = page[-1]
            next_cursor = encode_cursor(_cursor_value(last, sort_field), last.id)
        return page, next_cursor


def _cursor_value(product: Product, sort_field: str):
    """Same value find_page_by_cursor sorts and slices by, formatted for
    encode_cursor. datetime gets an explicit isoformat() rather than
    relying on encode_cursor's json default=str fallback (str(datetime)
    uses a space separator, not 'T') — PostgresProductRepository parses
    created_at cursors with datetime.fromisoformat, so the two must agree
    on format even though, in practice, a given deployment only ever uses
    one repository or the other."""
    value = getattr(product, sort_field, "")
    if isinstance(value, datetime):
        return value.isoformat()
    return value
