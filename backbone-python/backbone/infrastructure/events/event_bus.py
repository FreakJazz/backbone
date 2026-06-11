"""
Event Bus - Central event publication and subscription system
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Callable, Optional, Type, TypeVar, Awaitable
import asyncio
from collections import defaultdict
import inspect
from .base_event import BaseEvent
from ..logging.structured_logger import StructuredLogger
from ..exceptions.infrastructure_exceptions import InfrastructureException

T = TypeVar('T')
EventHandler = Callable[[BaseEvent], Awaitable[None]]


class IEventPublisher(ABC):
    """Contract for event publishers."""
    
    @abstractmethod
    async def publish(self, event: BaseEvent[Any]) -> None:
        """
        Publishes an event.
        
        Args:
            event: Event to publish
        """
        pass
    
    @abstractmethod
    async def publish_batch(self, events: List[BaseEvent[Any]]) -> None:
        """
        Publishes multiple events in batch.
        
        Args:
            events: List of events
        """
        pass


class IEventSubscriber(ABC):
    """Contract for event subscribers."""
    
    @abstractmethod
    async def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
        filter_func: Optional[Callable[[BaseEvent], bool]] = None
    ) -> None:
        """
        Subscribes handler to event type.
        
        Args:
            event_type: Event type
            handler: Event handler
            filter_func: Optional filter function
        """
        pass
    
    @abstractmethod
    async def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Unsubscribes handler from event.
        
        Args:
            event_type: Event type
            handler: Handler to unsubscribe
        """
        pass


