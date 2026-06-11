"""
Process Response Builder - Constructor de respuestas de escritura (CREATE / UPDATE / DELETE)
"""
from typing import Dict, Any, Optional


class ProcessResponseBuilder:
    """
    Constructor para operaciones de escritura.

    Contrato create/update: retorna solo el id.
    {"id": "uuid"}

    Contrato delete: retorna solo el id eliminado.
    {"id": "uuid"}

    Sin dependencia de FastAPI - retorna dict puro.
    """

    @staticmethod
    def created(entity_id: str) -> Dict[str, Any]:
        return {"id": entity_id}

    @staticmethod
    def updated(entity_id: str) -> Dict[str, Any]:
        return {"id": entity_id}

    @staticmethod
    def deleted(entity_id: str) -> Dict[str, Any]:
        return {"id": entity_id}

    @staticmethod
    def success(entity_id: Optional[str] = None) -> Dict[str, Any]:
        """Alias genérico para operaciones de escritura que devuelven un id."""
        if entity_id:
            return {"id": entity_id}
        return {}
