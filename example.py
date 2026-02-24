"""
Complete Backbone Framework Usage Example

This example demonstrates how to implement a complete application following
Clean Architecture with Event-Driven microservices using all framework components.
"""
import asyncio
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

# === FRAMEWORK IMPORTS ===
from backbone import (
    # Domain layer
    DomainException,
    FilterSpecification,
    BaseRepository,
    
    # Application layer 
    ApplicationException,
    
    # Infrastructure layer
    LoggerFactory,
    BaseTestCase,
    MockRepository,
    
    # Interface layer
    ProcessResponseBuilder,
    PaginatedResponseBuilder,
    ErrorResponseBuilder
)

# === EVENT SYSTEM IMPORTS ===
from backbone.domain.ports.event_bus import (
    EventBus,
    BaseEvent,
    DomainEvent,
    IntegrationEvent,
    EventStore
)
from backbone.application.event_handlers import (
    event_handler,
    RetryPolicy,
    EventHandlerRegistry
)
from backbone.infrastructure.messaging import (
    EventBusAdapterFactory
)
from backbone.infrastructure.persistence.event_store import (
    InMemoryEventStore
)


# === 1. DOMAIN LAYER ===

@dataclass
class User:
    """Domain Entity: User"""
    id: Optional[str] = None
    name: str = ""
    email: str = ""
    age: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None
    
    @classmethod
    def create(cls, user_data: dict) -> "User":
        """Factory method to create user with validation"""
        age = user_data.get("age", 0)
        if age < 18:
            raise DomainException(
                message="User must be at least 18 years old",
                error_code="11001001",
                context={"provided_age": age, "minimum_age": 18}
            )
        
        return cls(
            name=user_data["name"],
            email=user_data["email"],
            age=age,
            is_active=True,
            created_at=datetime.now()
        )


class UserValidationSpecification(FilterSpecification):
    """Specification for validating active adult users"""
    
    def __init__(self):
        # Users over 18 and active
        super().__init__("age", "gte", 18)
        self._and_spec = FilterSpecification("is_active", "eq", True)
    
    def is_satisfied_by(self, user: User) -> bool:
        """Validates if user meets the specification"""
        return user.age >= 18 and user.is_active


# === 2. APPLICATION LAYER ===

