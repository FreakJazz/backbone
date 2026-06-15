from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4


@dataclass
class Product:
    name: str
    price: float
    category: str
    status: str = "active"
    description: Optional[str] = None
    id: str = field(default_factory=lambda: uuid4().hex)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "category": self.category,
            "status": self.status,
            "description": self.description,
        }
