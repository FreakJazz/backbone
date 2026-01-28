"""
Excepciones personalizadas del sistema con RID y TraceID.
Estructura de código: XXYYZZ
- XX: Servicio (10=Auth, 20=Trip, 30=Gateway)
- YY: Capa (01=API, 02=Service, 03=Repository, 04=Domain)
- ZZ: Error específico (01-99)
"""
import uuid
from typing import Optional, Dict, Any
from datetime import datetime


def generate_rid() -> str:
    """Genera Request ID único para trazabilidad."""
    return uuid.uuid4().hex


def generate_trace_id() -> str:
    """Genera Trace ID único para transacciones distribuidas."""
    return uuid.uuid4().hex


class BaseAPIException(Exception):
    """
    Excepción base para todas las excepciones de la aplicación.
    
    Attributes:
        code: Código de error de 6 dígitos (XXYYZZ)
        message: Mensaje descriptivo del error
        http_code: Código HTTP (400, 404, 412, 500, etc.)
        details: Detalles adicionales
        rid: Request ID para trazabilidad
        trace_id: Trace ID para transacciones distribuidas
    """
    
    def __init__(
        self,
        code: int,
        message: str,
        http_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        rid: Optional[str] = None,
        trace_id: Optional[str] = None
    ):
        self.code = code
        self.message = message
        self.http_code = http_code
        self.details = details or {}
        self.rid = rid or generate_rid()
        self.trace_id = trace_id
        self.timestamp = datetime.utcnow().isoformat()
        super().__init__(self.message)
    
    def to_dict(self, include_internal_fields: bool = False) -> Dict[str, Any]:
        """
        Convierte la excepción a formato JSON para el cliente.
        
        Por defecto solo retorna campos públicos (rid, code, message).
        Los campos internos (httpCode, timestamp, traceId, details) se usan solo en logs.
        
        Args:
            include_internal_fields: Si True, incluye campos técnicos (solo para logs)
        
        Returns:
            Response mínimo para el cliente:
            {
                "rid": "b711f8e36b00950c3ae4b456fe16e9b6",
                "code": 100401,
                "message": "El email ya está registrado"
            }
        """
        # Campos públicos (siempre se envían al cliente)
        error_dict = {
            "rid": self.rid,
            "code": self.code,
            "message": self.message
        }
        
        # Campos internos (solo para logs, no para el cliente)
        if include_internal_fields:
            error_dict["httpCode"] = self.http_code
            error_dict["timestamp"] = self.timestamp
            
            if self.trace_id:
                error_dict["traceId"] = self.trace_id
            
            if self.details:
                error_dict["details"] = self.details
        
        return error_dict
    
    @property
    def service_code(self) -> int:
        """Extrae código de servicio (XX)."""
        return self.code // 10000
    
    @property
    def layer_code(self) -> int:
        """Extrae código de capa (YY)."""
        return (self.code // 100) % 100
    
    @property
    def error_number(self) -> int:
        """Extrae número de error (ZZ)."""
        return self.code % 100


# ============================================================================
# Excepciones por capa (para aplicar en cada microservicio)
# ============================================================================

class APILayerException(BaseAPIException):
    """Excepción en la capa de API (YY=01). HTTP 400."""
    
    def __init__(self, code: int, message: str, http_code: int = 400, **kwargs):
        super().__init__(code, message, http_code, **kwargs)


class ServiceLayerException(BaseAPIException):
    """Excepción en la capa de servicio (YY=02). HTTP 422."""
    
    def __init__(self, code: int, message: str, http_code: int = 422, **kwargs):
        super().__init__(code, message, http_code, **kwargs)


class RepositoryLayerException(BaseAPIException):
    """Excepción en la capa de repositorio (YY=03). HTTP 500."""
    
    def __init__(self, code: int, message: str, http_code: int = 500, **kwargs):
        super().__init__(code, message, http_code, **kwargs)


class DomainLayerException(BaseAPIException):
    """Excepción en la capa de dominio (YY=04). HTTP 400."""
    
    def __init__(self, code: int, message: str, http_code: int = 400, **kwargs):
        super().__init__(code, message, http_code, **kwargs)


# ============================================================================
# Excepciones HTTP comunes (usables en cualquier capa)
# ============================================================================

class NotFoundException(BaseAPIException):
    """Recurso no encontrado (404)."""
    
    def __init__(self, resource: str, resource_id: str, code: int, **kwargs):
        message = f"{resource} con ID {resource_id} no encontrado"
        super().__init__(code, message, http_code=404, **kwargs)


class ValidationException(BaseAPIException):
    """Error de validación (400)."""
    
    def __init__(self, message: str, code: int, field: Optional[str] = None, **kwargs):
        details = {"field": field} if field else {}
        super().__init__(code, message, http_code=400, details=details, **kwargs)


class UnauthorizedException(BaseAPIException):
    """No autorizado (401)."""
    
    def __init__(self, message: str = "No autorizado", code: int = 999901, **kwargs):
        super().__init__(code, message, http_code=401, **kwargs)


class ForbiddenException(BaseAPIException):
    """Acceso prohibido (403)."""
    
    def __init__(self, message: str = "Acceso prohibido", code: int = 999903, **kwargs):
        super().__init__(code, message, http_code=403, **kwargs)


class ConflictException(BaseAPIException):
    """Conflicto de recursos (409)."""
    
    def __init__(self, message: str, code: int, **kwargs):
        super().__init__(code, message, http_code=409, **kwargs)


class PreconditionFailedException(BaseAPIException):
    """Precondición fallida (412)."""
    
    def __init__(self, message: str, code: int, **kwargs):
        super().__init__(code, message, http_code=412, **kwargs)


class InternalServerException(BaseAPIException):
    """Error interno del servidor (500)."""
    
    def __init__(self, message: str = "Error interno del servidor", code: int = 999500, **kwargs):
        super().__init__(code, message, http_code=500, **kwargs)
