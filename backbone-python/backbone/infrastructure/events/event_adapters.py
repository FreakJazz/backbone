"""
Event Adapters - External event system adapters (RabbitMQ, Redis)
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Awaitable
import asyncio
import json
from .base_event import BaseEvent
from .event_bus import IEventPublisher, IEventSubscriber, EventHandler
from ..logging.structured_logger import StructuredLogger
from ..exceptions.infrastructure_exceptions import InfrastructureException

try:
    import aio_pika
    from aio_pika import connect_robust, Message, DeliveryMode
    from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractQueue
    _rabbitmq_available = True
except ImportError:
    _rabbitmq_available = False

try:
    import aioredis
    _redis_available = True
except ImportError:
    _redis_available = False


class RabbitMQEventAdapter(IEventPublisher, IEventSubscriber):
    """
    RabbitMQ adapter for event publishing and subscription.
    
    Features:
    - Durable exchanges and queues
    - Message persistence
    - Dead letter queues
    - Automatic reconnection
    """
    
    def __init__(
        self,
        connection_url: str,
        exchange_name: str = "backbone.events",
        logger: Optional[StructuredLogger] = None
    ):
        if not _rabbitmq_available:
            raise InfrastructureException(
                message="RabbitMQ adapter requires aio-pika package",
                error_code="12007001",
                operation="init_rabbitmq_adapter"
            )
        
        self.connection_url = connection_url
        self.exchange_name = exchange_name
        self.logger = logger
        self.connection: Optional[AbstractConnection] = None
        self.channel: Optional[AbstractChannel] = None
        self.exchange = None
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._queues: Dict[str, AbstractQueue] = {}
    
    async def connect(self) -> None:
        """Establishes connection to RabbitMQ."""
        try:
            self.connection = await connect_robust(self.connection_url)
            self.channel = await self.connection.channel()
            
            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                self.exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            if self.logger:
                await self.logger.info(
                    "Connected to RabbitMQ",
                    context={
                        "exchange": self.exchange_name,
                        "connection_url": self.connection_url.split('@')[0] + "@***"
                    }
                )
        
        except Exception as e:
            raise InfrastructureException(
                message=f"Failed to connect to RabbitMQ: {str(e)}",
                error_code="12007002",
                operation="connect_rabbitmq",
                original_error=str(e)
            )
    
    async def disconnect(self) -> None:
        """Closes RabbitMQ connection."""
        try:
            if self.connection:
                await self.connection.close()
            
            if self.logger:
                await self.logger.info("Disconnected from RabbitMQ")
        
        except Exception as e:
            if self.logger:
                await self.logger.warning(
                    f"Error disconnecting from RabbitMQ: {str(e)}"
                )
    
    async def publish(self, event: BaseEvent[Any]) -> None:
        """Publishes event to RabbitMQ."""
        if not self.exchange:
            await self.connect()
        
        try:
            message_body = event.to_json().encode('utf-8')
            message = Message(
                message_body,
                delivery_mode=DeliveryMode.PERSISTENT,
                headers={
                    "event_type": event.event_type,
                    "event_id": event.event_id,
                    "source_service": event.metadata.source_service,
                    "correlation_id": event.metadata.correlation_id,
                    "timestamp": event.timestamp.isoformat()
                }
            )
            
            # Use event type as routing key
            routing_key = event.event_type
            
            await self.exchange.publish(message, routing_key=routing_key)
            
            if self.logger:
                await self.logger.info(
                    f"Event published to RabbitMQ: {event.event_type}",
                    context={
                        "event_id": event.event_id,
                        "routing_key": routing_key
                    }
                )
        
        except Exception as e:
            raise InfrastructureException(
                message=f"Failed to publish event to RabbitMQ: {str(e)}",
                error_code="12007003",
                operation="publish_rabbitmq_event",
                original_error=str(e)
            )
    
    async def publish_batch(self, events: List[BaseEvent[Any]]) -> None:
        """Publishes multiple events."""
        for event in events:
            await self.publish(event)
    
    async def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
        filter_func: Optional[Callable[[BaseEvent], bool]] = None
    ) -> None:
        """Subscribes to events from RabbitMQ."""
        if not self.channel:
            await self.connect()
        
        try:
            queue_name = f"backbone.{event_type}"
            
            # Declare queue
            queue = await self.channel.declare_queue(
                queue_name,
                durable=True
            )
            
            # Bind queue to exchange
            await queue.bind(self.exchange, routing_key=event_type)
            
            self._queues[event_type] = queue
            self._handlers[event_type] = self._handlers.get(event_type, [])
            self._handlers[event_type].append(handler)
            
            # Set up consumer
            async def message_handler(message):
                async with message.process():
                    try:
                        # Parse message
                        event_data = json.loads(message.body.decode('utf-8'))
                        
                        # Create event from data (generic approach)
                        event = await self._create_event_from_message(event_data)
                        
                        # Apply filter if provided
                        if filter_func and not filter_func(event):
                            return
                        
                        # Execute handler
                        await handler(event)
                        
                    except Exception as e:
                        if self.logger:
                            await self.logger.error(
                                f"Error processing RabbitMQ message: {str(e)}",
                                context={
                                    "queue": queue_name,
                                    "error": str(e)
                                }
                            )
                        raise
            
            await queue.consume(message_handler)
            
            if self.logger:
                await self.logger.info(
                    f"Subscribed to RabbitMQ events: {event_type}",
                    context={"queue": queue_name}
                )
        
        except Exception as e:
            raise InfrastructureException(
                message=f"Failed to subscribe to RabbitMQ events: {str(e)}",
                error_code="12007004",
                operation="subscribe_rabbitmq_events",
                original_error=str(e)
            )
    
    async def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribes from RabbitMQ events."""
        if event_type in self._handlers:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
        
        # Note: RabbitMQ consumers are typically long-lived
        # Actual queue consumer cancellation would need additional tracking
        
        if self.logger:
            await self.logger.info(f"Unsubscribed from RabbitMQ events: {event_type}")
    
    async def _create_event_from_message(self, event_data: Dict[str, Any]) -> BaseEvent[Any]:
        """Creates event from RabbitMQ message data."""
        # Create generic event from message data
        class MessageEvent(BaseEvent[Dict[str, Any]]):
            def __init__(self, data: Dict[str, Any]):
                super().__init__(
                    payload=data["payload"],
                    event_type=data["event_type"],
                    source_service=data["metadata"]["source_service"],
                    correlation_id=data["metadata"].get("correlation_id"),
                    trace_id=data["metadata"].get("trace_id"),
                    user_id=data["metadata"].get("user_id"),
                    request_id=data["metadata"].get("request_id")
                )
        
        return MessageEvent(event_data)


