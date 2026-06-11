"""
Error Response Builder - Constructor de respuestas de error
"""
from typing import Dict, Any, Optional
from uuid import uuid4


class ErrorResponseBuilder:
    """
    Constructor para respuestas de error estándar.

    Contrato:
    {
        "request_id": "uuid",
        "status_code": 400,
        "message": "Validation failed",
        "code_error": "VALIDATION_ERROR"
    }

    Sin dependencia de FastAPI - retorna dict puro.
    """

    @staticmethod
    def _build(
        status_code: int,
        message: str,
        code_error: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "request_id": request_id or str(uuid4()),
            "status_code": status_code,
            "message": message,
            "code_error": code_error,
        }

    @staticmethod
    def from_exception(exception: Exception, request_id: Optional[str] = None) -> Dict[str, Any]:
        if hasattr(exception, "to_error_contract"):
            try:
                kernel_error = exception.to_error_contract()
                return ErrorResponseBuilder._build(
                    status_code=500,
                    message=kernel_error.get("message", str(exception)),
                    code_error=str(kernel_error.get("code")) if kernel_error.get("code") else None,
                    request_id=kernel_error.get("rid") or request_id,
                )
            except Exception:
                pass

        return ErrorResponseBuilder.internal_server_error(
            message=str(exception),
            request_id=request_id,
        )

    @staticmethod
    def validation_error(
        message: str = "Validation failed",
        field_errors: Optional[Dict[str, str]] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        response = ErrorResponseBuilder._build(
            status_code=400,
            message=message,
            code_error="VALIDATION_ERROR",
            request_id=request_id,
        )
        if field_errors:
            response["field_errors"] = field_errors
        return response

    @staticmethod
    def authentication_error(
        message: str = "Authentication required",
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return ErrorResponseBuilder._build(
            status_code=401,
            message=message,
            code_error="AUTHENTICATION_ERROR",
            request_id=request_id,
        )

    @staticmethod
    def authorization_error(
        message: str = "Access denied",
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return ErrorResponseBuilder._build(
            status_code=403,
            message=message,
            code_error="AUTHORIZATION_ERROR",
            request_id=request_id,
        )

    @staticmethod
    def not_found_error(
        message: str = "Resource not found",
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return ErrorResponseBuilder._build(
            status_code=404,
            message=message,
            code_error="NOT_FOUND",
            request_id=request_id,
        )

    @staticmethod
    def conflict_error(
        message: str = "Resource conflict",
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return ErrorResponseBuilder._build(
            status_code=409,
            message=message,
            code_error="CONFLICT",
            request_id=request_id,
        )

    @staticmethod
    def internal_server_error(
        message: str = "An unexpected error occurred",
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return ErrorResponseBuilder._build(
            status_code=500,
            message=message,
            code_error="INTERNAL_SERVER_ERROR",
            request_id=request_id,
        )

    @staticmethod
    def service_unavailable_error(
        message: str = "Service unavailable",
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return ErrorResponseBuilder._build(
            status_code=503,
            message=message,
            code_error="SERVICE_UNAVAILABLE",
            request_id=request_id,
        )
