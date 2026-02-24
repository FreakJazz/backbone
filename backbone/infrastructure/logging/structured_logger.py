"""
Structured Logger - Logger abstracto y desacoplado
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime
import json


class LogLevel(str, Enum):
    """Niveles de log estándar."""
    DEBUG = "debug"
    INFO = "info" 
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogEntry:
    """
    Entrada de log estructurada.
    
    Contiene toda la información necesaria para generar logs
    consistentes y estructurados.
    """
    
    def __init__(
        self,
        level: LogLevel,
        message: str,
        timestamp: datetime = None,
        context: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        rid: Optional[str] = None,
        trace_id: Optional[str] = None,
        service_name: Optional[str] = None,
        layer: Optional[str] = None,
        component: Optional[str] = None
    ):
        self.level = level
        self.message = message
        self.timestamp = timestamp or datetime.utcnow()
        self.context = context or {}
        self.extra = extra or {}
        self.exception = exception
        self.rid = rid
        self.trace_id = trace_id
        self.service_name = service_name
        self.layer = layer
        self.component = component
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la entrada a diccionario para serialización."""
        data = {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "message": self.message,
            "context": self.context,
            "extra": self.extra
        }
        
        # Campos opcionales
        if self.rid:
            data["rid"] = self.rid
        if self.trace_id:
            data["trace_id"] = self.trace_id
        if self.service_name:
            data["service"] = self.service_name
        if self.layer:
            data["layer"] = self.layer
        if self.component:
            data["component"] = self.component
            
        # Información de excepción
        if self.exception:
            data["exception"] = {
                "type": self.exception.__class__.__name__,
                "message": str(self.exception),
                "details": getattr(self.exception, "details", {})
            }
        
        return data
    
    def to_json(self) -> str:
        """Convierte a JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


class StructuredLogger(ABC):
    """
    Logger abstracto estructurado y desacoplado.
    
    Características:
    - Sin dependencia de librerías específicas (loguru, logging, etc.)
    - Logs estructurados JSON para ELK
    - Context enriquecido automáticamente
    - RID y trace_id automáticos
    - Configuración por entorno
    """
    
    def __init__(
        self,
        service_name: str,
        component: str = None,
        layer: str = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.service_name = service_name
        self.component = component
        self.layer = layer
        self.base_context = context or {}
    
    @abstractmethod
    def write_log(self, entry: LogEntry) -> None:
        """
        Escribe la entrada de log.
        
        Implementación específica en adaptadores concretos:
        - LoguruAdapter
        - StandardLoggingAdapter
        - ConsoleAdapter
        """
        pass
    
    def _create_entry(
        self,
        level: LogLevel,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        rid: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> LogEntry:
        """Crea una entrada de log con contexto enriquecido."""
        # Combinar contextos
        full_context = {**self.base_context}
        if context:
            full_context.update(context)
        
        # Handle both extra and extra_data for backward compatibility
        extra_info = extra or extra_data
        
        return LogEntry(
            level=level,
            message=message,
            context=full_context,
            extra=extra_info,
            exception=exception,
            rid=rid,
            trace_id=trace_id,
            service_name=self.service_name,
            layer=self.layer,
            component=self.component
        )
    
    def debug(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Log nivel DEBUG."""
        entry = self._create_entry(LogLevel.DEBUG, message, context, **kwargs)
        self.write_log(entry)
    
    def info(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Log nivel INFO."""
        entry = self._create_entry(LogLevel.INFO, message, context, **kwargs)
        self.write_log(entry)
    
    def warning(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Log nivel WARNING."""
        entry = self._create_entry(LogLevel.WARNING, message, context, **kwargs)
        self.write_log(entry)
    
    def error(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """Log nivel ERROR."""
        entry = self._create_entry(
            LogLevel.ERROR, 
            message, 
            context, 
            exception=exception, 
            **kwargs
        )
        self.write_log(entry)
    
    def critical(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """Log nivel CRITICAL."""
        entry = self._create_entry(
            LogLevel.CRITICAL, 
            message, 
            context, 
            exception=exception, 
            **kwargs
        )
        self.write_log(entry)
    
    def exception(
        self,
        message: str,
        exc: Exception,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Log de excepción (nivel ERROR)."""
        self.error(message, context=context, exception=exc, **kwargs)
    
    def log_kernel_exception(self, exception) -> None:
        """
        Log especializado para excepciones del kernel backbone.
        
        Extrae automáticamente información relevante de BaseKernelException.
        """
        # Import aquí para evitar circular imports
        from ...domain.exceptions.base_kernel_exception import BaseKernelException
        
        if isinstance(exception, BaseKernelException):
            context = exception.to_log_format()
            self.error(
                message=f"[{exception.code}] {exception.message}",
                context=context,
                exception=exception,
                rid=exception.rid
            )
        else:
            # Fallback para otras excepciones
            self.exception("Unhandled exception", exception)


class LoggerBuilder:
    """
    Builder para crear loggers estructurados de manera fluida.
    """
    
    def __init__(self):
        self._service_name = None
        self._component = None
        self._layer = None
        self._context = {}
        self._logger_class = None
    
    def service(self, name: str) -> 'LoggerBuilder':
        """Establece el nombre del servicio."""
        self._service_name = name
        return self
    
    def component(self, name: str) -> 'LoggerBuilder':
        """Establece el componente."""
        self._component = name
        return self
    
    def layer(self, name: str) -> 'LoggerBuilder':
        """Establece la capa arquitectónica."""
        self._layer = name
        return self
    
    def context(self, context: Dict[str, Any]) -> 'LoggerBuilder':
        """Establece el contexto base."""
        self._context.update(context)
        return self
    
    def implementation(self, logger_class: type) -> 'LoggerBuilder':
        """Establece la implementación concreta del logger."""
        self._logger_class = logger_class
        return self
    
    def build(self) -> StructuredLogger:
        """Construye el logger."""
        if not self._service_name:
            raise ValueError("Service name is required")
        if not self._logger_class:
            raise ValueError("Logger implementation class is required")
        
        return self._logger_class(
            service_name=self._service_name,
            component=self._component,
            layer=self._layer,
            context=self._context
        )