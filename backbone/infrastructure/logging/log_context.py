"""
Log Context - Context manager para enriquecer logs automáticamente
"""
from contextvars import ContextVar
from typing import Dict, Any, Optional
from uuid import uuid4


_request_id_context: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_trace_id_context: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
_user_id_context: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
_correlation_id_context: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
_context_data: ContextVar[Dict[str, Any]] = ContextVar("context_data", default={})


class LogContext:
    """
    Context manager para manejar información contextual de logs.

    Todos los logs emitidos dentro del contexto incluyen automáticamente
    request_id, trace_id, user_id y correlation_id.

    Examples:
        with LogContext(request_id="abc123", user_id="user-456"):
            logger.info("Processing request")

        @with_log_context(operation="create_user")
        def create_user(data): ...
    """

    def __init__(
        self,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        # backward-compat
        rid: Optional[str] = None,
        **extra_data,
    ):
        self.request_id = request_id or rid
        self.trace_id = trace_id
        self.user_id = user_id
        self.correlation_id = correlation_id
        self.extra_data = extra_data
        self._tokens = []

    def __enter__(self):
        if self.request_id is not None:
            self._tokens.append(_request_id_context.set(self.request_id))
        if self.trace_id is not None:
            self._tokens.append(_trace_id_context.set(self.trace_id))
        if self.user_id is not None:
            self._tokens.append(_user_id_context.set(self.user_id))
        if self.correlation_id is not None:
            self._tokens.append(_correlation_id_context.set(self.correlation_id))
        if self.extra_data:
            current = _context_data.get({})
            self._tokens.append(_context_data.set({**current, **self.extra_data}))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for token in reversed(self._tokens):
            token.var.reset(token)

    # --- setters ---

    @staticmethod
    def set_request_id(request_id: str) -> None:
        _request_id_context.set(request_id)

    @staticmethod
    def set_rid(rid: str) -> None:
        """Alias de set_request_id."""
        _request_id_context.set(rid)

    @staticmethod
    def set_trace_id(trace_id: str) -> None:
        _trace_id_context.set(trace_id)

    @staticmethod
    def set_user_id(user_id: str) -> None:
        _user_id_context.set(user_id)

    @staticmethod
    def set_correlation_id(correlation_id: str) -> None:
        _correlation_id_context.set(correlation_id)

    @staticmethod
    def add_data(key: str, value: Any) -> None:
        current = _context_data.get({})
        _context_data.set({**current, key: value})

    # --- getters ---

    @staticmethod
    def get_request_id() -> Optional[str]:
        return _request_id_context.get()

    @staticmethod
    def get_rid() -> Optional[str]:
        """Alias de get_request_id."""
        return _request_id_context.get()

    @staticmethod
    def get_trace_id() -> Optional[str]:
        return _trace_id_context.get()

    @staticmethod
    def get_user_id() -> Optional[str]:
        return _user_id_context.get()

    @staticmethod
    def get_correlation_id() -> Optional[str]:
        return _correlation_id_context.get()

    @staticmethod
    def get_context_data() -> Dict[str, Any]:
        return _context_data.get({})

    @staticmethod
    def get_all_context() -> Dict[str, Any]:
        """Retorna todo el contexto disponible para enriquecer un log entry."""
        context: Dict[str, Any] = {}

        request_id = LogContext.get_request_id()
        if request_id:
            context["request_id"] = request_id

        trace_id = LogContext.get_trace_id()
        if trace_id:
            context["trace_id"] = trace_id

        user_id = LogContext.get_user_id()
        if user_id:
            context["user_id"] = user_id

        correlation_id = LogContext.get_correlation_id()
        if correlation_id:
            context["correlation_id"] = correlation_id

        context.update(LogContext.get_context_data())
        return context

    # backward-compat alias
    get_current_context = get_all_context

    # --- factories ---

    @classmethod
    def operation_context(cls, operation: str, **extra_context):
        return cls(
            **{
                "operation": operation,
                "operation_id": str(uuid4()),
                **extra_context,
            }
        )

    @classmethod
    def request_context(cls, request_id: str = None, user_id: str = None, **extra_context):
        kwargs: Dict[str, Any] = {}
        if request_id:
            kwargs["request_id"] = request_id
        if user_id:
            kwargs["user_id"] = user_id
        kwargs.update(extra_context)
        return cls(**kwargs)

    @staticmethod
    def clear() -> None:
        _request_id_context.set(None)
        _trace_id_context.set(None)
        _user_id_context.set(None)
        _correlation_id_context.set(None)
        _context_data.set({})

    @staticmethod
    def generate_request_id() -> str:
        rid = uuid4().hex
        LogContext.set_request_id(rid)
        return rid

    @staticmethod
    def generate_rid() -> str:
        """Alias de generate_request_id."""
        return LogContext.generate_request_id()

    @staticmethod
    def generate_trace_id() -> str:
        trace_id = uuid4().hex
        LogContext.set_trace_id(trace_id)
        return trace_id


def with_log_context(**context_data):
    """
    Decorator para establecer contexto de log en funciones.

    @with_log_context(operation="create_user", component="user_service")
    def create_user(data): ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with LogContext(**context_data):
                return func(*args, **kwargs)
        return wrapper
    return decorator
