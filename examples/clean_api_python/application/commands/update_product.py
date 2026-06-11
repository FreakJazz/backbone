"""UpdateProduct command + handler — Application / Commands"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from backbone.infrastructure.logging import LoggerFactory
from examples.clean_api_python.domain.entities.product import ValidationError
from examples.clean_api_python.domain.repositories.product_repository import ProductRepository


@dataclass
class UpdateProductCommand:
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    stock: Optional[int] = None


@dataclass
class UpdateProductResult:
    product_id: str


class UpdateProductCommandHandler:

    def __init__(self, repository: ProductRepository):
        self.repository = repository
        self.logger = LoggerFactory.create_layer_logger(
            "product-api", "application", "UpdateProductCommandHandler"
        )

    def handle(self, command: UpdateProductCommand, context: Dict[str, Any]) -> UpdateProductResult:
        self.logger.info("Handling UpdateProductCommand", extra_data={"product_id": command.id})

        product = self.repository.find_by_id(command.id)
        if product is None:
            raise ValueError(f"Product {command.id} not found")

        if command.name is not None:
            product.name = command.name
        if command.description is not None:
            product.description = command.description
        if command.category is not None:
            product.category = command.category
        if command.price is not None:
            try:
                product.update_price(command.price)
            except ValidationError as e:
                raise ValueError(e.message)
        if command.stock is not None:
            try:
                product.update_stock(command.stock)
            except ValidationError as e:
                raise ValueError(e.message)

        try:
            product.validate()
        except ValidationError as e:
            raise ValueError(e.message)

        self.repository.update(product)
        self.logger.info("Product updated", extra_data={"product_id": product.id})

        return UpdateProductResult(product_id=product.id)
