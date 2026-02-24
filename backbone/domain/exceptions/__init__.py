"""
Domain layer exceptions - Códigos 11XXXXXX
"""
from .base_kernel_exception import BaseKernelException
from .domain_exceptions import (
    DomainException,
    BusinessRuleViolationException,
    InvalidEntityStateException,
    InvalidValueObjectException,
)

__all__ = [
    "BaseKernelException",
    "DomainException", 
    "BusinessRuleViolationException",
    "InvalidEntityStateException",
    "InvalidValueObjectException",
]