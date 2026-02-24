"""
Log Context - Context manager para enrichir logs automáticamente
"""
from contextvars import ContextVar
from typing import Dict, Any, Optional
from uuid import uuid4


# Context variables para información de request
_rid_context: ContextVar[Optional[str]] = ContextVar('rid', default=None)
_trace_id_context: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
_user_id_context: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
_correlation_id_context: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
_context_data: ContextVar[Dict[str, Any]] = ContextVar('context_data', default={})


class LogContext:
    """
    Context manager para manejar información contextual de logs.
    
    Permite establecer RID, trace_id, user_id y otros datos que se
    incluirán automáticamente en todos los logs dentro del contexto.
    
    Examples:
        # Establecer contexto manualmente
        LogContext.set_rid("abc123")
        LogContext.set_user_id("user-456")
        
        # Usar como context manager
        with LogContext(rid="abc123", user_id="user-456"):
            logger.info("This will include rid and user_id")
        
        # Agregar datos adicionales
        LogContext.add_data("operation", "create_user")
        LogContext.add_data("ip_address", "192.168.1.1")
    """
    
    def __init__(
        self,
        rid: Optional[str] = None,
        trace_id: Optional[str] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        **extra_data
    ):
        self.rid = rid
        self.trace_id = trace_id
        self.user_id = user_id
        self.correlation_id = correlation_id
        self.extra_data = extra_data
        
        # Tokens para restaurar contexto
        self._tokens = []
    
    def __enter__(self):
        """Establece el contexto al entrar."""
        if self.rid is not None:
            self._tokens.append(_rid_context.set(self.rid))
        if self.trace_id is not None:
            self._tokens.append(_trace_id_context.set(self.trace_id))
        if self.user_id is not None:
            self._tokens.append(_user_id_context.set(self.user_id))
        if self.correlation_id is not None:
            self._tokens.append(_correlation_id_context.set(self.correlation_id))
        
        # Agregar datos extra
        if self.extra_data:
            current_data = _context_data.get({})
            new_data = {**current_data, **self.extra_data}
            self._tokens.append(_context_data.set(new_data))
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restaura el contexto al salir."""
        for token in reversed(self._tokens):
            token.var.reset(token)
    
    @staticmethod
    def set_rid(rid: str) -> None:
        """Establece el Request ID en el contexto actual."""
        _rid_context.set(rid)
    
    @staticmethod
    def set_trace_id(trace_id: str) -> None:
        """Establece el Trace ID en el contexto actual."""
        _trace_id_context.set(trace_id)
    
    @staticmethod
    def set_user_id(user_id: str) -> None:
        """Establece el User ID en el contexto actual."""
        _user_id_context.set(user_id)
    
    @staticmethod
    def set_correlation_id(correlation_id: str) -> None:
        """Establece el Correlation ID en el contexto actual."""
        _correlation_id_context.set(correlation_id)
    
    @staticmethod
    def add_data(key: str, value: Any) -> None:
        """Agrega datos al contexto actual."""
        current_data = _context_data.get({})
        new_data = {**current_data, key: value}
        _context_data.set(new_data)
    
    @staticmethod
    def get_rid() -> Optional[str]:
        """Obtiene el Request ID del contexto actual."""
        return _rid_context.get()
    
    @staticmethod
    def get_trace_id() -> Optional[str]:
        """Obtiene el Trace ID del contexto actual."""
        return _trace_id_context.get()
    
    @staticmethod
    def get_user_id() -> Optional[str]:
        """Obtiene el User ID del contexto actual."""
        return _user_id_context.get()
    
    @staticmethod
    def get_correlation_id() -> Optional[str]:
        """Obtiene el Correlation ID del contexto actual."""
        return _correlation_id_context.get()
    
    @staticmethod
    def get_context_data() -> Dict[str, Any]:
        """Obtiene todos los datos del contexto actual."""
        return _context_data.get({})
    
    @staticmethod
    def get_all_context() -> Dict[str, Any]:
        """
        Obtiene todo el contexto actual para incluir en logs.
        
        Returns:
            Dict con toda la información contextual disponible
        """
        context = {}
        
        # Agregar IDs si están disponibles
        rid = LogContext.get_rid()
        if rid:
            context["rid"] = rid
        
        trace_id = LogContext.get_trace_id()
        if trace_id:
            context["trace_id"] = trace_id
        
        user_id = LogContext.get_user_id()
        if user_id:
            context["user_id"] = user_id
        
        correlation_id = LogContext.get_correlation_id()
        if correlation_id:
            context["correlation_id"] = correlation_id
        
        # Agregar datos extra
        context.update(LogContext.get_context_data())
        
        return context
    
    @staticmethod
    def get_current_context() -> Dict[str, Any]:
        """
        Alias for get_all_context() - obtains current context for logs.
        
        Returns:
            Dict con toda la información contextual disponible
        """
        return LogContext.get_all_context()
    
    @classmethod
    def operation_context(cls, operation: str, **extra_context):
        """
        Creates operation context manager.
        
        Args:
            operation: Name of the operation
            **extra_context: Additional context data
            
        Returns:
            Context manager with operation context
        """
        from uuid import uuid4
        context_data = {
            "operation": operation,
            "operation_id": str(uuid4()),
            **extra_context
        }
        return cls(**context_data)
    
    @classmethod
    def request_context(cls, request_id: str = None, user_id: str = None, **extra_context):
        """
        Creates request context manager.
        
        Args:
            request_id: Request ID
            user_id: User ID
            **extra_context: Additional context data
            
        Returns:
            Context manager with request context
        """
        context_data = {}
        if request_id:
            context_data["request_id"] = request_id
        if user_id:
            context_data["user_id"] = user_id
        context_data.update(extra_context)
        return cls(**context_data)
    
    @staticmethod
    def clear() -> None:
        """Limpia todo el contexto actual."""
        _rid_context.set(None)
        _trace_id_context.set(None)
        _user_id_context.set(None)
        _correlation_id_context.set(None)
        _context_data.set({})
    
    @staticmethod
    def generate_rid() -> str:
        """Genera un nuevo Request ID y lo establece en el contexto."""
        rid = uuid4().hex
        LogContext.set_rid(rid)
        return rid
    
    @staticmethod
    def generate_trace_id() -> str:
        """Genera un nuevo Trace ID y lo establece en el contexto."""
        trace_id = uuid4().hex
        LogContext.set_trace_id(trace_id)
        return trace_id


# Context manager decorator
def with_log_context(**context_data):
    """
    Decorator para establecer contexto de log en funciones.
    
    Args:
        **context_data: Datos de contexto a establecer
        
    Examples:
        @with_log_context(operation="create_user", component="user_service")
        def create_user(user_data):
            # Los logs dentro de esta función incluirán operation y component
            logger.info("Creating user")
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with LogContext(**context_data):
                return func(*args, **kwargs)
        return wrapper
    return decorator