"""
Infrastructure Persistence Adapters - Package initialization
"""

# Importación condicional de adaptadores
try:
    from .sqlalchemy_adapter import (
        SQLAlchemyRepository,
        SQLAlchemyUnitOfWork,
        SQLAlchemySpecificationTranslator
    )
    _sqlalchemy_available = True
except ImportError:
    _sqlalchemy_available = False

try:
    from .mongodb_adapter import (
        MongoDBRepository,
        MongoDBUnitOfWork,
        MongoDBSpecificationTranslator
    )
    _mongodb_available = True
except ImportError:
    _mongodb_available = False

# Exportar solo los adaptadores disponibles
__all__ = []

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

# Funciones de utilidad para verificar disponibilidad
def is_sqlalchemy_available() -> bool:
    """Verifica si SQLAlchemy está disponible."""
    return _sqlalchemy_available

def is_mongodb_available() -> bool:
    """Verifica si MongoDB (pymongo/motor) está disponible."""
    return _mongodb_available

def get_available_adapters() -> list[str]:
    """Retorna lista de adaptadores disponibles."""
    adapters = []
    if _sqlalchemy_available:
        adapters.append("sqlalchemy")
    if _mongodb_available:
        adapters.append("mongodb")
    return adapters