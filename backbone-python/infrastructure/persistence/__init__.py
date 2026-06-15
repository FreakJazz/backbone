"""
Infrastructure Persistence Layer
"""

# Repositorio base y UnitOfWork
from ...domain.repositories.base_repository import IRepository, BaseRepository
from ...domain.repositories.unit_of_work import IUnitOfWork, BaseUnitOfWork

# Adaptadores - importación condicional desde el paquete adapters
try:
    from .adapters import (
        SQLAlchemyRepository,
        SQLAlchemyUnitOfWork,
        SQLAlchemySpecificationTranslator,
        is_sqlalchemy_available
    )
    _sqlalchemy_available = is_sqlalchemy_available()
except ImportError:
    _sqlalchemy_available = False

try:
    from .adapters import (
        MongoDBRepository,
        MongoDBUnitOfWork,
        MongoDBSpecificationTranslator,
        is_mongodb_available
    )
    _mongodb_available = is_mongodb_available()
except ImportError:
    _mongodb_available = False

# Exportar contratos base siempre
__all__ = [
    "IRepository",
    "BaseRepository", 
    "IUnitOfWork",
    "BaseUnitOfWork"
]

# Exportar adaptadores solo si están disponibles
if _sqlalchemy_available:
    __all__.extend([
        "SQLAlchemyRepository",
        "SQLAlchemyUnitOfWork",
        "SQLAlchemySpecificationTranslator"
    ])

if _mongodb_available:
    __all__.extend([
        "MongoDBRepository", 
        "MongoDBUnitOfWork",
        "MongoDBSpecificationTranslator"
    ])

# Funciones de utilidad
def is_sqlalchemy_adapter_available() -> bool:
    """Verifica si el adaptador SQLAlchemy está disponible."""
    return _sqlalchemy_available

def is_mongodb_adapter_available() -> bool:
    """Verifica si el adaptador MongoDB está disponible."""
    return _mongodb_available

def get_available_adapters() -> list[str]:
    """Retorna lista de adaptadores disponibles."""
    adapters = []
    if _sqlalchemy_available:
        adapters.append("sqlalchemy")
    if _mongodb_available:
        adapters.append("mongodb") 
    return adapters