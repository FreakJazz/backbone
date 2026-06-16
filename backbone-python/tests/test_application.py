"""
Test Application Layer - Tests for use cases, services, and event handling system
"""
import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock
from backbone import (
    BaseTestCase,
    BaseEvent,
    DomainEvent,
    IntegrationEvent,
    SystemEvent,
    EventMetadata,
    InMemoryEventStore,
    JsonFileEventStore,
    MockRepository,
    ApplicationException,
    UseCaseException,
    ValidationException,
    AuthorizationException,
    ResourceNotFoundException,
    ResourceConflictException
)


# === MOCK ENTITIES AND SERVICES FOR TESTING ===

class SampleEntity:
    """Sample entity for application layer testing"""
    def __init__(self, id: str, name: str, email: str, age: int, is_active: bool = True):
        self.id = id
        self.name = name
        self.email = email
        self.age = age
        self.is_active = is_active


class SampleApplicationService:
    """Test application service for event testing"""
    
    def __init__(self, repository: MockRepository, event_bus=None):
        self.repository = repository
        self.event_bus = event_bus
        
    async def create_entity(self, entity_data: dict) -> SampleEntity:
        """Create entity and publish events"""
        # Validation
        if entity_data.get("age", 0) < 18:
            raise ValidationException(
                message="Entity must be at least 18 years old",
                validation_errors=[{"field": "age", "error": "Must be at least 18"}]
            )
        
        # Check for duplicates
        existing = await self.repository.get_all()
        for entity in existing:
            if entity.email == entity_data["email"]:
                raise ResourceConflictException(
                    message="Entity with this email already exists",
                    resource_type="entity",
                    conflict_field="email",
                    conflict_value=entity_data["email"]
                )
        
        # Create entity
        entity = SampleEntity(**entity_data)
        saved_entity = await self.repository.save(entity)
        
        # Publish events if event bus is available
        if self.event_bus:
            # Domain event
            domain_event = DomainEvent(
                event_name="EntityCreated",
                source="test-service",
                data={
                    "entity_id": saved_entity.id,
                    "email": saved_entity.email,
                    "age": saved_entity.age
                },
                microservice="test-service",
                functionality="create-entity"
            )
            await self.event_bus.publish(domain_event)
            
            # Integration event
            integration_event = IntegrationEvent(
                event_name="EntityRegistrationCompleted",
                source="test-service",
                data={"entity_id": saved_entity.id},
                target_services=["notification", "analytics"],
                microservice="test-service",
                functionality="complete-registration"
            )
            await self.event_bus.publish(integration_event)
        
        return saved_entity


# === EVENT SYSTEM TESTS ===

