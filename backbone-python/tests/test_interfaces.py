"""
Test Interface Layer - Tests for response builders, controllers, and presentation concerns
"""
import asyncio
from datetime import datetime, timezone
from backbone import (
    BaseTestCase,
    ProcessResponseBuilder,
    SimpleObjectResponseBuilder,
    PaginatedResponseBuilder,
    ErrorResponseBuilder,
    PresentationException,
    RequestValidationException,
    HttpException,
    SerializationException,
    DeserializationException
)


# === RESPONSE BUILDER TESTS ===

class TestProcessResponseBuilder(BaseTestCase):
    """Test process response builder for CRUD operations"""
    
    def test_create_response_success(self):
        """Test: Create response with 201 status"""
        # Arrange
        data = {"id": "123", "name": "Test Entity", "email": "test@example.com"}
        
        # Act
        response = ProcessResponseBuilder.success(
            data=data,
            message="Entity created successfully",
            status=201
        )
        
        # Assert
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["status_code"], 201)
        self.assertEqual(response["message"], "Entity created successfully")
        self.assertEqual(response["data"], data)
        self.assertIn("timestamp", response)
        self.assertIn("request_id", response)
    
    def test_update_response_success(self):
        """Test: Update response with 200 status"""
        # Arrange
        updated_data = {"id": "123", "name": "Updated Entity", "version": 2}
        
        # Act
        response = ProcessResponseBuilder.updated(
            data=updated_data,
            message="Entity updated successfully"
        )
        
        # Assert
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["status_code"], 200)
        self.assertEqual(response["message"], "Entity updated successfully")
        self.assertEqual(response["data"], updated_data)
    
    def test_delete_response_success(self):
        """Test: Delete response with 200 status"""
        # Act
        response = ProcessResponseBuilder.deleted(
            message="Entity deleted successfully",
            resource_id="123"
        )
        
        # Assert
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["status_code"], 200)
        self.assertEqual(response["message"], "Entity deleted successfully")
        self.assertIn("123", response["data"]["resource_id"])
    
    def test_completed_response_without_data(self):
        """Test: Completed response for operations without specific return data"""
        # Act
        response = ProcessResponseBuilder.completed(
            message="Operation completed successfully"
        )
        
        # Assert
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["status_code"], 200)
        self.assertEqual(response["message"], "Operation completed successfully")
        self.assertIsNone(response["data"])


class TestSimpleObjectResponseBuilder(BaseTestCase):
    """Test simple object response builder for single resource responses"""
    
    def test_found_response(self):
        """Test: Found response for retrieved resource"""
        # Arrange
        entity_data = {"id": "123", "name": "Found Entity", "is_active": True}
        
        # Act
        response = SimpleObjectResponseBuilder.found(
            data=entity_data,
            resource_type="entity"
        )
        
        # Assert
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["status_code"], 200)
        self.assertIn("entity found", response["message"].lower())
        self.assertEqual(response["data"], entity_data)
    
    def test_retrieved_response(self):
        """Test: Retrieved response for fetched resource"""
        # Arrange
        entity_data = {"id": "456", "name": "Retrieved Entity"}
        
        # Act
        response = SimpleObjectResponseBuilder.retrieved(
            data=entity_data,
            resource_type="user"
        )
        
        # Assert
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["status_code"], 200)
        self.assertIn("user retrieved", response["message"].lower())
        self.assertEqual(response["data"], entity_data)
    
    def test_details_response(self):
        """Test: Details response for detailed resource view"""
        # Arrange
        detailed_data = {
            "id": "789",
            "name": "Detailed Entity",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z"
        }
        
        # Act
        response = SimpleObjectResponseBuilder.details(
            data=detailed_data,
            resource_type="profile"
        )
        
        # Assert
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["status_code"], 200)
        self.assertIn("profile details", response["message"].lower())
        self.assertEqual(response["data"], detailed_data)
    
    def test_status_response(self):
        """Test: Status response for resource status checks"""
        # Arrange
        status_data = {"status": "active", "health": "ok", "last_check": "2024-01-01T12:00:00Z"}
        
        # Act
        response = SimpleObjectResponseBuilder.status(
            data=status_data,
            message="Service status retrieved"
        )
        
        # Assert
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["status_code"], 200)
        self.assertEqual(response["message"], "Service status retrieved")
        self.assertEqual(response["data"], status_data)


