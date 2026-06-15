from dataclasses import dataclass
from typing import Optional

from backbone.errors import ErrorCodes
from backbone.application.exceptions import ValidationException, ResourceNotFoundException

from domain.repositories.product_repository import IProductRepository


@dataclass
class UpdateProductCommand:
    product_id: str
    name: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None


class UpdateProductCommandHandler:
    def __init__(self, repo: IProductRepository) -> None:
        self._repo = repo

    def handle(self, cmd: UpdateProductCommand) -> str:
        product = self._repo.find_by_id(cmd.product_id)
        if not product:
            raise ResourceNotFoundException("Product", resource_id=cmd.product_id)

        if cmd.name is not None:
            if len(cmd.name.strip()) < 2:
                raise ValidationException(
                    "name must be at least 2 characters",
                    error_code=ErrorCodes.IFC_INVALID_REQUEST_BODY,
                    field="name",
                )
            product.name = cmd.name.strip()

        if cmd.price is not None:
            if cmd.price <= 0:
                raise ValidationException(
                    "price must be greater than 0",
                    error_code=ErrorCodes.IFC_INVALID_REQUEST_BODY,
                    field="price",
                )
            product.price = cmd.price

        if cmd.category is not None:
            product.category = cmd.category
        if cmd.description is not None:
            product.description = cmd.description

        self._repo.save(product)
        return product.id
