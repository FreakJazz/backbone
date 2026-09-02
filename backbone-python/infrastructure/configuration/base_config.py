"""
Base Configuration - Sistema de configuración con Pydantic Settings
"""
from typing import Optional, Dict, Any, List
from pydantic import Field, field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum
import os


class LogLevel(str, Enum):
    """Niveles de logging disponibles."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """Ambientes de ejecución."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseType(str, Enum):
    """Tipos de base de datos soportados."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"


class BaseAppConfig(BaseSettings):
    """
    Configuración base de la aplicación.

    Utiliza Pydantic Settings para cargar configuración
    desde variables de entorno, archivos .env, etc.

    No field declares `env=` explicitly — pydantic-settings v2 already maps
    each field to its same-named, case-insensitive environment variable
    (e.g. `app_name` -> `APP_NAME`) by default, which is exactly what every
    field below needs. That default replaced the `env=` kwarg from
    pydantic v1, deprecated since Pydantic 2.0.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # === Configuración de aplicación ===
    app_name: str = Field(default="Backbone App")
    app_version: str = Field(default="1.0.0")
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=True)
    secret_key: str = Field(min_length=32)

    # === Configuración de API ===
    api_prefix: str = Field(default="/api/v1")
    api_port: int = Field(default=8000, ge=1, le=65535)
    api_host: str = Field(default="0.0.0.0")
    cors_origins: List[str] = Field(default=["*"])

    # === Configuración de logging ===
    log_level: LogLevel = Field(default=LogLevel.INFO)
    log_format: str = Field(default="json")  # json, text
    log_file_path: Optional[str] = Field(default=None)

    # === Configuración de base de datos ===
    database_type: DatabaseType = Field(default=DatabaseType.POSTGRESQL)
    database_url: str = Field()
    database_pool_size: int = Field(default=10, ge=1)
    database_max_overflow: int = Field(default=20, ge=0)
    database_echo: bool = Field(default=False)

    # === Configuración de Redis (opcional) ===
    redis_url: Optional[str] = Field(default=None)
    redis_timeout: int = Field(default=10, ge=1)

    # === Configuración de seguridad ===
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_minutes: int = Field(default=60, ge=1)

    # === Configuración de observabilidad ===
    enable_metrics: bool = Field(default=True)
    enable_tracing: bool = Field(default=False)
    metrics_port: int = Field(default=9090, ge=1, le=65535)

    # === Configuración específica del negocio ===
    max_page_size: int = Field(default=100, ge=1, le=1000)
    default_page_size: int = Field(default=20, ge=1)
    request_timeout: int = Field(default=30, ge=1)

    @field_validator("debug")
    @classmethod
    def debug_should_be_false_in_production(cls, v: bool, info: ValidationInfo) -> bool:
        """Debug debe ser False en producción."""
        env = info.data.get("environment")
        if env == Environment.PRODUCTION and v:
            raise ValueError("Debug should be False in production")
        return v

    @field_validator("cors_origins")
    @classmethod
    def cors_origins_validation(cls, v: List[str], info: ValidationInfo) -> List[str]:
        """Validar CORS origins."""
        env = info.data.get("environment")
        if env == Environment.PRODUCTION and "*" in v:
            raise ValueError('CORS origins should not include "*" in production')
        return v

    @field_validator("log_level")
    @classmethod
    def log_level_production_validation(cls, v: LogLevel, info: ValidationInfo) -> LogLevel:
        """En producción, log level no debe ser DEBUG."""
        env = info.data.get("environment")
        if env == Environment.PRODUCTION and v == LogLevel.DEBUG:
            return LogLevel.INFO
        return v

    @field_validator("default_page_size")
    @classmethod
    def default_page_size_within_max(cls, v: int, info: ValidationInfo) -> int:
        """Default page size debe ser menor que max page size."""
        max_page_size = info.data.get("max_page_size", 100)
        if v > max_page_size:
            return max_page_size
        return v

    @property
    def is_development(self) -> bool:
        """Verifica si está en desarrollo."""
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        """Verifica si está en testing."""
        return self.environment == Environment.TESTING

    @property
    def is_production(self) -> bool:
        """Verifica si está en producción."""
        return self.environment == Environment.PRODUCTION

    def get_database_config(self) -> Dict[str, Any]:
        """Obtiene configuración específica de base de datos."""
        config = {
            "url": self.database_url,
            "echo": self.database_echo,
        }

        if self.database_type in [DatabaseType.POSTGRESQL, DatabaseType.MYSQL]:
            config.update({
                "pool_size": self.database_pool_size,
                "max_overflow": self.database_max_overflow,
                "pool_pre_ping": True,
                "pool_recycle": 3600,  # 1 hora
            })

        return config

    def get_logging_config(self) -> Dict[str, Any]:
        """Obtiene configuración de logging estructurado."""
        return {
            "level": self.log_level.value,
            "format": self.log_format,
            "file_path": self.log_file_path,
            "structured": True,
            "include_timestamp": True,
            "include_request_id": True,
        }

    def get_api_config(self) -> Dict[str, Any]:
        """Obtiene configuración de API."""
        return {
            "host": self.api_host,
            "port": self.api_port,
            "prefix": self.api_prefix,
            "cors_origins": self.cors_origins,
            "debug": self.debug,
            "docs_url": "/docs" if not self.is_production else None,
            "redoc_url": "/redoc" if not self.is_production else None,
        }

    def get_security_config(self) -> Dict[str, Any]:
        """Obtiene configuración de seguridad."""
        return {
            "jwt_secret": self.jwt_secret_key,
            "jwt_algorithm": self.jwt_algorithm,
            "jwt_expiration": self.jwt_expiration_minutes,
            "secret_key": self.secret_key,
        }