class TestBaseEvent(BaseTestCase):
    """Test base event functionality"""
    
    def test_base_event_creation(self):
        """Test: BaseEvent creates with proper structure"""
        # Arrange & Act
        event = BaseEvent(
            event_name="TestEvent",
            source="test-service",
            data={"test": "data"},
            microservice="test-service",
            functionality="test-function"
        )
        
        # Assert
        self.assertEqual(event.event_name, "TestEvent")
        self.assertEqual(event.source, "test-service")
        self.assertEqual(event.data, {"test": "data"})
        self.assertEqual(event.status, "created")
        self.assertIsNotNone(event.event_id)
        self.assertIsNotNone(event.timestamp)
        # metadata is a dictionary, not an EventMetadata instance
        self.assertIsInstance(event.metadata, dict)
        self.assertEqual(event.metadata["microservice"], "test-service")
        self.assertEqual(event.metadata["functionality"], "test-function")
    
    def test_event_status_transitions(self):
        """Test: Event status transitions work correctly"""
        # Arrange
        event = BaseEvent(
            event_name="TestEvent",
            source="test-service",
            data={"test": "data"},
            microservice="test-service",
            functionality="test-function"
        )
        
        # Act & Assert - Status transitions
        self.assertEqual(event.status, "created")
        
        event.mark_as_published()
        self.assertEqual(event.status, "published")
        
        event.mark_as_processed()
        self.assertEqual(event.status, "processed")
        
        # Test failure status
        event.mark_as_failed()
        self.assertEqual(event.status, "failed")
    
    def test_event_validation(self):
        """Test: Event validation works correctly"""
        # Arrange & Act
        event = BaseEvent(
            event_name="TestEvent",
            source="test-service",
            data={"test": "data"},
            microservice="test-service",
            functionality="test-function"
        )
        
        # Assert
        self.assertTrue(event.is_valid())
        
        # Test with required fields
        self.assertIsNotNone(event.event_name)
        self.assertIsNotNone(event.source)
        self.assertIsNotNone(event.metadata.get("microservice"))
        self.assertIsNotNone(event.metadata.get("functionality"))
    
    def test_domain_event_specialization(self):
        """Test: DomainEvent has proper domain-specific fields"""
        # Arrange & Act
        domain_event = DomainEvent(
            event_name="UserCreated",
            source="users-service",
            data={"user_id": "123"},
            microservice="users-service",
            functionality="create-user",
            aggregate_id="user-123",
            aggregate_version=1
        )
        
        # Assert
        self.assertEqual(domain_event.aggregate_id, "user-123")
        self.assertEqual(domain_event.aggregate_version, 1)
        self.assertEqual(domain_event.event_type, "domain")
    
    def test_integration_event_specialization(self):
        """Test: IntegrationEvent has proper integration fields"""
        # Arrange & Act
        integration_event = IntegrationEvent(
            event_name="UserRegistrationCompleted",
            source="users-service",
            data={"user_id": "123"},
            target_services=["notifications", "analytics"],
            microservice="users-service",
            functionality="complete-registration"
        )
        
        # Assert
        self.assertEqual(integration_event.target_services, ["notifications", "analytics"])
        self.assertEqual(integration_event.event_type, "integration")
    
    def test_system_event_specialization(self):
        """Test: SystemEvent has proper system fields"""
        # Arrange & Act
        system_event = SystemEvent(
            event_name="ServiceHealthCheck",
            source="health-monitor",
            data={"status": "healthy"},
            system_component="api-gateway",
            severity="info",
            microservice="health-monitor",
            functionality="health-check"
        )
        
        # Assert
        self.assertEqual(system_event.system_component, "api-gateway")
        self.assertEqual(system_event.severity, "info")
        self.assertEqual(system_event.event_type, "system")


# === EVENT STORE TESTS ===

class TestInMemoryEventStore(BaseTestCase):
    """Test in-memory event store"""

    def setUp(self):
        super().setUp()
        self.event_store = InMemoryEventStore()

    def test_save_and_retrieve_event(self):
        """Test: Save and retrieve single event"""
        import asyncio
        event = BaseEvent(
            event_name="TestEvent", source="test-service",
            data={"test": "data"}, microservice="test-service", functionality="test-function",
        )
        asyncio.run(self.event_store.save_event(event))
        retrieved = asyncio.run(self.event_store.get_event_by_id(event.event_id))
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.event_id, event.event_id)
        self.assertEqual(retrieved.event_name, "TestEvent")

    def test_get_events_by_source(self):
        """Test: Get events filtered by source"""
        import asyncio

        def _make(name, source):
            return BaseEvent(event_name=name, source=source, data={},
                             microservice=source, functionality="fn")

        e1, e2, e3 = _make("Event1", "service-a"), _make("Event2", "service-b"), _make("Event3", "service-a")
        for e in (e1, e2, e3):
            asyncio.run(self.event_store.save_event(e))

        result = asyncio.run(self.event_store.get_events_by_source("service-a"))
        self.assertEqual(len(result), 2)
        names = [e.event_name for e in result]
        self.assertIn("Event1", names)
        self.assertIn("Event3", names)
        self.assertNotIn("Event2", names)

    def test_get_events_by_name(self):
        """Test: Get events filtered by event name"""
        import asyncio

        def _make(name, source):
            return BaseEvent(event_name=name, source=source, data={},
                             microservice=source, functionality="fn")

        for e in (_make("UserCreated", "a"), _make("UserUpdated", "a"), _make("UserCreated", "b")):
            asyncio.run(self.event_store.save_event(e))

        result = asyncio.run(self.event_store.get_events_by_name("UserCreated"))
        self.assertEqual(len(result), 2)
        for e in result:
            self.assertEqual(e.event_name, "UserCreated")

    def test_get_events_with_limit(self):
        """Test: Get events with limit parameter"""
        import asyncio
        for i in range(5):
            e = BaseEvent(event_name=f"Event{i}", source="test-service",
                          data={"index": i}, microservice="test-service", functionality="fn")
            asyncio.run(self.event_store.save_event(e))

        limited = asyncio.run(self.event_store.get_events_by_source("test-service", limit=3))
        self.assertEqual(len(limited), 3)


