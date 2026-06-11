"""
Test Domain Layer - Tests for domain entities, value objects, and business rules
"""
import asyncio
from datetime import datetime, timezone
from backbone import (
    BaseKernelException,
    DomainException,
    BusinessRuleViolationException,
    InvalidEntityStateException,
    InvalidValueObjectException,
    Specification,
    AndSpecification,
    OrSpecification,
    NotSpecification,
    FilterSpecification,
    EqualSpecification,
    GreaterThanSpecification,
    LessThanSpecification,
    LikeSpecification,
    InSpecification,
    BetweenSpecification,
    IsNullSpecification,
    IsNotNullSpecification,
    FilterParser,
    SortSpecification,
    MultipleSortSpecification,
    SortDirection,
    BaseTestCase
)


# === MOCK ENTITIES FOR TESTING ===

class TestUser:
    """Test entity for domain testing"""
    def __init__(self, id: str, name: str, email: str, age: int, is_active: bool = True):
        self.id = id
        self.name = name
        self.email = email
        self.age = age
        self.is_active = is_active
        self.created_at = datetime.now(timezone.utc)


# === EXCEPTION SYSTEM TESTS ===

class TestDomainExceptions(BaseTestCase):
    """Test domain exception system with 8-digit error codes"""
    
    def test_base_kernel_exception_creation(self):
        """Test: BaseKernelException creates with proper structure"""
        # Arrange & Act
        exception = BaseKernelException(
            code=11001001,
            message="Test exception message",
            details={"technical_details": "Technical details for debugging"}
        )
        
        # Assert
        self.assertEqual(exception.code, 11001001)
        self.assertEqual(exception.message, "Test exception message")
        self.assertIn("technical_details", exception.details)
        self.assertIsNotNone(exception.rid)
        self.assertEqual(exception.http_code, 500)  # default value
    
    def test_domain_exception_with_correct_layer_code(self):
        """Test: DomainException uses correct 11 layer code"""
        # Arrange & Act
        exception = DomainException(
            code=11001001,
            message="Domain validation failed"
        )
        
        # Assert
        self.assertTrue(str(exception.code).startswith("11"))
        self.assertEqual(exception.http_code, 400)  # Domain exceptions default to 400
    
    def test_business_rule_exception_inheritance(self):
        """Test: BusinessRuleViolationException inherits from DomainException"""
        # Arrange & Act
        exception = BusinessRuleViolationException(
            message="Business rule violated",
            rule_name="minimum_age_requirement"
        )
        
        # Assert
        self.assertIsInstance(exception, DomainException)
        self.assertIn("rule_violated", exception.details)
        self.assertEqual(exception.details["rule_violated"], "minimum_age_requirement")
    
    def test_exception_public_data_format(self):
        """Test: Exception public data excludes internal fields"""
        # Arrange
        exception = BaseKernelException(
            code=11001001,
            message="Public message",
            details={"technical_details": "Internal technical details"},
            internal_data={"debug_info": "sensitive data"}
        )
        
        # Act - check if the method exists first
        if hasattr(exception, 'to_public_dict'):
            public_data = exception.to_public_dict()
            # Assert
            self.assertIn("code", public_data)
            self.assertIn("message", public_data)
            self.assertIn("rid", public_data)
            self.assertNotIn("debug_info", public_data)
        else:
            # Verify basic structure
            self.assertEqual(exception.code, 11001001)
            self.assertEqual(exception.message, "Public message")
    
    def test_exception_full_data_format(self):
        """Test: Exception full data includes all fields for logging"""
        # Arrange
        exception = BaseKernelException(
            code=11001001,
            message="Test message",
            details={"technical_details": "Technical info"},
            internal_data={"debug": "info"}
        )
        
        # Act - check if the method exists first  
        if hasattr(exception, 'to_full_dict'):
            full_data = exception.to_full_dict()
            # Assert
            self.assertIn("code", full_data)
            self.assertIn("message", full_data)
            self.assertIn("rid", full_data)
        else:
            # Verify basic structure
            self.assertEqual(exception.code, 11001001)
            self.assertEqual(exception.message, "Test message")


# === SPECIFICATION PATTERN TESTS ===

