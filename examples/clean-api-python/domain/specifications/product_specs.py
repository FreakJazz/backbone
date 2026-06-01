"""Product specifications - Domain layer"""
import sys
import os

# Add backbone to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from backbone.domain.specifications import FilterSpecification


def product_is_active() -> FilterSpecification:
    """Checks if a product is active"""
    return FilterSpecification("active", "=", True)


def product_in_category(category: str) -> FilterSpecification:
    """Checks if a product is in a specific category"""
    return FilterSpecification("category", "=", category)


def product_price_range(min_price: float, max_price: float) -> FilterSpecification:
    """Checks if product price is in range"""
    return FilterSpecification("price", ">=", min_price) & FilterSpecification("price", "<=", max_price)


def product_in_stock() -> FilterSpecification:
    """Checks if product is in stock"""
    return FilterSpecification("stock", ">", 0)


def product_by_name_pattern(pattern: str) -> FilterSpecification:
    """Searches products by name pattern"""
    return FilterSpecification("name", "LIKE", f"%{pattern}%")
