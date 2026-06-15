"""
Base Event System - Event system for microservices
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic, Type
from datetime import datetime, timezone
from dataclasses import dataclass
import uuid
import json


T = TypeVar('T')


@dataclass
class EventMetadata:
    """Event metadata for traceability."""
    event_id: str
    timestamp: datetime
    source_service: str
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts metadata to dictionary."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "source_service": self.source_service,
            "correlation_id": self.correlation_id,
            "trace_id": self.trace_id,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventMetadata':
        """Creates metadata from dictionary."""
        return cls(
            event_id=data["event_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source_service=data["source_service"],
            correlation_id=data.get("correlation_id"),
            trace_id=data.get("trace_id"),
            user_id=data.get("user_id"),
            request_id=data.get("request_id"),
            version=data.get("version", "1.0")
        )


class BaseEvent(ABC, Generic[T]):
    """
    Base event for the event system.
    
    All system events must inherit from this class
    and provide a typed payload.
    """
    
    def __init__(
        self,
        payload: T,
        event_type: str,
        source_service: str,
        correlation_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        self.payload = payload
        self.event_type = event_type
        self.metadata = EventMetadata(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            source_service=source_service,
            correlation_id=correlation_id,
            trace_id=trace_id,
            user_id=user_id,
            request_id=request_id
        )
    
    @property
    def event_id(self) -> str:
        """Unique event ID."""
        return self.metadata.event_id
    
    @property
    def timestamp(self) -> datetime:
        """Event timestamp."""
        return self.metadata.timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes complete event to dictionary.
        
        Returns:
            Dictionary with complete event
        """
        return {
            "event_type": self.event_type,
            "payload": self._serialize_payload(),
            "metadata": self.metadata.to_dict()
        }
    
    def to_json(self) -> str:
        """
        Serializes event to JSON.
        
        Returns:
            JSON string of the event
        """
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], payload_class: Type[T]) -> 'BaseEvent[T]':
        """
        Deserializes event from dictionary.
        
        Args:
            data: Event data
            payload_class: Payload class
            
        Returns:
            Event instance
        """
        metadata = EventMetadata.from_dict(data["metadata"])
        payload = payload_class(**data["payload"]) if hasattr(payload_class, '__init__') else data["payload"]
        
        event = cls(
            payload=payload,
            event_type=data["event_type"],
            source_service=metadata.source_service,
            correlation_id=metadata.correlation_id,
            trace_id=metadata.trace_id,
            user_id=metadata.user_id,
            request_id=metadata.request_id
        )
        event.metadata = metadata  # Preserve original metadata
        return event
    
    @classmethod
    def from_json(cls, json_str: str, payload_class: Type[T]) -> 'BaseEvent[T]':
        """
        Deserializes event from JSON.
        
        Args:
            json_str: JSON string
            payload_class: Payload class
            
        Returns:
            Event instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data, payload_class)
    
    def _serialize_payload(self) -> Any:
        """
        Serializes event payload.
        
        Override this method for complex payloads.
        """
        if hasattr(self.payload, 'dict'):
            return self.payload.dict()
        elif hasattr(self.payload, '__dict__'):
            return self.payload.__dict__
        else:
            return self.payload
    
    def __str__(self) -> str:
        return f"{self.event_type}({self.event_id})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(event_type='{self.event_type}', event_id='{self.event_id}')"


class DomainEvent(BaseEvent[T]):
    """Domain event - represents something that happened in the business."""
    
    def __init__(self, payload: T, event_type: str, **kwargs):
        super().__init__(payload, event_type, **kwargs)


class IntegrationEvent(BaseEvent[T]):
    """Integration event - for communication between microservices."""
    
    def __init__(
        self,
        payload: T,
        event_type: str,
        target_service: Optional[str] = None,
        **kwargs
    ):
        super().__init__(payload, event_type, **kwargs)
        self.target_service = target_service
    
    def to_dict(self) -> Dict[str, Any]:
        """Includes target_service in serialization."""
        data = super().to_dict()
        data["target_service"] = self.target_service
        return data


class SystemEvent(BaseEvent[T]):
    """System event - for technical/infrastructure events."""
    
    def __init__(self, payload: T, event_type: str, severity: str = "INFO", **kwargs):
        super().__init__(payload, event_type, **kwargs)
        self.severity = severity
    
    def to_dict(self) -> Dict[str, Any]:
        """Includes severity in serialization."""
        data = super().to_dict()
        data["severity"] = self.severity
        return data


# Common predefined events

class UserCreatedEvent(DomainEvent[Dict[str, Any]]):
    """Event: User created."""
    
    def __init__(self, user_data: Dict[str, Any], **kwargs):
        super().__init__(
            payload=user_data,
            event_type="user.created",
            **kwargs
        )


class UserUpdatedEvent(DomainEvent[Dict[str, Any]]):
    """Event: User updated."""
    
    def __init__(self, user_data: Dict[str, Any], **kwargs):
        super().__init__(
            payload=user_data,
            event_type="user.updated",
            **kwargs
        )


class UserDeletedEvent(DomainEvent[Dict[str, Any]]):
    """Event: User deleted."""
    
    def __init__(self, user_id: str, reason: Optional[str] = None, **kwargs):
        super().__init__(
            payload={"user_id": user_id, "reason": reason},
            event_type="user.deleted",
            **kwargs
        )


class EntityCreatedEvent(DomainEvent[Dict[str, Any]]):
    """Generic event: Entity created."""
    
    def __init__(self, entity_type: str, entity_data: Dict[str, Any], **kwargs):
        super().__init__(
            payload={"entity_type": entity_type, "data": entity_data},
            event_type=f"{entity_type.lower()}.created",
            **kwargs
        )


class EntityUpdatedEvent(DomainEvent[Dict[str, Any]]):
    """Generic event: Entity updated."""
    
    def __init__(self, entity_type: str, entity_data: Dict[str, Any], **kwargs):
        super().__init__(
            payload={"entity_type": entity_type, "data": entity_data},
            event_type=f"{entity_type.lower()}.updated",
            **kwargs
        )


class EntityDeletedEvent(DomainEvent[Dict[str, Any]]):
    """Generic event: Entity deleted."""
    
    def __init__(self, entity_type: str, entity_id: str, **kwargs):
        super().__init__(
            payload={"entity_type": entity_type, "entity_id": entity_id},
            event_type=f"{entity_type.lower()}.deleted",
            **kwargs
        )