class EventBusWithAdapters(IEventPublisher, IEventSubscriber):
    """
    Complete event bus with external adapters support.
    
    Features:
    - In-memory event handling
    - External publishers/subscribers (RabbitMQ, Redis)
    - Event persistence
    - Metrics and monitoring
    """
    
    def __init__(
        self,
        event_store=None,
        logger: Optional[StructuredLogger] = None
    ):
        self._handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._filters: Dict[str, List[Callable[[BaseEvent], bool]]] = defaultdict(list)
        self._publishers: List[IEventPublisher] = []
        self._subscribers: List[IEventSubscriber] = []
        self._event_store = event_store
        self._logger = logger
        self._event_count = 0
        self._error_count = 0
        self._is_running = False
    
    def add_publisher(self, publisher: IEventPublisher) -> None:
        """Adds external event publisher."""
        self._publishers.append(publisher)
    
    def add_subscriber(self, subscriber: IEventSubscriber) -> None:
        """Adds external event subscriber."""
        self._subscribers.append(subscriber)
    
    async def start(self) -> None:
        """Starts the event bus."""
        self._is_running = True
        
        # Start external publishers/subscribers
        for publisher in self._publishers:
            if hasattr(publisher, 'connect'):
                await publisher.connect()
        
        for subscriber in self._subscribers:
            if hasattr(subscriber, 'connect'):
                await subscriber.connect()
        
        if self._logger:
            await self._logger.info(
                "Event bus started",
                context={
                    "handlers": len(self._handlers),
                    "publishers": len(self._publishers),
                    "subscribers": len(self._subscribers)
                }
            )
    
    async def stop(self) -> None:
        """Stops the event bus."""
        self._is_running = False
        
        # Stop all publishers/subscribers
        for publisher in self._publishers:
            if hasattr(publisher, 'disconnect'):
                await publisher.disconnect()
        
        for subscriber in self._subscribers:
            if hasattr(subscriber, 'disconnect'):
                await subscriber.disconnect()
        
        if self._logger:
            await self._logger.info("Event bus stopped")
    
    async def publish(self, event: BaseEvent[Any]) -> None:
        """Publishes event to all subscribers."""
        if not self._is_running:
            await self.start()
        
        self._event_count += 1
        
        # Store event if store is configured
        if self._event_store:
            try:
                await self._event_store.save_event(event)
            except Exception as e:
                if self._logger:
                    await self._logger.error(
                        f"Failed to store event: {str(e)}",
                        context={"event_id": event.event_id}
                    )
        
        if self._logger:
            await self._logger.info(
                f"Publishing event: {event.event_type}",
                context={
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "source_service": event.metadata.source_service
                }
            )
        
        # Publish to external publishers
        for publisher in self._publishers:
            try:
                await publisher.publish(event)
            except Exception as e:
                self._error_count += 1
                if self._logger:
                    await self._logger.error(
                        f"External publisher failed: {str(e)}",
                        context={"event_id": event.event_id, "publisher": str(publisher)}
                    )
        
        # Handle local subscribers
        await self._handle_local_event(event)
    
    async def _handle_local_event(self, event: BaseEvent[Any]) -> None:
        """Handles event for local subscribers."""
        # Get handlers for specific event type
        handlers = self._handlers.get(event.event_type, [])
        
        # Get wildcard handlers (*)
        wildcard_handlers = self._handlers.get("*", [])
        
        all_handlers = handlers + wildcard_handlers
        
        if not all_handlers:
            if self._logger:
                await self._logger.debug(
                    f"No local handlers found for event: {event.event_type}",
                    context={"event_id": event.event_id}
                )
            return
        
        # Execute handlers in parallel
        tasks = []
        for handler in all_handlers:
            # Apply filters if they exist
            if await self._should_handle_event(event, event.event_type):
                tasks.append(self._execute_handler(handler, event))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log any exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self._error_count += 1
                    if self._logger:
                        await self._logger.error(
                            f"Handler execution failed: {str(result)}",
                            context={
                                "event_id": event.event_id,
                                "handler_index": i
                            }
                        )
    
    async def publish_batch(self, events: List[BaseEvent[Any]]) -> None:
        """Publishes multiple events."""
        # Store events if store is configured
        if self._event_store:
            for event in events:
                try:
                    await self._event_store.save_event(event)
                except Exception as e:
                    if self._logger:
                        await self._logger.error(
                            f"Failed to store event: {str(e)}",
                            context={"event_id": event.event_id}
                        )
        
        # Publish to external publishers
        for publisher in self._publishers:
            try:
                await publisher.publish_batch(events)
            except Exception as e:
                if self._logger:
                    await self._logger.error(
                        f"External batch publisher failed: {str(e)}",
                        context={"publisher": str(publisher)}
                    )
        
        # Handle local events
        tasks = [self._handle_local_event(event) for event in events]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
        filter_func: Optional[Callable[[BaseEvent], bool]] = None
    ) -> None:
        """Subscribes handler to event."""
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            
            if filter_func:
                self._filters[event_type].append(filter_func)
            
            if self._logger:
                await self._logger.info(
                    f"Handler subscribed to event: {event_type}",
                    context={
                        "event_type": event_type,
                        "handler": handler.__name__ if hasattr(handler, '__name__') else str(handler)
                    }
                )
        
        # Subscribe to external subscribers
        for subscriber in self._subscribers:
            try:
                await subscriber.subscribe(event_type, handler, filter_func)
            except Exception as e:
                if self._logger:
                    await self._logger.error(
                        f"External subscriber failed: {str(e)}",
                        context={"event_type": event_type, "subscriber": str(subscriber)}
                    )
    
    async def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribes handler from event."""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            
            if self._logger:
                await self._logger.info(
                    f"Handler unsubscribed from event: {event_type}",
                    context={"event_type": event_type}
                )
        
        # Unsubscribe from external subscribers
        for subscriber in self._subscribers:
            try:
                await subscriber.unsubscribe(event_type, handler)
            except Exception as e:
                if self._logger:
                    await self._logger.error(
                        f"External unsubscribe failed: {str(e)}",
                        context={"event_type": event_type, "subscriber": str(subscriber)}
                    )
    
    async def _should_handle_event(self, event: BaseEvent, event_type: str) -> bool:
        """Checks if event should be handled based on filters."""
        filters = self._filters.get(event_type, [])
        
        for filter_func in filters:
            try:
                if not filter_func(event):
                    return False
            except Exception as e:
                if self._logger:
                    await self._logger.error(
                        f"Error in event filter: {str(e)}",
                        context={"event_id": event.event_id, "filter": str(filter_func)}
                    )
                return False
        
        return True
    
    async def _execute_handler(self, handler: EventHandler, event: BaseEvent) -> None:
        """Executes handler with error handling."""
        try:
            if inspect.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            if self._logger:
                await self._logger.error(
                    f"Error in event handler: {str(e)}",
                    context={
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "handler": handler.__name__ if hasattr(handler, '__name__') else str(handler),
                        "error": str(e)
                    }
                )
            
            # Re-raise as InfrastructureException
            raise InfrastructureException(
                message=f"Event handler failed: {str(e)}",
                error_code="12005001",
                operation="execute_event_handler",
                original_error=str(e)
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Gets event bus metrics."""
        return {
            "total_events_published": self._event_count,
            "total_errors": self._error_count,
            "registered_handlers": {
                event_type: len(handlers) 
                for event_type, handlers in self._handlers.items()
            },
            "active_event_types": list(self._handlers.keys()),
            "external_publishers": len(self._publishers),
            "external_subscribers": len(self._subscribers),
            "is_running": self._is_running
        }
    
    def clear(self) -> None:
        """Clears all handlers (useful for testing)."""
        self._handlers.clear()
        self._filters.clear()
        self._event_count = 0
        self._error_count = 0


