"""
Domain layer exceptions - Códigos 11XXXXXX
"""
from typing import Dict, Any, Optional
from .base_kernel_exception import BaseKernelException


class DomainException(BaseKernelException):
    """
    Excepción base para la capa de dominio.
    
    Códigos: 11XXXXXX
    HTTP por defecto: 400 (Bad Request)
    
    Uso: Violaciones de reglas de negocio, estados inválidos de entidades
    """
    
    def __init__(
        self, 
        code: int, 
        message: str, 
        http_code: int = 400,
        **kwargs
    ):
        # Validar que el código pertenezca a la capa de dominio
        if not (11000000 <= code <= 11999999):
            raise ValueError(f"Domain exception code must be in range 11000000-11999999, got: {code}")
        
        super().__init__(code, message, http_code, **kwargs)


class BusinessRuleViolationException(DomainException):
    """
    Excepción para violaciones de reglas de negocio.
    
    Ejemplos:
    - Usuario menor de edad
    - Vehículo demasiado antiguo  
    - Rating fuera de rango
    """
    
    def __init__(
        self,
        message: str,
        rule_name: str,
        code: int = 11001001,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({"rule_violated": rule_name})
        kwargs['details'] = details
        
        super().__init__(code, message, **kwargs)


class InvalidEntityStateException(DomainException):
    """
    Excepción para estados inválidos de entidades.
    
    Ejemplos:
    - Usuario inactivo intentando hacer una acción
    - Conductor no verificado
    - Viaje ya completado
    """
    
    def __init__(
        self,
        message: str,
        entity_type: str,
        entity_id: str,
        current_state: str,
        required_state: str,
        code: int = 11002001,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            "entity_type": entity_type,
            "entity_id": entity_id,
            "current_state": current_state,
            "required_state": required_state
        })
        kwargs['details'] = details
        
        super().__init__(code, message, http_code=412, **kwargs)


class InvalidValueObjectException(DomainException):
    """
    Excepción para value objects inválidos.
    
    Ejemplos:
    - Coordenadas fuera de rango
    - Email con formato inválido
    - Rating con valor inválido
    """
    
    def __init__(
        self,
        message: str,
        value_object_type: str,
        invalid_value: Any,
        code: int = 11003001,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            "value_object_type": value_object_type,
            "invalid_value": str(invalid_value)
        })
        kwargs['details'] = details
        
        super().__init__(code, message, **kwargs)


# Catálogo de códigos de dominio
class DomainErrorCodes:
    """Códigos de error específicos del dominio 11XXXXXX"""
    
    # Business Rules (11001XXX)
    BUSINESS_RULE_VIOLATION = 11001001
    UNDERAGE_USER = 11001002
    VEHICLE_TOO_OLD = 11001003
    INVALID_VEHICLE_CAPACITY = 11001004
    MAX_TRIP_DURATION_EXCEEDED = 11001005
    
    # Entity State (11002XXX)  
    INVALID_ENTITY_STATE = 11002001
    USER_INACTIVE = 11002002
    DRIVER_NOT_VERIFIED = 11002003
    TRIP_ALREADY_COMPLETED = 11002004
    BOOKING_ALREADY_CANCELLED = 11002005
    LICENSE_EXPIRED = 11002006
    
    # Value Objects (11003XXX)
    INVALID_VALUE_OBJECT = 11003001
    INVALID_COORDINATES = 11003002
    INVALID_EMAIL_FORMAT = 11003003
    INVALID_PHONE_FORMAT = 11003004
    INVALID_RATING_VALUE = 11003005
    COORDINATES_OUT_OF_BOUNDS = 11003006
    
    # Aggregates (11004XXX)
    AGGREGATE_CONSISTENCY_VIOLATION = 11004001
    INVALID_AGGREGATE_STATE = 11004002
    
    # Domain Services (11005XXX)
    DOMAIN_SERVICE_ERROR = 11005001
    DISTANCE_CALCULATION_ERROR = 11005002
    PRICE_CALCULATION_ERROR = 11005003