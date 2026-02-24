"""
Event Store - JSON-based event persistence system
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, AsyncIterator
from datetime import datetime, timezone
import json
import os
import aiofiles
from pathlib import Path
from .base_event import BaseEvent
from ..logging.structured_logger import StructuredLogger
from ..exceptions.infrastructure_exceptions import InfrastructureException


class IEventStore(ABC):
    """Contract for event persistence."""
    
    @abstractmethod
    async def save_event(self, event: BaseEvent[Any]) -> None:
        """
        Saves an event to persistent storage.
        
        Args:
            event: Event to save
        """
        pass
    
    @abstractmethod
    async def save_events(self, events: List[BaseEvent[Any]]) -> None:
        """
        Saves multiple events to persistent storage.
        
        Args:
            events: List of events to save
        """
        pass
    
    @abstractmethod
    async def get_events_by_type(
        self, 
        event_type: str, 
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[BaseEvent[Any]]:
        """
        Retrieves events by type.
        
        Args:
            event_type: Type of events to retrieve
            limit: Maximum number of events to return
            offset: Number of events to skip
            
        Returns:
            List of events
        """
        pass
    
    @abstractmethod
    async def get_events_by_correlation_id(
        self, 
        correlation_id: str
    ) -> List[BaseEvent[Any]]:
        """
        Retrieves events by correlation ID.
        
        Args:
            correlation_id: Correlation ID to search for
            
        Returns:
            List of related events
        """
        pass
    
    @abstractmethod
    async def get_events_since(
        self, 
        since: datetime
    ) -> AsyncIterator[BaseEvent[Any]]:
        """
        Retrieves events since a specific timestamp.
        
        Args:
            since: Timestamp to search from
            
        Yields:
            Events since the timestamp
        """
        pass


class JsonFileEventStore(IEventStore):
    """
    JSON file-based event store.
    
    Stores events in individual JSON files organized by date
    for better performance and organization.
    
    Structure:
    /events
      /2024-01-15
        /user.created
          event_123.json
          event_456.json
        /user.updated
          event_789.json
    """
    
    def __init__(
        self, 
        base_path: str = "./events",
        logger: Optional[StructuredLogger] = None
    ):
        self.base_path = Path(base_path)
        self.logger = logger
        self._ensure_base_directory()
    
    def _ensure_base_directory(self):
        """Ensures base events directory exists."""
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_event_path(self, event: BaseEvent[Any]) -> Path:
        """
        Gets the file path for an event.
        
        Args:
            event: Event to get path for
            
        Returns:
            Path where event should be stored
        """
        # Organize by date and event type
        date_str = event.timestamp.strftime("%Y-%m-%d")
        event_dir = self.base_path / date_str / event.event_type
        event_dir.mkdir(parents=True, exist_ok=True)
        
        return event_dir / f"{event.event_id}.json"
    
    async def save_event(self, event: BaseEvent[Any]) -> None:
        """Saves single event to JSON file."""
        try:
            event_path = self._get_event_path(event)
            event_data = event.to_dict()
            
            async with aiofiles.open(event_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(event_data, indent=2, default=str))
            
            if self.logger:
                await self.logger.info(
                    f"Event saved to file: {event.event_type}",
                    context={
                        "event_id": event.event_id,
                        "file_path": str(event_path),
                        "event_type": event.event_type
                    }
                )
        
        except Exception as e:
            raise InfrastructureException(
                message=f"Failed to save event to file: {str(e)}",
                error_code="12006001",
                operation="save_event",
                original_error=str(e)
            )
    
    async def save_events(self, events: List[BaseEvent[Any]]) -> None:
        """Saves multiple events."""
        for event in events:
            await self.save_event(event)
    
    async def get_events_by_type(
        self, 
        event_type: str, 
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[BaseEvent[Any]]:
        """Retrieves events by type from JSON files."""
        try:
            events = []
            
            # Search across all date directories
            for date_dir in sorted(self.base_path.iterdir()):
                if not date_dir.is_dir():
                    continue
                
                event_type_dir = date_dir / event_type
                if not event_type_dir.exists():
                    continue
                
                # Read all event files in this type directory
                for event_file in sorted(event_type_dir.glob("*.json")):
                    try:
                        async with aiofiles.open(event_file, 'r', encoding='utf-8') as f:
                            content = await f.read()
                            event_data = json.loads(content)
                            
                            # Create generic event from data
                            event = await self._create_event_from_data(event_data)
                            events.append(event)
                            
                    except Exception as e:
                        if self.logger:
                            await self.logger.warning(
                                f"Failed to read event file: {event_file}",
                                context={"error": str(e)}
                            )
                        continue
            
            # Apply pagination
            if offset > 0:
                events = events[offset:]
            if limit:
                events = events[:limit]
            
            return events
            
        except Exception as e:
            raise InfrastructureException(
                message=f"Failed to retrieve events by type: {str(e)}",
                error_code="12006002",
                operation="get_events_by_type",
                original_error=str(e)
            )
    
    async def get_events_by_correlation_id(
        self, 
        correlation_id: str
    ) -> List[BaseEvent[Any]]:
        """Retrieves events by correlation ID."""
        try:
            events = []
            
            # Search across all directories and files
            for date_dir in self.base_path.iterdir():
                if not date_dir.is_dir():
                    continue
                
                for event_type_dir in date_dir.iterdir():
                    if not event_type_dir.is_dir():
                        continue
                    
                    for event_file in event_type_dir.glob("*.json"):
                        try:
                            async with aiofiles.open(event_file, 'r', encoding='utf-8') as f:
                                content = await f.read()
                                event_data = json.loads(content)
                                
                                # Check if correlation_id matches
                                if (
                                    event_data.get("metadata", {}).get("correlation_id") == 
                                    correlation_id
                                ):
                                    event = await self._create_event_from_data(event_data)
                                    events.append(event)
                                    
                        except Exception:
                            continue
            
            # Sort by timestamp
            events.sort(key=lambda e: e.timestamp)
            return events
            
        except Exception as e:
            raise InfrastructureException(
                message=f"Failed to retrieve events by correlation ID: {str(e)}",
                error_code="12006003",
                operation="get_events_by_correlation_id",
                original_error=str(e)
            )
    
    async def get_events_since(
        self, 
        since: datetime
    ) -> AsyncIterator[BaseEvent[Any]]:
        """Retrieves events since timestamp."""
        try:
            # Convert since to UTC if it has timezone info
            if since.tzinfo is not None:
                since_utc = since.astimezone(timezone.utc)
            else:
                since_utc = since.replace(tzinfo=timezone.utc)
            
            # Get date directories to search
            since_date = since_utc.date()
            
            for date_dir in sorted(self.base_path.iterdir()):
                if not date_dir.is_dir():
                    continue
                
                try:
                    dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d").date()
                    if dir_date < since_date:
                        continue
                except ValueError:
                    continue
                
                # Search in this date directory
                for event_type_dir in date_dir.iterdir():
                    if not event_type_dir.is_dir():
                        continue
                    
                    for event_file in sorted(event_type_dir.glob("*.json")):
                        try:
                            async with aiofiles.open(event_file, 'r', encoding='utf-8') as f:
                                content = await f.read()
                                event_data = json.loads(content)
                                
                                # Check timestamp
                                event_timestamp = datetime.fromisoformat(
                                    event_data["metadata"]["timestamp"]
                                )
                                
                                if event_timestamp >= since_utc:
                                    event = await self._create_event_from_data(event_data)
                                    yield event
                                    
                        except Exception:
                            continue
                            
        except Exception as e:
            raise InfrastructureException(
                message=f"Failed to retrieve events since timestamp: {str(e)}",
                error_code="12006004",
                operation="get_events_since",
                original_error=str(e)
            )
    
    async def _create_event_from_data(self, event_data: Dict[str, Any]) -> BaseEvent[Any]:
        """
        Creates a generic event from stored data.
        
        Args:
            event_data: Event data from JSON
            
        Returns:
            Generic BaseEvent instance
        """
        # Create a simple generic event class
        class StoredEvent(BaseEvent[Dict[str, Any]]):
            def __init__(self, event_data: Dict[str, Any]):
                # Extract data from stored format
                payload = event_data["payload"]
                event_type = event_data["event_type"]
                metadata = event_data["metadata"]
                
                super().__init__(
                    payload=payload,
                    event_type=event_type,
                    source_service=metadata["source_service"],
                    correlation_id=metadata.get("correlation_id"),
                    trace_id=metadata.get("trace_id"),
                    user_id=metadata.get("user_id"),
                    request_id=metadata.get("request_id")
                )
                
                # Restore original metadata
                self.metadata.event_id = metadata["event_id"]
                self.metadata.timestamp = datetime.fromisoformat(metadata["timestamp"])
                self.metadata.version = metadata.get("version", "1.0")
        
        return StoredEvent(event_data)
    
    async def get_event_statistics(self) -> Dict[str, Any]:
        """
        Gets statistics about stored events.
        
        Returns:
            Dictionary with event statistics
        """
        try:
            stats = {
                "total_events": 0,
                "events_by_type": {},
                "events_by_date": {},
                "date_range": {"earliest": None, "latest": None}
            }
            
            dates = []
            
            for date_dir in self.base_path.iterdir():
                if not date_dir.is_dir():
                    continue
                
                try:
                    date_str = date_dir.name
                    dates.append(date_str)
                    
                    date_events = 0
                    
                    for event_type_dir in date_dir.iterdir():
                        if not event_type_dir.is_dir():
                            continue
                        
                        event_type = event_type_dir.name
                        type_count = len(list(event_type_dir.glob("*.json")))
                        
                        stats["events_by_type"][event_type] = (
                            stats["events_by_type"].get(event_type, 0) + type_count
                        )
                        date_events += type_count
                    
                    stats["events_by_date"][date_str] = date_events
                    stats["total_events"] += date_events
                    
                except ValueError:
                    continue
            
            # Set date range
            if dates:
                dates.sort()
                stats["date_range"]["earliest"] = dates[0]
                stats["date_range"]["latest"] = dates[-1]
            
            return stats
            
        except Exception as e:
            if self.logger:
                await self.logger.error(
                    f"Failed to get event statistics: {str(e)}",
                    context={"error": str(e)}
                )
            return {"error": str(e)}


class EventStoreFactory:
    """Factory for creating event store instances."""
    
    @staticmethod
    def create_json_file_store(
        base_path: str = "./events",
        logger: Optional[StructuredLogger] = None
    ) -> JsonFileEventStore:
        """Creates JSON file-based event store."""
        return JsonFileEventStore(base_path, logger)
    
    @staticmethod
    def create_memory_store() -> 'InMemoryEventStore':
        """Creates in-memory event store for testing."""
        return InMemoryEventStore()


class InMemoryEventStore(IEventStore):
    """In-memory event store for testing."""
    
    def __init__(self):
        self._events: List[BaseEvent[Any]] = []
    
    async def save_event(self, event: BaseEvent[Any]) -> None:
        """Saves event to memory."""
        self._events.append(event)
    
    async def save_events(self, events: List[BaseEvent[Any]]) -> None:
        """Saves multiple events to memory."""
        self._events.extend(events)
    
    async def get_events_by_type(
        self, 
        event_type: str, 
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[BaseEvent[Any]]:
        """Gets events by type from memory."""
        filtered = [e for e in self._events if e.event_type == event_type]
        
        if offset > 0:
            filtered = filtered[offset:]
        if limit:
            filtered = filtered[:limit]
        
        return filtered
    
    async def get_events_by_correlation_id(
        self, 
        correlation_id: str
    ) -> List[BaseEvent[Any]]:
        """Gets events by correlation ID from memory."""
        return [
            e for e in self._events 
            if e.metadata.correlation_id == correlation_id
        ]
    
    async def get_events_since(
        self, 
        since: datetime
    ) -> AsyncIterator[BaseEvent[Any]]:
        """Gets events since timestamp from memory."""
        for event in self._events:
            if event.timestamp >= since:
                yield event
    
    async def get_event_by_id(self, event_id: str) -> Optional[BaseEvent[Any]]:
        """
        Gets event by ID from memory.
        
        Args:
            event_id: Event ID to search for
            
        Returns:
            Event if found, None otherwise
        """
        for event in self._events:
            if event.event_id == event_id:
                return event
        return None
    
    def clear(self) -> None:
        """Clears all events (for testing)."""
        self._events.clear()
    
    def get_all_events(self) -> List[BaseEvent[Any]]:
        """Gets all stored events (for testing)."""
        return self._events.copy()