class TestJsonFileEventStore(BaseTestCase):
    """Test JSON file event store"""
    
    def setUp(self):
        super().setUp()
        # Use in-memory file path for testing
        self.event_store = JsonFileEventStore("test_events.json")
    
    def test_save_event_to_file(self):
        """Test: Save event to JSON file"""
        import asyncio
        event = BaseEvent(
            event_name="FileTestEvent", source="file-service",
            data={"file": "test"}, microservice="file-service", functionality="file-operation",
        )
        try:
            asyncio.run(self.event_store.save_event(event))
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Failed to save event to file: {e}")


# === APPLICATION EXCEPTION TESTS ===

class TestApplicationExceptions(BaseTestCase):
    """Test application layer exceptions"""
    
    def test_use_case_exception_creation(self):
        """Test: UseCaseException creates with proper structure"""
        # Arrange & Act
        exception = UseCaseException(
            message="Use case failed",
            use_case_name="CreateUserUseCase"
        )
        
        # Assert
        self.assertEqual(exception.code, 10001001)  # default code
        self.assertEqual(exception.message, "Use case failed")
        self.assertIn("use_case", exception.details)
        self.assertEqual(exception.details["use_case"], "CreateUserUseCase")
        self.assertTrue(str(exception.code).startswith("10"))  # Application layer
    
    def test_validation_exception_with_field_errors(self):
        """Test: ValidationException includes field-specific errors"""
        # Arrange & Act
        field_errors = [
            {"field": "email", "error": "Invalid email format"},
            {"field": "age", "error": "Must be at least 18"}
        ]
        exception = ValidationException(
            message="Validation failed",
            validation_errors=field_errors
        )
        
        # Assert
        self.assertIn("validation_errors", exception.details)
        self.assertEqual(len(exception.details["validation_errors"]), 2)
        self.assertEqual(exception.details["validation_errors"][0]["field"], "email")
    
    def test_authorization_exception_with_resource_info(self):
        """Test: AuthorizationException includes resource details"""
        # Arrange & Act
        exception = AuthorizationException(
            message="Access denied",
            required_permission="user:write",
            user_id="123"
        )
        
        # Assert
        self.assertIn("required_permission", exception.details)
        self.assertEqual(exception.details["required_permission"], "user:write")
        self.assertIn("user_id", exception.details)
        self.assertEqual(exception.details["user_id"], "123")
        self.assertEqual(exception.http_code, 403)
    
    def test_resource_not_found_exception(self):
        """Test: ResourceNotFoundException includes resource details"""
        # Arrange & Act
        exception = ResourceNotFoundException(
            message="User not found",
            resource_type="user",
            resource_id="999"
        )
        
        # Assert
        self.assertIn("resource_type", exception.details)
        self.assertEqual(exception.details["resource_type"], "user")
        self.assertIn("resource_id", exception.details)
        self.assertEqual(exception.details["resource_id"], "999")
        self.assertEqual(exception.http_code, 404)
    
    def test_resource_conflict_exception(self):
        """Test: ResourceConflictException includes conflict details"""
        # Arrange & Act
        exception = ResourceConflictException(
            message="Email already exists",
            resource_type="user",
            conflict_field="email",
            conflict_value="alice@example.com"
        )
        
        # Assert
        self.assertIn("resource_type", exception.details)
        self.assertEqual(exception.details["resource_type"], "user")
        self.assertIn("conflict_field", exception.details)
        self.assertEqual(exception.details["conflict_field"], "email")
        self.assertIn("conflict_value", exception.details)
        self.assertEqual(exception.details["conflict_value"], "alice@example.com")
        self.assertEqual(exception.http_code, 409)


