"""
Middleware para manejar Request ID (RID) y Trace ID en todas las peticiones.
Proporciona trazabilidad completa con logging estructurado.
"""
import uuid
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from contextvars import ContextVar
from loguru import logger

# ContextVars para almacenar RID y TraceID en el contexto de la solicitud
rid_context: ContextVar[str] = ContextVar("rid", default="")
trace_id_context: ContextVar[str] = ContextVar("trace_id", default="")


def generate_rid() -> str:
    """Genera Request ID único (32 chars hex)."""
    return uuid.uuid4().hex


def generate_trace_id() -> str:
    """Genera Trace ID único para transacciones distribuidas (32 chars hex)."""
    return uuid.uuid4().hex


def get_current_rid() -> str:
    """Obtiene el RID del contexto actual."""
    return rid_context.get()


def get_current_trace_id() -> str:
    """Obtiene el Trace ID del contexto actual."""
    return trace_id_context.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware que:
    1. Genera o extrae RID de cada request
    2. Propaga TraceID entre microservicios (X-Trace-ID header)
    3. Agrega RID y TraceID a todos los logs
    4. Incluye RID y TraceID en response headers
    5. Mide tiempo de respuesta
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Procesa cada request agregando RID y TraceID.
        
        Args:
            request: Request de FastAPI
            call_next: Siguiente middleware/handler
            
        Returns:
            Response con headers de RID y TraceID
        """
        # 1. Generar o extraer RID
        rid = request.headers.get("X-Request-ID") or generate_rid()
        rid_context.set(rid)
        
        # 2. Extraer o generar TraceID (para trazabilidad entre microservicios)
        trace_id = request.headers.get("X-Trace-ID") or generate_trace_id()
        trace_id_context.set(trace_id)
        
        # 3. Agregar al state del request para acceso en endpoints
        request.state.rid = rid
        request.state.trace_id = trace_id
        
        # 4. Log de inicio de request
        start_time = time.time()
        logger.bind(
            rid=rid,
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown"
        ).info(f"Request started: {request.method} {request.url.path}")
        
        # 5. Procesar request
        try:
            response = await call_next(request)
        except Exception as exc:
            # Log de error
            duration = time.time() - start_time
            logger.bind(
                rid=rid,
                trace_id=trace_id,
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration * 1000, 2),
                error=str(exc)
            ).error(f"Request failed: {request.method} {request.url.path}")
            raise
        
        # 6. Agregar headers de trazabilidad a la respuesta
        response.headers["X-Request-ID"] = rid
        response.headers["X-Trace-ID"] = trace_id
        
        # 7. Log de finalización de request
        duration = time.time() - start_time
        logger.bind(
            rid=rid,
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2)
        ).info(f"Request completed: {request.method} {request.url.path} - {response.status_code}")
        
        return response


def get_request_id() -> str:
    """
    Obtiene el RID del contexto actual. Alias de get_current_rid().
    
    Returns:
        RID (32 chars hex) o empty string
    """
    return get_current_rid()
