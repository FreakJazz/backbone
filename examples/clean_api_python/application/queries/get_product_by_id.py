"""GetProductByID query + handler — Application / Queries"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from backbone.infrastructure.logging import LoggerFactory
from examples.clean_api_python.domain.entities.product import Product
from examples.clean_api_python.domain.repositories.product_repository import ProductRepository


@dataclass
class GetProductByIDQuery:
    id: str


@dataclass
class GetProductByIDResult:
    product: Product


class GetProductByIDQueryHandler:

    def __init__(self, repository: ProductRepository):
        self.repository = repository
        self.logger = LoggerFactory.create_layer_logger(
            "product-api", "application", "GetProductByIDQueryHandler"
        )

    def handle(self, query: GetProductByIDQuery, context: Dict[str, Any]) -> Optional[GetProductByIDResult]:
        self.logger.info("Handling GetProductByIDQuery", extra_data={"product_id": query.id})

        if not query.id:
            raise ValueError("product ID is required")

        product = self.repository.find_by_id(query.id)
        if product is None:
            self.logger.warning("Product not found", extra_data={"product_id": query.id})
            return None

        self.logger.info("Product found", extra_data={"product_id": product.id})
        return GetProductByIDResult(product=product)
