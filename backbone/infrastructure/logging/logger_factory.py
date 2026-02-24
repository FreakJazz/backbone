"""
Logger Factory - Factory para crear loggers desacoplados
"""
from typing import Dict, Any, Optional, List, Type, Union
from enum import Enum
from pathlib import Path
import sys
import os
from .structured_logger import StructuredLogger, LogLevel
from .log_context import LogContext
from .formatters import JSONFormatter, ConsoleFormatter, CompactJSONFormatter, FileFormatter


class Environment(str, Enum):
    """Entornos soportados."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogOutput:
    """Configuración de salida de log."""
    
    def __init__(
        self,
        name: str,
        formatter_class: Type,
        target: Union[str, Path, Any],
        level: LogLevel = LogLevel.INFO,
        formatter_config: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.formatter_class = formatter_class
        self.target = target
        self.level = level
        self.formatter_config = formatter_config or {}
        self.formatter = formatter_class(**self.formatter_config)


class LoggerConfig:
    """Configuración completa de logging."""
    
    def __init__(
        self,
        environment: Environment = Environment.DEVELOPMENT,
        service_name: str = "backbone",
        base_level: LogLevel = LogLevel.INFO,
        outputs: Optional[List[LogOutput]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.environment = environment
        self.service_name = service_name
        self.base_level = base_level
        self.outputs = outputs or []
        self.context = context or {}


class ConcreteStructuredLogger(StructuredLogger):
    """
    Implementación concreta del logger estructurado.
    
    Escribe a múltiples salidas con diferentes formateadores.
    """
    
    def __init__(
        self,
        service_name: str,
        outputs: List[LogOutput],
        component: str = None,
        layer: str = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(service_name, component, layer, context)
        self.outputs = outputs
    
    def write_log(self, entry) -> None:
        """
        Escribe log a todas las salidas configuradas.
        
        Args:
            entry: LogEntry a escribir
        """
        # Enriquecer con contexto automático
        context_data = LogContext.get_all_context()
        if context_data:
            entry.context.update(context_data)
            if "rid" in context_data:
                entry.rid = entry.rid or context_data["rid"]
            if "trace_id" in context_data:
                entry.trace_id = entry.trace_id or context_data["trace_id"]
        
        # Escribir a cada salida
        for output in self.outputs:
            # Verificar nivel mínimo
            level_priority = {
                LogLevel.DEBUG: 10,
                LogLevel.INFO: 20,
                LogLevel.WARNING: 30,
                LogLevel.ERROR: 40,
                LogLevel.CRITICAL: 50
            }
            
            if level_priority[entry.level] < level_priority[output.level]:
                continue
            
            # Formatear y escribir
            try:
                formatted_message = output.formatter.format(entry)
                self._write_to_target(formatted_message, output.target)
            except Exception as e:
                # Fallback a stderr si hay error escribiendo
                fallback_msg = f"Logger error: {e}. Original message: {entry.message}\n"
                sys.stderr.write(fallback_msg)
    
    def _write_to_target(self, message: str, target: Any) -> None:
        """
        Escribe mensaje al target específico.
        
        Args:
            message: Mensaje formateado
            target: Target de salida (stdout, stderr, file path, etc.)
        """
        if target == sys.stdout or target == sys.stderr:
            target.write(message + "\n")
            target.flush()
        elif isinstance(target, (str, Path)):
            # Escribir a archivo
            file_path = Path(target)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(message + "\n")
        elif hasattr(target, 'write'):
            # Cualquier objeto file-like
            target.write(message + "\n")
            if hasattr(target, 'flush'):
                target.flush()


class LoggerFactory:
    """
    Factory para crear loggers configurados por entorno.
    
    Características:
    - Configuración automática por entorno
    - Múltiples salidas (consola, archivos, etc.)
    - Formateadores apropiados por salida
    - Context enriquecido automáticamente
    - Sin dependencias de librerías específicas
    """
    
    _default_configs = {
        Environment.DEVELOPMENT: LoggerConfig(
            environment=Environment.DEVELOPMENT,
            base_level=LogLevel.DEBUG,
            outputs=[
                LogOutput(
                    name="console",
                    formatter_class=ConsoleFormatter,
                    target=sys.stdout,
                    level=LogLevel.DEBUG,
                    formatter_config={"use_colors": True, "include_context": True}
                )
            ]
        ),
        Environment.STAGING: LoggerConfig(
            environment=Environment.STAGING,
            base_level=LogLevel.INFO,
            outputs=[
                LogOutput(
                    name="console_json",
                    formatter_class=JSONFormatter,
                    target=sys.stdout,
                    level=LogLevel.INFO
                ),
                LogOutput(
                    name="error_file",
                    formatter_class=FileFormatter,
                    target="logs/errors.log",
                    level=LogLevel.ERROR
                )
            ]
        ),
        Environment.PRODUCTION: LoggerConfig(
            environment=Environment.PRODUCTION,
            base_level=LogLevel.WARNING,
            outputs=[
                LogOutput(
                    name="stdout_json",
                    formatter_class=CompactJSONFormatter,
                    target=sys.stdout,
                    level=LogLevel.INFO
                ),
                LogOutput(
                    name="stderr_errors",
                    formatter_class=CompactJSONFormatter,
                    target=sys.stderr,
                    level=LogLevel.ERROR
                )
            ]
        )
    }
    
    @classmethod
    def create_logger(
        cls,
        service_name: str,
        environment: Union[str, Environment] = Environment.DEVELOPMENT,
        component: str = None,
        layer: str = None,
        context: Optional[Dict[str, Any]] = None,
        config: Optional[LoggerConfig] = None
    ) -> StructuredLogger:
        """
        Crea un logger estructurado configurado.
        
        Args:
            service_name: Nombre del servicio
            environment: Entorno de ejecución
            component: Componente específico
            layer: Capa arquitectónica
            context: Contexto base
            config: Configuración customizada
            
        Returns:
            Logger estructurado configurado
            
        Examples:
            # Logger básico para desarrollo
            logger = LoggerFactory.create_logger("user-service")
            
            # Logger para producción con componente
            logger = LoggerFactory.create_logger(
                service_name="user-service",
                environment="production",
                component="user_repository",
                layer="infrastructure"
            )
            
            # Logger con contexto personalizado
            logger = LoggerFactory.create_logger(
                service_name="auth-service", 
                context={"version": "1.2.3", "region": "us-east-1"}
            )
        """
        # Convertir environment a enum si es string
        if isinstance(environment, str):
            try:
                environment = Environment(environment.lower())
            except ValueError:
                environment = Environment.DEVELOPMENT
        
        # Usar configuración proporcionada o por defecto
        if config is None:
            config = cls._default_configs.get(environment, cls._default_configs[Environment.DEVELOPMENT])
        
        # Establecer service name en config
        config.service_name = service_name
        
        # Combinar contextos
        full_context = {**config.context}
        if context:
            full_context.update(context)
        
        # Agregar información de entorno
        full_context.update({
            "environment": environment.value,
            "hostname": os.getenv("HOSTNAME", "unknown"),
            "pid": os.getpid()
        })
        
        return ConcreteStructuredLogger(
            service_name=service_name,
            outputs=config.outputs,
            component=component,
            layer=layer,
            context=full_context
        )
    
    @classmethod
    def create_for_layer(
        cls,
        service_name: str,
        layer: str,
        component: str = None,
        environment: Union[str, Environment] = Environment.DEVELOPMENT
    ) -> StructuredLogger:
        """
        Shortcut para crear logger específico de una capa arquitectónica.
        
        Args:
            service_name: Nombre del servicio
            layer: Capa (domain, application, infrastructure, interfaces)
            component: Componente específico
            environment: Entorno
            
        Returns:
            Logger configurado para la capa
        """
        return cls.create_logger(
            service_name=service_name,
            environment=environment,
            component=component,
            layer=layer
        )
    
    @classmethod
    def create_custom_config(
        cls,
        environment: Environment,
        service_name: str,
        outputs: List[LogOutput],
        base_level: LogLevel = LogLevel.INFO,
        context: Optional[Dict[str, Any]] = None
    ) -> LoggerConfig:
        """
        Crea una configuración personalizada de logging.
        
        Args:
            environment: Entorno
            service_name: Nombre del servicio
            outputs: Lista de salidas configuradas
            base_level: Nivel base de logging
            context: Contexto base
            
        Returns:
            Configuración personalizada
        """
        return LoggerConfig(
            environment=environment,
            service_name=service_name,
            base_level=base_level,
            outputs=outputs,
            context=context or {}
        )
    
    @classmethod
    def create_elk_ready_logger(
        cls,
        service_name: str,
        environment: Union[str, Environment] = Environment.PRODUCTION,
        log_level: LogLevel = LogLevel.INFO
    ) -> StructuredLogger:
        """
        Crea logger optimizado para ELK Stack.
        
        Args:
            service_name: Nombre del servicio
            environment: Entorno
            log_level: Nivel de logging
            
        Returns:
            Logger optimizado para ELK
        """
        config = LoggerConfig(
            environment=Environment(environment) if isinstance(environment, str) else environment,
            service_name=service_name,
            base_level=log_level,
            outputs=[
                LogOutput(
                    name="elk_stdout",
                    formatter_class=JSONFormatter,
                    target=sys.stdout,
                    level=log_level,
                    formatter_config={"include_traceback": True}
                )
            ]
        )
        
        return cls.create_logger(
            service_name=service_name,
            environment=environment,
            config=config
        )
    
    @classmethod 
    def create_development_logger(
        cls,
        component: str,
        service_name: str = "backbone"
    ) -> StructuredLogger:
        """
        Creates a logger configured for development environment.
        
        Args:
            component: Component name
            service_name: Service name (default: backbone)
            
        Returns:
            Development logger instance
        """
        return cls.create_logger(
            service_name=service_name,
            environment=Environment.DEVELOPMENT,
            component=component
        )
    
    @classmethod
    def create_production_logger(
        cls,
        component: str,
        service_name: str = "backbone"
    ) -> StructuredLogger:
        """
        Creates a logger configured for production environment.
        
        Args:
            component: Component name
            service_name: Service name (default: backbone)
            
        Returns:
            Production logger instance
        """
        return cls.create_logger(
            service_name=service_name,
            environment=Environment.PRODUCTION,
            component=component
        )
    
    @classmethod
    def create_layer_logger(
        cls,
        layer: str,
        component: str = None,
        service_name: str = "backbone"
    ) -> StructuredLogger:
        """
        Creates a logger for a specific architectural layer.
        
        Args:
            layer: Architectural layer name
            component: Component name (optional)
            service_name: Service name (default: backbone)
            
        Returns:
            Layer-specific logger instance
        """
        return cls.create_for_layer(
            service_name=service_name,
            layer=layer,
            component=component
        )