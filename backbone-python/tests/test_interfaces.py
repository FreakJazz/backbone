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
        """Test: created() returns {"id": entity_id}"""
        response = ProcessResponseBuilder.created("123")
        self.assertEqual(response, {"id": "123"})

    def test_update_response_success(self):
        """Test: updated() returns {"id": entity_id}"""
        response = ProcessResponseBuilder.updated("123")
        self.assertEqual(response, {"id": "123"})

    def test_delete_response_success(self):
        """Test: deleted() returns {"id": entity_id}"""
        response = ProcessResponseBuilder.deleted("123")
        self.assertEqual(response, {"id": "123"})

    def test_completed_response_without_data(self):
        """Test: success() without id returns empty dict"""
        response = ProcessResponseBuilder.success()
        self.assertEqual(response, {})


class TestSimpleObjectResponseBuilder(BaseTestCase):
    """Test simple object response builder — retorna el objeto directamente sin envelope"""

    def test_found_response(self):
        """Test: found() returns data dict as-is"""
        data = {"id": "123", "name": "Found Entity", "is_active": True}
        response = SimpleObjectResponseBuilder.found(data)
        self.assertEqual(response, data)

    def test_retrieved_response(self):
        """Test: retrieved() returns data dict as-is"""
        data = {"id": "456", "name": "Retrieved Entity"}
        response = SimpleObjectResponseBuilder.retrieved(data)
        self.assertEqual(response, data)

    def test_details_response(self):
        """Test: success() returns data dict as-is"""
        data = {"id": "789", "name": "Entity", "created_at": "2024-01-01T00:00:00Z"}
        response = SimpleObjectResponseBuilder.success(data)
        self.assertEqual(response, data)

    def test_status_response(self):
        """Test: found() with status data returns it directly"""
        data = {"status": "active", "health": "ok"}
        response = SimpleObjectResponseBuilder.found(data)
        self.assertEqual(response["status"], "active")
        self.assertEqual(response["health"], "ok")


class TestPaginatedResponseBuilder(BaseTestCase):
    """Test paginated response builder — contrato: {meta, items, pagination}"""

    def test_paginated_response_with_results(self):
        """Test: success() retorna meta + items + pagination"""
        items = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
        response = PaginatedResponseBuilder.success(
            items=items,
            total_count=10,
            page=0,
            page_size=3,
            message="Items retrieved successfully",
        )

        self.assertEqual(response["meta"]["status"], "success")
        self.assertEqual(response["meta"]["status_code"], 200)
        self.assertEqual(response["meta"]["message"], "Items retrieved successfully")
        self.assertEqual(response["items"], items)

        pag = response["pagination"]
        self.assertEqual(pag["total_count"], 10)
        self.assertEqual(pag["page"], 0)
        self.assertEqual(pag["page_size"], 3)

    def test_paginated_response_last_page(self):
        """Test: success() en última página mantiene parámetros correctos"""
        response = PaginatedResponseBuilder.success(
            items=[{"id": "4"}],
            total_count=4,
            page=1,
            page_size=3,
            message="Last page",
        )
        self.assertEqual(response["pagination"]["page"], 1)
        self.assertEqual(response["pagination"]["total_count"], 4)

    def test_from_repository_result_factory(self):
        """Test: from_repository_result() genera mensaje con el tipo de recurso"""
        items = [{"id": "1"}, {"id": "2"}]
        response = PaginatedResponseBuilder.from_repository_result(
            items=items,
            total_count=5,
            page=1,
            page_size=2,
            resource_type="user",
        )
        self.assertIn("users", response["meta"]["message"].lower())
        self.assertEqual(len(response["items"]), 2)
        self.assertEqual(response["pagination"]["total_count"], 5)

    def test_empty_response(self):
        """Test: empty() retorna items vacío con total_count=0"""
        response = PaginatedResponseBuilder.empty(
            resource_type="user",
            message="No users found matching criteria",
        )
        self.assertEqual(response["meta"]["status"], "success")
        self.assertEqual(response["meta"]["message"], "No users found matching criteria")
        self.assertEqual(response["items"], [])
        self.assertEqual(response["pagination"]["total_count"], 0)


