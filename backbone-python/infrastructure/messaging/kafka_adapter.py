"""
Kafka Event Bus Adapter - Infrastructure implementation for Apache Kafka
"""
from typing import Any, Dict, List, Optional, Callable
import asyncio
import json
from backbone.domain.ports.event_bus import EventBus, BaseEvent, EventHandler
from backbone.domain.exceptions import BaseKernelException
from ..exceptions import InfrastructureException
from backbone.infrastructure.logging.structured_logger import StructuredLogger

try:
    from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
    from aiokafka.errors import KafkaError
    _kafka_available = True
except ImportError:
    _kafka_available = False


class KafkaEventBusAdapter(EventBus):
    """
    Kafka adapter implementing EventBus port.
    
    Features:
    - Asynchronous Kafka producer/consumer
    - Topic-based event routing
    - Configurable serialization
    - Error handling with proper exceptions
    - Connection management
    """
    
    def __init__(
        self,
        bootstrap_servers: str,
        topic_prefix: str = "events",
        group_id: str = "backbone-consumer",
        logger: Optional[StructuredLogger] = None
    ):
        if not _kafka_available:
            raise InfrastructureException(
                message="Kafka adapter requires aiokafka package",
                error_code="12008001",
                operation="init_kafka_adapter"
            )
        
        self.bootstrap_servers = bootstrap_servers
        self.topic_prefix = topic_prefix
        self.group_id = group_id
        self.logger = logger
        
        self._producer: Optional[AIOKafkaProducer] = None
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._retry_policies: Dict[str, Dict[str, Any]] = {}
        self._consumer_task: Optional[asyncio.Task] = None
        self._is_running = False
    
    async def start(self) -> None:
        """Starts Kafka producer and consumer."""
        try:
            # Initialize producer
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: str(k).encode('utf-8') if k else None
            )
            await self._producer.start()
            
            # Initialize consumer
            self._consumer = AIOKafkaConsumer(
                group_id=self.group_id,
                bootstrap_servers=self.bootstrap_servers,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='latest'
            )
            await self._consumer.start()
            
            self._is_running = True
            
            # Start consumer task
            self._consumer_task = asyncio.create_task(self._consume_messages())
            
            if self.logger:
                await self.logger.info(
                    "Kafka event bus started",
                    context={
                        "bootstrap_servers": self.bootstrap_servers,
                        "group_id": self.group_id
                    }
                )
        
        except Exception as e:
            raise InfrastructureException(
                message=f"Failed to start Kafka event bus: {str(e)}",
                error_code="12008002",
                operation="start_kafka_bus",
                original_error=str(e)
            )
    
    async def stop(self) -> None:
        """Stops Kafka producer and consumer."""
        try:
            self._is_running = False
            
            # Cancel consumer task
            if self._consumer_task:
                self._consumer_task.cancel()
                try:
                    await self._consumer_task
                except asyncio.CancelledError:
                    pass
            
            # Stop producer and consumer
            if self._producer:
                await self._producer.stop()
            
            if self._consumer:
                await self._consumer.stop()
            
            if self.logger:
                await self.logger.info("Kafka event bus stopped")
        
        except Exception as e:
            if self.logger:
                await self.logger.warning(f"Error stopping Kafka event bus: {str(e)}")
    
    async def publish(self, event: BaseEvent) -> None:
        """Publishes event to Kafka topic."""
        if not self._is_running:
            await self.start()
        
        try:
            topic = f"{self.topic_prefix}.{event.event_name}"
            event_data = event.to_dict()
            
            # Send to Kafka
            await self._producer.send_and_wait(
                topic,
                value=event_data,
                key=event.event_id
            )
            
            event.mark_as_published()
            
            if self.logger:
                await self.logger.info(
                    f"Event published to Kafka: {event.event_name}",
                    context={
                        "event_id": event.event_id,
                        "topic": topic,
                        "microservice": event.metadata.get("microservice"),
                        "correlation_id": event.metadata.get("correlationId")
                    }
                )
        
        except KafkaError as e:
            event.mark_as_failed()
            raise InfrastructureException(
                message=f"Failed to publish event to Kafka: {str(e)}",
                error_code="12008003",
                operation="publish_kafka_event",
                original_error=str(e)
            )
        except Exception as e:
            event.mark_as_failed()
            raise InfrastructureException(
                message=f"Unexpected error publishing to Kafka: {str(e)}",
                error_code="12008004",
                operation="publish_kafka_event",
                original_error=str(e)
            )
    
    async def publish_batch(self, events: List[BaseEvent]) -> None:
        """Publishes batch of events to Kafka."""
        if not self._is_running:
            await self.start()
        
        try:
            # Send all events
            for event in events:
                topic = f"{self.topic_prefix}.{event.event_name}"
                event_data = event.to_dict()
                
                await self._producer.send_and_wait(
                    topic,
                    value=event_data,
                    key=event.event_id
                )
                
                event.mark_as_published()
            
            if self.logger:
                await self.logger.info(
                    f"Batch of {len(events)} events published to Kafka",
                    context={"event_count": len(events)}
                )
        
        except Exception as e:
            # Mark all events as failed
            for event in events:
                event.mark_as_failed()
            
            raise InfrastructureException(
                message=f"Failed to publish event batch to Kafka: {str(e)}",
                error_code="12008005",
                operation="publish_kafka_batch",
                original_error=str(e)
            )
    
    async def subscribe(
        self,
        event_name: str,
        handler: EventHandler,
        retry_policy: Optional[Dict[str, Any]] = None
    ) -> None:
        """Subscribes to events from Kafka topic."""
        try:
            topic = f"{self.topic_prefix}.{event_name}"
            
            # Store handler
            if event_name not in self._handlers:
                self._handlers[event_name] = []
            self._handlers[event_name].append(handler)
            
            # Store retry policy
            if retry_policy:
                self._retry_policies[event_name] = retry_policy
            
            # Subscribe to topic
            if self._consumer:
                self._consumer.subscribe([topic])
            
            if self.logger:
                await self.logger.info(
                    f"Subscribed to Kafka events: {event_name}",
                    context={
                        "topic": topic,
                        "handler": handler.__name__
                    }
                )
        
        except Exception as e:
            raise InfrastructureException(
                message=f"Failed to subscribe to Kafka events: {str(e)}",
                error_code="12008006",
                operation="subscribe_kafka_events",
                original_error=str(e)
            )
    
    async def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        """Unsubscribes from Kafka events."""
        if event_name in self._handlers:
            if handler in self._handlers[event_name]:
                self._handlers[event_name].remove(handler)
            
            # Remove retry policy if no more handlers
            if not self._handlers[event_name]:
                if event_name in self._retry_policies:
                    del self._retry_policies[event_name]
        
        if self.logger:
            await self.logger.info(
                f"Unsubscribed from Kafka events: {event_name}",
                context={"handler": handler.__name__}
            )
    
    async def _consume_messages(self) -> None:
        """Consumes messages from Kafka topics."""
        try:
            async for message in self._consumer:
                if not self._is_running:
                    break
                
                try:
                    # Extract event name from topic
                    topic = message.topic
                    event_name = topic.replace(f"{self.topic_prefix}.", "")
                    
                    # Get event data
                    event_data = message.value
                    
                    # Create event from data
                    event = await self._create_event_from_data(event_data)
                    
                    # Process event with handlers
                    await self._process_event(event_name, event)
                
                except Exception as e:
                    if self.logger:
                        await self.logger.error(
                            f"Error processing Kafka message: {str(e)}",
                            context={
                                "topic": message.topic,
                                "offset": message.offset,
                                "error": str(e)
                            }
                        )
        
        except asyncio.CancelledError:
            # Expected when stopping
            pass
        except Exception as e:
            if self.logger:
                await self.logger.error(
                    f"Error in Kafka consumer loop: {str(e)}",
                    context={"error": str(e)}
                )
    
    async def _create_event_from_data(self, event_data: Dict[str, Any]) -> BaseEvent:
        """Creates event from Kafka message data."""
        # Create BaseEvent from message data
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
    
    async def _process_event(self, event_name: str, event: BaseEvent) -> None:
        """Processes event with registered handlers."""
        handlers = self._handlers.get(event_name, [])
        
        if not handlers:
            if self.logger:
                await self.logger.debug(
                    f"No handlers found for Kafka event: {event_name}",
                    context={"event_id": event.event_id}
                )
            return
        
        # Execute handlers in parallel
        tasks = []
        for handler in handlers:
            tasks.append(self._execute_handler_with_retry(handler, event, event_name))
        
        # Wait for all handlers
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any failures
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                if self.logger:
                    await self.logger.error(
                        f"Kafka event handler failed: {str(result)}",
                        context={
                            "event_id": event.event_id,
                            "event_name": event_name,
                            "handler_index": i
                        }
                    )
    
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
                        f"Kafka handler attempt {attempt_num} failed: {str(e)}",
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
                f"Kafka handler failed after {max_attempts} attempts: {str(last_error)}",
                context={
                    "event_id": event.event_id,
                    "event_name": event_name,
                    "final_error": str(last_error)
                }
            )
        
        raise InfrastructureException(
            message=f"Kafka event handler failed after {max_attempts} attempts: {str(last_error)}",
            error_code="12008007",
            operation="execute_kafka_handler",
            original_error=str(last_error)
        )