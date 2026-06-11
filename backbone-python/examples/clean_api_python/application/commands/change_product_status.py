"""ChangeProductStatus command + handler — Application / Commands"""
from dataclasses import dataclass
from typing import Dict, Any
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from backbone.infrastructure.logging import LoggerFactory
from examples.clean_api_python.domain.repositories.product_repository import ProductRepository


@dataclass
class ChangeProductStatusCommand:
    id: str
    active: bool


class ChangeProductStatusCommandHandler:

    def __init__(self, repository: ProductRepository):
        self.repository = repository
        self.logger = LoggerFactory.create_layer_logger(
            "product-api", "application", "ChangeProductStatusCommandHandler"
        )

    def handle(self, command: ChangeProductStatusCommand, context: Dict[str, Any]) -> None:
        self.logger.info("Handling ChangeProductStatusCommand", extra_data={
            "product_id": command.id, "active": command.active,
        })

        product = self.repository.find_by_id(command.id)
        if product is None:
            raise ValueError(f"Product {command.id} not found")

        if command.active:
            product.activate()
        else:
            product.deactivate()

        self.repository.update(product)
        self.logger.info("Product status changed", extra_data={
            "product_id": product.id, "active": product.active,
        })