class TestPaginatedResponseBuilder(BaseTestCase):
    """Test paginated response builder for list responses"""
    
    def test_paginated_response_with_results(self):
        """Test: Paginated response with data and pagination info"""
        # Arrange
        items = [
            {"id": "1", "name": "Item 1"},
            {"id": "2", "name": "Item 2"},
            {"id": "3", "name": "Item 3"}
        ]
        
        # Act
        response = PaginatedResponseBuilder.success(
            items=items,
            total_count=10,
            page=0,
            page_size=3,
            message="Items retrieved successfully"
        )
        
        # Assert
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["status_code"], 200)
        self.assertEqual(response["message"], "Items retrieved successfully")
        self.assertEqual(response["data"]["items"], items)
        
        # Check pagination metadata
        pagination = response["data"]["pagination"]
        self.assertEqual(pagination["total_count"], 10)
        self.assertEqual(pagination["page"], 0)
        self.assertEqual(pagination["page_size"], 3)
        self.assertEqual(pagination["total_pages"], 4)  # ceil(10/3) = 4
        self.assertTrue(pagination["has_next"])
        self.assertFalse(pagination["has_previous"])
    
    def test_paginated_response_last_page(self):
        """Test: Paginated response for last page"""
        # Arrange
        items = [{"id": "4", "name": "Item 4"}]
        
        # Act
        response = PaginatedResponseBuilder.success(
            items=items,
            total_count=4,
            page=3,  # Last page (0-indexed)
            page_size=3,
            message="Last page retrieved"
        )
        
        # Assert
        pagination = response["data"]["pagination"]
        self.assertEqual(pagination["page"], 3)
        self.assertEqual(pagination["total_pages"], 2)  # ceil(4/3) = 2
        self.assertFalse(pagination["has_next"])
        self.assertTrue(pagination["has_previous"])
    
    def test_from_repository_result_factory(self):
        """Test: Factory method for repository results"""
        # Arrange
        items = [
            {"id": "1", "name": "Repo Item 1"},
            {"id": "2", "name": "Repo Item 2"}
        ]
        total_count = 5
        page = 1
        page_size = 2
        
        # Act
        response = PaginatedResponseBuilder.from_repository_result(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            resource_type="user"
        )
        
        # Assert
        self.assertEqual(response["status"], "success")
        self.assertIn("users retrieved", response["message"].lower())
        self.assertEqual(len(response["data"]["items"]), 2)
        
        pagination = response["data"]["pagination"]
        self.assertEqual(pagination["total_count"], 5)
        self.assertEqual(pagination["page"], 1)
        self.assertEqual(pagination["page_size"], 2)
    
    def test_empty_response(self):
        """Test: Empty response when no results"""
        # Act
        response = PaginatedResponseBuilder.empty(
            resource_type="user",
            message="No users found matching criteria"
        )
        
        # Assert
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["status_code"], 200)
        self.assertEqual(response["message"], "No users found matching criteria")
        self.assertEqual(response["data"]["items"], [])
        
        pagination = response["data"]["pagination"]
        self.assertEqual(pagination["total_count"], 0)
        self.assertEqual(pagination["page"], 0)
        self.assertEqual(pagination["total_pages"], 0)


class TestErrorResponseBuilder(BaseTestCase):
    """Test error response builder for error responses"""
    
    def test_validation_error_response(self):
        """Test: Validation error response with field errors"""
        # Arrange
        field_errors = {
            "email": "Invalid email format",
            "age": "Must be at least 18"
        }
        
        # Act
        response = ErrorResponseBuilder.validation_error(
            message="Validation failed",
            field_errors=field_errors
        )
        
        # Assert
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["status_code"], 400)
        self.assertEqual(response["message"], "Validation failed")
        self.assertEqual(response["error_details"]["field_errors"], field_errors)
    
    def test_authentication_error_response(self):
        """Test: Authentication error response"""
        # Act
        response = ErrorResponseBuilder.authentication_error(
            message="Authentication required"
        )
        
        # Assert
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["status_code"], 401)
        self.assertEqual(response["message"], "Authentication required")
        self.assertIn("request_id", response)
    
    def test_authorization_error_response(self):
        """Test: Authorization error response"""
        # Act
        response = ErrorResponseBuilder.authorization_error(
            message="Access denied",
            required_permission="user:write"
        )
        
        # Assert
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["status_code"], 403)
        self.assertEqual(response["message"], "Access denied")
        self.assertEqual(response["error_details"]["required_permission"], "user:write")
    
    def test_not_found_error_response(self):
        """Test: Not found error response"""
        # Act
        response = ErrorResponseBuilder.not_found_error(
            message="User not found",
            resource_type="user",
            resource_id="999"
        )
        
        # Assert
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["status_code"], 404)
        self.assertEqual(response["message"], "User not found")
        self.assertEqual(response["error_details"]["resource_type"], "user")
        self.assertEqual(response["error_details"]["resource_id"], "999")
    
    def test_conflict_error_response(self):
        """Test: Conflict error response"""
        # Act
        response = ErrorResponseBuilder.conflict_error(
            message="Email already exists",
            resource_type="user",
            conflict_field="email"
        )
        
        # Assert
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["status_code"], 409)
        self.assertEqual(response["message"], "Email already exists")
        self.assertEqual(response["error_details"]["resource_type"], "user")
        self.assertEqual(response["error_details"]["conflict_field"], "email")
    
    def test_internal_server_error_response(self):
        """Test: Internal server error response"""
        # Act
        response = ErrorResponseBuilder.internal_server_error(
            message="An unexpected error occurred"
        )
        
        # Assert
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["status_code"], 500)
        self.assertEqual(response["message"], "An unexpected error occurred")
    
    def test_service_unavailable_error_response(self):
        """Test: Service unavailable error response"""
        # Act
        response = ErrorResponseBuilder.service_unavailable_error(
            message="Database service unavailable"
        )
        
        # Assert
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["status_code"], 503)
        self.assertEqual(response["message"], "Database service unavailable")