class TestingConfig(BaseAppConfig):
    """Configuración específica para testing."""

    model_config = SettingsConfigDict(**{**BaseAppConfig.model_config, "env_file": ".env.test"})

    environment: Environment = Environment.TESTING
    debug: bool = True
    database_url: str = "sqlite:///:memory:"  # Base de datos en memoria
    database_echo: bool = False
    log_level: LogLevel = LogLevel.WARNING  # Menos verbose en tests

    # Overrides para testing
    jwt_expiration_minutes: int = 5  # Tokens cortos para tests
    max_page_size: int = 10  # Páginas pequeñas para tests


class DevelopmentConfig(BaseAppConfig):
    """Configuración específica para desarrollo."""

    model_config = SettingsConfigDict(**{**BaseAppConfig.model_config, "env_file": ".env.dev"})

    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    log_level: LogLevel = LogLevel.DEBUG
    database_echo: bool = True  # Ver queries SQL en desarrollo


class ProductionConfig(BaseAppConfig):
    """Configuración específica para producción."""

    model_config = SettingsConfigDict(**{**BaseAppConfig.model_config, "env_file": ".env.prod"})

    environment: Environment = Environment.PRODUCTION
    debug: bool = False
    log_level: LogLevel = LogLevel.INFO
    cors_origins: List[str] = []  # Debe ser configurado explícitamente
    database_echo: bool = False


def get_config_class() -> type[BaseAppConfig]:
    """
    Factory para obtener clase de configuración según el ambiente.

    Returns:
        Clase de configuración apropiada para el ambiente
    """
    env = os.getenv("ENVIRONMENT", "development").lower()

    config_mapping = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "staging": BaseAppConfig,  # Usar config base para staging
        "production": ProductionConfig,
    }

    return config_mapping.get(env, DevelopmentConfig)


def load_config() -> BaseAppConfig:
    """
    Carga configuración según el ambiente.

    Returns:
        Instancia de configuración cargada
    """
    config_class = get_config_class()
    return config_class()


# Global configuration instance
# Can be imported directly: from .base_config import config
# Load config only when needed to avoid validation errors during import
config = None


def get_config():
    """Get global configuration instance, loading if not already loaded"""
    global config
    if config is None:
        try:
            config = load_config()
        except Exception:
            # Create a minimal config for testing/development
            config = DevelopmentConfig(
                secret_key="dev-secret-key-for-testing",
                database_url="sqlite:///test.db",
                jwt_secret_key="dev-jwt-secret"
            )
    return config


# Funciones de utilidad para configuración dinámica

def reload_config() -> BaseAppConfig:
    """Recarga configuración (útil en tests)."""
    global config
    config = load_config()
    return config


def override_config(**overrides) -> BaseAppConfig:
    """
    Crea configuración con overrides temporales.

    Args:
        **overrides: Valores a sobrescribir

    Returns:
        Nueva instancia de configuración
    """
    config_class = get_config_class()

    # Obtener valores actuales
    current_values = config.model_dump()

    # Aplicar overrides
    current_values.update(overrides)

    # Crear nueva instancia
    return config_class(**current_values)


def get_feature_flags() -> Dict[str, bool]:
    """
    Obtiene feature flags desde configuración.

    Busca variables de entorno que empiecen con FEATURE_
    y las convierte en flags booleanos.

    Returns:
        Diccionario con feature flags
    """
    flags = {}

    for key, value in os.environ.items():
        if key.startswith("FEATURE_"):
            flag_name = key[8:].lower()  # Remover FEATURE_ prefix
            flags[flag_name] = value.lower() in ("true", "1", "yes", "on")

    return flags
