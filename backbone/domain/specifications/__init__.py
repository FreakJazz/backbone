"""
Specification Pattern - Especificaciones para filtros dinámicos
"""
from .base_specification import (
    Specification, 
    CompositeSpecification,
    AndSpecification,
    OrSpecification,
    NotSpecification
)
from .filter_specification import (
    FilterSpecification,
    EqualSpecification,
    NotEqualSpecification,
    LessThanSpecification,
    LessThanOrEqualSpecification,
    GreaterThanSpecification,
    GreaterThanOrEqualSpecification,
    LikeSpecification,
    InSpecification,
    BetweenSpecification,
    IsNullSpecification,
    IsNotNullSpecification,
)
from .filter_parser import FilterParser
from .sort_specification import SortSpecification, SortDirection, MultipleSortSpecification

__all__ = [
    "Specification",
    "CompositeSpecification",
    "AndSpecification",
    "OrSpecification", 
    "NotSpecification",
    "FilterSpecification",
    "EqualSpecification",
    "NotEqualSpecification",
    "LessThanSpecification",
    "LessThanOrEqualSpecification",
    "GreaterThanSpecification", 
    "GreaterThanOrEqualSpecification",
    "LikeSpecification",
    "InSpecification",
    "BetweenSpecification",
    "IsNullSpecification",
    "IsNotNullSpecification",
    "FilterParser",
    "SortSpecification",
    "SortDirection",
    "MultipleSortSpecification",
]