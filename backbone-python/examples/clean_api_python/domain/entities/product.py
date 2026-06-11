"""Product entity - Domain layer"""
from datetime import datetime
from uuid import uuid4
from typing import Optional


class ValidationError(Exception):
    """Domain validation error"""
    def __init__(self, field: str, message: str, code: int):
        self.field = field
        self.message = message
        self.code = code
        super().__init__(message)


class Product:
    """Product entity in the domain"""
    
    def __init__(
        self,
        name: str,
        description: str,
        category: str,
        price: float,
        stock: int,
        id: Optional[str] = None,
        active: bool = True,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id or str(uuid4())
        self.name = name
        self.description = description
        self.price = price
        self.category = category
        self.stock = stock
        self.active = active
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        
        self.validate()
    
    def validate(self) -> None:
        """Validates the product"""
        if not self.name or len(self.name) < 3:
            raise ValidationError(
                "name",
                "Product name must be at least 3 characters",
                11001001
            )
        
        if self.price <= 0:
            raise ValidationError(
                "price",
                "Product price must be greater than 0",
                11001002
            )
        
        if self.stock < 0:
            raise ValidationError(
                "stock",
                "Product stock cannot be negative",
                11001003
            )
        
        if not self.category:
            raise ValidationError(
                "category",
                "Product category is required",
                11001004
            )
    
    def update_stock(self, quantity: int) -> None:
        """Updates the stock quantity"""
        if quantity < 0:
            raise ValidationError(
                "stock",
                "Stock quantity cannot be negative",
                11001003
            )
        self.stock = quantity
        self.updated_at = datetime.now()
    
    def update_price(self, price: float) -> None:
        """Updates the price"""
        if price <= 0:
            raise ValidationError(
                "price",
                "Product price must be greater than 0",
                11001002
            )
        self.price = price
        self.updated_at = datetime.now()
    
    def deactivate(self) -> None:
        """Marks the product as inactive"""
        self.active = False
        self.updated_at = datetime.now()
    
    def activate(self) -> None:
        """Marks the product as active"""
        self.active = True
        self.updated_at = datetime.now()
    
    def is_in_stock(self) -> bool:
        """Checks if product is in stock"""
        return self.stock > 0
    
    def to_dict(self) -> dict:
        """Converts to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "category": self.category,
            "stock": self.stock,
            "active": self.active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