class UserService:
    """Application service for user management with events"""
    
    def __init__(self, user_repository: BaseRepository[User, str], event_bus: EventBus):
        self._user_repository = user_repository
        self._event_bus = event_bus
        self._logger = LoggerFactory.create_logger("UserService")
    
    async def create_user(self, user_data: dict) -> User:
        """
        Creates a new user and publishes domain event.
        
        Args:
            user_data: User data
            
        Returns:
            Created user
            
        Raises:
            ApplicationException: If creation fails
        """
        try:
            await self._logger.info("Creating user", context={"email": user_data.get("email")})
            
            # Check unique email
            existing_users = await self._user_repository.find_by_specification(
                FilterSpecification("email", "eq", user_data["email"])
            )
            
            if existing_users:
                raise DomainException(
                    message="User with this email already exists",
                    error_code="11001002",
                    context={"email": user_data["email"]}
                )
            
            # Create domain entity (includes validation)
            user = User.create(user_data)
            
            # Persist user
            saved_user = await self._user_repository.save(user)
            
            # Publish domain event
            domain_event = DomainEvent(
                event_name="UserCreated",
                aggregate_id=saved_user.id,
                aggregate_type="User",
                source="users-service",
                data={
                    "user_id": saved_user.id,
                    "email": saved_user.email,
                    "name": saved_user.name,
                    "age": saved_user.age
                },
                microservice="users-service",
                functionality="create-user"
            )
            
            await self._event_bus.publish(domain_event)
            
            # Publish integration event for other microservices
            integration_event = IntegrationEvent(
                event_name="UserRegistrationCompleted",
                source="users-service",
                target_services=["notifications", "analytics", "profiles"],
                data={
                    "user_id": saved_user.id,
                    "email": saved_user.email,
                    "registration_date": saved_user.created_at.isoformat() if saved_user.created_at else None
                },
                microservice="users-service",
                functionality="complete-registration"
            )
            
            await self._event_bus.publish(integration_event)
            
            await self._logger.info(
                "User created successfully with events", 
                context={
                    "user_id": saved_user.id, 
                    "email": saved_user.email,
                    "events_published": ["UserCreated", "UserRegistrationCompleted"]
                }
            )
            
            return saved_user
            
        except DomainException:
            # Re-raise domain exceptions
            raise
        except Exception as e:
            await self._logger.error(
                "Failed to create user",
                context={"error": str(e), "user_data": user_data}
            )
            raise ApplicationException(
                message="Failed to create user",
                error_code="10001001",
                operation="create_user",
                original_error=str(e)
            )
    
    async def get_active_adult_users(self, page: int = 0, page_size: int = 20) -> tuple[List[User], int]:
        """
        Gets paginated active adult users.
        
        Args:
            page: Page number
            page_size: Page size
            
        Returns:
            Tuple (users, total)
        """
        try:
            # Create specification for active adult users
            spec = FilterSpecification("age", "gte", 18).and_(
                FilterSpecification("is_active", "eq", True)
            )
            
            # Get paginated results
            users, total = await self._user_repository.find_paginated_by_specification(
                spec, page, page_size
            )
            
            await self._logger.info(
                "Active adult users retrieved",
                context={"count": len(users), "total": total, "page": page}
            )
            
            return users, total
            
        except Exception as e:
            await self._logger.error("Failed to get users", context={"error": str(e)})
            raise ApplicationException(
                message="Failed to retrieve users",
                error_code="10001002", 
                operation="get_active_adult_users",
                original_error=str(e)
            )


# === 3. EVENT HANDLERS (APPLICATION LAYER) ===

class NotificationService:
    """Service for sending notifications"""
    
    def __init__(self):
        self._logger = LoggerFactory.create_logger("NotificationService")
    
    async def send_welcome_email(self, user_email: str, user_name: str):
        """Simulates sending welcome email"""
        await self._logger.info(
            f"Sending welcome email to {user_email}",
            context={"email": user_email, "name": user_name}
        )
        # Simulate email sending
        await asyncio.sleep(0.1)
        print(f"📧 Welcome email sent to {user_name} ({user_email})")


class AnalyticsService:
    """Service for analytics tracking"""
    
    def __init__(self):
        self._logger = LoggerFactory.create_logger("AnalyticsService")
        self._user_count = 0
    
    async def increment_user_count(self, user_data: dict):
        """Increments user registration metrics"""
        self._user_count += 1
        await self._logger.info(
            "User count incremented",
            context={"new_count": self._user_count, "user_id": user_data.get("user_id")}
        )
        print(f"📊 Analytics: Total users registered: {self._user_count}")


class ProfileService:
    """Service for user profile management"""
    
    def __init__(self):
        self._logger = LoggerFactory.create_logger("ProfileService")
    
    async def create_user_profile(self, user_data: dict):
        """Creates user profile"""
        await self._logger.info(
            "Creating user profile",
            context={"user_id": user_data.get("user_id")}
        )
        # Simulate profile creation
        await asyncio.sleep(0.05)
        print(f"👤 User profile created for user {user_data.get('user_id')}")


# Event handlers with automatic retry, validation, and logging
notification_service = NotificationService()
analytics_service = AnalyticsService()
profile_service = ProfileService()

# Retry policy for critical operations
critical_retry_policy = RetryPolicy(
    max_attempts=3,
    delay_seconds=1,
    exponential_backoff=True,
    max_delay_seconds=10
)

