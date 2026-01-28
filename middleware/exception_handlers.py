"""
Exception handlers globales con RID, TraceID y códigos de error por capas.
Retorna formato estándar y logging automático estructurado.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger
from shared.exceptions import BaseAPIException
from shared.middleware.request_id import get_current_rid, get_current_trace_id


async def base_exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
    """
    Handler para todas las excepciones que heredan de BaseAPIException.
    
    Args:
        request: Request de FastAPI
        exc: Excepción capturada
        
    Returns:
        JSONResponse con formato estándar: {rid, code, httpCode, message, traceId, details}
    """
    # 1. Obtener RID y TraceID del contexto
    rid = get_current_rid() or (request.state.rid if hasattr(request.state, 'rid') else 'unknown')
    trace_id = get_current_trace_id() or (request.state.trace_id if hasattr(request.state, 'trace_id') else None)
    
    # 2. Actualizar RID y TraceID en la excepción
    exc.rid = rid
    if trace_id:
        exc.trace_id = trace_id
    
    # 3. Log estructurado del error (CON todos los campos internos)
    logger.bind(
        rid=rid,
        trace_id=trace_id,
        error_code=exc.code,
        http_code=exc.http_code,
        service_code=exc.service_code,
        layer_code=exc.layer_code,
        error_number=exc.error_number,
        path=str(request.url),
        method=request.method,
        details=exc.details  # Details en logs, NO en response
    ).error(f"[{exc.code}] {exc.message}")
    
    # 4. Retornar respuesta JSON mínima al cliente (rid, code, message)
    return JSONResponse(
        status_code=exc.http_code,
        content=exc.to_dict(include_internal_fields=False)
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handler para errores de validación de Pydantic (400).
    
    Args:
        request: Request de FastAPI
        exc: Error de validación de Pydantic
        
    Returns:
        JSONResponse con formato estándar
    """
    # 1. Obtener RID y TraceID
    rid = get_current_rid() or (request.state.rid if hasattr(request.state, 'rid') else 'unknown')
    trace_id = get_current_trace_id() or (request.state.trace_id if hasattr(request.state, 'trace_id') else None)
    
    # 2. Extraer detalles de los errores de validación
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    # 3. Log del error (CON detalles técnicos)
    logger.bind(
        rid=rid,
        trace_id=trace_id,
        path=str(request.url),
        method=request.method,
        validation_errors=errors  # En logs, NO en response
    ).warning("Validation error in request")
    
    # 4. Construir respuesta mínima para el cliente
    error_response = {
        "rid": rid,
        "code": 999400,
        "message": "Error de validación en la solicitud"
    }
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handler para errores de SQLAlchemy (base de datos) (500).
    
    Args:
        request: Request de FastAPI
        exc: Error de SQLAlchemy
        
    Returns:
        JSONResponse con formato estándar (sin exponer detalles de DB)
    """
    # 1. Obtener RID y TraceID
    rid = get_current_rid() or (request.state.rid if hasattr(request.state, 'rid') else 'unknown')
    trace_id = get_current_trace_id() or (request.state.trace_id if hasattr(request.state, 'trace_id') else None)
    
    # 2. Log del error (CON detalles técnicos)
    logger.bind(
        rid=rid,
        trace_id=trace_id,
        path=str(request.url),
        method=request.method,
        error_type=type(exc).__name__,
        db_error=str(exc)  # En logs, NO en response
    ).error(f"Database error: {str(exc)}")
    
    # 3. Construir respuesta mínima (sin exponer detalles de DB)
    error_response = {
        "rid": rid,
        "code": 999500,
        "message": "Error interno del servidor"
    }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler genérico para todas las excepciones no capturadas (500).
    
    Args:
        request: Request de FastAPI
        exc: Excepción no controlada
        
    Returns:
        JSONResponse con formato estándar
    """
    # 1. Obtener RID y TraceID
    rid = get_current_rid() or (request.state.rid if hasattr(request.state, 'rid') else 'unknown')
    trace_id = get_current_trace_id() or (request.state.trace_id if hasattr(request.state, 'trace_id') else None)
    
    # 2. Log crítico del error (CON detalles técnicos)
    logger.bind(
        rid=rid,
        trace_id=trace_id,
        path=str(request.url),
        method=request.method,
        error_type=type(exc).__name__,
        error_message=str(exc),
        traceback=True  # En logs, NO en response
    ).critical(f"Unhandled exception: {type(exc).__name__}: {str(exc)}")
    
    # 3. Construir respuesta mínima para el cliente
    error_response = {
        "rid": rid,
        "code": 999999,
        "message": "Error interno del servidor"
    }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


def register_exception_handlers(app) -> None:
    """
    Registra todos los exception handlers en la aplicación FastAPI.
    
    Args:
        app: Instancia de FastAPI
    """
    app.add_exception_handler(BaseAPIException, base_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers registered successfully")