# === PRESENTATION EXCEPTION TESTS ===

class TestPresentationExceptions(BaseTestCase):
    """Test presentation layer exceptions"""
    
    def test_request_validation_exception_creation(self):
        """Test: RequestValidationException creates with field errors"""
        # Arrange & Act
        field_errors = [{"field": "name", "error": "Required field"}, {"field": "email", "error": "Invalid format"}]
        exception = RequestValidationException(
            message="Request validation failed",
            field_errors=field_errors
        )
        
        # Assert
        self.assertEqual(exception.code, 13001001)  # default code
        self.assertEqual(exception.message, "Request validation failed")
        self.assertIn("field_errors", exception.details)
        self.assertEqual(len(exception.details["field_errors"]), 2)
        self.assertTrue(str(exception.code).startswith("13"))  # Presentation layer
    
    def test_http_exception_with_status_code(self):
        """Test: HttpException includes HTTP-specific details"""
        # Arrange & Act
        exception = HttpException(
            message="Bad request",
            http_method="POST",
            endpoint="/api/users",
            expected_content_type="application/json",
            received_content_type="text/plain"
        )
        
        # Assert
        self.assertIn("http_method", exception.details)
        self.assertEqual(exception.details["http_method"], "POST")
        self.assertIn("endpoint", exception.details)
        self.assertEqual(exception.details["endpoint"], "/api/users")
    
    def test_serialization_exception_with_data_info(self):
        """Test: SerializationException includes data context"""
        # Arrange & Act
        exception = SerializationException(
            message="Failed to serialize response",
            object_type="User",
            serialization_format="json"
        )
        
        # Assert
        self.assertIn("object_type", exception.details)
        self.assertEqual(exception.details["object_type"], "User")
        self.assertIn("serialization_format", exception.details)
        self.assertEqual(exception.details["serialization_format"], "json")
    
    def test_deserialization_exception_with_input_info(self):
        """Test: DeserializationException includes input context"""
        # Arrange & Act
        exception = DeserializationException(
            message="Failed to deserialize request",
            expected_type="UserRequest",
            received_data='{"invalid": json}',
            deserialization_format="json"
        )
        
        # Assert
        self.assertIn("expected_type", exception.details)
        self.assertEqual(exception.details["expected_type"], "UserRequest")
        self.assertIn("received_data", exception.details)
        self.assertEqual(exception.details["received_data"], '{"invalid": json}')


# === RESPONSE BUILDER INTEGRATION TESTS ===

class TestResponseBuilderIntegration(BaseTestCase):
    """Integration tests for response builders working together"""
    
    def test_consistent_response_format_across_builders(self):
        """Test: All builders produce consistent base format"""
        # Arrange & Act
        success_response = ProcessResponseBuilder.success(
            data={"test": "data"}, 
            message="Success"
        )
        
        error_response = ErrorResponseBuilder.validation_error(
            message="Validation failed"
        )
        
        paginated_response = PaginatedResponseBuilder.success(
            items=[{"id": "1"}],
            total_count=1,
            page=0,
            page_size=10,
            message="Items found"
        )
        
        # Assert - All responses have consistent base fields
        for response in [success_response, error_response, paginated_response]:
            self.assertIn("status", response)
            self.assertIn("status_code", response)
            self.assertIn("message", response)
            self.assertIn("timestamp", response)
            self.assertIn("request_id", response)
    
    def test_response_builders_with_context(self):
        """Test: Response builders work with contextual information"""
        # Arrange - Simulate request context
        request_id = "test-req-123"
        
        # Act
        response = SimpleObjectResponseBuilder.success(
            data={"id": "123", "name": "Test"},
            message="Entity retrieved",
            request_id=request_id
        )
        
        # Assert
        self.assertEqual(response["request_id"], request_id)
        self.assertIn("timestamp", response)