@event_handler("UserCreated", retry_policy=critical_retry_policy)
async def handle_user_created_notifications(event: BaseEvent):
    """
    Handles user creation for notifications.
    Features: automatic validation, retry, error handling, logging
    """
    user_data = event.data
    await notification_service.send_welcome_email(
        user_data["email"],
        user_data["name"]
    )

@event_handler("UserRegistrationCompleted")
async def handle_user_registration_analytics(event: BaseEvent):
    """Handles user registration completion for analytics"""
    await analytics_service.increment_user_count(event.data)

@event_handler("UserRegistrationCompleted") 
async def handle_user_registration_profile(event: BaseEvent):
    """Handles user registration completion for profile creation"""
    await profile_service.create_user_profile(event.data)

@event_handler("UserCreated")
async def handle_user_created_logging(event: BaseEvent):
    """Additional handler for comprehensive logging"""
    logger = LoggerFactory.create_logger("UserEventLogger")
    await logger.info(
        f"User creation event processed: {event.event_name}",
        context={
            "event_id": event.event_id,
            "user_id": event.data.get("user_id"),
            "correlation_id": event.metadata.get("correlationId"),
            "event_status": event.status
        }
    )


# === 4. INTERFACE LAYER ===

class UserController:
    """Controller for user API with event integration"""
    
    def __init__(self, user_service: UserService, event_store: EventStore):
        self._user_service = user_service
        self._event_store = event_store
    
    async def create_user_endpoint(self, request_data: dict) -> dict:
        """
        Endpoint for creating user with event publishing.
        
        Args:
            request_data: Request data
            
        Returns:
            Response dictionary
        """
        try:
            user = await self._user_service.create_user(request_data)
            
            return ProcessResponseBuilder.success(
                data={
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "age": user.age,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                },
                message="User created successfully with events published",
                metadata={
                    "operation": "create_user",
                    "events_published": ["UserCreated", "UserRegistrationCompleted"]
                }
            )
            
        except (DomainException, ApplicationException) as e:
            return ErrorResponseBuilder.from_exception(e)
    
    async def list_users_endpoint(self, query_params: dict) -> dict:
        """
        Endpoint for listing active adult users.
        
        Args:
            query_params: Query parameters
            
        Returns:
            Response dictionary with pagination
        """
        try:
            page = int(query_params.get("page", 0))
            page_size = int(query_params.get("page_size", 20))
            
            users, total = await self._user_service.get_active_adult_users(page, page_size)
            
            # Convert users to dictionaries
            users_data = [
                {
                    "id": user.id,
                    "name": user.name, 
                    "email": user.email,
                    "age": user.age,
                    "is_active": user.is_active
                }
                for user in users
            ]
            
            return PaginatedResponseBuilder.from_repository_result(
                users_data, total, page, page_size
            )
            
        except Exception as e:
            return ErrorResponseBuilder.from_exception(e)
    
    async def get_user_events_endpoint(self, query_params: dict) -> dict:
        """
        Endpoint for retrieving user-related events.
        
        Args:
            query_params: Query parameters
            
        Returns:
            Response with event history
        """
        try:
            source = query_params.get("source", "users-service")
            limit = int(query_params.get("limit", 50))
            
            # Get events from event store
            events = await self._event_store.get_events_by_source(source, limit=limit)
            
            events_data = [
                {
                    "event_id": event.event_id,
                    "event_name": event.event_name,
                    "timestamp": event.timestamp.isoformat(),
                    "status": event.status,
                    "data": event.data,
                    "metadata": event.metadata
                }
                for event in events
            ]
            
            return ProcessResponseBuilder.success(
                data=events_data,
                message=f"Retrieved {len(events)} events",
                metadata={
                    "operation": "get_user_events",
                    "source": source,
                    "total_events": len(events)
                }
            )
            
        except Exception as e:
            return ErrorResponseBuilder.from_exception(e)


# === 5. TESTING WITH EVENTS ===