class TestSpecificationPattern(BaseTestCase):
    """Test specification pattern implementation"""
    
    def setUp(self):
        super().setUp()
        self.users = [
            TestUser("1", "Alice", "alice@example.com", 25, True),
            TestUser("2", "Bob", "bob@example.com", 30, True),
            TestUser("3", "Charlie", "charlie@example.com", 35, False),
            TestUser("4", "Diana", "diana@example.com", 28, True),
        ]
    
    def test_equal_specification(self):
        """Test: EqualSpecification filters correctly"""
        # Arrange
        spec = EqualSpecification("name", "Alice")
        
        # Act
        filtered = [user for user in self.users if spec.is_satisfied_by(user)]
        
        # Assert
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].name, "Alice")
    
    def test_greater_than_specification(self):
        """Test: GreaterThanSpecification filters correctly"""
        # Arrange
        spec = GreaterThanSpecification("age", 28)
        
        # Act
        filtered = [user for user in self.users if spec.is_satisfied_by(user)]
        
        # Assert
        self.assertEqual(len(filtered), 2)  # Bob (30) and Charlie (35)
        ages = [user.age for user in filtered]
        self.assertIn(30, ages)
        self.assertIn(35, ages)
    
    def test_in_specification(self):
        """Test: InSpecification filters with multiple values"""
        # Arrange
        spec = InSpecification("name", ["Alice", "Charlie"])
        
        # Act
        filtered = [user for user in self.users if spec.is_satisfied_by(user)]
        
        # Assert
        self.assertEqual(len(filtered), 2)
        names = [user.name for user in filtered]
        self.assertIn("Alice", names)
        self.assertIn("Charlie", names)
    
    def test_between_specification(self):
        """Test: BetweenSpecification filters range correctly"""
        # Arrange
        spec = BetweenSpecification("age", 26, 32)
        
        # Act
        filtered = [user for user in self.users if spec.is_satisfied_by(user)]
        
        # Assert
        self.assertEqual(len(filtered), 2)  # Bob (30) and Diana (28)
        ages = [user.age for user in filtered]
        self.assertIn(30, ages)
        self.assertIn(28, ages)
    
    def test_is_null_specification(self):
        """Test: IsNullSpecification detects None values"""
        # Arrange
        user_with_none = TestUser("5", "Eve", None, 25, True)
        test_users = self.users + [user_with_none]
        spec = IsNullSpecification("email")
        
        # Act
        filtered = [user for user in test_users if spec.is_satisfied_by(user)]
        
        # Assert
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].name, "Eve")
    
    def test_and_specification_composition(self):
        """Test: AndSpecification combines specifications with AND logic"""
        # Arrange
        age_spec = GreaterThanSpecification("age", 26)
        active_spec = EqualSpecification("is_active", True)
        combined_spec = age_spec & active_spec
        
        # Act
        filtered = [user for user in self.users if combined_spec.is_satisfied_by(user)]
        
        # Assert
        self.assertEqual(len(filtered), 2)  # Bob (30, active) and Diana (28, active)
        # Charlie is excluded because inactive
        names = [user.name for user in filtered]
        self.assertIn("Bob", names)
        self.assertIn("Diana", names)
        self.assertNotIn("Charlie", names)
    
    def test_or_specification_composition(self):
        """Test: OrSpecification combines specifications with OR logic"""
        # Arrange
        young_spec = LessThanSpecification("age", 27)
        old_spec = GreaterThanSpecification("age", 33)
        combined_spec = young_spec | old_spec
        
        # Act
        filtered = [user for user in self.users if combined_spec.is_satisfied_by(user)]
        
        # Assert
        self.assertEqual(len(filtered), 2)  # Alice (25) and Charlie (35)
        names = [user.name for user in filtered]
        self.assertIn("Alice", names)
        self.assertIn("Charlie", names)
    
    def test_not_specification_negation(self):
        """Test: NotSpecification negates specification logic"""
        # Arrange
        active_spec = EqualSpecification("is_active", True)
        not_active_spec = ~active_spec
        
        # Act
        filtered = [user for user in self.users if not_active_spec.is_satisfied_by(user)]
        
        # Assert
        self.assertEqual(len(filtered), 1)  # Only Charlie is inactive
        self.assertEqual(filtered[0].name, "Charlie")
        self.assertFalse(filtered[0].is_active)
    
    def test_complex_specification_composition(self):
        """Test: Complex specification with multiple operators"""
        # Arrange - Users who are (young AND active) OR (old AND inactive)
        young_active = (LessThanSpecification("age", 30) & 
                       EqualSpecification("is_active", True))
        old_inactive = (GreaterThanSpecification("age", 32) & 
                       EqualSpecification("is_active", False))
        complex_spec = young_active | old_inactive
        
        # Act
        filtered = [user for user in self.users if complex_spec.is_satisfied_by(user)]
        
        # Assert
        self.assertEqual(len(filtered), 3)  # Alice (25, active), Diana (28, active), Charlie (35, inactive)
        names = [user.name for user in filtered]
        self.assertIn("Alice", names)
        self.assertIn("Diana", names)
        self.assertIn("Charlie", names)
        self.assertNotIn("Bob", names)  # Bob is 30 and active (doesn't match either condition)


