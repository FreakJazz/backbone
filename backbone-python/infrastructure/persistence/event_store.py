"""
Event Store Implementation - Infrastructure layer event persistence
"""
from typing import List, Optional, Dict, Any
import os
import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from backbone.domain.ports.event_bus import EventStore, BaseEvent
from ..exceptions import InfrastructureException
from backbone.infrastructure.logging.structured_logger import StructuredLogger

try:
    import aiofiles
    _aiofiles_available = True
except ImportError:
    _aiofiles_available = False


class JsonFileEventStore(EventStore):
    """
    JSON-based file event store for persistence.
    
    Features:
    - Date-organized file structure
    - Asynchronous file operations  
    - Event indexing by source and name
    - Configurable retention
    """
    
    def __init__(
        self,
        storage_path: str = "events",
        logger: Optional[StructuredLogger] = None
    ):
        self.storage_path = Path(storage_path)
        self.logger = logger
        
        # Create storage directory
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create index directory
        self.index_path = self.storage_path / "indexes"
        self.index_path.mkdir(exist_ok=True)
    
    async def save_event(self, event: BaseEvent) -> None:
        """Saves event to JSON file organized by date."""
        if not _aiofiles_available:
            # Fallback to synchronous implementation
            await self._save_event_sync(event)
            return
        
        try:
            # Organize by date
            date_str = event.created_at.strftime("%Y-%m-%d")
            date_dir = self.storage_path / date_str
            date_dir.mkdir(exist_ok=True)
            
            # Save to file named by event ID
            file_path = date_dir / f"{event.event_id}.json"
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(event.to_json())
            
            # Update indexes
            await self._update_indexes(event, date_str)
            
            if self.logger:
                await self.logger.debug(
                    f"Event saved to storage: {event.event_name}",
                    context={
                        "event_id": event.event_id,
                        "file_path": str(file_path)
                    }
                )
        
        except Exception as e:
            raise InfrastructureException(
                message=f"Failed to save event to storage: {str(e)}",
                error_code="12011001",
                operation="save_event_to_file",
                original_error=str(e)
            )
    
    async def _save_event_sync(self, event: BaseEvent) -> None:
        """Synchronous fallback for saving events."""
        try:
            # Organize by date
            date_str = event.created_at.strftime("%Y-%m-%d")
            date_dir = self.storage_path / date_str
            date_dir.mkdir(exist_ok=True)
            
            # Save to file named by event ID
            file_path = date_dir / f"{event.event_id}.json"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(event.to_json())
            
            # Update indexes synchronously
            await self._update_indexes_sync(event, date_str)
            
            if self.logger:
                await self.logger.debug(
                    f"Event saved to storage (sync): {event.event_name}",
                    context={
                        "event_id": event.event_id,
                        "file_path": str(file_path)
                    }
                )
        
        except Exception as e:
            raise InfrastructureException(
                message=f"Failed to save event to storage (sync): {str(e)}",
                error_code="12011002",
                operation="save_event_to_file_sync",
                original_error=str(e)
            )
    
    async def get_events_by_source(
        self,
        source: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[BaseEvent]:
        """Retrieves events by source from index."""
        try:
            source_index_file = self.index_path / f"source_{source}.json"
            
            if not source_index_file.exists():
                return []
            
            # Read source index
            if _aiofiles_available:
                async with aiofiles.open(source_index_file, 'r', encoding='utf-8') as f:
                    index_data = json.loads(await f.read())
            else:
                with open(source_index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
            
            # Get event IDs with pagination
            event_ids = index_data.get("event_ids", [])[offset:offset + limit]
            
            # Load events
            events = []
            for event_info in event_ids:
                event_id = event_info["event_id"]
                date_str = event_info["date"]
                
                event = await self._load_event(event_id, date_str)
                if event:
                    events.append(event)
            
            return events
        
        except Exception as e:
            raise InfrastructureException(
                message=f"Failed to get events by source: {str(e)}",
                error_code="12011003",
                operation="get_events_by_source",
                original_error=str(e)
            )
    
    async def get_events_by_name(
        self,
        event_name: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[BaseEvent]:
        """Retrieves events by name from index."""
        try:
            name_index_file = self.index_path / f"name_{event_name}.json"
            
            if not name_index_file.exists():
                return []
            
            # Read name index
            if _aiofiles_available:
                async with aiofiles.open(name_index_file, 'r', encoding='utf-8') as f:
                    index_data = json.loads(await f.read())
            else:
                with open(name_index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
            
            # Get event IDs with pagination
            event_ids = index_data.get("event_ids", [])[offset:offset + limit]
            
            # Load events
            events = []
            for event_info in event_ids:
                event_id = event_info["event_id"]
                date_str = event_info["date"]
                
                event = await self._load_event(event_id, date_str)
                if event:
                    events.append(event)
            
            return events
        
        except Exception as e:
            raise InfrastructureException(
                message=f"Failed to get events by name: {str(e)}",
                error_code="12011004",
                operation="get_events_by_name",
                original_error=str(e)
            )
    
    async def _load_event(self, event_id: str, date_str: str) -> Optional[BaseEvent]:
        """Loads event from file."""
        try:
            file_path = self.storage_path / date_str / f"{event_id}.json"
            
            if not file_path.exists():
                return None
            
            if _aiofiles_available:
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    event_data = json.loads(await f.read())
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    event_data = json.load(f)
            
            # Create event from data
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
            event.timestamp = datetime.fromisoformat(event_data["timestamp"].replace('Z', '+00:00'))
            event.created_at = datetime.fromisoformat(event_data["createdAt"].replace('Z', '+00:00'))
            event.updated_at = datetime.fromisoformat(event_data["updatedAt"].replace('Z', '+00:00'))
            event.status = event_data["status"]
            
            return event
        
        except Exception as e:
            if self.logger:
                await self.logger.warning(
                    f"Failed to load event {event_id}: {str(e)}",
                    context={"event_id": event_id, "date": date_str}
                )
            return None
    
    async def _update_indexes(self, event: BaseEvent, date_str: str) -> None:
        """Updates index files for efficient querying."""
        if not _aiofiles_available:
            await self._update_indexes_sync(event, date_str)
            return
        
        event_info = {
            "event_id": event.event_id,
            "date": date_str,
            "timestamp": event.timestamp.isoformat()
        }
        
        # Update source index
        await self._update_index_file(f"source_{event.source}.json", event_info)
        
        # Update name index
        await self._update_index_file(f"name_{event.event_name}.json", event_info)
    
    async def _update_indexes_sync(self, event: BaseEvent, date_str: str) -> None:
        """Synchronous fallback for updating indexes."""
        event_info = {
            "event_id": event.event_id,
            "date": date_str,
            "timestamp": event.timestamp.isoformat()
        }
        
        # Update source index
        self._update_index_file_sync(f"source_{event.source}.json", event_info)
        
        # Update name index
        self._update_index_file_sync(f"name_{event.event_name}.json", event_info)
    
    async def _update_index_file(self, index_filename: str, event_info: Dict[str, str]) -> None:
        """Updates an index file with new event info."""
        index_file = self.index_path / index_filename
        
        # Load existing index
        if index_file.exists():
            async with aiofiles.open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.loads(await f.read())
        else:
            index_data = {"event_ids": []}
        
        # Add new event (keep sorted by timestamp, most recent first)
        index_data["event_ids"].append(event_info)
        index_data["event_ids"].sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Keep only last 10000 events per index
        index_data["event_ids"] = index_data["event_ids"][:10000]
        
        # Save updated index
        async with aiofiles.open(index_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(index_data, ensure_ascii=False, indent=2))
    
    def _update_index_file_sync(self, index_filename: str, event_info: Dict[str, str]) -> None:
        """Synchronous fallback for updating index files."""
        index_file = self.index_path / index_filename
        
        # Load existing index
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
        else:
            index_data = {"event_ids": []}
        
        # Add new event (keep sorted by timestamp, most recent first)
        index_data["event_ids"].append(event_info)
        index_data["event_ids"].sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Keep only last 10000 events per index
        index_data["event_ids"] = index_data["event_ids"][:10000]
        
        # Save updated index
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)


class InMemoryEventStore(EventStore):
    """
    In-memory event store for testing and development.
    
    Features:
    - Fast in-memory storage
    - Event filtering and searching
    - No persistence (data lost on restart)
    """
    
    def __init__(self, logger: Optional[StructuredLogger] = None):
        self.events: List[BaseEvent] = []
        self.events_by_source: Dict[str, List[BaseEvent]] = {}
        self.events_by_name: Dict[str, List[BaseEvent]] = {}
        self.logger = logger
        self._lock = asyncio.Lock()
    
    async def save_event(self, event: BaseEvent) -> None:
        """Saves event to memory."""
        async with self._lock:
            self.events.append(event)
            
            # Update indexes
            if event.source not in self.events_by_source:
                self.events_by_source[event.source] = []
            self.events_by_source[event.source].append(event)
            
            if event.event_name not in self.events_by_name:
                self.events_by_name[event.event_name] = []
            self.events_by_name[event.event_name].append(event)
            
            if self.logger:
                await self.logger.debug(
                    f"Event saved to memory: {event.event_name}",
                    context={
                        "event_id": event.event_id,
                        "total_events": len(self.events)
                    }
                )
    
    async def get_events_by_source(
        self,
        source: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[BaseEvent]:
        """Retrieves events by source from memory."""
        async with self._lock:
            events = self.events_by_source.get(source, [])
            # Sort by timestamp, most recent first
            events.sort(key=lambda e: e.timestamp, reverse=True)
            return events[offset:offset + limit]
    
    async def get_events_by_name(
        self,
        event_name: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[BaseEvent]:
        """Retrieves events by name from memory."""
        async with self._lock:
            events = self.events_by_name.get(event_name, [])
            # Sort by timestamp, most recent first
            events.sort(key=lambda e: e.timestamp, reverse=True)
            return events[offset:offset + limit]
    
    async def get_event_by_id(self, event_id: str) -> Optional[BaseEvent]:
        """
        Retrieves event by ID from memory.
        
        Args:
            event_id: Event ID to search for
            
        Returns:
            Event if found, None otherwise
        """
        async with self._lock:
            for event in self.events:
                if event.event_id == event_id:
                    return event
            return None
    
    def clear(self) -> None:
        """Clears all events (useful for testing)."""
        self.events.clear()
        self.events_by_source.clear()
        self.events_by_name.clear()
    
    def get_total_count(self) -> int:
        """Gets total number of stored events."""
        return len(self.events)
    
    def get_sources(self) -> List[str]:
        """Gets list of all event sources."""
        return list(self.events_by_source.keys())
    
    def get_event_names(self) -> List[str]:
        """Gets list of all event names."""
        return list(self.events_by_name.keys())