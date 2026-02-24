"""
Domain Repositories - Contratos de repositorio (puertos)
"""
from .base_repository import IRepository, IReadOnlyRepository
from .unit_of_work import IUnitOfWork
from .query_builder import QueryBuilder

__all__ = [
    "IRepository",
    "IReadOnlyRepository", 
    "IUnitOfWork",
    "QueryBuilder",
]