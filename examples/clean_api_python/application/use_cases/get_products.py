"""Get products use case - Application layer"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import sys
import os

# Add backbone to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from backbone.domain.specifications import FilterSpecification, SortSpecification
from backbone.infrastructure.logging import LoggerFactory, LogLevel
from examples.clean_api_python.domain.entities.product import Product
from examples.clean_api_python.domain.repositories.product_repository import ProductRepository
from examples.clean_api_python.domain.specifications import product_specs
import time


@dataclass
class GetProductsInput:
    """Input for getting products with filters"""
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    in_stock: bool = False
    active: bool = True
    name_pattern: Optional[str] = None
    page: int = 1
    page_size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"


@dataclass
class GetProductsOutput:
    """Output of getting products"""
    products: List[Product]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class GetProductsUseCase:
    """Handles getting products with filters"""
    
    def __init__(self, repository: ProductRepository):
        self.repository = repository
        self.logger = LoggerFactory.create_layer_logger(
            "product-api",
            "application",
            "GetProductsUseCase"
        )
    
    def execute(self, input: GetProductsInput, context: Dict[str, Any]) -> GetProductsOutput:
        """Executes the use case with Specification Pattern"""
        self.logger.info(
            "Getting products with filters",
            extra_data={
                "category": input.category,
                "min_price": input.min_price,
                "max_price": input.max_price,
                "in_stock": input.in_stock,
                "page": input.page,
                "page_size": input.page_size
            }
        )
        
        # Construir filtros con Specification Pattern
        start = time.time()
        filters = self._build_filters(input)
        sorts = self._build_sorts(input)
        
        self.logger.debug(
            "Query criteria built",
            extra_data={
                "filters_applied": self._get_applied_filters(input),
                "filters_count": len(filters)
            }
        )
        
        # Obtener total count
        total_count = self.repository.count(filters)
        
        # Obtener productos
        try:
            products = self.repository.find_by_criteria(
                filters=filters,
                sorts=sorts,
                page=input.page,
                page_size=input.page_size
            )
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            self.logger.error(
                "Failed to get products",
                extra_data={
                    "error": str(e),
                    "duration_ms": duration_ms,
                    "error_code": 10002002
                }
            )
            raise Exception(f"Failed to get products: {str(e)}")
        
        duration_ms = int((time.time() - start) * 1000)
        
        # Calcular paginación
        total_pages = (total_count + input.page_size - 1) // input.page_size
        
        output = GetProductsOutput(
            products=products,
            total_count=total_count,
            page=input.page,
            page_size=input.page_size,
            total_pages=total_pages,
            has_next=input.page < total_pages,
            has_previous=input.page > 1
        )
        
        self.logger.info(
            "Products retrieved successfully",
            extra_data={
                "count": len(products),
                "total_count": total_count,
                "duration_ms": duration_ms
            }
        )
        
        return output
    
    def _build_filters(self, input: GetProductsInput) -> List[FilterSpecification]:
        """Builds filters with Specification Pattern"""
        filters = []
        
        # Filtro de activo por defecto
        if input.active:
            filters.append(product_specs.product_is_active())
        
        # Filtro por categoría
        if input.category:
            filters.append(product_specs.product_in_category(input.category))
        
        # Filtro por rango de precio
        if input.min_price and input.max_price:
            filters.append(product_specs.product_price_range(input.min_price, input.max_price))
        elif input.min_price:
            filters.append(FilterSpecification("price", ">=", input.min_price))
        elif input.max_price:
            filters.append(FilterSpecification("price", "<=", input.max_price))
        
        # Filtro por stock
        if input.in_stock:
            filters.append(product_specs.product_in_stock())
        
        # Filtro por nombre (pattern)
        if input.name_pattern:
            filters.append(product_specs.product_by_name_pattern(input.name_pattern))
        
        return filters
    
    def _build_sorts(self, input: GetProductsInput) -> List[SortSpecification]:
        """Builds sorting"""
        return [SortSpecification(input.sort_by, input.sort_order)]
    
    def _get_applied_filters(self, input: GetProductsInput) -> List[str]:
        """Returns applied filters for logging"""
        filters = []
        if input.category:
            filters.append("category")
        if input.min_price or input.max_price:
            filters.append("price_range")
        if input.in_stock:
            filters.append("in_stock")
        if input.name_pattern:
            filters.append("name_pattern")
        return filters