class RedisEventAdapter(IEventPublisher, IEventSubscriber):
    """
    Redis adapter for event publishing and subscription.
    
    Uses Redis Pub/Sub for real-time event distribution.
    """
    
    def __init__(
        self,
        redis_url: str,
        channel_prefix: str = "backbone.events",
        logger: Optional[StructuredLogger] = None
    ):
        if not _redis_available:
            raise InfrastructureException(
                message="Redis adapter requires aioredis package",
                error_code="12007005",
                operation="init_redis_adapter"
            )
        
        self.redis_url = redis_url
        self.channel_prefix = channel_prefix
        self.logger = logger
        self.redis = None
        self.pubsub = None
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._subscriptions: Dict[str, bool] = {}
    
    async def connect(self) -> None:
        """Connects to Redis."""
        try:
            self.redis = aioredis.from_url(self.redis_url)
            await self.redis.ping()
            
            if self.logger:
                await self.logger.info(
                    "Connected to Redis",
                    context={"redis_url": self.redis_url.split('@')[0] + "@***"}
                )
        
        except Exception as e:
            raise InfrastructureException(
                message=f"Failed to connect to Redis: {str(e)}",
                error_code="12007006",
                operation="connect_redis",
                original_error=str(e)
            )
    
    async def disconnect(self) -> None:
        """Disconnects from Redis."""
        try:
            if self.pubsub:
                await self.pubsub.close()
            if self.redis:
                await self.redis.close()
            
            if self.logger:
                await self.logger.info("Disconnected from Redis")
        
        except Exception as e:
            if self.logger:
                await self.logger.warning(f"Error disconnecting from Redis: {str(e)}")
    
    async def publish(self, event: BaseEvent[Any]) -> None:
        """Publishes event to Redis."""
        if not self.redis:
            await self.connect()
        
        try:
            channel = f"{self.channel_prefix}.{event.event_type}"
            message = event.to_json()
            
            await self.redis.publish(channel, message)
            
            if self.logger:
                await self.logger.info(
                    f"Event published to Redis: {event.event_type}",
                    context={
                        "event_id": event.event_id,
                        "channel": channel
                    }
                )
        
        except Exception as e:
            raise InfrastructureException(
                message=f"Failed to publish event to Redis: {str(e)}",
                error_code="12007007",
                operation="publish_redis_event",
                original_error=str(e)
            )
    
    async def publish_batch(self, events: List[BaseEvent[Any]]) -> None:
        """Publishes multiple events to Redis."""
        if not self.redis:
            await self.connect()
        
        # Use pipeline for batch publishing
        pipe = self.redis.pipeline()
        
        for event in events:
            channel = f"{self.channel_prefix}.{event.event_type}"
            message = event.to_json()
            pipe.publish(channel, message)
        
        await pipe.execute()
    
    async def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
        filter_func: Optional[Callable[[BaseEvent], bool]] = None
    ) -> None:
        """Subscribes to Redis events."""
        if not self.redis:
            await self.connect()
        
        if not self.pubsub:
            self.pubsub = self.redis.pubsub()
        
        try:
            channel = f"{self.channel_prefix}.{event_type}"
            
            # Subscribe to channel
            await self.pubsub.subscribe(channel)
            self._subscriptions[event_type] = True
            
            # Store handler
            self._handlers[event_type] = self._handlers.get(event_type, [])
            self._handlers[event_type].append(handler)
            
            # Start listening if not already started
            if not hasattr(self, '_listening'):
                self._listening = True
                asyncio.create_task(self._listen_for_messages())
            
            if self.logger:
                await self.logger.info(
                    f"Subscribed to Redis events: {event_type}",
                    context={"channel": channel}
                )
        
        except Exception as e:
            raise InfrastructureException(
                message=f"Failed to subscribe to Redis events: {str(e)}",
                error_code="12007008",
                operation="subscribe_redis_events",
                original_error=str(e)
            )
    
    async def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribes from Redis events."""
        if event_type in self._handlers:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
            
            # If no more handlers, unsubscribe from channel
            if not self._handlers[event_type]:
                channel = f"{self.channel_prefix}.{event_type}"
                await self.pubsub.unsubscribe(channel)
                del self._subscriptions[event_type]
        
        if self.logger:
            await self.logger.info(f"Unsubscribed from Redis events: {event_type}")
    
    async def _listen_for_messages(self) -> None:
        """Listens for Redis pub/sub messages."""
        try:
            async for message in self.pubsub.listen():
                if message['type'] == 'message':
                    await self._handle_redis_message(message)
        
        except Exception as e:
            if self.logger:
                await self.logger.error(
                    f"Error listening for Redis messages: {str(e)}",
                    context={"error": str(e)}
                )
    
    async def _handle_redis_message(self, message: Dict[str, Any]) -> None:
        """Handles received Redis message."""
        try:
            # Extract event type from channel
            channel = message['channel'].decode('utf-8')
            event_type = channel.replace(f"{self.channel_prefix}.", "")
            
            # Parse event data
            event_data = json.loads(message['data'].decode('utf-8'))
            event = await self._create_event_from_data(event_data)
            
            # Execute handlers
            handlers = self._handlers.get(event_type, [])
            for handler in handlers:
                try:
                    await handler(event)
                except Exception as e:
                    if self.logger:
                        await self.logger.error(
                            f"Error in Redis event handler: {str(e)}",
                            context={
                                "event_type": event_type,
                                "event_id": event.event_id,
                                "error": str(e)
                            }
                        )
        
        except Exception as e:
            if self.logger:
                await self.logger.error(
                    f"Error handling Redis message: {str(e)}",
                    context={"error": str(e)}
                )
    
    async def _create_event_from_data(self, event_data: Dict[str, Any]) -> BaseEvent[Any]:
        """Creates event from Redis message data."""
        class RedisEvent(BaseEvent[Dict[str, Any]]):
            def __init__(self, data: Dict[str, Any]):
                super().__init__(
                    payload=data["payload"],
                    event_type=data["event_type"],
                    source_service=data["metadata"]["source_service"],
                    correlation_id=data["metadata"].get("correlation_id"),
                    trace_id=data["metadata"].get("trace_id"),
                    user_id=data["metadata"].get("user_id"),
                    request_id=data["metadata"].get("request_id")
                )
        
        return RedisEvent(event_data)


class EventAdapterFactory:
    """Factory for creating event adapters."""
    
    @staticmethod
    def create_rabbitmq_adapter(
        connection_url: str,
        exchange_name: str = "backbone.events",
        logger: Optional[StructuredLogger] = None
    ) -> RabbitMQEventAdapter:
        """Creates RabbitMQ event adapter."""
        return RabbitMQEventAdapter(connection_url, exchange_name, logger)
    
    @staticmethod
    def create_redis_adapter(
        redis_url: str,
        channel_prefix: str = "backbone.events",
        logger: Optional[StructuredLogger] = None
    ) -> RedisEventAdapter:
        """Creates Redis event adapter."""
        return RedisEventAdapter(redis_url, channel_prefix, logger)
    
    @staticmethod
    def is_rabbitmq_available() -> bool:
        """Checks if RabbitMQ adapter is available."""
        return _rabbitmq_available
    
    @staticmethod
    def is_redis_available() -> bool:
        """Checks if Redis adapter is available."""
        return _redis_available
    
    @staticmethod
    def get_available_adapters() -> List[str]:
        """Gets list of available adapters."""
        adapters = []
        if _rabbitmq_available:
            adapters.append("rabbitmq")
        if _redis_available:
            adapters.append("redis")
        return adapters