"""
Event Bus Port - Domain contract for event publishing and subscription
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Callable, Optional, Awaitable
from datetime import datetime, timezone

EventHandler = Callable[['BaseEvent'], Awaitable[None]]


class BaseEvent:
    """
    Base event class following the specified format.
    
    Format:
    {
        "eventId": "uuid",
        "eventName": "UserCreated", 
        "eventVersion": "1.0",
        "source": "industrial_prom",
        "timestamp": "ISO8601",
        "data": {},
        "metadata": {
            "microservice": "users-service",
            "functionality": "create-user", 
            "correlationId": "uuid"
        },
        "createdAt": "ISO8601",
        "updatedAt": "ISO8601", 
        "status": "published|failed|processed"
    }
    """
    
    def __init__(
        self,
        event_name: str,
        source: str,
        data: Dict[str, Any],
        microservice: str,
        functionality: str,
        correlation_id: Optional[str] = None,
        event_version: str = "1.0",
        event_id: Optional[str] = None
    ):
        from uuid import uuid4
        from datetime import datetime, timezone
        
        self.event_id = event_id or str(uuid4())
        self.event_name = event_name
        self.event_version = event_version
        self.source = source
        self.timestamp = datetime.now(timezone.utc)
        self.data = data
        self.metadata = {
            "microservice": microservice,
            "functionality": functionality,
            "correlationId": correlation_id or str(uuid4())
        }
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.status = "created"
    
    def mark_as_published(self) -> None:
        """Marks event as published."""
        from datetime import datetime, timezone
        self.status = "published"
        self.updated_at = datetime.now(timezone.utc)
    
    def mark_as_failed(self) -> None:
        """Marks event as failed."""
        from datetime import datetime, timezone
        self.status = "failed"
        self.updated_at = datetime.now(timezone.utc)
    
    def mark_as_processed(self) -> None:
        """Marks event as processed."""
        from datetime import datetime, timezone
        self.status = "processed"
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts event to dictionary."""
        return {
            "eventId": self.event_id,
            "eventName": self.event_name,
            "eventVersion": self.event_version,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "metadata": self.metadata,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
            "status": self.status
        }
    
    def to_json(self) -> str:
        """Converts event to JSON string."""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    def is_valid(self) -> bool:
        """
        Validates that event has all required fields.
        
        Returns:
            True if event is valid
        """
        return all([
            self.event_name,
            self.source,
            self.metadata.get("microservice"),
            self.metadata.get("functionality")
        ])


class DomainEvent(BaseEvent):
    """Domain event for business logic changes."""
    
    def __init__(
        self,
        event_name: str,
        source: str,
        data: Dict[str, Any],
        microservice: str,
        functionality: str,
        aggregate_id: Optional[str] = None,
        aggregate_type: Optional[str] = None,
        aggregate_version: Optional[int] = None,
        correlation_id: Optional[str] = None,
        event_version: str = "1.0"
    ):
        super().__init__(
            event_name=event_name,
            source=source,
            data=data,
            microservice=microservice,
            functionality=functionality,
            correlation_id=correlation_id,
            event_version=event_version
        )
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type
        self.aggregate_version = aggregate_version
        self.event_type = "domain"
        
        # Add to metadata
        self.metadata.update({
            "eventType": "domain"
        })
        if aggregate_id:
            self.metadata["aggregateId"] = aggregate_id
        if aggregate_type:
            self.metadata["aggregateType"] = aggregate_type
        if aggregate_version is not None:
            self.metadata["aggregateVersion"] = aggregate_version


class IntegrationEvent(BaseEvent):
    """Integration event for cross-microservice communication."""
    
    def __init__(
        self,
        event_name: str,
        source: str,
        target_services: List[str],
        data: Dict[str, Any],
        microservice: str,
        functionality: str,
        correlation_id: Optional[str] = None,
        event_version: str = "1.0"
    ):
        super().__init__(
            event_name=event_name,
            source=source,
            data=data,
            microservice=microservice,
            functionality=functionality,
            correlation_id=correlation_id,
            event_version=event_version
        )
        self.target_services = target_services
        self.event_type = "integration"
        
        self.metadata.update({
            "targetServices": target_services,
            "eventType": "integration"
        })


class SystemEvent(BaseEvent):
    """System event for infrastructure/operational concerns."""
    
    def __init__(
        self,
        event_name: str,
        source: str,
        severity: str,
        data: Dict[str, Any],
        microservice: str,
        functionality: str,
        system_component: Optional[str] = None,
        correlation_id: Optional[str] = None,
        event_version: str = "1.0"
    ):
        super().__init__(
            event_name=event_name,
            source=source,
            data=data,
            microservice=microservice,
            functionality=functionality,
            correlation_id=correlation_id,
            event_version=event_version
        )
        self.severity = severity
        self.system_component = system_component
        self.event_type = "system"
        
        self.metadata.update({
            "severity": severity,
            "eventType": "system"
        })
        if system_component:
            self.metadata["systemComponent"] = system_component


class EventBus(ABC):
    """
    Abstract Event Bus port for hexagonal architecture.
    
    This interface defines the contract for event publishing and subscription
    without coupling to specific messaging technologies (Kafka, RabbitMQ, etc.).
    """
    
    @abstractmethod
    async def publish(self, event: BaseEvent) -> None:
        """
        Publishes an event to the event bus.
        
        Args:
            event: Event to publish
            
        Raises:
            DomainException: If event validation fails
            ApplicationException: If publishing logic fails
        """
        pass
    
    @abstractmethod
    async def publish_batch(self, events: List[BaseEvent]) -> None:
        """
        Publishes multiple events in batch.
        
        Args:
            events: List of events to publish
            
        Raises:
            ApplicationException: If batch publishing fails
        """
        pass
    
    @abstractmethod
    async def subscribe(
        self,
        event_name: str,
        handler: EventHandler,
        retry_policy: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Subscribes a handler to an event.
        
        Args:
            event_name: Name of event to subscribe to
            handler: Event handler function
            retry_policy: Optional retry configuration
            
        Raises:
            ApplicationException: If subscription fails
        """
        pass
    
    @abstractmethod
    async def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        """
        Unsubscribes a handler from an event.
        
        Args:
            event_name: Name of event to unsubscribe from
            handler: Event handler to remove
        """
        pass


class EventStore(ABC):
    """
    Abstract Event Store for persisting events.
    
    Enables event sourcing and audit trails.
    """
    
    @abstractmethod
    async def save_event(self, event: BaseEvent) -> None:
        """
        Persists an event.
        
        Args:
            event: Event to persist
        """
        pass
    
    @abstractmethod
    async def get_events_by_source(
        self,
        source: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[BaseEvent]:
        """
        Retrieves events by source.
        
        Args:
            source: Event source
            limit: Maximum number of events
            offset: Offset for pagination
            
        Returns:
            List of events
        """
        pass
    
    @abstractmethod
    async def get_events_by_name(
        self,
        event_name: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[BaseEvent]:
        """
        Retrieves events by name.
        
        Args:
            event_name: Event name
            limit: Maximum number of events
            offset: Offset for pagination
            
        Returns:
            List of events
        """
        pass