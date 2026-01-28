"""
Configuración de logging estructurado con Loguru.
Incluye rotación de archivos, niveles por entorno y formato JSON.
"""
import sys
import json
from pathlib import Path
from loguru import logger
from typing import Optional


class LogConfig:
    """Configuración centralizada de logging."""
    
    # Niveles de log por entorno
    LOG_LEVELS = {
        "development": "DEBUG",
        "staging": "INFO",
        "production": "WARNING"
    }
    
    # Formato para consola (desarrollo)
    CONSOLE_FORMAT = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Formato JSON para archivos (producción)
    JSON_FORMAT = "{message}"
    
    @staticmethod
    def serialize_log(record: dict) -> str:
        """
        Serializa el log en formato JSON.
        
        Args:
            record: Registro de log de Loguru
            
        Returns:
            String JSON con todos los campos del log
        """
        log_data = {
            "timestamp": record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "level": record["level"].name,
            "logger": record["name"],
            "function": record["function"],
            "line": record["line"],
            "message": record["message"],
        }
        
        # Agregar campos extra si existen
        if record["extra"]:
            log_data["extra"] = record["extra"]
        
        # Agregar información de excepción si existe
        if record["exception"]:
            log_data["exception"] = {
                "type": record["exception"].type.__name__,
                "value": str(record["exception"].value),
                "traceback": record["exception"].traceback
            }
        
        return json.dumps(log_data, ensure_ascii=False)
    
    @classmethod
    def configure_logging(
        cls,
        environment: str = "development",
        log_dir: Optional[Path] = None,
        service_name: str = "app"
    ) -> None:
        """
        Configura el sistema de logging.
        
        Args:
            environment: Entorno de ejecución (development, staging, production)
            log_dir: Directorio para guardar logs (None = no guardar archivos)
            service_name: Nombre del servicio para los logs
        """
        # Remover handlers por defecto
        logger.remove()
        
        # Obtener nivel de log según entorno
        log_level = cls.LOG_LEVELS.get(environment, "INFO")
        
        # Handler para consola (siempre activo)
        if environment == "development":
            # En desarrollo: formato colorido y legible
            logger.add(
                sys.stdout,
                format=cls.CONSOLE_FORMAT,
                level=log_level,
                colorize=True,
                backtrace=True,
                diagnose=True
            )
        else:
            # En producción: formato JSON para análisis
            logger.add(
                sys.stdout,
                format=cls.JSON_FORMAT,
                level=log_level,
                serialize=True
            )
        
        # Handlers para archivos (si se especifica directorio)
        if log_dir:
            log_dir = Path(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Archivo de logs general con rotación
            logger.add(
                log_dir / f"{service_name}.log",
                format=cls.JSON_FORMAT,
                level=log_level,
                rotation="100 MB",  # Rotar cuando alcance 100 MB
                retention="30 days",  # Mantener logs por 30 días
                compression="zip",  # Comprimir logs rotados
                serialize=True,
                backtrace=True,
                diagnose=environment == "development"
            )
            
            # Archivo separado para errores
            logger.add(
                log_dir / f"{service_name}_errors.log",
                format=cls.JSON_FORMAT,
                level="ERROR",
                rotation="50 MB",
                retention="90 days",  # Mantener errores por más tiempo
                compression="zip",
                serialize=True,
                backtrace=True,
                diagnose=True
            )
        
        # Configurar contexto global
        logger.configure(
            extra={
                "service": service_name,
                "environment": environment
            }
        )
        
        logger.info(
            f"Logging configured for {service_name}",
            extra={
                "environment": environment,
                "level": log_level,
                "log_dir": str(log_dir) if log_dir else None
            }
        )


# Ejemplo de uso en servicios:
# from shared.logging_config import LogConfig
# LogConfig.configure_logging(
#     environment="development",
#     log_dir=Path("logs"),
#     service_name="auth-service"
# )
