"""
Event Handlers - Application layer event handling decorators and utilities
"""
from typing import Any, Dict, Optional, Callable, Awaitable, List
import inspect
from functools import wraps
from backbone.domain.ports.event_bus import BaseEvent, EventHandler, EventBus
from ..exceptions import ApplicationException
from backbone.infrastructure.logging.structured_logger import StructuredLogger


class RetryPolicy:
    """Retry policy configuration for event handlers."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        delay_seconds: int = 1,
        exponential_backoff: bool = True,
        max_delay_seconds: int = 60
    ):
        self.max_attempts = max_attempts
        self.delay_seconds = delay_seconds
        self.exponential_backoff = exponential_backoff
        self.max_delay_seconds = max_delay_seconds


def event_handler(
    event_name: str,
    retry_policy: Optional[RetryPolicy] = None,
    dead_letter_enabled: bool = True,
    validate_event: bool = True
):
    """
    Decorator for event handlers with automatic logging, error handling and retry.
    
    Features:
    - Automatic event validation
    - Error handling with proper exceptions
    - Configurable retry policy
    - Dead letter handling
    - Automatic logging
    
    Usage:
        @event_handler("UserCreated")
        async def handle_user_created(event: BaseEvent):
            # Handler logic here
            pass
    """
    def decorator(handler_func: EventHandler) -> EventHandler:
        @wraps(handler_func)
        async def wrapper(event: BaseEvent, logger: Optional[StructuredLogger] = None) -> None:
            handler_name = handler_func.__name__
            
            if logger:
                await logger.info(
                    f"Processing event: {event_name}",
                    context={
                        "event_id": event.event_id,
                        "event_name": event.event_name,
                        "handler": handler_name,
                        "correlation_id": event.metadata.get("correlationId"),
                        "microservice": event.metadata.get("microservice")
                    }
                )
            
            # Validate event if requested
            if validate_event:
                if not await _validate_event(event, event_name, logger):
                    return
            
            # Execute handler with retry policy
            await _execute_with_retry(
                handler_func,
                event,
                retry_policy or RetryPolicy(),
                handler_name,
                logger
            )
            
            # Mark event as processed
            event.mark_as_processed()
            
            if logger:
                await logger.info(
                    f"Event processed successfully: {event_name}",
                    context={
                        "event_id": event.event_id,
                        "handler": handler_name,
                        "status": "processed"
                    }
                )
        
        # Store metadata on function for registration
        wrapper._event_name = event_name
        wrapper._retry_policy = retry_policy
        wrapper._dead_letter_enabled = dead_letter_enabled
        wrapper._validate_event = validate_event
        wrapper._original_handler = handler_func
        
        return wrapper
    
    return decorator


async def _validate_event(event: BaseEvent, expected_name: str, logger: Optional[StructuredLogger]) -> bool:
    """Validates event structure and name."""
    try:
        # Check event name matches
        if event.event_name != expected_name:
            error_msg = f"Event name mismatch. Expected: {expected_name}, Got: {event.event_name}"
            if logger:
                await logger.error(
                    error_msg,
                    context={
                        "event_id": event.event_id,
                        "expected_name": expected_name,
                        "actual_name": event.event_name
                    }
                )
            event.mark_as_failed()
            return False
        
        # Check required fields
        required_fields = ["event_id", "event_name", "source", "timestamp", "data", "metadata"]
        for field in required_fields:
            if not hasattr(event, field) or getattr(event, field) is None:
                error_msg = f"Missing required field: {field}"
                if logger:
                    await logger.error(
                        error_msg,
                        context={
                            "event_id": event.event_id,
                            "missing_field": field
                        }
                    )
                event.mark_as_failed()
                return False
        
        # Check metadata structure
        required_metadata = ["microservice", "functionality", "correlationId"]
        for field in required_metadata:
            if field not in event.metadata or event.metadata[field] is None:
                error_msg = f"Missing required metadata field: {field}"
                if logger:
                    await logger.error(
                        error_msg,
                        context={
                            "event_id": event.event_id,
                            "missing_metadata": field
                        }
                    )
                event.mark_as_failed()
                return False
        
        return True
        
    except Exception as e:
        error_msg = f"Event validation failed: {str(e)}"
        if logger:
            await logger.error(
                error_msg,
                context={
                    "event_id": getattr(event, 'event_id', 'unknown'),
                    "error": str(e)
                }
            )
        event.mark_as_failed()
        return False


async def _execute_with_retry(
    handler_func: EventHandler,
    event: BaseEvent,
    retry_policy: RetryPolicy,
    handler_name: str,
    logger: Optional[StructuredLogger]
) -> None:
    """Executes handler with retry policy."""
    import asyncio
    
    last_error = None
    
    for attempt in range(retry_policy.max_attempts):
        try:
            # Execute the handler
            if inspect.iscoroutinefunction(handler_func):
                await handler_func(event)
            else:
                handler_func(event)
            
            # Success - exit retry loop
            return
            
        except Exception as e:
            last_error = e
            attempt_num = attempt + 1
            
            if logger:
                await logger.warning(
                    f"Event handler attempt {attempt_num} failed: {str(e)}",
                    context={
                        "event_id": event.event_id,
                        "handler": handler_name,
                        "attempt": attempt_num,
                        "max_attempts": retry_policy.max_attempts,
                        "error": str(e)
                    }
                )
            
            # If not last attempt, wait before retry
            if attempt_num < retry_policy.max_attempts:
                delay = retry_policy.delay_seconds
                
                if retry_policy.exponential_backoff:
                    delay = min(
                        retry_policy.delay_seconds * (2 ** attempt),
                        retry_policy.max_delay_seconds
                    )
                
                if logger:
                    await logger.info(
                        f"Retrying in {delay} seconds",
                        context={
                            "event_id": event.event_id,
                            "handler": handler_name,
                            "delay_seconds": delay
                        }
                    )
                
                await asyncio.sleep(delay)
    
    # All attempts failed
    event.mark_as_failed()
    
    if logger:
        await logger.error(
            f"Event handler failed after {retry_policy.max_attempts} attempts",
            context={
                "event_id": event.event_id,
                "handler": handler_name,
                "final_error": str(last_error)
            }
        )
    
    # Convert to appropriate exception type
    if isinstance(last_error, ApplicationException):
        raise last_error
    else:
        raise ApplicationException(
            message=f"Event handler failed after {retry_policy.max_attempts} attempts: {str(last_error)}",
            error_code="10006001",
            operation=f"execute_event_handler_{handler_name}",
            original_error=str(last_error)
        )


class EventHandlerRegistry:
    """Registry for automatically registering decorated event handlers."""
    
    def __init__(self, event_bus: EventBus, logger: Optional[StructuredLogger] = None):
        self.event_bus = event_bus
        self.logger = logger
        self.registered_handlers: Dict[str, List[EventHandler]] = {}
    
    async def register_handlers(self, *handler_objects: Any) -> None:
        """
        Registers all decorated handlers from objects.
        
        Args:
            *handler_objects: Objects containing decorated event handlers
        """
        for obj in handler_objects:
            await self._register_object_handlers(obj)
    
    async def register_handler_functions(self, *handler_functions: EventHandler) -> None:
        """
        Registers individual decorated handler functions.
        
        Args:
            *handler_functions: Decorated handler functions
        """
        for handler in handler_functions:
            if hasattr(handler, '_event_name'):
                await self._register_single_handler(handler)
    
    async def _register_object_handlers(self, obj: Any) -> None:
        """Registers handlers from a specific object."""
        for attr_name in dir(obj):
            if attr_name.startswith('_'):
                continue
                
            attr = getattr(obj, attr_name)
            
            if (
                callable(attr) and
                hasattr(attr, '_event_name') and
                hasattr(attr, '_original_handler')
            ):
                # Bind method to object
                bound_handler = attr
                await self._register_single_handler(bound_handler)
    
    async def _register_single_handler(self, handler: EventHandler) -> None:
        """Registers a single decorated handler."""
        event_name = handler._event_name
        retry_policy_dict = None
        
        if handler._retry_policy:
            retry_policy_dict = {
                "max_attempts": handler._retry_policy.max_attempts,
                "delay_seconds": handler._retry_policy.delay_seconds,
                "exponential_backoff": handler._retry_policy.exponential_backoff,
                "max_delay_seconds": handler._retry_policy.max_delay_seconds
            }
        
        await self.event_bus.subscribe(event_name, handler, retry_policy_dict)
        
        # Track registered handlers
        if event_name not in self.registered_handlers:
            self.registered_handlers[event_name] = []
        self.registered_handlers[event_name].append(handler)
        
        if self.logger:
            await self.logger.info(
                f"Registered event handler: {handler.__name__} for event: {event_name}",
                context={
                    "event_name": event_name,
                    "handler": handler.__name__,
                    "retry_policy": retry_policy_dict is not None
                }
            )
    
    async def unregister_handlers(self, *handler_objects: Any) -> None:
        """Unregisters handlers from objects."""
        for obj in handler_objects:
            await self._unregister_object_handlers(obj)
    
    async def _unregister_object_handlers(self, obj: Any) -> None:
        """Unregisters handlers from a specific object."""
        for attr_name in dir(obj):
            if attr_name.startswith('_'):
                continue
                
            attr = getattr(obj, attr_name)
            
            if (
                callable(attr) and
                hasattr(attr, '_event_name')
            ):
                event_name = attr._event_name
                
                await self.event_bus.unsubscribe(event_name, attr)
                
                # Remove from tracking
                if event_name in self.registered_handlers:
                    if attr in self.registered_handlers[event_name]:
                        self.registered_handlers[event_name].remove(attr)
                    
                    if not self.registered_handlers[event_name]:
                        del self.registered_handlers[event_name]
                
                if self.logger:
                    await self.logger.info(
                        f"Unregistered event handler: {attr.__name__} from event: {event_name}",
                        context={
                            "event_name": event_name,
                            "handler": attr.__name__
                        }
                    )
    
    def get_registered_handlers(self) -> Dict[str, List[str]]:
        """Gets list of registered handlers by event name."""
        return {
            event_name: [handler.__name__ for handler in handlers]
            for event_name, handlers in self.registered_handlers.items()
        }