"""
Simple Object Response Builder - Constructor de respuestas de objeto único
"""
from typing import Dict, Any


class SimpleObjectResponseBuilder:
    """
    Constructor para respuestas GET de un solo recurso.

    Contrato: retorna el objeto directamente, sin envelope.
    {
        "id": "uuid",
        "name": "...",
        ...
    }

    Sin dependencia de FastAPI - retorna dict puro.
    """

    @staticmethod
    def success(data: Dict[str, Any]) -> Dict[str, Any]:
        return data

    @staticmethod
    def found(data: Dict[str, Any]) -> Dict[str, Any]:
        return data

    @staticmethod
    def retrieved(data: Dict[str, Any]) -> Dict[str, Any]:
        return data
