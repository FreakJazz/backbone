"""
Base Configuration - Sistema de configuración con Pydantic Settings
"""
from typing import Optional, Dict, Any, List
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, validator
except ImportError:
    try:
        # Fallback for older Pydantic versions
        from pydantic import BaseSettings, Field, validator
    except ImportError:
        # If pydantic-settings is not available, create a mock
        class BaseSettings:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        def Field(**kwargs):
            return None
            
        def validator(*args, **kwargs):
            def decorator(func):
                return func
            return decorator
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
    """
    
    # === Configuración de aplicación ===
    app_name: str = Field(default="Backbone App", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    secret_key: str = Field(env="SECRET_KEY", min_length=32)
    
    # === Configuración de API ===
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    api_port: int = Field(default=8000, env="API_PORT", ge=1, le=65535)
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    # === Configuración de logging ===
    log_level: LogLevel = Field(default=LogLevel.INFO, env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json, text
    log_file_path: Optional[str] = Field(default=None, env="LOG_FILE_PATH")
    
    # === Configuración de base de datos ===
    database_type: DatabaseType = Field(default=DatabaseType.POSTGRESQL, env="DATABASE_TYPE")
    database_url: str = Field(env="DATABASE_URL")
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE", ge=1)
    database_max_overflow: int = Field(default=20, env="DATABASE_MAX_OVERFLOW", ge=0)
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    # === Configuración de Redis (opcional) ===
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    redis_timeout: int = Field(default=10, env="REDIS_TIMEOUT", ge=1)
    
    # === Configuración de seguridad ===
    jwt_secret_key: str = Field(env="JWT_SECRET_KEY", min_length=32)
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=60, env="JWT_EXPIRATION_MINUTES", ge=1)
    
    # === Configuración de observabilidad ===
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    enable_tracing: bool = Field(default=False, env="ENABLE_TRACING")
    metrics_port: int = Field(default=9090, env="METRICS_PORT", ge=1, le=65535)
    
    # === Configuración específica del negocio ===
    max_page_size: int = Field(default=100, env="MAX_PAGE_SIZE", ge=1, le=1000)
    default_page_size: int = Field(default=20, env="DEFAULT_PAGE_SIZE", ge=1)
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT", ge=1)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Para campos sensibles, usar SecretStr en producción
        # secrets_dir = "/run/secrets"  # Para Docker secrets
    
    @validator('debug')
    def debug_should_be_false_in_production(cls, v, values):
        """Debug debe ser False en producción."""
        env = values.get('environment')
        if env == Environment.PRODUCTION and v:
            raise ValueError('Debug should be False in production')
        return v
    
    @validator('cors_origins')
    def cors_origins_validation(cls, v, values):
        """Validar CORS origins."""
        env = values.get('environment')
        if env == Environment.PRODUCTION and "*" in v:
            raise ValueError('CORS origins should not include "*" in production')
        return v
    
    @validator('log_level')
    def log_level_production_validation(cls, v, values):
        """En producción, log level no debe ser DEBUG."""
        env = values.get('environment')
        if env == Environment.PRODUCTION and v == LogLevel.DEBUG:
            return LogLevel.INFO
        return v
    
    @validator('default_page_size')
    def default_page_size_within_max(cls, v, values):
        """Default page size debe ser menor que max page size."""
        max_page_size = values.get('max_page_size', 100)
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
    
    environment: Environment = Environment.TESTING
    debug: bool = True
    database_url: str = "sqlite:///:memory:"  # Base de datos en memoria
    database_echo: bool = False
    log_level: LogLevel = LogLevel.WARNING  # Menos verbose en tests
    
    # Overrides para testing
    jwt_expiration_minutes: int = 5  # Tokens cortos para tests
    max_page_size: int = 10  # Páginas pequeñas para tests
    
    class Config(BaseAppConfig.Config):
        env_file = ".env.test"


class DevelopmentConfig(BaseAppConfig):
    """Configuración específica para desarrollo."""
    
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    log_level: LogLevel = LogLevel.DEBUG
    database_echo: bool = True  # Ver queries SQL en desarrollo
    
    class Config(BaseAppConfig.Config):
        env_file = ".env.dev"


class ProductionConfig(BaseAppConfig):
    """Configuración específica para producción."""
    
    environment: Environment = Environment.PRODUCTION
    debug: bool = False
    log_level: LogLevel = LogLevel.INFO
    cors_origins: List[str] = []  # Debe ser configurado explícitamente
    database_echo: bool = False
    
    class Config(BaseAppConfig.Config):
        env_file = ".env.prod"


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
    current_values = config.dict()
    
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