"""
Simple Object Response Builder - Constructor de respuestas de objetos simples
"""
from typing import Dict, Any, Optional, Union, List
from datetime import datetime
from uuid import uuid4


class SimpleObjectResponseBuilder:
    """
    Constructor para respuestas de objetos simples (GET single resource).
    
    Contrato de éxito:
    {
        "status": "success",
        "status_code": 200,
        "message": "Entity found",
        "data": {
            "id": "uuid",
            "name": "...",
            "email": "..."
        },
        "timestamp": "2024-01-01T12:00:00.000Z",
        "request_id": "uuid"
    }
    
    Sin dependencia de FastAPI - retorna dict puro.
    """
    
    @staticmethod
    def success(
        data: Dict[str, Any],
        message: str = "Consulta exitosa",
        status_code: int = 200,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Construye una respuesta exitosa con objeto simple.
        
        Args:
            data: Objeto/entidad a retornar
            message: Mensaje descriptivo
            status_code: Código de estado HTTP (200 por defecto)
            request_id: ID de la request (opcional)
            
        Returns:
            Dict con formato estándar de respuesta de objeto
        """
        return {
            "status": "success",
            "status_code": status_code,
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id or str(uuid4())
        }
    
    @staticmethod
    def found(data: Dict[str, Any], resource_type: str = "Recurso") -> Dict[str, Any]:
        """
        Shortcut para recurso encontrado.
        
        Args:
            data: Objeto encontrado
            resource_type: Tipo de recurso (para el mensaje)
            
        Returns:
            Dict con respuesta estándar de recurso encontrado
        """
        return SimpleObjectResponseBuilder.success(
            data=data,
            message=f"{resource_type} found",
            status_code=200
        )
    
    @staticmethod
    def retrieved(data: Dict[str, Any], resource_type: str = "Recurso") -> Dict[str, Any]:
        """
        Shortcut para recurso obtenido/recuperado.
        
        Args:
            data: Objeto obtenido
            resource_type: Tipo de recurso (para el mensaje)
            
        Returns:
            Dict con respuesta estándar de recurso obtenido
        """
        return SimpleObjectResponseBuilder.success(
            data=data,
            message=f"{resource_type} retrieved successfully",
            status_code=200
        )
    
    @staticmethod
    def details(data: Dict[str, Any], resource_type: str = "Recurso") -> Dict[str, Any]:
        """
        Shortcut para detalles de recurso.
        
        Args:
            data: Detalles del recurso
            resource_type: Tipo de recurso (para el mensaje)
            
        Returns:
            Dict con respuesta estándar de detalles
        """
        return SimpleObjectResponseBuilder.success(
            data=data,
            message=f"{resource_type} details",
            status_code=200
        )
    
    @staticmethod
    def status(
        data: Dict[str, Any], 
        message: str = "Status retrieved"
    ) -> Dict[str, Any]:
        """
        Shortcut para verificaciones de estado.
        
        Args:
            data: Estado del servicio/recurso
            message: Mensaje personalizado
            
        Returns:
            Dict con respuesta estándar de estado
        """
        return SimpleObjectResponseBuilder.success(
            data=data,
            message=message,
            status_code=200
        )