# === APPLICATION SERVICE TESTS ===

class TestApplicationServiceWithEvents(BaseTestCase):
    """Test application service with event publishing"""
    
    def setUp(self):
        super().setUp()
        self.repository = MockRepository(SampleEntity)
        
        # Mock event bus
        self.event_bus = Mock()
        self.event_bus.publish = AsyncMock()
        
        self.service = SampleApplicationService(self.repository, self.event_bus)
    
    def test_create_entity_success_publishes_events(self):
        """Test: Successful entity creation publishes domain and integration events"""
        import asyncio
        entity_data = {"id": "1", "name": "Test Entity", "email": "test@example.com", "age": 25}
        entity = asyncio.run(self.service.create_entity(entity_data))
        self.assertEqual(entity.name, "Test Entity")
        self.assertEqual(self.event_bus.publish.call_count, 2)
        calls = self.event_bus.publish.call_args_list
        self.assertEqual(calls[0][0][0].event_name, "EntityCreated")
        self.assertEqual(calls[1][0][0].event_name, "EntityRegistrationCompleted")

    def test_validation_failure_no_events_published(self):
        """Test: Validation failure doesn't publish events"""
        import asyncio
        entity_data = {"id": "1", "name": "Minor", "email": "minor@example.com", "age": 16}
        with self.assertRaises(ValidationException):
            asyncio.run(self.service.create_entity(entity_data))
        self.event_bus.publish.assert_not_called()

    def test_conflict_failure_no_events_published(self):
        """Test: Resource conflict doesn't publish events"""
        import asyncio
        self.repository.seed_data([SampleEntity("1", "Existing", "test@example.com", 30)])
        entity_data = {"id": "2", "name": "New", "email": "test@example.com", "age": 25}
        with self.assertRaises(ResourceConflictException):
            asyncio.run(self.service.create_entity(entity_data))
        self.event_bus.publish.assert_not_called()


# === INTEGRATION TESTS ===

class TestEventDrivenApplicationFlow(BaseTestCase):
    """Integration tests for event-driven application flow"""
    
    def setUp(self):
        super().setUp()
        self.event_store = InMemoryEventStore()
        self.repository = MockRepository(SampleEntity)
        
        # Real event bus mock that stores events
        class TestEventBus:
            def __init__(self, event_store):
                self.event_store = event_store
                self.published_events = []
            
            async def publish(self, event):
                await self.event_store.save_event(event)
                event.mark_as_published()
                self.published_events.append(event)
        
        self.event_bus = TestEventBus(self.event_store)
        self.service = SampleApplicationService(self.repository, self.event_bus)
    
    def test_complete_event_driven_flow(self):
        """Test: Complete flow from entity creation to event persistence"""
        import asyncio
        entity_data = {"id": "flow-test", "name": "Flow Test Entity",
                       "email": "flow@example.com", "age": 28}
        entity = asyncio.run(self.service.create_entity(entity_data))
        self.assertEqual(entity.name, "Flow Test Entity")
        self.assertEqual(len(self.event_bus.published_events), 2)
        stored = asyncio.run(self.event_store.get_events_by_source("test-service"))
        self.assertEqual(len(stored), 2)
        names = [e.event_name for e in stored]
        self.assertIn("EntityCreated", names)
        self.assertIn("EntityRegistrationCompleted", names)
        for e in stored:
            self.assertEqual(e.status, "published")


# === RUN TESTS ===

