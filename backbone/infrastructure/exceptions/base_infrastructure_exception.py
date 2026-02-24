"""
Base Infrastructure Exception - Códigos 12XXXXXX
"""
from typing import Dict, Any, Optional
from ...domain.exceptions.base_kernel_exception import BaseKernelException


class InfrastructureException(BaseKernelException):
    """
    Excepción base para la capa de infraestructura.
    
    Códigos: 12XXXXXX
    HTTP por defecto: 500 (Internal Server Error)
    
    Uso:
    - Errores de base de datos
    - Errores de servicios externos
    - Errores de configuración
    - Errores de sistema de archivos
    """
    
    def __init__(
        self, 
        code: int, 
        message: str, 
        http_code: int = 500,
        **kwargs
    ):
        # Validar que el código pertenezca a la capa de infraestructura
        if not (12000000 <= code <= 12999999):
            raise ValueError(f"Infrastructure exception code must be in range 12000000-12999999, got: {code}")
        
        super().__init__(code, message, http_code, **kwargs)