from dataclasses import dataclass
from typing import Any, Dict

from backbone.application.exceptions import ResourceNotFoundException
from backbone.infrastructure.logging import LoggerFactory

from domain.repositories.product_repository import IProductRepository


@dataclass
class GetProductByIdQuery:
    product_id: str


class GetProductByIdQueryHandler:
    def __init__(self, repo: IProductRepository) -> None:
        self._repo = repo
        self._logger = LoggerFactory.create_for_layer(
            service_name="clean-api-python", layer="application", component="GetProductByIdQueryHandler",
        )

    def handle(self, query: GetProductByIdQuery) -> Dict[str, Any]:
        product = self._repo.find_by_id(query.product_id)
        if not product:
            self._logger.warning("Product not found", context={"id": query.product_id})
            raise ResourceNotFoundException(
                "Product not found",
                resource_type="Product",
                resource_id=query.product_id,
            )
        self._logger.info("Product found", context={"id": product.id})
        return product.to_dict()