# Legacy alias for backwards compatibility
InMemoryEventBus = EventBusWithAdapters


class EventBusFactory:
    """Factory for creating Event Bus instances."""
    
    _instance: Optional[IEventPublisher] = None
    
    @classmethod
    def create_event_bus(
        cls,
        event_store=None,
        logger: Optional[StructuredLogger] = None
    ) -> EventBusWithAdapters:
        """Creates complete event bus."""
        return EventBusWithAdapters(event_store, logger)
    
    @classmethod
    def create_in_memory_bus(
        cls,
        logger: Optional[StructuredLogger] = None
    ) -> EventBusWithAdapters:
        """Creates in-memory event bus (legacy compatibility)."""
        return EventBusWithAdapters(logger=logger)
    
    @classmethod
    def set_global_instance(cls, event_bus: IEventPublisher) -> None:
        """Sets global Event Bus instance."""
        cls._instance = event_bus
    
    @classmethod
    def get_global_instance(cls) -> Optional[IEventPublisher]:
        """Gets global Event Bus instance."""
        return cls._instance
    
    @classmethod
    def get_or_create_instance(
        cls,
        event_store=None,
        logger: Optional[StructuredLogger] = None
    ) -> IEventPublisher:
        """Gets global instance or creates a new one."""
        if cls._instance is None:
            cls._instance = cls.create_event_bus(event_store, logger)
        return cls._instance


# Decorators for ease of use

def event_handler(event_type: str, filter_func: Optional[Callable[[BaseEvent], bool]] = None):
    """
    Decorator to mark functions as event handlers.
    
    Args:
        event_type: Event type to handle
        filter_func: Optional filter function
    
    Usage:
        @event_handler("user.created")
        async def handle_user_created(event: BaseEvent):
            print(f"User created: {event.payload}")
    """
    def decorator(func: EventHandler) -> EventHandler:
        func._event_type = event_type
        func._filter_func = filter_func
        return func
    return decorator


class EventHandlerRegistry:
    """Registry for auto-registering decorated handlers."""
    
    def __init__(self, event_bus: IEventSubscriber):
        self.event_bus = event_bus
    
    async def register_handlers(self, *handler_objects) -> None:
        """
        Registers all decorated handlers in objects.
        
        Args:
            *handler_objects: Objects with decorated handlers
        """
        for obj in handler_objects:
            await self._register_object_handlers(obj)
    
    async def _register_object_handlers(self, obj: Any) -> None:
        """Registers handlers from a specific object."""
        for attr_name in dir(obj):
            attr = getattr(obj, attr_name)
            
            if (
                callable(attr) and 
                hasattr(attr, '_event_type') and 
                not attr_name.startswith('_')
            ):
                await self.event_bus.subscribe(
                    attr._event_type,
                    attr,
                    getattr(attr, '_filter_func', None)
                )