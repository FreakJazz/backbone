"""
Log Formatters - Formateadores para diferentes salidas
"""
import json
import sys
from datetime import datetime
from typing import Dict, Any, TextIO
from .structured_logger import LogEntry, LogLevel


class BaseFormatter:
    """Formateador base para logs."""
    
    def format(self, entry: LogEntry) -> str:
        """
        Formatea una entrada de log.
        
        Args:
            entry: Entrada de log a formatear
            
        Returns:
            String formateado
        """
        raise NotImplementedError


class JSONFormatter(BaseFormatter):
    """
    Formateador JSON para ELK Stack.
    
    Genera logs en formato JSON estructurado, optimizado para:
    - Elasticsearch
    - Logstash
    - Kibana
    - Fluentd
    - Otros sistemas de análisis de logs
    """
    
    def __init__(self, include_traceback: bool = True):
        self.include_traceback = include_traceback
    
    def format(self, entry: LogEntry) -> str:
        """
        Formatea entrada como JSON.
        
        Args:
            entry: Entrada de log
            
        Returns:
            JSON string con toda la información estructurada
        """
        data = entry.to_dict()
        
        # Agregar información de traceback para errores
        if (entry.exception and 
            self.include_traceback and 
            entry.level in (LogLevel.ERROR, LogLevel.CRITICAL)):
            
            import traceback
            data["exception"]["traceback"] = traceback.format_exception(
                type(entry.exception),
                entry.exception,
                entry.exception.__traceback__
            )
        
        return json.dumps(data, ensure_ascii=False, default=str)


class ConsoleFormatter(BaseFormatter):
    """
    Formateador para consola con colores (desarrollo).
    
    Genera logs legibles para desarrollo local con:
    - Colores por nivel
    - Formato compacto
    - Información contextual relevante
    """
    
    # Códigos ANSI para colores
    COLORS = {
        LogLevel.DEBUG: "\033[36m",     # Cyan
        LogLevel.INFO: "\033[32m",      # Green
        LogLevel.WARNING: "\033[33m",   # Yellow
        LogLevel.ERROR: "\033[31m",     # Red
        LogLevel.CRITICAL: "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    def __init__(self, use_colors: bool = None, include_context: bool = True):
        # Detectar si soporta colores automáticamente
        if use_colors is None:
            use_colors = (
                hasattr(sys.stdout, 'isatty') and 
                sys.stdout.isatty() and 
                sys.platform != 'win32'  # Windows console support varies
            )
        
        self.use_colors = use_colors
        self.include_context = include_context
    
    def format(self, entry: LogEntry) -> str:
        """
        Formatea entrada para consola.
        
        Formato: [TIMESTAMP] LEVEL | SERVICE.COMPONENT | RID | MESSAGE | CONTEXT
        
        Args:
            entry: Entrada de log
            
        Returns:
            String formateado para consola
        """
        # Color para el nivel
        level_str = entry.level.value.upper()
        if self.use_colors:
            color = self.COLORS.get(entry.level, "")
            level_str = f"{color}{self.BOLD}{level_str:<8}{self.RESET}"
        else:
            level_str = f"{level_str:<8}"
        
        # Timestamp
        timestamp = entry.timestamp.strftime("%H:%M:%S.%f")[:-3]
        
        # Service/Component
        service_info = entry.service_name or "unknown"
        if entry.component:
            service_info = f"{service_info}.{entry.component}"
        
        # RID/Trace
        tracking_info = ""
        if entry.rid:
            tracking_info = f" | {entry.rid[:8]}"
        if entry.trace_id:
            tracking_info += f" | trace:{entry.trace_id[:8]}"
        
        # Mensaje base
        base_msg = f"[{timestamp}] {level_str} | {service_info:<20}{tracking_info} | {entry.message}"
        
        # Contexto adicional
        if self.include_context and (entry.context or entry.extra):
            context_items = []
            
            # Contexto importante primero
            if entry.context:
                for key, value in entry.context.items():
                    if key not in ("rid", "trace_id", "service", "component"):
                        context_items.append(f"{key}={value}")
            
            # Extra data
            if entry.extra:
                for key, value in entry.extra.items():
                    context_items.append(f"{key}={value}")
            
            if context_items:
                context_str = " | " + " ".join(context_items[:3])  # Limitar a 3 items
                base_msg += context_str
        
        # Información de excepción
        if entry.exception:
            base_msg += f" | Exception: {entry.exception.__class__.__name__}: {str(entry.exception)}"
        
        return base_msg


class CompactJSONFormatter(JSONFormatter):
    """
    Formateador JSON compacto para producción.
    
    Similar al JSONFormatter pero omite campos opcionales para reducir
    el tamaño de logs en producción.
    """
    
    def format(self, entry: LogEntry) -> str:
        """
        Formatea como JSON compacto.
        
        Omite campos vacíos y reduce información no crítica.
        """
        data = {
            "ts": entry.timestamp.isoformat(),
            "level": entry.level.value,
            "msg": entry.message,
        }
        
        # Solo agregar campos que tienen valor
        if entry.rid:
            data["rid"] = entry.rid
        if entry.trace_id:
            data["trace"] = entry.trace_id
        if entry.service_name:
            data["svc"] = entry.service_name
        if entry.component:
            data["comp"] = entry.component
        if entry.layer:
            data["layer"] = entry.layer
        
        # Contexto solo si hay información importante
        important_context = {}
        for key, value in (entry.context or {}).items():
            if key not in ("rid", "trace_id", "service", "component", "layer"):
                important_context[key] = value
        
        if important_context:
            data["ctx"] = important_context
        
        if entry.extra:
            data["extra"] = entry.extra
        
        # Excepción
        if entry.exception:
            data["err"] = {
                "type": entry.exception.__class__.__name__,
                "msg": str(entry.exception)
            }
        
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))


class FileFormatter(BaseFormatter):
    """
    Formateador para archivos de log.
    
    Combina legibilidad con información completa.
    """
    
    def format(self, entry: LogEntry) -> str:
        """
        Formatea para archivo de log.
        
        Formato más detallado que consola pero más legible que JSON puro.
        """
        timestamp = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level_str = f"[{entry.level.value.upper():<8}]"
        
        # Header
        header = f"{timestamp} {level_str}"
        
        # Service info
        service_info = entry.service_name or "unknown"
        if entry.component:
            service_info += f".{entry.component}"
        if entry.layer:
            service_info += f"({entry.layer})"
        
        header += f" {service_info}"
        
        # RID
        if entry.rid:
            header += f" [{entry.rid}]"
        
        # Message
        message_line = f"{header} - {entry.message}"
        
        lines = [message_line]
        
        # Context adicional
        if entry.context or entry.extra:
            context_data = {**(entry.context or {}), **(entry.extra or {})}
            for key, value in context_data.items():
                lines.append(f"    {key}: {value}")
        
        # Excepción
        if entry.exception:
            lines.append(f"    Exception: {entry.exception.__class__.__name__}: {str(entry.exception)}")
            if hasattr(entry.exception, 'details') and entry.exception.details:
                lines.append(f"    Details: {entry.exception.details}")
        
        return "\n".join(lines)