"""
Base Presentation Exception - Códigos 13XXXXXX
"""
from typing import Dict, Any, Optional
from ...domain.exceptions.base_kernel_exception import BaseKernelException


class PresentationException(BaseKernelException):
    """
    Excepción base para la capa de presentación/interfaces.
    
    Códigos: 13XXXXXX  
    HTTP por defecto: 400 (Bad Request)
    
    Uso:
    - Errores de validación de requests
    - Errores de serialización/deserialización
    - Errores de formato HTTP
    - Errores de adaptadores de entrada
    """
    
    def __init__(
        self, 
        code: int, 
        message: str, 
        http_code: int = 400,
        **kwargs
    ):
        # Validar que el código pertenezca a la capa de presentación
        if not (13000000 <= code <= 13999999):
            raise ValueError(f"Presentation exception code must be in range 13000000-13999999, got: {code}")
        
        super().__init__(code, message, http_code, **kwargs)