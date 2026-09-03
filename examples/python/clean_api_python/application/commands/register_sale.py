from dataclasses import dataclass

from backbone.errors import ErrorCodes
from backbone.application.exceptions import ValidationException, ResourceNotFoundException, ResourceConflictException
from backbone.infrastructure.exceptions import DatabaseException
from backbone.infrastructure.logging import LoggerFactory

from domain.entities.sale import Sale
from domain.repositories.product_repository import IProductRepository, InsufficientStockError
from domain.repositories.sale_repository import ISaleRepository


@dataclass
class RegisterSaleCommand:
    product_id: str
    quantity: int


class RegisterSaleCommandHandler:
    """Coordinates two independent stores for one business action: PostgreSQL
    owns the authoritative stock count, MongoDB owns the append-only sales
    log. There is no distributed transaction here — stock is decremented
    first (the step that can legitimately fail, e.g. insufficient stock) and
    the sale is recorded only after that succeeds. If the Mongo insert
    itself fails, stock has already moved and this raises without rolling
    it back; a production system would reconcile that gap with an
    outbox/saga instead of a bare two-step call."""

    def __init__(self, products: IProductRepository, sales: ISaleRepository) -> None:
        self._products = products
        self._sales = sales
        self._logger = LoggerFactory.create_for_layer(
            service_name="clean-api-python", layer="application", component="RegisterSaleCommandHandler",
        )

    def handle(self, cmd: RegisterSaleCommand) -> str:
        if cmd.quantity <= 0:
            raise ValidationException(
                "quantity must be greater than 0",
                code=ErrorCodes.APP_VALIDATION_FAILURE,
            )

        product = self._products.find_by_id(cmd.product_id)
        if not product:
            self._logger.warning("Product not found", context={"id": cmd.product_id})
            raise ResourceNotFoundException(
                "Product not found", resource_type="Product", resource_id=cmd.product_id,
            )

        try:
            self._products.adjust_stock(cmd.product_id, -cmd.quantity)
        except InsufficientStockError:
            self._logger.warning(
                "Insufficient stock for sale",
                context={"product_id": cmd.product_id, "quantity": cmd.quantity},
            )
            raise ResourceConflictException(
                "insufficient stock for this sale",
                resource_type="Product",
                conflict_field="stock",
                conflict_value=str(cmd.quantity),
                code=ErrorCodes.APP_CONFLICT,
            )

        sale = Sale(product_id=cmd.product_id, quantity=cmd.quantity, unit_price=product.price)
        try:
            saved = self._sales.save(sale)
        except Exception as exc:
            # Stock was already decremented in Postgres — flagged here rather
            # than silently propagated, since this is exactly the
            # inconsistency window a saga/outbox pattern exists to close.
            db_exc = DatabaseException(
                "Sale record failed after stock was decremented - data inconsistency",
                operation="save_sale",
                table="sales",
                original_error=str(exc),
            )
            self._logger.log_kernel_exception(db_exc)
            raise db_exc from exc

        self._logger.info(
            "Sale registered",
            context={"sale_id": saved.id, "product_id": cmd.product_id, "quantity": cmd.quantity},
        )
        return saved.id
