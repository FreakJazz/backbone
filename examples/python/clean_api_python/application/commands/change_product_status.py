from dataclasses import dataclass

from backbone.errors import ErrorCodes
from backbone.application.exceptions import ValidationException, ResourceNotFoundException
from backbone.infrastructure.logging import LoggerFactory

from domain.repositories.product_repository import IProductRepository

VALID_STATUSES = {"active", "inactive", "discontinued"}


@dataclass
class ChangeProductStatusCommand:
    product_id: str
    status: str


class ChangeProductStatusCommandHandler:
    def __init__(self, repo: IProductRepository) -> None:
        self._repo = repo
        self._logger = LoggerFactory.create_for_layer(
            service_name="clean-api-python", layer="application", component="ChangeProductStatusCommandHandler",
        )

    def handle(self, cmd: ChangeProductStatusCommand) -> str:
        if cmd.status not in VALID_STATUSES:
            raise ValidationException(
                f"status must be one of: {', '.join(sorted(VALID_STATUSES))}",
                code=ErrorCodes.APP_VALIDATION_FAILURE,
            )
        product = self._repo.find_by_id(cmd.product_id)
        if not product:
            self._logger.warning("Product not found", context={"id": cmd.product_id})
            raise ResourceNotFoundException(
                "Product not found",
                resource_type="Product",
                resource_id=cmd.product_id,
            )
        product.status = cmd.status
        self._repo.save(product)
        self._logger.info("Product status changed", context={"id": product.id, "status": cmd.status})
        return product.id
