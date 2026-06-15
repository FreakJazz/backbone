"""
Paginated Response Builder - Constructor de respuestas paginadas
"""
from typing import Dict, Any, List, Optional


class PaginatedResponseBuilder:
    """
    Constructor para respuestas paginadas (GET lista de recursos).

    Contrato:
    {
        "meta": {
            "status": "success",
            "status_code": 200,
            "message": "Items retrieved successfully"
        },
        "items": [{}, {}],
        "pagination": {
            "total_count": 100,
            "page": 0,
            "page_size": 10,
            "total_pages": 10
        }
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
    ) -> Dict[str, Any]:
        return {
            "meta": {
                "status": "success",
                "status_code": status_code,
                "message": message,
            },
            "items": items,
            "pagination": {
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
            },
        }

    @staticmethod
    def from_repository_result(
        items: List[Dict[str, Any]],
        total_count: int,
        page: int,
        page_size: int,
        resource_type: str = "Resources",
    ) -> Dict[str, Any]:
        plural = resource_type + "s" if not resource_type.endswith("s") else resource_type
        return PaginatedResponseBuilder.success(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            message=f"{plural} retrieved successfully",
        )

    @staticmethod
    def empty(
        resource_type: str = "Resources",
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        default_message = f"No {resource_type.lower()} found"
        return PaginatedResponseBuilder.success(
            items=[],
            total_count=0,
            page=0,
            page_size=0,
            message=message or default_message,
        )