async def run_application_tests():
    """Run all application layer tests"""
    print("🎯 Running Application Layer Tests\n")
    
    # Event system tests
    event_tests = TestBaseEvent()
    event_tests.setUp()
    
    event_test_methods = [
        ("test_base_event_creation", event_tests.test_base_event_creation),
        ("test_event_status_transitions", event_tests.test_event_status_transitions),
        ("test_event_validation", event_tests.test_event_validation),
        ("test_domain_event_specialization", event_tests.test_domain_event_specialization),
        ("test_integration_event_specialization", event_tests.test_integration_event_specialization),
        ("test_system_event_specialization", event_tests.test_system_event_specialization),
    ]
    
    for test_name, test_method in event_test_methods:
        try:
            test_method()
            print(f"   ✅ {test_name}: PASSED")
        except Exception as e:
            print(f"   ❌ {test_name}: FAILED - {e}")
    
    # Event store tests
    store_tests = TestInMemoryEventStore()
    store_tests.setUp()
    
    store_test_methods = [
        ("test_save_and_retrieve_event", store_tests.test_save_and_retrieve_event),
        ("test_get_events_by_source", store_tests.test_get_events_by_source),
        ("test_get_events_by_name", store_tests.test_get_events_by_name),
        ("test_get_events_with_limit", store_tests.test_get_events_with_limit),
    ]
    
    for test_name, test_method in store_test_methods:
        try:
            await test_method()
            print(f"   ✅ {test_name}: PASSED")
        except Exception as e:
            print(f"   ❌ {test_name}: FAILED - {e}")
    
    # File event store tests
    file_store_tests = TestJsonFileEventStore()
    file_store_tests.setUp()
    
    file_store_test_methods = [
        ("test_save_event_to_file", file_store_tests.test_save_event_to_file),
    ]
    
    for test_name, test_method in file_store_test_methods:
        try:
            await test_method()
            print(f"   ✅ {test_name}: PASSED")
        except Exception as e:
            print(f"   ❌ {test_name}: FAILED - {e}")
    
    # Application exception tests
    app_exception_tests = TestApplicationExceptions()
    app_exception_tests.setUp()
    
    app_exception_test_methods = [
        ("test_use_case_exception_creation", app_exception_tests.test_use_case_exception_creation),
        ("test_validation_exception_with_field_errors", app_exception_tests.test_validation_exception_with_field_errors),
        ("test_authorization_exception_with_resource_info", app_exception_tests.test_authorization_exception_with_resource_info),
        ("test_resource_not_found_exception", app_exception_tests.test_resource_not_found_exception),
        ("test_resource_conflict_exception", app_exception_tests.test_resource_conflict_exception),
    ]
    
    for test_name, test_method in app_exception_test_methods:
        try:
            test_method()
            print(f"   ✅ {test_name}: PASSED")
        except Exception as e:
            print(f"   ❌ {test_name}: FAILED - {e}")
    
    # Application service tests
    service_test_methods = [
        ("test_create_entity_success_publishes_events", "test_create_entity_success_publishes_events"),
        ("test_validation_failure_no_events_published", "test_validation_failure_no_events_published"),
        ("test_conflict_failure_no_events_published", "test_conflict_failure_no_events_published"),
    ]
    
    for test_name, method_name in service_test_methods:
        try:
            service_tests = TestApplicationServiceWithEvents()
            service_tests.setUp()
            test_method = getattr(service_tests, method_name)
            await test_method()
            print(f"   ✅ {test_name}: PASSED")
        except Exception as e:
            print(f"   ❌ {test_name}: FAILED - {e}")
    
    # Integration tests
    integration_tests = TestEventDrivenApplicationFlow()
    integration_tests.setUp()
    
    integration_test_methods = [
        ("test_complete_event_driven_flow", integration_tests.test_complete_event_driven_flow),
    ]
    
    for test_name, test_method in integration_test_methods:
        try:
            await test_method()
            print(f"   ✅ {test_name}: PASSED")
        except Exception as e:
            print(f"   ❌ {test_name}: FAILED - {e}")
    
    print("\n📊 Application Layer Tests Completed!")


if __name__ == "__main__":
    asyncio.run(run_application_tests())