# === RUN TESTS ===

def run_interface_tests():
    """Run all interface layer tests"""
    print("🖥️ Running Interface Layer Tests\n")
    
    # Process response builder tests
    process_tests = TestProcessResponseBuilder()
    process_tests.setUp()
    
    process_test_methods = [
        ("test_create_response_success", process_tests.test_create_response_success),
        ("test_update_response_success", process_tests.test_update_response_success),
        ("test_delete_response_success", process_tests.test_delete_response_success),
        ("test_completed_response_without_data", process_tests.test_completed_response_without_data),
    ]
    
    for test_name, test_method in process_test_methods:
        try:
            test_method()
            print(f"   ✅ {test_name}: PASSED")
        except Exception as e:
            print(f"   ❌ {test_name}: FAILED - {e}")
    
    # Simple object response builder tests
    simple_tests = TestSimpleObjectResponseBuilder()
    simple_tests.setUp()
    
    simple_test_methods = [
        ("test_found_response", simple_tests.test_found_response),
        ("test_retrieved_response", simple_tests.test_retrieved_response),
        ("test_details_response", simple_tests.test_details_response),
        ("test_status_response", simple_tests.test_status_response),
    ]
    
    for test_name, test_method in simple_test_methods:
        try:
            test_method()
            print(f"   ✅ {test_name}: PASSED")
        except Exception as e:
            print(f"   ❌ {test_name}: FAILED - {e}")
    
    # Paginated response builder tests
    paginated_tests = TestPaginatedResponseBuilder()
    paginated_tests.setUp()
    
    paginated_test_methods = [
        ("test_paginated_response_with_results", paginated_tests.test_paginated_response_with_results),
        ("test_paginated_response_last_page", paginated_tests.test_paginated_response_last_page),
        ("test_from_repository_result_factory", paginated_tests.test_from_repository_result_factory),
        ("test_empty_response", paginated_tests.test_empty_response),
    ]
    
    for test_name, test_method in paginated_test_methods:
        try:
            test_method()
            print(f"   ✅ {test_name}: PASSED")
        except Exception as e:
            print(f"   ❌ {test_name}: FAILED - {e}")
    
    # Error response builder tests
    error_tests = TestErrorResponseBuilder()
    error_tests.setUp()
    
    error_test_methods = [
        ("test_validation_error_response", error_tests.test_validation_error_response),
        ("test_authentication_error_response", error_tests.test_authentication_error_response),
        ("test_authorization_error_response", error_tests.test_authorization_error_response),
        ("test_not_found_error_response", error_tests.test_not_found_error_response),
        ("test_conflict_error_response", error_tests.test_conflict_error_response),
        ("test_internal_server_error_response", error_tests.test_internal_server_error_response),
        ("test_service_unavailable_error_response", error_tests.test_service_unavailable_error_response),
    ]
    
    for test_name, test_method in error_test_methods:
        try:
            test_method()
            print(f"   ✅ {test_name}: PASSED")
        except Exception as e:
            print(f"   ❌ {test_name}: FAILED - {e}")
    
    # Presentation exception tests
    presentation_exception_tests = TestPresentationExceptions()
    presentation_exception_tests.setUp()
    
    presentation_exception_test_methods = [
        ("test_request_validation_exception_creation", presentation_exception_tests.test_request_validation_exception_creation),
        ("test_http_exception_with_status_code", presentation_exception_tests.test_http_exception_with_status_code),
        ("test_serialization_exception_with_data_info", presentation_exception_tests.test_serialization_exception_with_data_info),
        ("test_deserialization_exception_with_input_info", presentation_exception_tests.test_deserialization_exception_with_input_info),
    ]
    
    for test_name, test_method in presentation_exception_test_methods:
        try:
            test_method()
            print(f"   ✅ {test_name}: PASSED")
        except Exception as e:
            print(f"   ❌ {test_name}: FAILED - {e}")
    
    # Integration tests
    integration_tests = TestResponseBuilderIntegration()
    integration_tests.setUp()
    
    integration_test_methods = [
        ("test_consistent_response_format_across_builders", integration_tests.test_consistent_response_format_across_builders),
        ("test_response_builders_with_context", integration_tests.test_response_builders_with_context),
    ]
    
    for test_name, test_method in integration_test_methods:
        try:
            test_method()
            print(f"   ✅ {test_name}: PASSED")
        except Exception as e:
            print(f"   ❌ {test_name}: FAILED - {e}")
    
    print("\n📊 Interface Layer Tests Completed!")


if __name__ == "__main__":
    run_interface_tests()