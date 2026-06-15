from dataclasses import dataclass
from typing import Optional

from backbone.errors import ErrorCodes
from backbone.application.exceptions import ValidationException, ResourceConflictException

from domain.entities.product import Product
from domain.repositories.product_repository import IProductRepository


@dataclass
class CreateProductCommand:
    name: str
    price: float
    category: str
    description: Optional[str] = None


class CreateProductCommandHandler:
    def __init__(self, repo: IProductRepository) -> None:
        self._repo = repo

    def handle(self, cmd: CreateProductCommand) -> str:
        if not cmd.name or len(cmd.name.strip()) < 2:
            raise ValidationException(
                "name must be at least 2 characters",
                code=ErrorCodes.APP_VALIDATION_FAILURE,
            )
        if cmd.price <= 0:
            raise ValidationException(
                "price must be greater than 0",
                code=ErrorCodes.APP_VALIDATION_FAILURE,
            )
        if not cmd.category:
            raise ValidationException(
                "category is required",
                code=ErrorCodes.APP_VALIDATION_FAILURE,
            )

        existing = self._repo.find_by_name(cmd.name)
        if existing:
            raise ResourceConflictException(
                "a product with that name already exists",
                resource_type="Product",
                conflict_field="name",
                conflict_value=cmd.name.strip(),
                code=ErrorCodes.APP_CONFLICT,
            )

        product = Product(
            name=cmd.name.strip(),
            price=cmd.price,
            category=cmd.category,
            description=cmd.description,
        )
        saved = self._repo.save(product)
        return saved.id
