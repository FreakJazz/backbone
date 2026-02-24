"""
Security layer exceptions - Códigos 14XXXXXX
"""
from typing import Dict, Any, Optional, List
from ...domain.exceptions.base_kernel_exception import BaseKernelException


class SecurityException(BaseKernelException):
    """
    Excepción base para la capa de seguridad.
    
    Códigos: 14XXXXXX
    HTTP por defecto: 401 (Unauthorized)
    
    Uso:
    - Errores de autenticación
    - Errores de autorización
    - Errores de tokens
    - Errores de seguridad en general
    """
    
    def __init__(
        self, 
        code: int, 
        message: str, 
        http_code: int = 401,
        **kwargs
    ):
        # Validar que el código pertenezca a la capa de seguridad
        if not (14000000 <= code <= 14999999):
            raise ValueError(f"Security exception code must be in range 14000000-14999999, got: {code}")
        
        super().__init__(code, message, http_code, **kwargs)


class AuthenticationException(SecurityException):
    """
    Excepción para errores de autenticación.
    
    Ejemplos:
    - Credenciales inválidas
    - Token expirado
    - Token inválido
    """
    
    def __init__(
        self,
        message: str,
        authentication_method: str = None,
        code: int = 14001001,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if authentication_method:
            details.update({"authentication_method": authentication_method})
        kwargs['details'] = details
        
        super().__init__(code, message, **kwargs)


class AuthorizationSecurityException(SecurityException):
    """
    Excepción para errores de autorización de seguridad.
    
    Diferente a las de aplicación - estas son a nivel de seguridad.
    """
    
    def __init__(
        self,
        message: str,
        required_role: str = None,
        user_roles: List[str] = None,
        code: int = 14002001,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            "required_role": required_role,
            "user_roles": user_roles
        })
        kwargs['details'] = details
        
        super().__init__(code, message, http_code=403, **kwargs)


class TokenException(SecurityException):
    """
    Excepción para errores de tokens.
    """
    
    def __init__(
        self,
        message: str,
        token_type: str = None,
        code: int = 14003001,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if token_type:
            details.update({"token_type": token_type})
        kwargs['details'] = details
        
        super().__init__(code, message, **kwargs)


# Catálogo de códigos de seguridad
class SecurityErrorCodes:
    """Códigos de error específicos de seguridad 14XXXXXX"""
    
    # Authentication (14001XXX)
    AUTHENTICATION_ERROR = 14001001
    INVALID_CREDENTIALS = 14001002
    USER_NOT_FOUND = 14001003
    INCORRECT_PASSWORD = 14001004
    
    # Authorization (14002XXX)
    AUTHORIZATION_ERROR = 14002001
    INSUFFICIENT_PRIVILEGES = 14002002
    ROLE_NOT_ASSIGNED = 14002003
    
    # Token (14003XXX)
    TOKEN_ERROR = 14003001
    TOKEN_EXPIRED = 14003002
    TOKEN_INVALID = 14003003
    TOKEN_MISSING = 14003004
    REFRESH_TOKEN_INVALID = 14003005