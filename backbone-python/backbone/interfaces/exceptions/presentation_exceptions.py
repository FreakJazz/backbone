"""
Presentation layer exceptions - Códigos 13XXXXXX
"""
from typing import Dict, Any, Optional, List
from .base_presentation_exception import PresentationException


class RequestValidationException(PresentationException):
    """
    Excepción para errores de validación de requests.
    
    Diferente a las validaciones de aplicación/dominio.
    Estas son validaciones de formato HTTP, JSON, etc.
    """
    
    def __init__(
        self,
        message: str,
        field_errors: List[Dict[str, str]] = None,
        code: int = 13001001,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if field_errors:
            details.update({"field_errors": field_errors})
        kwargs['details'] = details
        
        super().__init__(code, message, **kwargs)


class HttpException(PresentationException):
    """
    Excepción para errores específicos HTTP.
    
    Ejemplos:
    - Método HTTP no permitido
    - Content-Type inválido
    - Headers faltantes
    """
    
    def __init__(
        self,
        message: str,
        http_method: str = None,
        endpoint: str = None,
        expected_content_type: str = None,
        received_content_type: str = None,
        code: int = 13002001,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            "http_method": http_method,
            "endpoint": endpoint,
            "expected_content_type": expected_content_type,
            "received_content_type": received_content_type
        })
        kwargs['details'] = details
        
        super().__init__(code, message, **kwargs)


class SerializationException(PresentationException):
    """
    Excepción para errores de serialización.
    
    Cuando no se puede convertir un objeto a JSON/XML/etc.
    """
    
    def __init__(
        self,
        message: str,
        object_type: str,
        serialization_format: str = "json",
        code: int = 13003001,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            "object_type": object_type,
            "serialization_format": serialization_format
        })
        kwargs['details'] = details
        
        super().__init__(code, message, http_code=500, **kwargs)


class DeserializationException(PresentationException):
    """
    Excepción para errores de deserialización.
    
    Cuando no se puede convertir JSON/XML/etc. a objeto.
    """
    
    def __init__(
        self,
        message: str,
        expected_type: str,
        received_data: str = None,
        deserialization_format: str = "json",
        code: int = 13004001,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            "expected_type": expected_type,
            "received_data": received_data,
            "deserialization_format": deserialization_format
        })
        kwargs['details'] = details
        
        super().__init__(code, message, **kwargs)


# Catálogo de códigos de presentación
class PresentationErrorCodes:
    """Códigos de error específicos de presentación 13XXXXXX"""
    
    # Request Validation (13001XXX)
    REQUEST_VALIDATION_ERROR = 13001001
    INVALID_JSON_FORMAT = 13001002
    MISSING_REQUIRED_FIELD = 13001003
    INVALID_FIELD_TYPE = 13001004
    INVALID_FIELD_VALUE = 13001005
    
    # HTTP (13002XXX)
    HTTP_ERROR = 13002001
    METHOD_NOT_ALLOWED = 13002002
    UNSUPPORTED_MEDIA_TYPE = 13002003
    MISSING_HEADER = 13002004
    INVALID_HEADER_VALUE = 13002005
    
    # Serialization (13003XXX)
    SERIALIZATION_ERROR = 13003001
    JSON_SERIALIZATION_ERROR = 13003002
    XML_SERIALIZATION_ERROR = 13003003
    
    # Deserialization (13004XXX)
    DESERIALIZATION_ERROR = 13004001
    JSON_DESERIALIZATION_ERROR = 13004002
    XML_DESERIALIZATION_ERROR = 13004003
    INVALID_REQUEST_BODY = 13004004