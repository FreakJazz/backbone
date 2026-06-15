from dataclasses import dataclass
from typing import Optional

from backbone.errors import ErrorCodes
from backbone.application.exceptions import ValidationException

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
                error_code=ErrorCodes.IFC_INVALID_REQUEST_BODY,
                field="name",
            )
        if cmd.price <= 0:
            raise ValidationException(
                "price must be greater than 0",
                error_code=ErrorCodes.IFC_INVALID_REQUEST_BODY,
                field="price",
            )
        if not cmd.category:
            raise ValidationException(
                "category is required",
                error_code=ErrorCodes.IFC_INVALID_REQUEST_BODY,
                field="category",
            )

        product = Product(
            name=cmd.name.strip(),
            price=cmd.price,
            category=cmd.category,
            description=cmd.description,
        )
        saved = self._repo.save(product)
        return saved.id
