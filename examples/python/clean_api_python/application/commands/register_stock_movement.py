from dataclasses import dataclass
from typing import Optional

from backbone.errors import ErrorCodes
from backbone.application.exceptions import ValidationException, ResourceNotFoundException, ResourceConflictException

from domain.entities.stock_movement import StockMovement
from domain.repositories.product_repository import IProductRepository, InsufficientStockError
from domain.repositories.stock_movement_repository import IStockMovementRepository


@dataclass
class RegisterStockMovementCommand:
    product_id: str
    type: str  # IN | OUT | ADJUSTMENT
    quantity: int  # IN/OUT: must be > 0. ADJUSTMENT: signed delta, may be negative.
    reason: Optional[str] = None


class RegisterStockMovementCommandHandler:
    def __init__(self, products: IProductRepository, movements: IStockMovementRepository) -> None:
        self._products = products
        self._movements = movements

    def handle(self, cmd: RegisterStockMovementCommand) -> str:
        if cmd.type == "IN":
            if cmd.quantity <= 0:
                raise ValidationException(
                    "quantity must be greater than 0 for IN movements",
                    code=ErrorCodes.APP_VALIDATION_FAILURE,
                )
            delta, quantity = cmd.quantity, cmd.quantity
        elif cmd.type == "OUT":
            if cmd.quantity <= 0:
                raise ValidationException(
                    "quantity must be greater than 0 for OUT movements",
                    code=ErrorCodes.APP_VALIDATION_FAILURE,
                )
            delta, quantity = -cmd.quantity, cmd.quantity
        elif cmd.type == "ADJUSTMENT":
            if cmd.quantity == 0:
                raise ValidationException(
                    "quantity must be non-zero for ADJUSTMENT movements",
                    code=ErrorCodes.APP_VALIDATION_FAILURE,
                )
            delta, quantity = cmd.quantity, abs(cmd.quantity)
        else:
            raise ValidationException(
                "type must be one of: IN, OUT, ADJUSTMENT",
                code=ErrorCodes.APP_VALIDATION_FAILURE,
            )

        if not self._products.exists(cmd.product_id):
            raise ResourceNotFoundException(
                "Product not found", resource_type="Product", resource_id=cmd.product_id,
            )

        try:
            self._products.adjust_stock(cmd.product_id, delta)
        except InsufficientStockError:
            raise ResourceConflictException(
                "movement would take stock below zero",
                resource_type="Product",
                conflict_field="stock",
                conflict_value=str(cmd.quantity),
                code=ErrorCodes.APP_CONFLICT,
            )

        movement = StockMovement(
            product_id=cmd.product_id, type=cmd.type, quantity=quantity, delta=delta, reason=cmd.reason,
        )
        saved = self._movements.save(movement)
        return saved.id
