"""
Schemas de paginación estándar para todos los servicios.
"""
from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel, Field, field_validator

T = TypeVar('T')


class PaginationParams(BaseModel):
    """
    Parámetros de paginación estándar.
    
    Uso en endpoints:
        def get_users(pagination: PaginationParams = Depends()):
            ...
    """
    page: int = Field(
        default=0,
        ge=0,
        description="Número de página (0-indexed)"
    )
    page_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Cantidad de elementos por página (máx. 100)"
    )
    
    @field_validator('page_size')
    @classmethod
    def validate_page_size(cls, v):
        """Limita page_size a 100 elementos máximo."""
        if v > 100:
            return 100
        return v
    
    @property
    def offset(self) -> int:
        """Calcula el offset para la query SQL."""
        return self.page * self.page_size
    
    @property
    def limit(self) -> int:
        """Retorna el límite (alias de page_size)."""
        return self.page_size


class FilterParams(BaseModel):
    """
    Parámetros de filtros opcionales estándar.
    
    Extender esta clase para filtros específicos:
    
        class UserFilterParams(FilterParams):
            role: Optional[str] = None
            is_active: Optional[bool] = None
    """
    search: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Búsqueda por texto (nombre, email, etc.)"
    )
    sort_by: Optional[str] = Field(
        default="created_at",
        description="Campo por el cual ordenar"
    )
    sort_order: Optional[str] = Field(
        default="desc",
        pattern="^(asc|desc)$",
        description="Orden: asc o desc"
    )


class PaginationMetadata(BaseModel):
    """
    Metadata de paginación para responses.
    
    El frontend puede calcular has_next y has_previous fácilmente:
    - has_next = page < total_pages - 1
    - has_previous = page > 0
    """
    page: int = Field(description="Página actual (0-indexed)")
    page_size: int = Field(description="Elementos por página")
    total_items: int = Field(description="Total de elementos disponibles")
    total_pages: int = Field(description="Total de páginas")
    
    @classmethod
    def create(
        cls,
        page: int,
        page_size: int,
        total_items: int
    ) -> "PaginationMetadata":
        """
        Factory method para crear metadata de paginación.
        
        Args:
            page: Página actual (0-indexed)
            page_size: Elementos por página
            total_items: Total de elementos
            
        Returns:
            PaginationMetadata con campos esenciales
        """
        total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 0
        
        return cls(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Response paginado genérico.
    
    Uso:
        return PaginatedResponse[UserResponse](
            items=users,
            pagination=PaginationMetadata.create(page=0, page_size=10, total_items=50)
        )
    """
    items: List[T] = Field(description="Lista de elementos")
    pagination: PaginationMetadata = Field(description="Metadata de paginación")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [{"id": 1, "name": "Example"}],
                "pagination": {
                    "page": 0,
                    "page_size": 10,
                    "total_items": 50,
                    "total_pages": 5
                }
            }
        }


class UserFilterParams(FilterParams):
    """Filtros específicos para usuarios."""
    role: Optional[str] = Field(
        default=None,
        description="Filtrar por rol: passenger, driver, admin"
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Filtrar por estado activo"
    )
    identification_type: Optional[str] = Field(
        default=None,
        description="Tipo de identificación: cedula, pasaporte, ruc"
    )


class DriverFilterParams(FilterParams):
    """Filtros específicos para conductores."""
    is_available: Optional[bool] = Field(
        default=None,
        description="Filtrar por disponibilidad"
    )
    vehicle_type: Optional[str] = Field(
        default=None,
        description="Tipo de vehículo"
    )
    min_rating: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=5.0,
        description="Rating mínimo (0-5)"
    )
    license_status: Optional[str] = Field(
        default=None,
        description="Estado de licencia: active, expired, suspended"
    )


class BookingFilterParams(FilterParams):
    """Filtros específicos para reservas."""
    status: Optional[str] = Field(
        default=None,
        description="Estado: pending, assigned, in_progress, completed, cancelled"
    )
    booking_type: Optional[str] = Field(
        default=None,
        description="Tipo: immediate, scheduled"
    )
    passenger_id: Optional[str] = Field(
        default=None,
        description="ID del pasajero"
    )
    driver_id: Optional[str] = Field(
        default=None,
        description="ID del conductor"
    )
    date_from: Optional[str] = Field(
        default=None,
        description="Fecha desde (YYYY-MM-DD)"
    )
    date_to: Optional[str] = Field(
        default=None,
        description="Fecha hasta (YYYY-MM-DD)"
    )