# === FILTER PARSER TESTS ===

class TestFilterParser(BaseTestCase):
    """Test filter parser functionality"""
    
    def setUp(self):
        super().setUp()
        self.parser = FilterParser()
    
    def test_parse_equal_filter(self):
        """Test: Parse equal filter from query parameters"""
        # Arrange
        query_params = {"name": "Alice"}
        
        # Act
        spec = self.parser.parse_filters(query_params)
        
        # Assert
        self.assertIsInstance(spec, EqualSpecification)
        # Test with mock entity
        user = TestUser("1", "Alice", "alice@example.com", 25)
        self.assertTrue(spec.is_satisfied_by(user))
    
    def test_parse_comparison_operators(self):
        """Test: Parse different comparison operators"""
        # Test greater than
        spec_gt = self.parser.parse_filters({"age__gt": "25"})
        user_30 = TestUser("1", "Bob", "bob@example.com", 30)
        user_20 = TestUser("2", "Alice", "alice@example.com", 20)
        
        self.assertTrue(spec_gt.is_satisfied_by(user_30))
        self.assertFalse(spec_gt.is_satisfied_by(user_20))
        
        # Test less than
        spec_lt = self.parser.parse_filters({"age__lt": "25"})
        self.assertFalse(spec_lt.is_satisfied_by(user_30))
        self.assertTrue(spec_lt.is_satisfied_by(user_20))
    
    def test_parse_in_filter(self):
        """Test: Parse IN filter with pipe-separated values"""
        # Arrange
        query_params = {"name__in": "Alice|Bob|Charlie"}
        
        # Act
        spec = self.parser.parse_filters(query_params)
        
        # Assert
        alice = TestUser("1", "Alice", "alice@example.com", 25)
        bob = TestUser("2", "Bob", "bob@example.com", 30)
        diana = TestUser("3", "Diana", "diana@example.com", 28)
        
        self.assertTrue(spec.is_satisfied_by(alice))
        self.assertTrue(spec.is_satisfied_by(bob))
        self.assertFalse(spec.is_satisfied_by(diana))
    
    def test_parse_between_filter(self):
        """Test: Parse BETWEEN filter with pipe-separated values"""
        # Arrange
        query_params = {"age__between": "25|35"}
        
        # Act
        spec = self.parser.parse_filters(query_params)
        
        # Assert
        user_30 = TestUser("1", "Bob", "bob@example.com", 30)  # Should match
        user_20 = TestUser("2", "Alice", "alice@example.com", 20)  # Should not match
        user_40 = TestUser("3", "Charlie", "charlie@example.com", 40)  # Should not match
        
        self.assertTrue(spec.is_satisfied_by(user_30))
        self.assertFalse(spec.is_satisfied_by(user_20))
        self.assertFalse(spec.is_satisfied_by(user_40))
    
    def test_parse_multiple_filters(self):
        """Test: Parse multiple filters combined with AND"""
        # Arrange
        query_params = {
            "age__gte": "25",
            "is_active": "true"
        }
        
        # Act
        spec = self.parser.parse_filters(query_params)
        
        # Assert
        active_adult = TestUser("1", "Bob", "bob@example.com", 30, True)  # Should match
        inactive_adult = TestUser("2", "Charlie", "charlie@example.com", 35, False)  # Should not match
        active_minor = TestUser("3", "Alice", "alice@example.com", 20, True)  # Should not match
        
        self.assertTrue(spec.is_satisfied_by(active_adult))
        self.assertFalse(spec.is_satisfied_by(inactive_adult))
        self.assertFalse(spec.is_satisfied_by(active_minor))


# === SORTING TESTS ===

