"""
Infrastructure layer exceptions - Códigos 12XXXXXX
"""
from .base_infrastructure_exception import InfrastructureException
from .infrastructure_exceptions import (
    DatabaseException,
    ExternalServiceException,
    ConfigurationException,
    CacheException,
    FileSystemException,
    InfrastructureErrorCodes,
)

__all__ = [
    "InfrastructureException",
    "DatabaseException",
    "ExternalServiceException", 
    "ConfigurationException",
    "CacheException",
    "FileSystemException",
    "InfrastructureErrorCodes",
]