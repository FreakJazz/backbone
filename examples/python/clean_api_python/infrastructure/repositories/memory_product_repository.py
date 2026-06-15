from typing import Dict, List, Optional, Tuple

from backbone.domain.specifications import Specification

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

    def delete(self, product_id: str) -> None:
        self._store.pop(product_id, None)

    def exists(self, product_id: str) -> bool:
        return product_id in self._store
