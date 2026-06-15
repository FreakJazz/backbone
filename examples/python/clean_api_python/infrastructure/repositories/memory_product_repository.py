from typing import Any, Dict, List, Optional, Tuple

from domain.entities.product import Product
from domain.repositories.product_repository import IProductRepository


class MemoryProductRepository(IProductRepository):
    def __init__(self) -> None:
        self._store: Dict[str, Product] = {}

    def save(self, product: Product) -> Product:
        self._store[product.id] = product
        return product

    def find_by_id(self, product_id: str) -> Optional[Product]:
        return self._store.get(product_id)

    def find_all(
        self,
        filters: Optional[list] = None,
        sort_by: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Product], int]:
        products = list(self._store.values())

        if filters:
            products = [p for p in products if self._matches(p, filters)]

        if sort_by and ":" in sort_by:
            field, direction = sort_by.split(":", 1)
            reverse = direction.lower() == "desc"
            products.sort(key=lambda p: getattr(p, field, ""), reverse=reverse)

        total = len(products)
        start = (page - 1) * page_size
        return products[start: start + page_size], total

    def delete(self, product_id: str) -> None:
        self._store.pop(product_id, None)

    def exists(self, product_id: str) -> bool:
        return product_id in self._store

    def _matches(self, product: Product, filters: list) -> bool:
        """Simple spec evaluation — each spec has .is_satisfied_by()."""
        for spec in filters:
            if hasattr(spec, "is_satisfied_by"):
                if not spec.is_satisfied_by(product.to_dict()):
                    return False
        return True
