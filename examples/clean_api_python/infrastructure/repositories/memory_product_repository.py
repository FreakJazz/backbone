"""Memory product repository - Infrastructure layer"""
from typing import List, Optional, Tuple
import sys
import os
from datetime import datetime
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from backbone.domain.specifications import Specification
from backbone.infrastructure.logging import LoggerFactory
from examples.clean_api_python.domain.entities.product import Product
from examples.clean_api_python.domain.repositories.product_repository import ProductRepository


class MemoryProductRepository(ProductRepository):
    """In-memory product repository implementation"""

    def __init__(self):
        self.products: dict = {}
        self.logger = LoggerFactory.create_layer_logger(
            "product-api", "infrastructure", "MemoryProductRepository"
        )

    def create(self, product: Product) -> None:
        start = time.time()
        if product.id in self.products:
            raise ValueError(f"Product with ID {product.id} already exists")
        self.products[product.id] = product
        self.logger.info("Product created", extra_data={
            "product_id": product.id, "duration_ms": int((time.time() - start) * 1000)
        })

    def find_by_id(self, id: str) -> Optional[Product]:
        return self.products.get(id)

    def find_all(self) -> List[Product]:
        return list(self.products.values())

    def find_by_criteria(
        self,
        filters: Optional[Specification] = None,
        sorts: Optional[List[Tuple[str, str]]] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> List[Product]:
        """
        Finds products using Specification + sort tuples + pagination.

        filters — a composed Specification (from FilterParser) or None
        sorts   — list of (field, direction) tuples e.g. [("price", "desc")]
        """
        start = time.time()

        results = list(self.products.values())

        # Apply specification filter
        if filters is not None:
            results = [p for p in results if filters.is_satisfied_by(p)]

        # Apply sorting — list of (field, direction) tuples
        if sorts:
            for field, direction in reversed(sorts):
                reverse = direction.lower() == "desc"
                try:
                    results = sorted(results, key=lambda p: getattr(p, field), reverse=reverse)
                except AttributeError:
                    pass

        # Pagination
        offset = (page - 1) * page_size
        results = results[offset: offset + page_size]

        duration_ms = int((time.time() - start) * 1000)
        self.logger.info("Products found by criteria", extra_data={
            "count": len(results), "duration_ms": duration_ms
        })
        return results

    def count(self, filters: Optional[Specification] = None) -> int:
        start = time.time()
        results = list(self.products.values())
        if filters is not None:
            results = [p for p in results if filters.is_satisfied_by(p)]
        count = len(results)
        self.logger.debug("Count query executed", extra_data={
            "count": count, "duration_ms": int((time.time() - start) * 1000)
        })
        return count

    def update(self, product: Product) -> None:
        if product.id not in self.products:
            raise ValueError("Product not found")
        product.updated_at = datetime.now()
        self.products[product.id] = product
        self.logger.info("Product updated", extra_data={"product_id": product.id})

    def delete(self, id: str) -> None:
        if id not in self.products:
            raise ValueError("Product not found")
        del self.products[id]
        self.logger.info("Product deleted", extra_data={"product_id": id})

    def exists_by_id(self, id: str) -> bool:
        return id in self.products
