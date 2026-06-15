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
        # Acepta códigos legacy 10XXXXXX y nuevos 9-dígitos 12XXXXXXX (Application layer)
        if not ((10000000 <= code <= 10999999) or (120000000 <= code <= 129999999)):
            raise ValueError(f"Application exception code must be in range 10000000-10999999 or 120000000-129999999, got: {code}")
        
        super().__init__(code, message, http_code, **kwargs)