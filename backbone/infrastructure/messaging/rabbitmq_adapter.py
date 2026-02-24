"""
RabbitMQ Event Bus Adapter - Infrastructure implementation for RabbitMQ
"""
from typing import Any, Dict, List, Optional, Callable
import asyncio
import json
from backbone.domain.ports.event_bus import EventBus, BaseEvent, EventHandler
from ..exceptions import InfrastructureException
from backbone.infrastructure.logging.structured_logger import StructuredLogger

try:
    import aio_pika
    from aio_pika import connect_robust, Message, DeliveryMode
    from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractQueue
    _rabbitmq_available = True
except ImportError:
    _rabbitmq_available = False


class RabbitMQEventBusAdapter(EventBus):
    """
    RabbitMQ adapter implementing EventBus port.
    
    Features:
    - Durable exchanges and queues
    - Message persistence
    - Topic-based routing
    - Dead letter queues
    - Automatic reconnection
    """
    
    def __init__(
        self,
        connection_url: str,
        exchange_name: str = "backbone.events",
        queue_prefix: str = "backbone",
        logger: Optional[StructuredLogger] = None
    ):
        if not _rabbitmq_available:
            raise InfrastructureException(
                message="RabbitMQ adapter requires aio-pika package",
                error_code="12009001",
                operation="init_rabbitmq_adapter"
            )
        
        self.connection_url = connection_url
        self.exchange_name = exchange_name
        self.queue_prefix = queue_prefix
        self.logger = logger
        
        self.connection: Optional[AbstractConnection] = None
        self.channel: Optional[AbstractChannel] = None
        self.exchange = None
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._retry_policies: Dict[str, Dict[str, Any]] = {}
        self._queues: Dict[str, AbstractQueue] = {}
        self._is_running = False
    
    async def start(self) -> None:
        """Starts RabbitMQ connection."""
        try:
            self.connection = await connect_robust(self.connection_url)
            self.channel = await self.connection.channel()
            
            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                self.exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            self._is_running = True
            
            if self.logger:
                await self.logger.info(
                    "RabbitMQ event bus started",
                    context={
                        "exchange": self.exchange_name,
                        "connection_url": self.connection_url.split('@')[0] + "@***"
                    }
                )
        
        except Exception as e:
            raise InfrastructureException(
                message=f"Failed to start RabbitMQ event bus: {str(e)}",
                error_code="12009002",
                operation="start_rabbitmq_bus",
                original_error=str(e)
            )
    
    async def stop(self) -> None:
        """Stops RabbitMQ connection."""
        try:
            self._is_running = False
            
            if self.connection:
                await self.connection.close()
            
            if self.logger:
                await self.logger.info("RabbitMQ event bus stopped")
        
        except Exception as e:
            if self.logger:
                await self.logger.warning(f"Error stopping RabbitMQ event bus: {str(e)}")
    
    async def publish(self, event: BaseEvent) -> None:
        """Publishes event to RabbitMQ exchange."""
        if not self._is_running:
            await self.start()
        
        try:
            message_body = json.dumps(event.to_dict()).encode('utf-8')
            message = Message(
                message_body,
                delivery_mode=DeliveryMode.PERSISTENT,
                headers={
                    "event_name": event.event_name,
                    "event_id": event.event_id,
                    "source": event.source,
                    "microservice": event.metadata.get("microservice"),
                    "correlation_id": event.metadata.get("correlationId"),
                    "timestamp": event.timestamp.isoformat()
                }
            )
            
            # Use event name as routing key
            routing_key = event.event_name
            
            await self.exchange.publish(message, routing_key=routing_key)
            
            event.mark_as_published()
            
            if self.logger:
                await self.logger.info(
                    f"Event published to RabbitMQ: {event.event_name}",
                    context={
                        "event_id": event.event_id,
                        "routing_key": routing_key,
                        "microservice": event.metadata.get("microservice"),
                        "correlation_id": event.metadata.get("correlationId")
                    }
                )
        
        except Exception as e:
            event.mark_as_failed()
            raise InfrastructureException(
                message=f"Failed to publish event to RabbitMQ: {str(e)}",
                error_code="12009003",
                operation="publish_rabbitmq_event",
                original_error=str(e)
            )
    
    async def publish_batch(self, events: List[BaseEvent]) -> None:
        """Publishes batch of events to RabbitMQ."""
        if not self._is_running:
            await self.start()
        
        try:
            for event in events:
                await self.publish(event)
            
            if self.logger:
                await self.logger.info(
                    f"Batch of {len(events)} events published to RabbitMQ",
                    context={"event_count": len(events)}
                )
        
        except Exception as e:
            # Mark remaining events as failed
            for event in events:
                if event.status != "published":
                    event.mark_as_failed()
            
            raise InfrastructureException(
                message=f"Failed to publish event batch to RabbitMQ: {str(e)}",
                error_code="12009004",
                operation="publish_rabbitmq_batch",
                original_error=str(e)
            )
    
    async def subscribe(
        self,
        event_name: str,
        handler: EventHandler,
        retry_policy: Optional[Dict[str, Any]] = None
    ) -> None:
        """Subscribes to events from RabbitMQ."""
        if not self._is_running:
            await self.start()
        
        try:
            queue_name = f"{self.queue_prefix}.{event_name}"
            
            # Declare queue
            queue = await self.channel.declare_queue(
                queue_name,
                durable=True
            )
            
            # Bind queue to exchange with event name routing key
            await queue.bind(self.exchange, routing_key=event_name)
            
            self._queues[event_name] = queue
            
            # Store handler and retry policy
            if event_name not in self._handlers:
                self._handlers[event_name] = []
            self._handlers[event_name].append(handler)
            
            if retry_policy:
                self._retry_policies[event_name] = retry_policy
            
            # Set up consumer
            async def message_handler(message):
                async with message.process():
                    try:
                        # Parse message
                        event_data = json.loads(message.body.decode('utf-8'))
                        
                        # Create event from data
                        event = await self._create_event_from_data(event_data)
                        
                        # Execute handler with retry
                        await self._execute_handler_with_retry(handler, event, event_name)
                        
                    except Exception as e:
                        if self.logger:
                            await self.logger.error(
                                f"Error processing RabbitMQ message: {str(e)}",
                                context={
                                    "queue": queue_name,
                                    "message_id": message.message_id,
                                    "error": str(e)
                                }
                            )
                        raise
            
            await queue.consume(message_handler)
            
            if self.logger:
                await self.logger.info(
                    f"Subscribed to RabbitMQ events: {event_name}",
                    context={
                        "queue": queue_name,
                        "handler": handler.__name__
                    }
                )
        
        except Exception as e:
            raise InfrastructureException(
                message=f"Failed to subscribe to RabbitMQ events: {str(e)}",
                error_code="12009005",
                operation="subscribe_rabbitmq_events",
                original_error=str(e)
            )
    
    async def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        """Unsubscribes from RabbitMQ events."""
        if event_name in self._handlers:
            if handler in self._handlers[event_name]:
                self._handlers[event_name].remove(handler)
            
            # Remove retry policy if no more handlers
            if not self._handlers[event_name]:
                if event_name in self._retry_policies:
                    del self._retry_policies[event_name]
        
        # Note: RabbitMQ consumers are typically long-lived
        # Actual queue consumer cancellation would need additional tracking
        
        if self.logger:
            await self.logger.info(
                f"Unsubscribed from RabbitMQ events: {event_name}",
                context={"handler": handler.__name__}
            )
    
    async def _create_event_from_data(self, event_data: Dict[str, Any]) -> BaseEvent:
        """Creates event from RabbitMQ message data."""
        event = BaseEvent(
            event_name=event_data["eventName"],
            source=event_data["source"],
            data=event_data["data"],
            microservice=event_data["metadata"]["microservice"],
            functionality=event_data["metadata"]["functionality"],
            correlation_id=event_data["metadata"].get("correlationId"),
            event_version=event_data.get("eventVersion", "1.0"),
            event_id=event_data["eventId"]
        )
        
        # Set timestamps and status
        from datetime import datetime
        event.timestamp = datetime.fromisoformat(event_data["timestamp"].replace('Z', '+00:00'))
        event.created_at = datetime.fromisoformat(event_data["createdAt"].replace('Z', '+00:00'))
        event.updated_at = datetime.fromisoformat(event_data["updatedAt"].replace('Z', '+00:00'))
        event.status = event_data["status"]
        
        return event
    
    async def _execute_handler_with_retry(
        self,
        handler: EventHandler,
        event: BaseEvent,
        event_name: str
    ) -> None:
        """Executes handler with retry policy."""
        retry_policy = self._retry_policies.get(event_name, {})
        max_attempts = retry_policy.get("max_attempts", 1)
        delay_seconds = retry_policy.get("delay_seconds", 1)
        exponential_backoff = retry_policy.get("exponential_backoff", False)
        
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                await handler(event, self.logger)
                return  # Success
            
            except Exception as e:
                last_error = e
                attempt_num = attempt + 1
                
                if self.logger:
                    await self.logger.warning(
                        f"RabbitMQ handler attempt {attempt_num} failed: {str(e)}",
                        context={
                            "event_id": event.event_id,
                            "event_name": event_name,
                            "attempt": attempt_num,
                            "max_attempts": max_attempts
                        }
                    )
                
                # Wait before retry if not last attempt
                if attempt_num < max_attempts:
                    delay = delay_seconds
                    if exponential_backoff:
                        delay = delay_seconds * (2 ** attempt)
                    
                    await asyncio.sleep(delay)
        
        # All attempts failed
        if self.logger:
            await self.logger.error(
                f"RabbitMQ handler failed after {max_attempts} attempts: {str(last_error)}",
                context={
                    "event_id": event.event_id,
                    "event_name": event_name,
                    "final_error": str(last_error)
                }
            )
        
        raise InfrastructureException(
            message=f"RabbitMQ event handler failed after {max_attempts} attempts: {str(last_error)}",
            error_code="12009006",
            operation="execute_rabbitmq_handler",
            original_error=str(last_error)
        )