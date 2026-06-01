"""Create product use case - Application layer"""
from dataclasses import dataclass
from typing import Dict, Any
import sys
import os

# Add backbone to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from backbone.application.exceptions import ValidationException
from backbone.infrastructure.logging import LoggerFactory, LogLevel
from examples.clean_api_python.domain.entities.product import Product, ValidationError
from examples.clean_api_python.domain.repositories.product_repository import ProductRepository
import time


@dataclass
class CreateProductInput:
    """Input for creating a product"""
    name: str
    description: str
    price: float
    category: str
    stock: int


@dataclass
class CreateProductOutput:
    """Output of product creation"""
    product: Product


class CreateProductUseCase:
    """Handles product creation"""
    
    def __init__(self, repository: ProductRepository):
        self.repository = repository
        self.logger = LoggerFactory.create_layer_logger(
            "product-api",
            "application",
            "CreateProductUseCase"
        )
    
    def execute(self, input: CreateProductInput, context: Dict[str, Any]) -> CreateProductOutput:
        """Executes the use case"""
        self.logger.log(
            LogLevel.INFO,
            "Creating product",
            extra_data={
                "name": input.name,
                "category": input.category,
                "price": input.price
            },
            context=context
        )
        
        # Validar input
        self._validate_input(input)
        
        # Crear entidad de dominio
        try:
            product = Product(
                name=input.name,
                description=input.description,
                category=input.category,
                price=input.price,
                stock=input.stock
            )
        except ValidationError as e:
            self.logger.log(
                LogLevel.ERROR,
                "Domain validation failed",
                extra_data={
                    "error": str(e),
                    "field": e.field,
                    "code": e.code
                },
                context=context
            )
            raise ValidationException(
                "Product validation failed",
                [{"field": e.field, "message": e.message}]
            )
        
        # Guardar en repositorio
        start = time.time()
        try:
            self.repository.create(product)
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            self.logger.log(
                LogLevel.ERROR,
                "Failed to save product",
                extra_data={
                    "error": str(e),
                    "duration_ms": duration_ms,
                    "error_code": 10001003
                },
                context=context
            )
            raise Exception(f"Failed to create product: {str(e)}")
        
        duration_ms = int((time.time() - start) * 1000)
        self.logger.log(
            LogLevel.INFO,
            "Product created successfully",
            extra_data={
                "product_id": product.id,
                "duration_ms": duration_ms
            },
            context=context
        )
        
        return CreateProductOutput(product=product)
    
    def _validate_input(self, input: CreateProductInput) -> None:
        """Validates input"""
        if not input.name:
            raise ValueError("name is required")
        if not input.category:
            raise ValueError("category is required")
        if input.price <= 0:
            raise ValueError("price must be greater than 0")
        if input.stock < 0:
            raise ValueError("stock cannot be negative")
