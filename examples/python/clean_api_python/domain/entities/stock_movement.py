from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

MOVEMENT_TYPES = {"IN", "OUT", "ADJUSTMENT"}


@dataclass
class StockMovement:
    """Append-only audit record stored in MongoDB. Products (the mutable,
    consistency-critical side) live in PostgreSQL; the history of *why*
    stock changed lives here as an event log."""

    product_id: str
    type: str  # IN | OUT | ADJUSTMENT — metadata only, see delta
    quantity: int  # always positive; sign is implied by type
    delta: int  # signed change actually applied to stock
    reason: Optional[str] = None
    id: str = field(default_factory=lambda: uuid4().hex)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_doc(self) -> dict:
        return {
            "_id": self.id,
            "product_id": self.product_id,
            "type": self.type,
            "quantity": self.quantity,
            "delta": self.delta,
            "reason": self.reason,
            "created_at": self.created_at,
        }

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "type": self.type,
            "quantity": self.quantity,
            "delta": self.delta,
            "reason": self.reason,
            "created_at": self.created_at.isoformat(),
        }
