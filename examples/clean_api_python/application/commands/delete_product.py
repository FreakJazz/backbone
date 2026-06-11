"""DeleteProduct command + handler — Application / Commands"""
from dataclasses import dataclass
from typing import Dict, Any
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from backbone.infrastructure.logging import LoggerFactory
from examples.clean_api_python.domain.repositories.product_repository import ProductRepository


@dataclass
class DeleteProductCommand:
    id: str


class DeleteProductCommandHandler:

    def __init__(self, repository: ProductRepository):
        self.repository = repository
        self.logger = LoggerFactory.create_layer_logger(
            "product-api", "application", "DeleteProductCommandHandler"
        )

    def handle(self, command: DeleteProductCommand, context: Dict[str, Any]) -> None:
        self.logger.info("Handling DeleteProductCommand", extra_data={"product_id": command.id})

        if not self.repository.exists_by_id(command.id):
            raise ValueError(f"Product {command.id} not found")

        self.repository.delete(command.id)
        self.logger.info("Product deleted", extra_data={"product_id": command.id})
