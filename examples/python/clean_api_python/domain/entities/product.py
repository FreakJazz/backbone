from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4


@dataclass
class Product:
    """Lives in PostgreSQL. `stock` is the single source of truth for
    availability — Sale and StockMovement (both in Mongo) only ever move it
    through IProductRepository.adjust_stock, never by writing it directly."""

    name: str
    price: float
    category: str
    status: str = "active"
    description: Optional[str] = None
    stock: int = 0
    id: str = field(default_factory=lambda: uuid4().hex)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "category": self.category,
            "status": self.status,
            "description": self.description,
            "stock": self.stock,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
