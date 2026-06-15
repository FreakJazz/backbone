"""
Error Response Builder — constructor de respuestas de error estándar.

error_code es SIEMPRE obligatorio en la respuesta.
Cada método tiene un código por defecto del catálogo backbone (backbone.errors.ErrorCodes).
El caller puede sobreescribirlo pasando error_code=miCodigo.

Catálogo de capas:

    11 = Domain        → 110000001, 110000002, ...
    12 = Application   → 120000001, 120000002, ...
    13 = Interface     → 130000001, 130000002, ...
    14 = Infrastructure→ 140000001, 140000002, ...

Contrato de respuesta:

    {
        "rid":         "uuid",       ← siempre presente, auto-generado si no se pasa
        "status_code": 400,
        "message":     "...",
        "error_code":  130000001,    ← siempre presente, código del catálogo
    }
"""
from typing import Dict, Any, Optional
from uuid import uuid4

from backbone.errors import ErrorCodes


def _new_rid() -> str:
    """Genera un Request ID único (UUID4 hex, 32 chars sin guiones)."""
    return uuid4().hex


class ErrorResponseBuilder:
    """Constructor de respuestas de error del backbone."""

    @staticmethod
    def _build(
        status_code: int,
        message: str,
        error_code: int,
        rid: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "rid": rid or _new_rid(),
            "status_code": status_code,
            "message": message,
            "error_code": error_code,
        }

    @staticmethod
    def from_exception(
        exception: Exception,
        rid: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Construye la respuesta de error a partir de cualquier excepción.

        Si la excepción es un BaseKernelException (o subclase), extrae:
          - rid: del propio objeto (trazabilidad garantizada)
          - status_code: http_code de la excepción
          - message: mensaje limpio (sin prefijos ni RID embebido)
          - error_code: código numérico de la excepción

        Para excepciones genéricas devuelve 500 con mensaje seguro,
        sin exponer detalles internos al cliente.
        """
        if hasattr(exception, "to_error_contract"):
            try:
                contract = exception.to_error_contract()
                return ErrorResponseBuilder._build(
                    status_code=contract.get("status_code", 500),
                    message=contract.get("message", "An unexpected error occurred"),
                    error_code=contract.get("error_code", ErrorCodes.INFRA_DB_FAILURE),
                    rid=contract.get("rid") or rid,
                )
            except Exception:
                pass

        # Excepción genérica — nunca exponer detalles internos al cliente
        return ErrorResponseBuilder.internal_server_error(rid=rid)

    @staticmethod
    def validation_error(
        message: str = "Validation failed",
        rid: Optional[str] = None,
        error_code: Optional[int] = None,
    ) -> Dict[str, Any]:
        """400 — default: 130000001 (Interface — invalid request body)."""
        return ErrorResponseBuilder._build(
            status_code=400,
            message=message,
            error_code=error_code or ErrorCodes.IFC_INVALID_REQUEST_BODY,
            rid=rid,
        )

    @staticmethod
    def authentication_error(
        message: str = "Authentication required",
        rid: Optional[str] = None,
        error_code: Optional[int] = None,
    ) -> Dict[str, Any]:
        """401 — default: 130000006 (Interface — unauthorized)."""
        return ErrorResponseBuilder._build(
            status_code=401,
            message=message,
            error_code=error_code or ErrorCodes.IFC_UNAUTHORIZED,
            rid=rid,
        )

    @staticmethod
    def authorization_error(
        message: str = "Access denied",
        rid: Optional[str] = None,
        error_code: Optional[int] = None,
    ) -> Dict[str, Any]:
        """403 — default: 130000007 (Interface — forbidden)."""
        return ErrorResponseBuilder._build(
            status_code=403,
            message=message,
            error_code=error_code or ErrorCodes.IFC_FORBIDDEN,
            rid=rid,
        )

    @staticmethod
    def not_found_error(
        message: str = "Resource not found",
        rid: Optional[str] = None,
        error_code: Optional[int] = None,
    ) -> Dict[str, Any]:
        """404 — default: 120000004 (Application — resource not found)."""
        return ErrorResponseBuilder._build(
            status_code=404,
            message=message,
            error_code=error_code or ErrorCodes.APP_RESOURCE_NOT_FOUND,
            rid=rid,
        )

    @staticmethod
    def conflict_error(
        message: str = "Resource conflict",
        rid: Optional[str] = None,
        error_code: Optional[int] = None,
    ) -> Dict[str, Any]:
        """409 — default: 120000006 (Application — conflict)."""
        return ErrorResponseBuilder._build(
            status_code=409,
            message=message,
            error_code=error_code or ErrorCodes.APP_CONFLICT,
            rid=rid,
        )

    @staticmethod
    def internal_server_error(
        message: str = "An unexpected error occurred",
        rid: Optional[str] = None,
        error_code: Optional[int] = None,
    ) -> Dict[str, Any]:
        """500 — default: 140000001 (Infrastructure — DB failure).
        En sistemas bancarios pasar siempre mensaje genérico para no
        exponer detalles internos al cliente.
        """
        return ErrorResponseBuilder._build(
            status_code=500,
            message=message,
            error_code=error_code or ErrorCodes.INFRA_DB_FAILURE,
            rid=rid,
        )

    @staticmethod
    def service_unavailable_error(
        message: str = "Service unavailable",
        rid: Optional[str] = None,
        error_code: Optional[int] = None,
    ) -> Dict[str, Any]:
        """503 — default: 140000005 (Infrastructure — service unavailable)."""
        return ErrorResponseBuilder._build(
            status_code=503,
            message=message,
            error_code=error_code or ErrorCodes.INFRA_SERVICE_UNAVAILABLE,
            rid=rid,
        )