class EventAwareTestCase(BaseTestCase):
    """Extended test case with event testing capabilities"""
    
    def setUp(self):
        super().setUp()
        self.event_store = InMemoryEventStore()
        # Use in-memory event bus for testing (no external dependencies)
        self.event_bus = self.create_in_memory_event_bus()
        
    def create_in_memory_event_bus(self):
        """Creates in-memory event bus for testing"""
        # In a real scenario, you'd import the in-memory implementation
        # For this example, we'll create a simple mock
        class MockEventBus:
            def __init__(self, event_store):
                self.events_published = []
                self.event_store = event_store
            
            async def publish(self, event):
                self.events_published.append(event)
                await self.event_store.save_event(event)
                event.mark_as_published()
            
            async def publish_batch(self, events):
                for event in events:
                    await self.publish(event)
                    
            async def subscribe(self, event_name, handler, retry_policy=None):
                pass  # Mock implementation
                
            async def unsubscribe(self, event_name, handler):
                pass  # Mock implementation
                
        return MockEventBus(self.event_store)


class UserServiceWithEventsTest(EventAwareTestCase):
    """Unit tests for UserService with event testing"""
    
    def setUp(self):
        super().setUp()
        self.mock_repo = MockRepository(User)
        self.user_service = UserService(self.mock_repo, self.event_bus)
    
    async def test_create_adult_user_success_with_events(self):
        """Test: create adult user successfully and verify events"""
        # Arrange
        user_data = {
            "name": "John Doe",
            "email": "john@example.com", 
            "age": 25
        }
        
        # Act
        user = await self.user_service.create_user(user_data)
        
        # Assert user creation
        self.assertEqual(user.name, "John Doe")
        self.assertEqual(user.email, "john@example.com")
        self.assertEqual(user.age, 25)
        self.assertTrue(user.is_active)
        
        # Verify user was saved in repository
        saved_users = self.mock_repo.get_saved_entities()
        self.assertEqual(len(saved_users), 1)
        
        # Verify events were published
        published_events = self.event_bus.events_published
        self.assertEqual(len(published_events), 2)
        
        # Verify domain event
        domain_event = published_events[0]
        self.assertEqual(domain_event.event_name, "UserCreated")
        self.assertEqual(domain_event.data["email"], "john@example.com")
        self.assertEqual(domain_event.status, "published")
        
        # Verify integration event
        integration_event = published_events[1]
        self.assertEqual(integration_event.event_name, "UserRegistrationCompleted")
        self.assertIn("notifications", integration_event.target_services)
        self.assertIn("analytics", integration_event.target_services)
    
    async def test_create_minor_user_raises_domain_exception_no_events(self):
        """Test: create minor user raises exception and no events published"""
        # Arrange
        user_data = {
            "name": "Minor User",
            "email": "minor@example.com",
            "age": 16
        }
        
        # Act & Assert
        with self.assertRaisesDomainException("11001001"):
            await self.user_service.create_user(user_data)
        
        # Verify no events were published on failure
        self.assertEqual(len(self.event_bus.events_published), 0)
    
    async def test_create_duplicate_email_raises_domain_exception_no_events(self):
        """Test: create user with duplicate email raises exception and no events"""
        # Arrange - create existing user
        existing_user = User(
            id="1", 
            name="Existing", 
            email="existing@example.com",
            age=30
        )
        self.mock_repo.seed_data([existing_user])
        
        user_data = {
            "name": "New User",
            "email": "existing@example.com",  # Duplicate email
            "age": 25
        }
        
        # Act & Assert
        with self.assertRaisesDomainException("11001002"):
            await self.user_service.create_user(user_data)
        
        # Verify no events were published on failure
        self.assertEqual(len(self.event_bus.events_published), 0)
    
    async def test_event_store_integration(self):
        """Test: verify events are stored in event store"""
        # Arrange
        user_data = {
            "name": "Alice Cooper",
            "email": "alice@example.com",
            "age": 28
        }
        
        # Act
        await self.user_service.create_user(user_data)
        
        # Assert events in store
        user_events = await self.event_store.get_events_by_source("users-service")
        self.assertEqual(len(user_events), 2)
        
        creation_events = await self.event_store.get_events_by_name("UserCreated")
        self.assertEqual(len(creation_events), 1)
        self.assertEqual(creation_events[0].data["email"], "alice@example.com")