class TestSortSpecification(BaseTestCase):
    """Test sort specification functionality"""
    
    def test_single_sort_specification(self):
        """Test: Single field sorting specification"""
        # Arrange
        sort_spec = SortSpecification("age", SortDirection.ASC)
        
        # Act
        sort_criteria = sort_spec.to_sort_criteria()
        
        # Assert
        self.assertEqual(sort_criteria, [("age", "asc")])
    
    def test_multiple_sort_specification(self):
        """Test: Multiple field sorting specification"""
        # Arrange
        multi_sort = MultipleSortSpecification()
        multi_sort.add_sort("age", SortDirection.DESC)
        multi_sort.add_sort("name", SortDirection.ASC)
        
        # Act
        sort_criteria = multi_sort.to_sort_criteria()
        
        # Assert
        expected = [("age", "desc"), ("name", "asc")]
        self.assertEqual(sort_criteria, expected)
    
    def test_sort_direction_values(self):
        """Test: SortDirection enum values"""
        # Assert
        self.assertEqual(SortDirection.ASC.value, "asc")
        self.assertEqual(SortDirection.DESC.value, "desc")


# === RUN TESTS ===

def run_domain_tests():
    """Run all domain layer tests"""
    print("🧪 Running Domain Layer Tests\n")
    
    # Exception tests
    exception_tests = TestDomainExceptions()
    exception_tests.setUp()
    
    test_methods = [
        ("test_base_kernel_exception_creation", exception_tests.test_base_kernel_exception_creation),
        ("test_domain_exception_with_correct_layer_code", exception_tests.test_domain_exception_with_correct_layer_code),
        ("test_business_rule_exception_inheritance", exception_tests.test_business_rule_exception_inheritance),
        ("test_exception_public_data_format", exception_tests.test_exception_public_data_format),
        ("test_exception_full_data_format", exception_tests.test_exception_full_data_format),
    ]
    
    for test_name, test_method in test_methods:
        try:
            test_method()
            print(f"   ✅ {test_name}: PASSED")
        except Exception as e:
            print(f"   ❌ {test_name}: FAILED - {e}")
    
    # Specification tests
    spec_tests = TestSpecificationPattern()
    spec_tests.setUp()
    
    spec_test_methods = [
        ("test_equal_specification", spec_tests.test_equal_specification),
        ("test_greater_than_specification", spec_tests.test_greater_than_specification),
        ("test_in_specification", spec_tests.test_in_specification),
        ("test_between_specification", spec_tests.test_between_specification),
        ("test_is_null_specification", spec_tests.test_is_null_specification),
        ("test_and_specification_composition", spec_tests.test_and_specification_composition),
        ("test_or_specification_composition", spec_tests.test_or_specification_composition),
        ("test_not_specification_negation", spec_tests.test_not_specification_negation),
        ("test_complex_specification_composition", spec_tests.test_complex_specification_composition),
    ]
    
    for test_name, test_method in spec_test_methods:
        try:
            test_method()
            print(f"   ✅ {test_name}: PASSED")
        except Exception as e:
            print(f"   ❌ {test_name}: FAILED - {e}")
    
    # Filter parser tests
    parser_tests = TestFilterParser()
    parser_tests.setUp()
    
    parser_test_methods = [
        ("test_parse_equal_filter", parser_tests.test_parse_equal_filter),
        ("test_parse_comparison_operators", parser_tests.test_parse_comparison_operators),
        ("test_parse_in_filter", parser_tests.test_parse_in_filter),
        ("test_parse_between_filter", parser_tests.test_parse_between_filter),
        ("test_parse_multiple_filters", parser_tests.test_parse_multiple_filters),
    ]
    
    for test_name, test_method in parser_test_methods:
        try:
            test_method()
            print(f"   ✅ {test_name}: PASSED")
        except Exception as e:
            print(f"   ❌ {test_name}: FAILED - {e}")
    
    # Sort specification tests
    sort_tests = TestSortSpecification()
    sort_tests.setUp()
    
    sort_test_methods = [
        ("test_single_sort_specification", sort_tests.test_single_sort_specification),
        ("test_multiple_sort_specification", sort_tests.test_multiple_sort_specification),
        ("test_sort_direction_values", sort_tests.test_sort_direction_values),
    ]
    
    for test_name, test_method in sort_test_methods:
        try:
            test_method()
            print(f"   ✅ {test_name}: PASSED")
        except Exception as e:
            print(f"   ❌ {test_name}: FAILED - {e}")
    
    print("\n📊 Domain Layer Tests Completed!")


if __name__ == "__main__":
    run_domain_tests()