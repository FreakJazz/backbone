"""
Log Formatters - Formateadores para diferentes salidas
"""
import json
import sys
from typing import TextIO
from .structured_logger import LogEntry, LogLevel


class BaseFormatter:
    def format(self, entry: LogEntry) -> str:
        raise NotImplementedError


class JSONFormatter(BaseFormatter):
    """
    Formateador JSON completo para ELK Stack / Elasticsearch / Kibana.
    Emite el mismo shape que backbone-go.
    """

    def __init__(self, include_traceback: bool = True):
        self.include_traceback = include_traceback

    def format(self, entry: LogEntry) -> str:
        return entry.to_json()


class ConsoleFormatter(BaseFormatter):
    """
    Formateador legible para consola en desarrollo, con colores opcionales.
    Formato: [HH:MM:SS.mmm] LEVEL | service.component | request_id | message | ctx...
    """

    COLORS = {
        LogLevel.DEBUG: "\033[36m",
        LogLevel.INFO: "\033[32m",
        LogLevel.WARNING: "\033[33m",
        LogLevel.ERROR: "\033[31m",
        LogLevel.CRITICAL: "\033[35m",
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def __init__(self, use_colors: bool = None, include_context: bool = True):
        if use_colors is None:
            use_colors = (
                hasattr(sys.stdout, "isatty")
                and sys.stdout.isatty()
                and sys.platform != "win32"
            )
        self.use_colors = use_colors
        self.include_context = include_context

    def format(self, entry: LogEntry) -> str:
        level_str = entry.level.value
        if self.use_colors:
            color = self.COLORS.get(entry.level, "")
            level_str = f"{color}{self.BOLD}{level_str:<8}{self.RESET}"
        else:
            level_str = f"{level_str:<8}"

        timestamp = entry.timestamp.strftime("%H:%M:%S.%f")[:-3]

        service_info = entry.service_name or "unknown"
        if entry.component:
            service_info = f"{service_info}.{entry.component}"

        tracking = ""
        if entry.request_id:
            tracking = f" | {entry.request_id[:8]}"
        if entry.trace_id:
            tracking += f" | trace:{entry.trace_id[:8]}"

        base_msg = f"[{timestamp}] {level_str} | {service_info:<20}{tracking} | {entry.message}"

        if self.include_context and (entry.context or entry.extra_data):
            items = []
            skip = {"request_id", "trace_id", "service", "component"}
            for key, value in (entry.context or {}).items():
                if key not in skip:
                    items.append(f"{key}={value}")
            for key, value in (entry.extra_data or {}).items():
                items.append(f"{key}={value}")
            if items:
                base_msg += " | " + " ".join(items[:3])

        if entry.exception:
            base_msg += f" | {entry.exception.__class__.__name__}: {entry.exception}"

        return base_msg


class CompactJSONFormatter(BaseFormatter):
    """
    JSON compacto para producción — omite campos vacíos, usa keys cortas.
    """

    def format(self, entry: LogEntry) -> str:
        data = {
            "ts": entry.timestamp.isoformat() + "Z",
            "lvl": entry.level.value,
            "msg": entry.message,
        }

        if entry.request_id:
            data["rid"] = entry.request_id
        if entry.trace_id:
            data["trace"] = entry.trace_id
        if entry.user_id:
            data["uid"] = entry.user_id
        if entry.service_name:
            data["svc"] = entry.service_name
        if entry.component:
            data["comp"] = entry.component
        if entry.layer:
            data["layer"] = entry.layer
        if entry.environment:
            data["env"] = entry.environment

        skip = {"request_id", "trace_id", "user_id", "service", "component", "layer"}
        important_ctx = {k: v for k, v in (entry.context or {}).items() if k not in skip}
        if important_ctx:
            data["ctx"] = important_ctx

        if entry.extra_data:
            data["extra"] = entry.extra_data

        if entry.exception:
            data["err"] = {
                "type": entry.exception.__class__.__name__,
                "msg": str(entry.exception),
            }
            if entry.error_code:
                data["err"]["code"] = entry.error_code

        return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


class FileFormatter(BaseFormatter):
    """
    Formateador para archivos de log — legible y detallado.
    """

    def format(self, entry: LogEntry) -> str:
        timestamp = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level_str = f"[{entry.level.value:<8}]"

        service_info = entry.service_name or "unknown"
        if entry.component:
            service_info += f".{entry.component}"
        if entry.layer:
            service_info += f"({entry.layer})"

        header = f"{timestamp} {level_str} {service_info}"
        if entry.request_id:
            header += f" [{entry.request_id}]"

        lines = [f"{header} - {entry.message}"]

        if entry.context or entry.extra_data:
            combined = {**(entry.context or {}), **(entry.extra_data or {})}
            for key, value in combined.items():
                lines.append(f"    {key}: {value}")

        if entry.exception:
            lines.append(
                f"    Exception: {entry.exception.__class__.__name__}: {entry.exception}"
            )
            details = getattr(entry.exception, "details", None)
            if details:
                lines.append(f"    Details: {details}")

        return "\n".join(lines)
