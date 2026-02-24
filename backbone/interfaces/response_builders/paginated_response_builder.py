"""
Paginated Response Builder - Constructor de respuestas paginadas
"""
from typing import Dict, Any, List, Optional
from math import ceil
from datetime import datetime
from uuid import uuid4


class PaginatedResponseBuilder:
    """
    Constructor para respuestas paginadas (GET con múltiples recursos).
    
    Contrato de respuesta lista paginada:
    {
        "status": "success",
        "status_code": 200,
        "message": "Items retrieved successfully",
        "data": {
            "items": [{}, {}],
            "pagination": {
                "total_count": 100,
                "page": 0,
                "page_size": 20,
                "total_pages": 5,
                "has_next": true,
                "has_previous": false
            }
        },
        "timestamp": "2024-01-01T12:00:00.000Z",
        "request_id": "uuid"
    }
    
    Sin dependencia de FastAPI - retorna dict puro.
    """
    
    @staticmethod
    def success(
        items: List[Dict[str, Any]],
        total_count: int,
        page: int,
        page_size: int,
        message: str = "Items retrieved successfully",
        status_code: int = 200,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Construye una respuesta paginada exitosa.
        
        Args:
            items: Lista de elementos
            total_count: Total de elementos disponibles  
            page: Página actual (0-indexed)
            page_size: Elementos por página
            message: Mensaje descriptivo
            status_code: Código de estado HTTP
            request_id: ID de la request (opcional)
            
        Returns:
            Dict con formato estándar de respuesta paginada
        """
        total_pages = ceil(total_count / page_size) if page_size > 0 else 0
        has_next = (page + 1) < total_pages
        has_previous = page > 0
        
        return {
            "status": "success",
            "status_code": status_code,
            "message": message,
            "data": {
                "items": items,
                "pagination": {
                    "total_count": total_count,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_previous": has_previous
                }
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id or str(uuid4())
        }
    
    @staticmethod
    def from_repository_result(
        items: List[Dict[str, Any]],
        total_count: int,
        page: int,
        page_size: int,
        resource_type: str = "Resources"
    ) -> Dict[str, Any]:
        """
        Factory method para resultados de repositorio.
        
        Args:
            items: Lista de elementos del repositorio
            total_count: Total de elementos
            page: Página actual
            page_size: Elementos por página
            resource_type: Tipo de recurso (para el mensaje)
            
        Returns:
            Dict con respuesta paginada
        """
        # Ensure plural form for message
        plural_resource = resource_type + "s" if not resource_type.endswith('s') else resource_type
        
        return PaginatedResponseBuilder.success(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            message=f"{plural_resource} retrieved successfully"
        )
    
    @staticmethod
    def empty(
        resource_type: str = "Resources",
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Construye una respuesta para lista vacía.
        
        Args:
            resource_type: Tipo de recurso
            message: Mensaje personalizado (opcional)
            
        Returns:
            Dict con respuesta paginada vacía
        """
        default_message = f"No {resource_type.lower()} found"
        final_message = message or default_message
        
        return PaginatedResponseBuilder.success(
            items=[],
            total_count=0,
            page=0,
            page_size=0,
            message=final_message
        )

    
    @staticmethod
    def extended(
        data: List[Dict[str, Any]],
        page: int,
        page_size: int,
        total: int,
        resource_type: str = "Recursos"
    ) -> Dict[str, Any]:
        """
        Respuesta paginada con información extendida de navegación.
        
        Args:
            data: Lista de elementos
            page: Página actual
            page_size: Elementos por página
            total: Total de elementos
            resource_type: Tipo de recurso
            
        Returns:
            Dict con respuesta paginada extendida
        """
        response = PaginatedResponseBuilder.from_repository_result(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            resource_type=resource_type
        )
        
        # Reemplazar paginación básica con extendida
        response["body"]["pagination"] = PaginatedResponseBuilder.calculate_pagination_info(
            page=page,
            page_size=page_size,
            total=total
        )
        
        return response