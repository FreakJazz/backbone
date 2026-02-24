"""
Redis Event Bus Adapter - Infrastructure implementation for Redis Pub/Sub
"""
from typing import Any, Dict, List, Optional, Callable
import asyncio
import json
from backbone.domain.ports.event_bus import EventBus, BaseEvent, EventHandler
from ..exceptions import InfrastructureException
from backbone.infrastructure.logging.structured_logger import StructuredLogger

try:
    import aioredis
    _redis_available = True
except ImportError:
    _redis_available = False


class RedisEventBusAdapter(EventBus):
    """
    Redis Pub/Sub adapter implementing EventBus port.
    
    Features:
    - Redis Pub/Sub for real-time events
    - Channel-based routing  
    - Lightweight messaging
    - Connection management
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
                error_code="12010001",
                operation="init_redis_adapter"
            )
        
        self.redis_url = redis_url
        self.channel_prefix = channel_prefix
        self.logger = logger
        
        self.redis = None
        self.pubsub = None
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._retry_policies: Dict[str, Dict[str, Any]] = {}
        self._subscriptions: Dict[str, bool] = {}
        self._listener_task: Optional[asyncio.Task] = None
        self._is_running = False
    
    async def start(self) -> None:
        """Starts Redis connection."""
        try:
            self.redis = aioredis.from_url(self.redis_url)
            await self.redis.ping()
            
            self.pubsub = self.redis.pubsub()
            self._is_running = True
            
            # Start message listener
            self._listener_task = asyncio.create_task(self._listen_for_messages())
            
            if self.logger:
                await self.logger.info(
                    "Redis event bus started",
                    context={
                        "redis_url": self.redis_url.split('@')[0] + "@***" if '@' in self.redis_url else self.redis_url
                    }
                )
        
        except Exception as e:
            raise InfrastructureException(
                message=f"Failed to start Redis event bus: {str(e)}",
                error_code="12010002",
                operation="start_redis_bus",
                original_error=str(e)
            )
    
    async def stop(self) -> None:
        """Stops Redis connection."""
        try:
            self._is_running = False
            
            # Cancel listener task
            if self._listener_task:
                self._listener_task.cancel()
                try:
                    await self._listener_task
                except asyncio.CancelledError:
                    pass
            
            # Close connections
            if self.pubsub:
                await self.pubsub.close()
            if self.redis:
                await self.redis.close()
            
            if self.logger:
                await self.logger.info("Redis event bus stopped")
        
        except Exception as e:
            if self.logger:
                await self.logger.warning(f"Error stopping Redis event bus: {str(e)}")
    
    async def publish(self, event: BaseEvent) -> None:
        """Publishes event to Redis channel."""
        if not self._is_running:
            await self.start()
        
        try:
            channel = f"{self.channel_prefix}.{event.event_name}"
            message = json.dumps(event.to_dict())
            
            await self.redis.publish(channel, message)
            
            event.mark_as_published()
            
            if self.logger:
                await self.logger.info(
                    f"Event published to Redis: {event.event_name}",
                    context={
                        "event_id": event.event_id,
                        "channel": channel,
                        "microservice": event.metadata.get("microservice"),
                        "correlation_id": event.metadata.get("correlationId")
                    }
                )
        
        except Exception as e:
            event.mark_as_failed()
            raise InfrastructureException(
                message=f"Failed to publish event to Redis: {str(e)}",
                error_code="12010003",
                operation="publish_redis_event",
                original_error=str(e)
            )
    
    async def publish_batch(self, events: List[BaseEvent]) -> None:
        """Publishes batch of events to Redis."""
        if not self._is_running:
            await self.start()
        
        try:
            # Use pipeline for batch publishing
            pipe = self.redis.pipeline()
            
            for event in events:
                channel = f"{self.channel_prefix}.{event.event_name}"
                message = json.dumps(event.to_dict())
                pipe.publish(channel, message)
            
            await pipe.execute()
            
            # Mark all as published
            for event in events:
                event.mark_as_published()
            
            if self.logger:
                await self.logger.info(
                    f"Batch of {len(events)} events published to Redis",
                    context={"event_count": len(events)}
                )
        
        except Exception as e:
            # Mark all events as failed
            for event in events:
                event.mark_as_failed()
            
            raise InfrastructureException(
                message=f"Failed to publish event batch to Redis: {str(e)}",
                error_code="12010004",
                operation="publish_redis_batch",
                original_error=str(e)
            )
    
    async def subscribe(
        self,
        event_name: str,
        handler: EventHandler,
        retry_policy: Optional[Dict[str, Any]] = None
    ) -> None:
        """Subscribes to Redis events."""
        if not self._is_running:
            await self.start()
        
        try:
            channel = f"{self.channel_prefix}.{event_name}"
            
            # Subscribe to channel
            await self.pubsub.subscribe(channel)
            self._subscriptions[event_name] = True
            
            # Store handler and retry policy
            if event_name not in self._handlers:
                self._handlers[event_name] = []
            self._handlers[event_name].append(handler)
            
            if retry_policy:
                self._retry_policies[event_name] = retry_policy
            
            if self.logger:
                await self.logger.info(
                    f"Subscribed to Redis events: {event_name}",
                    context={
                        "channel": channel,
                        "handler": handler.__name__
                    }
                )
        
        except Exception as e:
            raise InfrastructureException(
                message=f"Failed to subscribe to Redis events: {str(e)}",
                error_code="12010005",
                operation="subscribe_redis_events",
                original_error=str(e)
            )
    
    async def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        """Unsubscribes from Redis events."""
        if event_name in self._handlers:
            if handler in self._handlers[event_name]:
                self._handlers[event_name].remove(handler)
            
            # If no more handlers, unsubscribe from channel
            if not self._handlers[event_name]:
                channel = f"{self.channel_prefix}.{event_name}"
                await self.pubsub.unsubscribe(channel)
                del self._subscriptions[event_name]
                
                if event_name in self._retry_policies:
                    del self._retry_policies[event_name]
        
        if self.logger:
            await self.logger.info(
                f"Unsubscribed from Redis events: {event_name}",
                context={"handler": handler.__name__}
            )
    
    async def _listen_for_messages(self) -> None:
        """Listens for Redis pub/sub messages."""
        try:
            async for message in self.pubsub.listen():
                if not self._is_running:
                    break
                
                if message['type'] == 'message':
                    await self._handle_redis_message(message)
        
        except asyncio.CancelledError:
            # Expected when stopping
            pass
        except Exception as e:
            if self.logger:
                await self.logger.error(
                    f"Error in Redis listener loop: {str(e)}",
                    context={"error": str(e)}
                )
    
    async def _handle_redis_message(self, message: Dict[str, Any]) -> None:
        """Handles received Redis message."""
        try:
            # Extract event name from channel
            channel = message['channel'].decode('utf-8')
            event_name = channel.replace(f"{self.channel_prefix}.", "")
            
            # Parse event data
            event_data = json.loads(message['data'].decode('utf-8'))
            event = await self._create_event_from_data(event_data)
            
            # Process with handlers
            handlers = self._handlers.get(event_name, [])
            
            if not handlers:
                if self.logger:
                    await self.logger.debug(
                        f"No handlers found for Redis event: {event_name}",
                        context={"event_id": event.event_id}
                    )
                return
            
            # Execute handlers in parallel
            tasks = []
            for handler in handlers:
                tasks.append(self._execute_handler_with_retry(handler, event, event_name))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log any failures
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    if self.logger:
                        await self.logger.error(
                            f"Redis event handler failed: {str(result)}",
                            context={
                                "event_id": event.event_id,
                                "event_name": event_name,
                                "handler_index": i
                            }
                        )
        
        except Exception as e:
            if self.logger:
                await self.logger.error(
                    f"Error handling Redis message: {str(e)}",
                    context={"error": str(e)}
                )
    
    async def _create_event_from_data(self, event_data: Dict[str, Any]) -> BaseEvent:
        """Creates event from Redis message data."""
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
                        f"Redis handler attempt {attempt_num} failed: {str(e)}",
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
                f"Redis handler failed after {max_attempts} attempts: {str(last_error)}",
                context={
                    "event_id": event.event_id,
                    "event_name": event_name,
                    "final_error": str(last_error)
                }
            )
        
        raise InfrastructureException(
            message=f"Redis event handler failed after {max_attempts} attempts: {str(last_error)}",
            error_code="12010006",
            operation="execute_redis_handler",
            original_error=str(last_error)
        )