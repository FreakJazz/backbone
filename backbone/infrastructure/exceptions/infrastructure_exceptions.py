"""
Infrastructure layer exceptions - Códigos 12XXXXXX
"""
from typing import Dict, Any, Optional
from .base_infrastructure_exception import InfrastructureException


class DatabaseException(InfrastructureException):
    """
    Excepción para errores de base de datos.
    
    Ejemplos:
    - Error de conexión
    - Constraint violation
    - Timeout
    """
    
    def __init__(
        self,
        message: str,
        operation: str,
        table: str = None,
        original_error: str = None,
        code: int = 12001001,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            "operation": operation,
            "table": table,
            "original_error": original_error
        })
        kwargs['details'] = details
        
        super().__init__(code, message, **kwargs)


class ExternalServiceException(InfrastructureException):
    """
    Excepción para servicios externos.
    
    Ejemplos:
    - API de terceros no responde
    - Timeout en servicio externo
    - Error de autenticación con servicio externo
    """
    
    def __init__(
        self,
        message: str,
        service_name: str,
        endpoint: str = None,
        status_code: int = None,
        response_body: str = None,
        code: int = 12002001,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            "service_name": service_name,
            "endpoint": endpoint,
            "status_code": status_code,
            "response_body": response_body
        })
        kwargs['details'] = details
        
        # Mapear status codes a HTTP codes apropiados
        if status_code:
            if 400 <= status_code < 500:
                http_code = 424  # Failed Dependency
            elif status_code >= 500:
                http_code = 502  # Bad Gateway
            else:
                http_code = 500
        else:
            http_code = 500
            
        super().__init__(code, message, http_code=http_code, **kwargs)


class ConfigurationException(InfrastructureException):
    """
    Excepción para errores de configuración.
    
    Ejemplos:
    - Variable de entorno faltante
    - Configuración inválida
    - Archivo de configuración no encontrado
    """
    
    def __init__(
        self,
        message: str,
        config_key: str = None,
        config_value: str = None,
        code: int = 12003001,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            "config_key": config_key,
            "config_value": config_value
        })
        kwargs['details'] = details
        
        super().__init__(code, message, **kwargs)


class CacheException(InfrastructureException):
    """
    Excepción para errores de caché (Redis, Memcached, etc.).
    
    Ejemplos:
    - Error de conexión a Redis
    - Timeout en operación de caché
    - Error de serialización
    """
    
    def __init__(
        self,
        message: str,
        cache_operation: str,
        cache_key: str = None,
        code: int = 12004001,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            "cache_operation": cache_operation,
            "cache_key": cache_key
        })
        kwargs['details'] = details
        
        super().__init__(code, message, **kwargs)


class FileSystemException(InfrastructureException):
    """
    Excepción para errores del sistema de archivos.
    
    Ejemplos:
    - Archivo no encontrado
    - Permisos insuficientes
    - Espacio en disco insuficiente
    """
    
    def __init__(
        self,
        message: str,
        file_path: str,
        operation: str,
        code: int = 12005001,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            "file_path": file_path,
            "operation": operation
        })
        kwargs['details'] = details
        
        super().__init__(code, message, **kwargs)


# Catálogo de códigos de infraestructura
class InfrastructureErrorCodes:
    """Códigos de error específicos de infraestructura 12XXXXXX"""
    
    # Database (12001XXX)
    DATABASE_ERROR = 12001001
    DATABASE_CONNECTION_ERROR = 12001002
    DATABASE_TIMEOUT_ERROR = 12001003
    DATABASE_CONSTRAINT_ERROR = 12001004
    DATABASE_INTEGRITY_ERROR = 12001005
    
    # External Services (12002XXX)
    EXTERNAL_SERVICE_ERROR = 12002001
    EXTERNAL_SERVICE_TIMEOUT = 12002002
    EXTERNAL_SERVICE_UNAUTHORIZED = 12002003
    EXTERNAL_SERVICE_NOT_FOUND = 12002004
    EXTERNAL_SERVICE_UNAVAILABLE = 12002005
    
    # Configuration (12003XXX)
    CONFIGURATION_ERROR = 12003001
    MISSING_ENVIRONMENT_VARIABLE = 12003002
    INVALID_CONFIGURATION_VALUE = 12003003
    CONFIGURATION_FILE_NOT_FOUND = 12003004
    
    # Cache (12004XXX)
    CACHE_ERROR = 12004001
    CACHE_CONNECTION_ERROR = 12004002
    CACHE_TIMEOUT_ERROR = 12004003
    CACHE_SERIALIZATION_ERROR = 12004004
    
    # File System (12005XXX)
    FILE_SYSTEM_ERROR = 12005001
    FILE_NOT_FOUND = 12005002
    INSUFFICIENT_PERMISSIONS = 12005003
    DISK_SPACE_FULL = 12005004