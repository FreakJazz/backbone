"""
Base Kernel Exception - Excepción base para todo el sistema backbone
"""
import uuid
from typing import Dict, Any, Optional
from datetime import datetime


class BaseKernelException(Exception):
    """
    Excepción base del kernel backbone.
    
    Características:
    - Códigos de error de 8 dígitos: CCLLLLLL
      - CC: Código de capa (10=Application, 11=Domain, 12=Infrastructure, 13=Presentation, 14=Security)  
      - LLLLLL: Código específico de la capa
    - RID automático para trazabilidad
    - Contrato de error estándar
    - Logging estructurado
    - Sin dependencias externas
    
    Ejemplo de uso:
        raise ApplicationException(10001001, "Usuario no encontrado")
    """
    
    def __init__(
        self,
        code: int,
        message: str,
        http_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        rid: Optional[str] = None,
        internal_data: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa una excepción del kernel.
        
        Args:
            code: Código de error de 8 dígitos (CCLLLLLL)
            message: Mensaje para el usuario final
            http_code: Código HTTP (400, 401, 404, 422, 500, etc.)
            details: Información adicional (NO se envía al cliente)
            rid: Request ID para trazabilidad (se genera si no se provee)
            internal_data: Datos internos para debugging (solo logs)
        """
        self.code = code
        self.message = message
        self.http_code = http_code
        self.details = details or {}
        self.rid = rid or self._generate_rid()
        self.internal_data = internal_data or {}
        self.timestamp = datetime.utcnow().isoformat()
        
        # Validar código de 8 dígitos
        if not (10000000 <= code <= 99999999):
            raise ValueError(f"Error code must be 8 digits, got: {code}")
        
        super().__init__(message)
    
    @staticmethod
    def _generate_rid() -> str:
        """Genera un Request ID único para trazabilidad."""
        return uuid.uuid4().hex
    
    def to_error_contract(self) -> Dict[str, Any]:
        """
        Convierte a formato de contrato de error estándar.
        
        SOLO campos públicos para el cliente:
        {
            "rid": "string",
            "code": 10001001,
            "message": "string"
        }
        
        Returns:
            Dict con el contrato de error mínimo
        """
        return {
            "rid": self.rid,
            "code": self.code,
            "message": self.message
        }
    
    def to_log_format(self) -> Dict[str, Any]:
        """
        Convierte a formato completo para logging.
        
        Incluye TODOS los campos para análisis interno:
        - Campo públicos (rid, code, message)
        - Campos internos (httpCode, timestamp, details, internal_data)
        - Metadata de la excepción
        
        Returns:
            Dict con información completa para logs
        """
        return {
            # Campos públicos
            "rid": self.rid,
            "code": self.code, 
            "message": self.message,
            
            # Campos internos (solo para logs)
            "httpCode": self.http_code,
            "timestamp": self.timestamp,
            "layer_code": self.layer_code,
            "layer_name": self.layer_name,
            "details": self.details,
            "internal_data": self.internal_data,
            "exception_type": self.__class__.__name__
        }
    
    @property
    def layer_code(self) -> int:
        """Extrae el código de capa (primeros 2 dígitos)."""
        return self.code // 1000000
    
    @property 
    def layer_name(self) -> str:
        """Nombre de la capa basado en el código."""
        layer_map = {
            10: "Application",
            11: "Domain", 
            12: "Infrastructure",
            13: "Presentation",
            14: "Security"
        }
        return layer_map.get(self.layer_code, "Unknown")
    
    @property
    def specific_code(self) -> int:
        """Extrae el código específico de la capa (últimos 6 dígitos)."""
        return self.code % 1000000
    
    def __str__(self) -> str:
        """Representación string para debugging."""
        return f"[{self.code}] {self.message} (RID: {self.rid})"
    
    def __repr__(self) -> str:
        """Representación detallada para debugging."""
        return (
            f"{self.__class__.__name__}("
            f"code={self.code}, "
            f"message='{self.message}', "
            f"http_code={self.http_code}, "
            f"rid='{self.rid}'"
            f")"
        )