class TestErrorResponseBuilder(BaseTestCase):
    """Test error response builder — contrato alineado con backbone-go."""

    def test_validation_error_response(self):
        """Test: Validation error — 400 con estructura estándar, sin field_errors."""
        response = ErrorResponseBuilder.validation_error(message="Validation failed")
        self.assertEqual(response["status_code"], 400)
        self.assertEqual(response["message"], "Validation failed")
        self.assertEqual(response["error_code"], 130000001)  # IFC_INVALID_REQUEST_BODY
        self.assertIn("rid", response)
        self.assertNotIn("field_errors", response)
        self.assertNotIn("code_error", response)

    def test_validation_error_custom_code(self):
        """Test: El caller puede sobreescribir el código por defecto."""
        response = ErrorResponseBuilder.validation_error(
            message="Filtro inválido",
            error_code=110000005,  # DOMAIN_INVALID_FILTER
        )
        self.assertEqual(response["error_code"], 110000005)

    def test_authentication_error_response(self):
        """Test: Authentication error — 401 con código de catálogo."""
        response = ErrorResponseBuilder.authentication_error(message="Authentication required")
        self.assertEqual(response["status_code"], 401)
        self.assertEqual(response["error_code"], 130000006)  # IFC_UNAUTHORIZED
        self.assertIn("rid", response)

    def test_authorization_error_response(self):
        """Test: Authorization error — 403 con código de catálogo."""
        response = ErrorResponseBuilder.authorization_error(message="Access denied")
        self.assertEqual(response["status_code"], 403)
        self.assertEqual(response["error_code"], 130000007)  # IFC_FORBIDDEN

    def test_not_found_error_response(self):
        """Test: Not found error — 404 con código de catálogo."""
        response = ErrorResponseBuilder.not_found_error(message="User not found")
        self.assertEqual(response["status_code"], 404)
        self.assertEqual(response["error_code"], 120000004)  # APP_RESOURCE_NOT_FOUND

    def test_conflict_error_response(self):
        """Test: Conflict error — 409 con código de catálogo."""
        response = ErrorResponseBuilder.conflict_error(message="Email already exists")
        self.assertEqual(response["status_code"], 409)
        self.assertEqual(response["error_code"], 120000006)  # APP_CONFLICT

    def test_internal_server_error_response(self):
        """Test: Internal server error — 500 con código de catálogo, sin detalles."""
        response = ErrorResponseBuilder.internal_server_error(message="An unexpected error occurred")
        self.assertEqual(response["status_code"], 500)
        self.assertEqual(response["error_code"], 140000001)  # INFRA_DB_FAILURE
        self.assertNotIn("code_error", response)

    def test_internal_server_error_default_message(self):
        """Test: Sin mensaje → usa el mensaje genérico seguro."""
        response = ErrorResponseBuilder.internal_server_error()
        self.assertEqual(response["status_code"], 500)
        self.assertEqual(response["message"], "An unexpected error occurred")
        self.assertEqual(response["error_code"], 140000001)

    def test_service_unavailable_error_response(self):
        """Test: Service unavailable — 503 con código de catálogo."""
        response = ErrorResponseBuilder.service_unavailable_error(message="Database service unavailable")
        self.assertEqual(response["status_code"], 503)
        self.assertEqual(response["error_code"], 140000005)  # INFRA_SERVICE_UNAVAILABLE

    def test_error_code_always_present(self):
        """Test: error_code SIEMPRE presente en todos los métodos."""
        methods = [
            lambda: ErrorResponseBuilder.validation_error("v"),
            lambda: ErrorResponseBuilder.authentication_error("a"),
            lambda: ErrorResponseBuilder.authorization_error("f"),
            lambda: ErrorResponseBuilder.not_found_error("n"),
            lambda: ErrorResponseBuilder.conflict_error("c"),
            lambda: ErrorResponseBuilder.internal_server_error("i"),
            lambda: ErrorResponseBuilder.service_unavailable_error("s"),
        ]
        for fn in methods:
            response = fn()
            self.assertIn("error_code", response)
            self.assertNotEqual(response["error_code"], 0)

    def test_rid_auto_generated_when_not_supplied(self):
        """Test: RID se genera automáticamente y es único por llamada."""
        r1 = ErrorResponseBuilder.not_found_error("x")
        r2 = ErrorResponseBuilder.not_found_error("x")
        self.assertIn("rid", r1)
        self.assertNotEqual(r1["rid"], r2["rid"])

    def test_rid_preserved_when_supplied(self):
        """Test: RID pasado explícitamente se conserva."""
        rid = "my-trace-id-abc"
        response = ErrorResponseBuilder.not_found_error("x", rid=rid)
        self.assertEqual(response["rid"], rid)

    def test_from_exception_kernel(self):
        """Test: from_exception usa rid, http_code y code del BaseKernelException."""
        from backbone.domain.exceptions.base_kernel_exception import BaseKernelException

        exc = BaseKernelException(code=11003007, message="Filtro inválido", http_code=400)
        response = ErrorResponseBuilder.from_exception(exc)

        self.assertEqual(response["status_code"], 400)
        self.assertEqual(response["message"], "Filtro inválido")
        self.assertEqual(response["error_code"], 11003007)
        self.assertEqual(response["rid"], exc.rid)

    def test_from_exception_generic(self):
        """Test: Excepción genérica → 500 seguro, sin exponer detalles internos."""
        response = ErrorResponseBuilder.from_exception(ValueError("internal detail"))
        self.assertEqual(response["status_code"], 500)
        self.assertEqual(response["message"], "An unexpected error occurred")
        self.assertNotIn("internal detail", response["message"])
        self.assertEqual(response["error_code"], 140000001)


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
    
    def test_consistent_error_fields(self):
        """Test: ErrorResponseBuilder siempre incluye rid, status_code y message."""
        for build_fn, kwargs in [
            (ErrorResponseBuilder.validation_error,       {"message": "v"}),
            (ErrorResponseBuilder.authentication_error,   {"message": "a"}),
            (ErrorResponseBuilder.not_found_error,        {"message": "n"}),
            (ErrorResponseBuilder.internal_server_error,  {"message": "i"}),
        ]:
            response = build_fn(**kwargs)
            self.assertIn("rid",         response, f"{build_fn.__name__} debe tener rid")
            self.assertIn("status_code", response, f"{build_fn.__name__} debe tener status_code")
            self.assertIn("message",     response, f"{build_fn.__name__} debe tener message")
            self.assertNotIn("code_error",  response, f"{build_fn.__name__} no debe tener code_error")
            self.assertNotIn("request_id",  response, f"{build_fn.__name__} no debe tener request_id")

    def test_response_builders_with_rid(self):
        """Test: ErrorResponseBuilder acepta rid externo para trazabilidad."""
        rid = "test-req-123"
        response = ErrorResponseBuilder.not_found_error(message="Not found", rid=rid)
        self.assertEqual(response["rid"], rid)


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
        ("test_consistent_error_fields", integration_tests.test_consistent_error_fields),
        ("test_response_builders_with_rid", integration_tests.test_response_builders_with_rid),
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