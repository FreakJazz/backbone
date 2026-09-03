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

    def __post_init__(self) -> None:
        # The `description` column is NOT NULL DEFAULT '' (see
        # infrastructure/database/postgres.py) — backbone-go's equivalent
        # field is a plain (non-pointer) string, so "no description" is
        # already "" there by Go's own zero-value rules and this case never
        # arises. Python's Optional[str] has no such built-in zero value, so
        # "no description" (None, e.g. an omitted JSON field in
        # CreateProductCommand) must be normalized here — otherwise the
        # INSERT in PostgresProductRepository.save() fails with a
        # NotNullViolation for the most ordinary "just don't send one" case.
        if self.description is None:
            self.description = ""

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
