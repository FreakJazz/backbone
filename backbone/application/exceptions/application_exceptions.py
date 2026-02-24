"""
Application layer exceptions - Códigos 10XXXXXX
"""
from typing import Dict, Any, Optional, List
from .base_application_exception import ApplicationException


class UseCaseException(ApplicationException):
    """
    Excepción para casos de uso fallidos.
    
    Ejemplos:
    - Caso de uso de registro fallido
    - Caso de uso de actualización fallido
    """
    
    def __init__(
        self,
        message: str,
        use_case_name: str,
        code: int = 10001001,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({"use_case": use_case_name})
        kwargs['details'] = details
        
        super().__init__(code, message, **kwargs)


class ValidationException(ApplicationException):
    """
    Excepción para errores de validación en aplicación.
    
    Diferentes a las validaciones de dominio.
    Estas son validaciones de casos de uso.
    """
    
    def __init__(
        self,
        message: str,
        validation_errors: List[Dict[str, str]] = None,
        code: int = 10002001,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if validation_errors:
            details.update({"validation_errors": validation_errors})
        kwargs['details'] = details
        
        super().__init__(code, message, http_code=400, **kwargs)


class AuthorizationException(ApplicationException):
    """
    Excepción para errores de autorización.
    
    Usuario autenticado pero sin permisos.
    """
    
    def __init__(
        self,
        message: str,
        required_permission: str = None,
        user_id: str = None,
        code: int = 10003001,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if required_permission:
            details.update({"required_permission": required_permission})
        if user_id:
            details.update({"user_id": user_id})
        kwargs['details'] = details
        
        super().__init__(code, message, http_code=403, **kwargs)


class ResourceNotFoundException(ApplicationException):
    """
    Excepción para recursos no encontrados.
    """
    
    def __init__(
        self,
        message: str,
        resource_type: str,
        resource_id: str,
        code: int = 10004001,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            "resource_type": resource_type,
            "resource_id": resource_id
        })
        kwargs['details'] = details
        
        super().__init__(code, message, http_code=404, **kwargs)


class ResourceConflictException(ApplicationException):
    """
    Excepción para conflictos de recursos.
    
    Ejemplos:
    - Email ya existe
    - Licencia ya registrada
    """
    
    def __init__(
        self,
        message: str,
        resource_type: str,
        conflict_field: str,
        conflict_value: str,
        code: int = 10005001,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            "resource_type": resource_type,
            "conflict_field": conflict_field,
            "conflict_value": conflict_value
        })
        kwargs['details'] = details
        
        super().__init__(code, message, http_code=409, **kwargs)


class ApplicationServiceException(ApplicationException):
    """
    Excepción para servicios de aplicación.
    """
    
    def __init__(
        self,
        message: str,
        service_name: str,
        operation: str,
        code: int = 10006001,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            "service_name": service_name,
            "operation": operation
        })
        kwargs['details'] = details
        
        super().__init__(code, message, **kwargs)


# Catálogo de códigos de aplicación
class ApplicationErrorCodes:
    """Códigos de error específicos de aplicación 10XXXXXX"""
    
    # Use Cases (10001XXX)
    USE_CASE_ERROR = 10001001
    CREATE_USER_USE_CASE_ERROR = 10001002
    UPDATE_USER_USE_CASE_ERROR = 10001003
    DELETE_USER_USE_CASE_ERROR = 10001004
    CREATE_TRIP_USE_CASE_ERROR = 10001005
    
    # Validation (10002XXX)
    VALIDATION_ERROR = 10002001
    INPUT_VALIDATION_ERROR = 10002002
    BUSINESS_VALIDATION_ERROR = 10002003
    
    # Authorization (10003XXX)
    AUTHORIZATION_ERROR = 10003001
    INSUFFICIENT_PERMISSIONS = 10003002
    ROLE_REQUIRED = 10003003
    
    # Resource Not Found (10004XXX)
    RESOURCE_NOT_FOUND = 10004001
    USER_NOT_FOUND = 10004002
    DRIVER_NOT_FOUND = 10004003
    TRIP_NOT_FOUND = 10004004
    BOOKING_NOT_FOUND = 10004005
    
    # Resource Conflict (10005XXX)
    RESOURCE_CONFLICT = 10005001
    EMAIL_ALREADY_EXISTS = 10005002
    IDENTIFICATION_ALREADY_EXISTS = 10005003
    LICENSE_ALREADY_EXISTS = 10005004
    VEHICLE_PLATE_ALREADY_EXISTS = 10005005
    
    # Application Services (10006XXX)
    APPLICATION_SERVICE_ERROR = 10006001
    USER_SERVICE_ERROR = 10006002
    TRIP_SERVICE_ERROR = 10006003
    NOTIFICATION_SERVICE_ERROR = 10006004