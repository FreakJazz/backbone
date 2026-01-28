"""
Modelos base compartidos entre todos los microservicios
"""
from datetime import datetime
from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel, Field
from enum import Enum


# ==========================================
# BASE ENTITY
# ==========================================
class BaseEntity(BaseModel):
    """Entidad base para todos los modelos de dominio"""
    id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    is_deleted: bool = False
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ==========================================
# RESPONSE MODELS
# ==========================================
T = TypeVar('T')


class ProcessResponse(BaseModel, Generic[T]):
    """
    Respuesta estándar para todas las operaciones.
    
    Soporta:
    - Respuestas simples: ProcessResponse(success=True, data=user)
    - Respuestas con metadata: ProcessResponse(success=True, data=items, metadata={...})
    """
    success: bool
    message: str
    data: Optional[T] = None
    error_code: Optional[str] = None
    metadata: Optional[dict] = None  # Para paginación y otros metadatos
    
    @classmethod
    def success_response(cls, data: T, message: str = "Operation successful", metadata: Optional[dict] = None):
        return cls(
            success=True,
            message=message,
            data=data,
            metadata=metadata
        )
    
    @classmethod
    def error_response(cls, message: str, error_code: str):
        return cls(
            success=False,
            message=message,
            error_code=error_code,
            data=None
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Respuesta paginada para listados.
    
    DEPRECADO: Usar ProcessResponse con metadata en su lugar.
    
    Ejemplo nuevo:
        ProcessResponse(
            success=True,
            message="OK",
            data=items,
            metadata={
                "pagination": {
                    "page": 0,
                    "page_size": 10,
                    "total_items": 50,
                    "total_pages": 5,
                    "has_next": True,
                    "has_previous": False
                }
            }
        )
    """
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    
    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int):
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages - 1 if total_pages > 0 else False,
            has_previous=page > 0
        )


class ErrorDetail(BaseModel):
    """Detalle de error"""
    field: Optional[str] = None
    message: str
    code: str


class ValidationErrorResponse(BaseModel):
    """Respuesta de error de validación"""
    success: bool = False
    message: str = "Validation error"
    errors: List[ErrorDetail]


# ==========================================
# ENUMS COMUNES
# ==========================================
class UserRole(str, Enum):
    """Roles de usuario"""
    PASSENGER = "passenger"
    DRIVER = "driver"
    ADMIN = "admin"
    SUPPORT = "support"


class UserStatus(str, Enum):
    """Estados de usuario"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"


class DocumentType(str, Enum):
    """Tipos de documento"""
    NATIONAL_ID = "cedula"
    PASSPORT = "passport"
    DRIVER_LICENSE = "license"
    VEHICLE_REGISTRATION = "vehicle_registration"


class TripStatus(str, Enum):
    """Estados de viaje"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    CANCELLED_BY_DRIVER = "cancelled_by_driver"
    CANCELLED_BY_PASSENGER = "cancelled_by_passenger"


class BookingStatus(str, Enum):
    """Estados de reserva"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class PaymentStatus(str, Enum):
    """Estados de pago"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    """Métodos de pago"""
    CASH = "efectivo"
    CARD = "tarjeta"
    TRANSFER = "transferencia"


class CityType(str, Enum):
    """Tipos de ciudad"""
    PRIMARY = "primary"  # Quito, Guayaquil, Cuenca
    SECONDARY = "secondary"  # Destinos intermedios


class RouteType(str, Enum):
    """Tipos de ruta"""
    MAIN = "main"  # Entre ciudades principales
    INTERMEDIATE = "intermediate"  # Con paradas intermedias
    RETURN = "return"  # Rutas de regreso desde destinos


# ==========================================
# VALUE OBJECTS
# ==========================================
class Coordinates(BaseModel):
    """Coordenadas geográficas"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    
    class Config:
        frozen = True


class Address(BaseModel):
    """Dirección completa"""
    street: str
    city: str
    province: str
    postal_code: Optional[str] = None
    coordinates: Optional[Coordinates] = None
    reference: Optional[str] = None
    
    class Config:
        frozen = True


class Rating(BaseModel):
    """Calificación"""
    score: float = Field(..., ge=1.0, le=5.0)
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Money(BaseModel):
    """Representación de dinero"""
    amount: float = Field(..., ge=0)
    currency: str = Field(default="USD")
    
    def __add__(self, other: 'Money'):
        if self.currency != other.currency:
            raise ValueError("Cannot add amounts in different currencies")
        return Money(amount=self.amount + other.amount, currency=self.currency)
    
    def __mul__(self, multiplier: float):
        return Money(amount=self.amount * multiplier, currency=self.currency)
    
    class Config:
        frozen = True


# ==========================================
# REQUEST MODELS COMUNES
# ==========================================
class PaginationParams(BaseModel):
    """Parámetros de paginación"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$")


class DateRangeFilter(BaseModel):
    """Filtro por rango de fechas"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


# ==========================================
# METADATA
# ==========================================
class AuditMetadata(BaseModel):
    """Metadata de auditoría"""
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
