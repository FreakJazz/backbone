"""CreateProduct command + handler — Application / Commands"""
from dataclasses import dataclass
from typing import Dict, Any
import sys, os, time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from backbone.application.exceptions import ValidationException
from backbone.infrastructure.logging import LoggerFactory
from examples.clean_api_python.domain.entities.product import Product, ValidationError
from examples.clean_api_python.domain.repositories.product_repository import ProductRepository


@dataclass
class CreateProductCommand:
    name: str
    description: str
    price: float
    category: str
    stock: int


@dataclass
class CreateProductResult:
    product_id: str


class CreateProductCommandHandler:

    def __init__(self, repository: ProductRepository):
        self.repository = repository
        self.logger = LoggerFactory.create_layer_logger(
            "product-api", "application", "CreateProductCommandHandler"
        )

    def handle(self, command: CreateProductCommand, context: Dict[str, Any]) -> CreateProductResult:
        self.logger.info("Handling CreateProductCommand", extra_data={
            "name": command.name, "category": command.category, "price": command.price,
        })

        self._validate(command)

        try:
            product = Product(
                name=command.name,
                description=command.description,
                category=command.category,
                price=command.price,
                stock=command.stock,
            )
        except ValidationError as e:
            raise ValidationException("Product validation failed", [{"field": e.field, "message": e.message}])

        start = time.time()
        self.repository.create(product)
        self.logger.info("Product created", extra_data={
            "product_id": product.id, "duration_ms": int((time.time() - start) * 1000),
        })

        return CreateProductResult(product_id=product.id)

    def _validate(self, command: CreateProductCommand) -> None:
        if not command.name:
            raise ValueError("name is required")
        if not command.category:
            raise ValueError("category is required")
        if command.price <= 0:
            raise ValueError("price must be greater than 0")
        if command.stock < 0:
            raise ValueError("stock cannot be negative")