# === 6. EVENT HANDLER TESTS ===

class EventHandlerTest(BaseTestCase):
    """Tests for event handlers"""
    
    def setUp(self):
        super().setUp()
        self.notification_service = NotificationService()
        self.analytics_service = AnalyticsService()
        self.profile_service = ProfileService()
    
    async def test_notification_handler(self):
        """Test notification event handler"""
        # Arrange
        event = BaseEvent(
            event_name="UserCreated",
            source="users-service",
            data={
                "user_id": "123",
                "email": "test@example.com",
                "name": "Test User"
            },
            microservice="users-service",
            functionality="create-user"
        )
        
        # Act
        await handle_user_created_notifications(event)
        
        # Assert (in real scenario, you'd verify email service was called)
        self.assertEqual(event.status, "processed")
    
    async def test_analytics_handler(self):
        """Test analytics event handler"""
        # Arrange
        initial_count = self.analytics_service._user_count
        event = BaseEvent(
            event_name="UserRegistrationCompleted",
            source="users-service",
            data={"user_id": "123"},
            microservice="users-service",
            functionality="complete-registration"
        )
        
        # Act
        await handle_user_registration_analytics(event)
        
        # Assert
        self.assertEqual(self.analytics_service._user_count, initial_count + 1)


# === 7. COMPLETE DEMO EXECUTION ===

async def setup_event_system():
    """Sets up complete event system for demo"""
    
    # Create event store
    event_store = InMemoryEventStore()
    
    # For demo, we'll use an in-memory event bus
    # In production, you'd choose Kafka/RabbitMQ/Redis adapter
    class DemoEventBus:
        def __init__(self, event_store):
            self.event_store = event_store
            self.handlers = {}
            
        async def publish(self, event):
            # Store event
            await self.event_store.save_event(event)
            event.mark_as_published()
            
            # Execute handlers for this event type
            handlers = self.handlers.get(event.event_name, [])
            for handler in handlers:
                try:
                    await handler(event)
                    event.mark_as_processed()
                except Exception as e:
                    print(f"❌ Event handler failed: {e}")
                    event.mark_as_failed()
            
            print(f"📨 Event published: {event.event_name} (ID: {event.event_id})")
            
        async def subscribe(self, event_name, handler, retry_policy=None):
            if event_name not in self.handlers:
                self.handlers[event_name] = []
            self.handlers[event_name].append(handler)
            
        async def publish_batch(self, events):
            for event in events:
                await self.publish(event)
                
        async def unsubscribe(self, event_name, handler):
            if event_name in self.handlers and handler in self.handlers[event_name]:
                self.handlers[event_name].remove(handler)
    
    event_bus = DemoEventBus(event_store)
    
    # Register event handlers
    await event_bus.subscribe("UserCreated", handle_user_created_notifications)
    await event_bus.subscribe("UserRegistrationCompleted", handle_user_registration_analytics)
    await event_bus.subscribe("UserRegistrationCompleted", handle_user_registration_profile)
    await event_bus.subscribe("UserCreated", handle_user_created_logging)
    
    return event_bus, event_store


