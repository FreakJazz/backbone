from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class Sale:
    """Append-only record stored in MongoDB, one per completed sale.
    unit_price is a snapshot taken at sale time — never recomputed from the
    current Product.price, since that would silently rewrite history
    whenever the catalog price changes later."""

    product_id: str
    quantity: int
    unit_price: float
    id: str = field(default_factory=lambda: uuid4().hex)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def total_amount(self) -> float:
        return self.unit_price * self.quantity

    def to_doc(self) -> dict:
        return {
            "_id": self.id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_amount": self.total_amount,
            "created_at": self.created_at,
        }

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_amount": self.total_amount,
            "created_at": self.created_at.isoformat(),
        }
