"""
Structured Logger - Logger abstracto y desacoplado
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime
import json


class LogLevel(str, Enum):
    """Niveles de log estándar."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEntry:
    """
    Entrada de log estructurada.

    Contrato JSON unificado (mismo shape que backbone-go):
    {
        "timestamp": "2024-01-01T12:00:00.000Z",
        "level": "INFO",
        "service": "my-service",
        "component": "UserHandler",
        "layer": "interfaces",
        "method": "create_user",
        "message": "User created",
        "request_id": "uuid",
        "trace_id": "uuid",
        "user_id": "uuid",
        "environment": "development",
        "extra_data": {},
        "context": {},
        "error": {
            "type": "ValidationError",
            "message": "...",
            "code": 40001,
            "stack_trace": "..."
        }
    }
    """

    def __init__(
        self,
        level: LogLevel,
        message: str,
        timestamp: datetime = None,
        context: Optional[Dict[str, Any]] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        user_id: Optional[str] = None,
        service_name: Optional[str] = None,
        layer: Optional[str] = None,
        component: Optional[str] = None,
        method: Optional[str] = None,
        environment: Optional[str] = None,
        error_code: Optional[int] = None,
    ):
        self.level = level
        self.message = message
        self.timestamp = timestamp or datetime.utcnow()
        self.context = context or {}
        self.extra_data = extra_data or {}
        self.exception = exception
        self.request_id = request_id
        self.trace_id = trace_id
        self.user_id = user_id
        self.service_name = service_name
        self.layer = layer
        self.component = component
        self.method = method
        self.environment = environment
        self.error_code = error_code

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "timestamp": self.timestamp.isoformat() + "Z",
            "level": self.level.value,
            "message": self.message,
        }

        if self.service_name:
            data["service"] = self.service_name
        if self.component:
            data["component"] = self.component
        if self.layer:
            data["layer"] = self.layer
        if self.method:
            data["method"] = self.method
        if self.request_id:
            data["request_id"] = self.request_id
        if self.trace_id:
            data["trace_id"] = self.trace_id
        if self.user_id:
            data["user_id"] = self.user_id
        if self.environment:
            data["environment"] = self.environment
        if self.extra_data:
            data["extra_data"] = self.extra_data
        if self.context:
            data["context"] = self.context

        if self.exception:
            import traceback as tb
            error: Dict[str, Any] = {
                "type": self.exception.__class__.__name__,
                "message": str(self.exception),
            }
            if self.error_code is not None:
                error["code"] = self.error_code
            elif hasattr(self.exception, "code"):
                error["code"] = self.exception.code
            stack = tb.format_exception(
                type(self.exception), self.exception, self.exception.__traceback__
            )
            if stack:
                error["stack_trace"] = "".join(stack)
            details = getattr(self.exception, "details", None)
            if details:
                error["details"] = details
            data["error"] = error

        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


class StructuredLogger(ABC):
    """
    Logger abstracto estructurado y desacoplado.

    - Sin dependencia de librerías específicas
    - Logs JSON estructurados (mismo shape en Python y Go)
    - Contexto enriquecido automáticamente desde LogContext
    """

    def __init__(
        self,
        service_name: str,
        component: str = None,
        layer: str = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.service_name = service_name
        self.component = component
        self.layer = layer
        self.base_context = context or {}

    @abstractmethod
    def write_log(self, entry: LogEntry) -> None:
        pass

    def _create_entry(
        self,
        level: LogLevel,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        user_id: Optional[str] = None,
        method: Optional[str] = None,
        error_code: Optional[int] = None,
        # backward-compat aliases
        extra: Optional[Dict[str, Any]] = None,
        rid: Optional[str] = None,
    ) -> LogEntry:
        full_context = {**self.base_context}
        if context:
            full_context.update(context)

        env = full_context.pop("environment", None)

        return LogEntry(
            level=level,
            message=message,
            context=full_context,
            extra_data=extra_data or extra,
            exception=exception,
            request_id=request_id or rid,
            trace_id=trace_id,
            user_id=user_id,
            service_name=self.service_name,
            layer=self.layer,
            component=self.component,
            method=method,
            environment=env,
            error_code=error_code,
        )

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        entry = self._create_entry(LogLevel.DEBUG, message, context, **kwargs)
        self.write_log(entry)

    def info(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        entry = self._create_entry(LogLevel.INFO, message, context, **kwargs)
        self.write_log(entry)

    def warning(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        entry = self._create_entry(LogLevel.WARNING, message, context, **kwargs)
        self.write_log(entry)

    def error(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        **kwargs,
    ) -> None:
        entry = self._create_entry(LogLevel.ERROR, message, context, exception=exception, **kwargs)
        self.write_log(entry)

    def critical(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        **kwargs,
    ) -> None:
        entry = self._create_entry(LogLevel.CRITICAL, message, context, exception=exception, **kwargs)
        self.write_log(entry)

    def exception(self, message: str, exc: Exception, context: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        self.error(message, context=context, exception=exc, **kwargs)

    def log_kernel_exception(self, exception) -> None:
        from ...domain.exceptions.base_kernel_exception import BaseKernelException

        if isinstance(exception, BaseKernelException):
            context = exception.to_log_format()
            self.error(
                message=f"[{exception.code}] {exception.message}",
                context=context,
                exception=exception,
                request_id=exception.rid,
                error_code=exception.code,
            )
        else:
            self.exception("Unhandled exception", exception)


class LoggerBuilder:
    """Builder fluido para crear loggers."""

    def __init__(self):
        self._service_name = None
        self._component = None
        self._layer = None
        self._context = {}
        self._logger_class = None

    def service(self, name: str) -> "LoggerBuilder":
        self._service_name = name
        return self

    def component(self, name: str) -> "LoggerBuilder":
        self._component = name
        return self

    def layer(self, name: str) -> "LoggerBuilder":
        self._layer = name
        return self

    def context(self, context: Dict[str, Any]) -> "LoggerBuilder":
        self._context.update(context)
        return self

    def implementation(self, logger_class: type) -> "LoggerBuilder":
        self._logger_class = logger_class
        return self

    def build(self) -> StructuredLogger:
        if not self._service_name:
            raise ValueError("Service name is required")
        if not self._logger_class:
            raise ValueError("Logger implementation class is required")

        return self._logger_class(
            service_name=self._service_name,
            component=self._component,
            layer=self._layer,
            context=self._context,
        )