async def demo_complete_usage():
    """Complete demonstration of Backbone framework with events"""
    
    print("🎯 Complete Backbone Framework Demo with Event-Driven Architecture\n")
    
    # Setup event system
    event_bus, event_store = await setup_event_system()
    
    # Setup repositories and services
    mock_repo = MockRepository(User)
    user_service = UserService(mock_repo, event_bus)
    controller = UserController(user_service, event_store)
    
    print("📋 1. Create user with automatic event publishing:")
    try:
        response = await controller.create_user_endpoint({
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "age": 28
        })
        print(f"   ✅ Response: {response}\n")
        
        # Wait for event handlers to complete
        await asyncio.sleep(0.2)
        
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
    
    print("📋 2. Attempt to create minor user (should fail, no events):")
    try:
        response = await controller.create_user_endpoint({
            "name": "Bob Minor", 
            "email": "bob@example.com",
            "age": 16  # Under age
        })
        print(f"   Response: {response}\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
    
    print("📋 3. Create second user to demonstrate multiple events:")
    try:
        response = await controller.create_user_endpoint({
            "name": "Charlie Brown",
            "email": "charlie@example.com",
            "age": 35
        })
        print(f"   ✅ Response: {response}\n")
        
        await asyncio.sleep(0.2)
        
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
    
    print("📋 4. List active users:")
    try:
        # Seed additional users for demonstration
        mock_repo.seed_data([
            User(id="seed1", name="Diana", email="diana@example.com", age=29, is_active=True),
            User(id="seed2", name="Eve", email="eve@example.com", age=22, is_active=False)  # Inactive
        ])
        
        response = await controller.list_users_endpoint({"page": "0", "page_size": "10"})
        print(f"   ✅ Response: {response}\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
    
    print("📋 5. Retrieve event history:")
    try:
        response = await controller.get_user_events_endpoint({
            "source": "users-service",
            "limit": "10"
        })
        print(f"   ✅ Event History: {response}\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
    
    print("📋 6. Event store queries:")
    try:
        # Query events by source
        user_events = await event_store.get_events_by_source("users-service")
        print(f"   📊 Total events from users-service: {len(user_events)}")
        
        # Query events by name
        creation_events = await event_store.get_events_by_name("UserCreated")
        print(f"   📊 UserCreated events: {len(creation_events)}")
        
        registration_events = await event_store.get_events_by_name("UserRegistrationCompleted")
        print(f"   📊 UserRegistrationCompleted events: {len(registration_events)}\n")
        
    except Exception as e:
        print(f"   ❌ Event query error: {e}\n")
    
    print("🧪 7. Run unit tests with events:")
    test_case = UserServiceWithEventsTest()
    test_case.setUp()
    
    try:
        await test_case.test_create_adult_user_success_with_events()
        print("   ✅ test_create_adult_user_success_with_events: PASSED")
    except Exception as e:
        print(f"   ❌ test_create_adult_user_success_with_events: FAILED - {e}")
    
    try:
        await test_case.test_create_minor_user_raises_domain_exception_no_events()
        print("   ✅ test_create_minor_user_raises_domain_exception_no_events: PASSED")
    except Exception as e:
        print(f"   ❌ test_create_minor_user_raises_domain_exception_no_events: FAILED - {e}")
    
    try:
        await test_case.test_event_store_integration()
        print("   ✅ test_event_store_integration: PASSED")
    except Exception as e:
        print(f"   ❌ test_event_store_integration: FAILED - {e}")
    
    print("\n🎉 Complete demo finished!")
    print("\n📝 Summary of features demonstrated:")
    print("   🏗️  Clean Architecture with strict layer separation")
    print("   🔢 8-digit exception system with proper error codes")
    print("   🎯 Specification pattern for dynamic filters")
    print("   📋 Repository pattern with mock implementation")
    print("   🔧 Decoupled response builders")
    print("   📊 Structured logging with context")
    print("   🧪 Complete testing framework")
    print("   🔄 Event-driven architecture with:")
    print("      • Domain and integration events")
    print("      • Automatic event handlers with retry")
    print("      • Event validation and status tracking") 
    print("      • Event store for persistence and querying")
    print("      • Hexagonal architecture (no external dependencies in domain)")


if __name__ == "__main__":
    asyncio.run(demo_complete_usage())