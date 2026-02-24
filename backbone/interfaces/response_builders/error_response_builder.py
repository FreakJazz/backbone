"""
Error Response Builder - Constructor de respuestas de error
"""
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import uuid4


class ErrorResponseBuilder:
    """
    Constructor para respuestas de error estándar.
    
    Contrato de error:
    {
        "status": "error",
        "status_code": 400,
        "message": "Validation failed",
        "error_details": {
            "field_errors": {...}
        },
        "timestamp": "2024-01-01T12:00:00.000Z",
        "request_id": "uuid"
    }
    
    Sin dependencia de FastAPI - retorna dict puro.
    """
    
    @staticmethod
    def from_exception(exception: Exception) -> Dict[str, Any]:
        """
        Construye respuesta de error desde excepción.
        
        Args:
            exception: Excepción a convertir
            
        Returns:
            Dict con formato estándar de error
        """
        # Try to get error code from kernel exceptions
        try:
            if hasattr(exception, 'to_error_contract'):
                # For BaseKernelException, convert to new format
                kernel_error = exception.to_error_contract()
                return {
                    "status": "error",
                    "status_code": 500,  # Default to 500 for kernel errors
                    "message": kernel_error.get("message", str(exception)),
                    "error_details": {
                        "error_code": kernel_error.get("code"),
                        "request_id": kernel_error.get("rid")
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "request_id": kernel_error.get("rid", str(uuid4()))
                }
        except:
            pass
        
        # Default error handling
        return ErrorResponseBuilder.internal_server_error(
            message=str(exception)
        )
    
    @staticmethod
    def _create_error_response(
        message: str,
        status_code: int,
        error_details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crear respuesta de error base.
        
        Args:
            message: Mensaje del error
            status_code: Código de estado HTTP
            error_details: Detalles adicionales del error
            request_id: ID de la request (opcional)
            
        Returns:
            Dict con formato estándar de error
        """
        response = {
            "status": "error",
            "status_code": status_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id or str(uuid4())
        }
        
        if error_details:
            response["error_details"] = error_details
            
        return response
    
    @staticmethod
    def validation_error(
        message: str = "Validation failed",
        field_errors: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Error de validación (400).
        
        Args:
            message: Mensaje del error
            field_errors: Errores específicos por campo
            
        Returns:
            Dict con error de validación
        """
        error_details = {}
        if field_errors:
            error_details["field_errors"] = field_errors
            
        return ErrorResponseBuilder._create_error_response(
            message=message,
            status_code=400,
            error_details=error_details if error_details else None
        )
    
    @staticmethod
    def authentication_error(
        message: str = "Authentication required"
    ) -> Dict[str, Any]:
        """
        Error de autenticación (401).
        
        Args:
            message: Mensaje del error
            
        Returns:
            Dict con error de autenticación
        """
        return ErrorResponseBuilder._create_error_response(
            message=message,
            status_code=401
        )
    
    @staticmethod
    def authorization_error(
        message: str = "Access denied",
        required_permission: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Error de autorización (403).
        
        Args:
            message: Mensaje del error
            required_permission: Permiso requerido
            
        Returns:
            Dict con error de autorización
        """
        error_details = {}
        if required_permission:
            error_details["required_permission"] = required_permission
            
        return ErrorResponseBuilder._create_error_response(
            message=message,
            status_code=403,
            error_details=error_details if error_details else None
        )
    
    @staticmethod
    def not_found_error(
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Error de recurso no encontrado (404).
        
        Args:
            message: Mensaje del error
            resource_type: Tipo de recurso
            resource_id: ID del recurso
            
        Returns:
            Dict con error de recurso no encontrado
        """
        error_details = {}
        if resource_type:
            error_details["resource_type"] = resource_type
        if resource_id:
            error_details["resource_id"] = resource_id
            
        return ErrorResponseBuilder._create_error_response(
            message=message,
            status_code=404,
            error_details=error_details if error_details else None
        )
    
    @staticmethod
    def conflict_error(
        message: str = "Resource conflict",
        resource_type: Optional[str] = None,
        conflict_field: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Error de conflicto de recursos (409).
        
        Args:
            message: Mensaje del error
            resource_type: Tipo de recurso
            conflict_field: Campo que tiene conflicto
            
        Returns:
            Dict con error de conflicto
        """
        error_details = {}
        if resource_type:
            error_details["resource_type"] = resource_type
        if conflict_field:
            error_details["conflict_field"] = conflict_field
            
        return ErrorResponseBuilder._create_error_response(
            message=message,
            status_code=409,
            error_details=error_details if error_details else None
        )
    
    @staticmethod
    def internal_server_error(
        message: str = "An unexpected error occurred"
    ) -> Dict[str, Any]:
        """
        Error interno del servidor (500).
        
        Args:
            message: Mensaje del error
            
        Returns:
            Dict con error interno del servidor
        """
        return ErrorResponseBuilder._create_error_response(
            message=message,
            status_code=500
        )
    
    @staticmethod
    def service_unavailable_error(
        message: str = "Service unavailable"
    ) -> Dict[str, Any]:
        """
        Error de servicio no disponible (503).
        
        Args:
            message: Mensaje del error
            
        Returns:
            Dict con error de servicio no disponible
        """
        return ErrorResponseBuilder._create_error_response(
            message=message,
            status_code=503
        )
