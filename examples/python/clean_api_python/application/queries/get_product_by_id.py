from dataclasses import dataclass
from typing import Any, Dict

from backbone.application.exceptions import ResourceNotFoundException

from domain.repositories.product_repository import IProductRepository


@dataclass
class GetProductByIdQuery:
    product_id: str


class GetProductByIdQueryHandler:
    def __init__(self, repo: IProductRepository) -> None:
        self._repo = repo

    def handle(self, query: GetProductByIdQuery) -> Dict[str, Any]:
        product = self._repo.find_by_id(query.product_id)
        if not product:
            raise ResourceNotFoundException(
                "Product not found",
                resource_type="Product",
                resource_id=query.product_id,
            )
        return product.to_dict()
