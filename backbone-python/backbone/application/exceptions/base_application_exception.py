"""
Base Application Exception - Códigos 10XXXXXX
"""
from typing import Dict, Any, Optional
from ...domain.exceptions.base_kernel_exception import BaseKernelException


class ApplicationException(BaseKernelException):
    """
    Excepción base para la capa de aplicación.
    
    Códigos: 10XXXXXX
    HTTP por defecto: 422 (Unprocessable Entity)
    
    Uso: 
    - Casos de uso fallidos
    - Validaciones de aplicación
    - Lógica de coordinación
    - Autorización
    """
    
    def __init__(
        self, 
        code: int, 
        message: str, 
        http_code: int = 422,
        **kwargs
    ):
        # Validar que el código pertenezca a la capa de aplicación
        if not (10000000 <= code <= 10999999):
            raise ValueError(f"Application exception code must be in range 10000000-10999999, got: {code}")
        
        super().__init__(code, message, http_code, **kwargs)