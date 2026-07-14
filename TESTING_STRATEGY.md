# Testing Strategy with Backbone

**Complete guide to testing microservices using the backbone framework**

---

## Table of Contents
1. Testing Philosophy
2. Mock Repository Pattern
3. Error Code Validation
4. RID Propagation Testing
5. Specification Testing
6. Test Fixtures & Utilities
7. Integration Testing Examples

---

## 1. Testing Philosophy

### Core Principles

backbone testing follows Clean Architecture layers:

```
┌─────────────────────────────────────────┐
│ Test Layer (Interface)                  │
│ - HTTP handlers, route handlers         │
│ - Assert status codes, response shape   │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│ Test Layer (Application)                │
│ - Commands, queries, handlers           │
│ - Assert business logic, exceptions     │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│ Test Layer (Domain)                     │
│ - Entities, value objects               │
│ - Assert invariants, rules              │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│ Mock/Test Repository (Infrastructure)   │
│ - In-memory, predictable behavior       │
│ - No database, no I/O                   │
└─────────────────────────────────────────┘
```

**Testing strategy:**
- ✅ Unit test domain and application logic
- ✅ Mock repositories (not databases)
- ✅ Assert error codes, not error messages
- ✅ Validate response shape matches backbone contract
- ✅ Test RID propagation through the stack
- ✅ Use test fixtures for consistent data

---

## 2. Mock Repository Pattern

### Go: In-Memory Repository for Testing

```go
package infrastructure

import (
    "context"
    "fmt"
    "sort"
    "sync"

    "your-app/domain"
    "your-app/domain/specifications"
)

// MockProductRepository — in-memory implementation for testing
type MockProductRepository struct {
    products map[string]*domain.Product
    mu       sync.RWMutex
}

func NewMockProductRepository() *MockProductRepository {
    return &MockProductRepository{
        products: make(map[string]*domain.Product),
    }
}

func (r *MockProductRepository) FindByID(ctx context.Context, id string) (*domain.Product, error) {
    r.mu.RLock()
    defer r.mu.RUnlock()

    p, exists := r.products[id]
    if !exists {
        return nil, fmt.Errorf("product not found")
    }
    return p, nil
}

func (r *MockProductRepository) FindByName(ctx context.Context, name string) (*domain.Product, error) {
    r.mu.RLock()
    defer r.mu.RUnlock()

    for _, p := range r.products {
        if p.Name == name {
            return p, nil
        }
    }
    return nil, nil
}

func (r *MockProductRepository) FindByCriteria(ctx context.Context, c *specifications.Criteria) ([]*domain.Product, error) {
    r.mu.RLock()
    defer r.mu.RUnlock()

    var results []*domain.Product

    for _, p := range r.products {
        if r.matchesSpecification(p, c.Specification) {
            results = append(results, p)
        }
    }

    // Apply sorting
    if c.SortField != "" {
        sort.Slice(results, func(i, j int) bool {
            cmp := r.compareProducts(results[i], results[j], c.SortField)
            if c.SortDirection == "desc" {
                return cmp > 0
            }
            return cmp < 0
        })
    }

    // Apply pagination
    start := (c.Page - 1) * c.PageSize
    end := start + c.PageSize
    if start >= len(results) {
        return []*domain.Product{}, nil
    }
    if end > len(results) {
        end = len(results)
    }
    return results[start:end], nil
}

func (r *MockProductRepository) Create(ctx context.Context, p *domain.Product) error {
    r.mu.Lock()
    defer r.mu.Unlock()

    if _, exists := r.products[p.ID]; exists {
        return fmt.Errorf("product already exists")
    }
    r.products[p.ID] = p
    return nil
}

func (r *MockProductRepository) Count(ctx context.Context, c *specifications.Criteria) (int, error) {
    r.mu.RLock()
    defer r.mu.RUnlock()

    count := 0
    for _, p := range r.products {
        if r.matchesSpecification(p, c.Specification) {
            count++
        }
    }
    return count, nil
}

// Helper: Match specification
func (r *MockProductRepository) matchesSpecification(p *domain.Product, spec *specifications.Specification) bool {
    if spec == nil {
        return true
    }
    // Implement your specification matching logic
    // For this example, simplified
    return true
}

// Helper: Compare products by field
func (r *MockProductRepository) compareProducts(a, b *domain.Product, field string) int {
    switch field {
    case "price":
        if a.Price < b.Price {
            return -1
        }
        if a.Price > b.Price {
            return 1
        }
        return 0
    case "name":
        if a.Name < b.Name {
            return -1
        }
        if a.Name > b.Name {
            return 1
        }
        return 0
    }
    return 0
}

// Test helper: Pre-populate repository
func (r *MockProductRepository) Seed(products ...*domain.Product) {
    r.mu.Lock()
    defer r.mu.Unlock()
    for _, p := range products {
        r.products[p.ID] = p
    }
}
```

### Python: In-Memory Repository for Testing

```python
from typing import List, Optional, Dict, Any
from threading import RLock
from your_app.domain import Product
from your_app.domain.specifications import Criteria, Specification

class MockProductRepository:
    def __init__(self):
        self.products: Dict[str, Product] = {}
        self._lock = RLock()

    def find_by_id(self, product_id: str) -> Optional[Product]:
        with self._lock:
            return self.products.get(product_id)

    def find_by_name(self, name: str) -> Optional[Product]:
        with self._lock:
            for product in self.products.values():
                if product.name == name:
                    return product
            return None

    def find_by_criteria(self, criteria: Criteria) -> List[Product]:
        with self._lock:
            results = list(self.products.values())

            # Filter by specification
            if criteria.specification:
                results = [p for p in results if self._matches_specification(p, criteria.specification)]

            # Sort
            if criteria.sort_field:
                reverse = criteria.sort_direction.lower() == "desc"
                results = sorted(results,
                    key=lambda p: getattr(p, criteria.sort_field),
                    reverse=reverse)

            # Paginate
            start = (criteria.page - 1) * criteria.page_size
            end = start + criteria.page_size
            return results[start:end]

    def count(self, criteria: Criteria) -> int:
        with self._lock:
            results = list(self.products.values())
            if criteria.specification:
                results = [p for p in results if self._matches_specification(p, criteria.specification)]
            return len(results)

    def create(self, product: Product) -> None:
        with self._lock:
            if product.id in self.products:
                raise Exception("product already exists")
            self.products[product.id] = product

    def update(self, product: Product) -> None:
        with self._lock:
            if product.id not in self.products:
                raise Exception("product not found")
            self.products[product.id] = product

    @staticmethod
    def _matches_specification(product: Product, spec: Specification) -> bool:
        # Implement your specification matching logic
        return True

    # Test helper: Pre-populate repository
    def seed(self, *products: Product) -> None:
        with self._lock:
            for product in products:
                self.products[product.id] = product

    # Test helper: Clear all data
    def clear(self) -> None:
        with self._lock:
            self.products.clear()
```

---

## 3. Error Code Validation

### Go: Assert Error Codes in Tests

```go
package application

import (
    "context"
    "testing"

    bberrors "github.com/freakjazz/backbone-go/errors"
    "your-app/application/commands"
    "your-app/domain"
    "your-app/infrastructure"
)

func TestCreateProductCommandHandler_WhenNameIsEmpty_ReturnsValidationError(t *testing.T) {
    // Arrange
    repo := infrastructure.NewMockProductRepository()
    handler := commands.NewCreateProductCommandHandler(repo)

    cmd := commands.CreateProductCommand{
        Name:  "", // Invalid: empty
        Price: 100.0,
    }

    // Act
    result, err := handler.Handle(context.Background(), cmd)

    // Assert
    if err == nil {
        t.Fatal("expected error, got nil")
    }

    appErr, ok := err.(*commands.AppError)
    if !ok {
        t.Fatalf("expected AppError, got %T", err)
    }

    // ✅ Key assertion: validate error code
    expectedCode := bberrors.IfcInvalidRequestBody.Int() // 130000001
    if appErr.Code != expectedCode {
        t.Errorf("expected error code %d, got %d", expectedCode, appErr.Code)
    }

    if result != nil {
        t.Errorf("expected nil result, got %v", result)
    }
}

func TestCreateProductCommandHandler_WhenConflict_ReturnsConflictError(t *testing.T) {
    // Arrange
    repo := infrastructure.NewMockProductRepository()
    
    // Pre-populate with existing product
    existing := &domain.Product{ID: "p1", Name: "Laptop", Price: 999.0}
    repo.Seed(existing)

    handler := commands.NewCreateProductCommandHandler(repo)

    cmd := commands.CreateProductCommand{
        Name:  "Laptop", // Duplicate name
        Price: 1500.0,
    }

    // Act
    result, err := handler.Handle(context.Background(), cmd)

    // Assert
    if err == nil {
        t.Fatal("expected error, got nil")
    }

    appErr, ok := err.(*commands.AppError)
    if !ok {
        t.Fatalf("expected AppError, got %T", err)
    }

    // ✅ Assert conflict error
    expectedCode := bberrors.AppConflict.Int() // 120000006
    if appErr.Code != expectedCode {
        t.Errorf("expected error code %d, got %d", expectedCode, appErr.Code)
    }

    if result != nil {
        t.Errorf("expected nil result, got %v", result)
    }
}

func TestCreateProductCommandHandler_Success(t *testing.T) {
    // Arrange
    repo := infrastructure.NewMockProductRepository()
    handler := commands.NewCreateProductCommandHandler(repo)

    cmd := commands.CreateProductCommand{
        Name:  "Laptop Pro",
        Price: 1500.0,
    }

    // Act
    result, err := handler.Handle(context.Background(), cmd)

    // Assert
    if err != nil {
        t.Fatalf("expected no error, got %v", err)
    }

    if result == nil {
        t.Fatal("expected result, got nil")
    }

    if result.ID == "" {
        t.Errorf("expected non-empty ID")
    }

    // Verify product was created
    created, _ := repo.FindByID(context.Background(), result.ID)
    if created == nil {
        t.Errorf("product not found in repository")
    }
}
```

### Python: Assert Error Codes in Tests

```python
import pytest
from your_app.application.commands import CreateProductCommandHandler
from your_app.domain import Product
from your_app.infrastructure import MockProductRepository
from backbone import ValidationException, ResourceConflictException
from backbone.errors import ErrorCodes

class TestCreateProductCommandHandler:
    def setup_method(self):
        self.repo = MockProductRepository()
        self.handler = CreateProductCommandHandler(self.repo)

    def test_when_name_is_empty_returns_validation_error(self):
        # Arrange
        cmd = CreateProductCommand(name="", price=100.0)

        # Act & Assert
        with pytest.raises(ValidationException) as exc_info:
            self.handler.handle(cmd)

        # ✅ Assert error code
        assert exc_info.value.code == ErrorCodes.IFC_INVALID_REQUEST_BODY  # 130000001
        assert "name" in exc_info.value.message.lower()

    def test_when_conflict_returns_conflict_error(self):
        # Arrange
        existing = Product(id="p1", name="Laptop", price=999.0)
        self.repo.seed(existing)

        cmd = CreateProductCommand(name="Laptop", price=1500.0)

        # Act & Assert
        with pytest.raises(ResourceConflictException) as exc_info:
            self.handler.handle(cmd)

        # ✅ Assert conflict error
        assert exc_info.value.code == ErrorCodes.APP_CONFLICT  # 120000006

    def test_success_creates_product(self):
        # Arrange
        cmd = CreateProductCommand(name="Laptop Pro", price=1500.0)

        # Act
        result = self.handler.handle(cmd)

        # Assert
        assert result is not None
        assert result.id != ""

        # Verify created
        created = self.repo.find_by_id(result.id)
        assert created is not None
        assert created.name == "Laptop Pro"
```

---

## 4. RID Propagation Testing

### Go: Test RID Through the Stack

```go
package interfaces

import (
    "bytes"
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "testing"

    "your-app/application/commands"
    "your-app/infrastructure"
    bberrors "github.com/freakjazz/backbone-go/errors"
    "github.com/freakjazz/backbone-go/interfaces/responses"
)

func TestCreateProductHandler_RIDPropagation(t *testing.T) {
    // Arrange
    repo := infrastructure.NewMockProductRepository()
    handler := NewProductCommandHandler(repo)

    requestID := "test-rid-12345"
    payload := map[string]interface{}{
        "name":  "Laptop",
        "price": 1500.0,
    }

    body, _ := json.Marshal(payload)
    req := httptest.NewRequest(
        "POST",
        "/products",
        bytes.NewBuffer(body),
    )
    req.Header.Set("X-Request-ID", requestID)
    req.Header.Set("Content-Type", "application/json")

    w := httptest.NewRecorder()

    // Act
    handler.CreateProduct(w, req)

    // Assert
    if w.Code != http.StatusCreated {
        t.Errorf("expected 201, got %d", w.Code)
    }

    var response map[string]interface{}
    json.Unmarshal(w.Body.Bytes(), &response)

    // ✅ Assert RID is in response
    if response["rid"] != requestID {
        t.Errorf("expected rid %s, got %v", requestID, response["rid"])
    }
}

func TestCreateProductHandler_ErrorRIDPropagation(t *testing.T) {
    // Arrange
    repo := infrastructure.NewMockProductRepository()

    // Pre-populate conflict
    repo.Seed(&domain.Product{ID: "p1", Name: "Laptop", Price: 999.0})

    handler := NewProductCommandHandler(repo)

    requestID := "test-rid-conflict"
    payload := map[string]interface{}{
        "name":  "Laptop", // Duplicate
        "price": 1500.0,
    }

    body, _ := json.Marshal(payload)
    req := httptest.NewRequest(
        "POST",
        "/products",
        bytes.NewBuffer(body),
    )
    req.Header.Set("X-Request-ID", requestID)
    req.Header.Set("Content-Type", "application/json")

    w := httptest.NewRecorder()

    // Act
    handler.CreateProduct(w, req)

    // Assert
    if w.Code != http.StatusConflict {
        t.Errorf("expected 409, got %d", w.Code)
    }

    var errorResponse map[string]interface{}
    json.Unmarshal(w.Body.Bytes(), &errorResponse)

    // ✅ Assert RID is in error response
    if errorResponse["rid"] != requestID {
        t.Errorf("expected rid %s in error, got %v", requestID, errorResponse["rid"])
    }

    // ✅ Assert error code
    if int(errorResponse["error_code"].(float64)) != bberrors.AppConflict.Int() {
        t.Errorf("expected error code %d, got %v", bberrors.AppConflict.Int(), errorResponse["error_code"])
    }
}
```

### Python: Test RID Through the Stack

```python
import json
import pytest
from flask import Flask
from your_app import create_app
from your_app.infrastructure import MockProductRepository

@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_create_product_rid_propagation(client):
    # Arrange
    request_id = "test-rid-12345"
    payload = {"name": "Laptop", "price": 1500.0}

    # Act
    response = client.post(
        "/api/v1/products",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"X-Request-ID": request_id}
    )

    # Assert
    assert response.status_code == 201
    data = json.loads(response.data)

    # ✅ Assert RID is in response
    assert data["id"] is not None
    # Note: For success, backbone typically returns just the ID
    # For errors, the RID would be in the error response

def test_create_product_error_rid_propagation(client, app):
    # Arrange
    repo = MockProductRepository()
    repo.seed(Product(id="p1", name="Laptop", price=999.0))

    request_id = "test-rid-conflict"
    payload = {"name": "Laptop", "price": 1500.0}  # Duplicate

    # Act
    response = client.post(
        "/api/v1/products",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"X-Request-ID": request_id}
    )

    # Assert
    assert response.status_code == 409
    data = json.loads(response.data)

    # ✅ Assert RID is in error response
    assert data["rid"] == request_id
    assert data["error_code"] == ErrorCodes.APP_CONFLICT  # 120000006
```

---

## 5. Specification Testing

### Go: Test Filter/Query Parsing

```go
package domain

import (
    "context"
    "testing"

    "your-app/domain/specifications"
)

func TestParseFilterParams_EqualOperator(t *testing.T) {
    // Arrange
    filters := []string{"status,eq,active"}
    criteria := specifications.ParseFilterParams(filters, 1, 10, "created_at", "desc")

    // Act
    repo := &testRepository{} // In-memory test repo
    products := repo.FindByCriteria(context.Background(), criteria)

    // Assert
    if len(products) != 2 { // Assuming 2 active products
        t.Errorf("expected 2 active products, got %d", len(products))
    }

    for _, p := range products {
        if p.Status != "active" {
            t.Errorf("product status should be active, got %s", p.Status)
        }
    }
}

func TestParseFilterParams_BetweenOperator(t *testing.T) {
    // Arrange
    filters := []string{"price,between,500|2000"}
    criteria := specifications.ParseFilterParams(filters, 1, 10, "price", "asc")

    // Act
    repo := &testRepository{}
    products := repo.FindByCriteria(context.Background(), criteria)

    // Assert
    for _, p := range products {
        if p.Price < 500 || p.Price > 2000 {
            t.Errorf("product price out of range: %f", p.Price)
        }
    }
}

func TestParseFilterParams_MultipleFilters(t *testing.T) {
    // Arrange
    filters := []string{
        "status,eq,active,and",
        "category,eq,Electronics,and",
        "price,between,500|2000",
    }
    criteria := specifications.ParseFilterParams(filters, 1, 10, "price", "desc")

    // Act
    repo := &testRepository{}
    products := repo.FindByCriteria(context.Background(), criteria)

    // Assert
    for _, p := range products {
        if p.Status != "active" {
            t.Errorf("expected active status")
        }
        if p.Category != "Electronics" {
            t.Errorf("expected Electronics category")
        }
        if p.Price < 500 || p.Price > 2000 {
            t.Errorf("expected price in range")
        }
    }

    // Verify sorting (desc by price)
    for i := 0; i < len(products)-1; i++ {
        if products[i].Price < products[i+1].Price {
            t.Errorf("expected descending sort")
        }
    }
}

func TestParseFilterParams_InvalidOperator(t *testing.T) {
    // Arrange
    filters := []string{"price,invalid_op,500"}

    // Act & Assert
    _, err := specifications.ParseFilterParams(filters, 1, 10, "", "")
    if err == nil {
        t.Fatal("expected error for invalid operator")
    }
}
```

### Python: Test Filter/Query Parsing

```python
import pytest
from your_app.domain.specifications import FilterParser, EqualSpecification, BetweenSpecification
from your_app.infrastructure import MockProductRepository
from your_app.domain import Product

class TestFilterParsing:
    def setup_method(self):
        self.repo = MockProductRepository()
        
        # Seed test data
        self.repo.seed(
            Product(id="1", name="Laptop", price=1500, status="active", category="Electronics"),
            Product(id="2", name="Mouse", price=50, status="active", category="Electronics"),
            Product(id="3", name="Desk", price=800, status="inactive", category="Furniture"),
            Product(id="4", name="Phone", price=900, status="active", category="Electronics"),
        )

    def test_equal_operator(self):
        # Arrange
        parser = FilterParser()
        filters = ["status,eq,active"]
        spec = parser.parse_filters(filters)

        # Act
        products = self.repo.find_by_criteria(spec)

        # Assert
        assert len(products) == 3
        for p in products:
            assert p.status == "active"

    def test_between_operator(self):
        # Arrange
        parser = FilterParser()
        filters = ["price,between,500|2000"]
        spec = parser.parse_filters(filters)

        # Act
        products = self.repo.find_by_criteria(spec)

        # Assert
        for p in products:
            assert 500 <= p.price <= 2000

    def test_multiple_filters_with_and(self):
        # Arrange
        parser = FilterParser()
        filters = [
            "status,eq,active,and",
            "category,eq,Electronics,and",
            "price,between,500|2000"
        ]
        spec = parser.parse_filters(filters)

        # Act
        products = self.repo.find_by_criteria(spec)

        # Assert
        assert len(products) == 2  # Laptop and Phone
        for p in products:
            assert p.status == "active"
            assert p.category == "Electronics"
            assert 500 <= p.price <= 2000

    def test_invalid_operator_raises_error(self):
        # Arrange
        parser = FilterParser()
        filters = ["price,invalid_op,500"]

        # Act & Assert
        with pytest.raises(Exception):
            parser.parse_filters(filters)
```

---

## 6. Test Fixtures & Utilities

### Go: Test Fixtures

```go
package tests

import (
    "your-app/domain"
)

// ProductFixtures — pre-built test data
type ProductFixtures struct{}

func (f *ProductFixtures) ActiveLaptop() *domain.Product {
    return &domain.Product{
        ID:       "prod-laptop-1",
        Name:     "Laptop Pro",
        Price:    1500.0,
        Status:   "active",
        Category: "Electronics",
        Stock:    100,
    }
}

func (f *ProductFixtures) InactiveFurniture() *domain.Product {
    return &domain.Product{
        ID:       "prod-desk-1",
        Name:     "Wooden Desk",
        Price:    800.0,
        Status:   "inactive",
        Category: "Furniture",
        Stock:    5,
    }
}

func (f *ProductFixtures) LowStockPhone() *domain.Product {
    return &domain.Product{
        ID:       "prod-phone-1",
        Name:     "Smartphone",
        Price:    900.0,
        Status:   "active",
        Category: "Electronics",
        Stock:    2,
    }
}

// ErrorCodeValidator — assert error codes in tests
type ErrorCodeValidator struct {
    t testing.T
}

func NewErrorCodeValidator(t testing.T) *ErrorCodeValidator {
    return &ErrorCodeValidator{t: t}
}

func (v *ErrorCodeValidator) AssertCode(err error, expectedCode int) {
    if err == nil {
        v.t.Fatal("expected error, got nil")
    }
    appErr, ok := err.(*domain.AppError)
    if !ok {
        v.t.Fatalf("expected AppError, got %T", err)
    }
    if appErr.Code != expectedCode {
        v.t.Errorf("expected code %d, got %d", expectedCode, appErr.Code)
    }
}

// ResponseValidator — assert response shape
type ResponseValidator struct {
    t testing.T
}

func (v *ResponseValidator) AssertErrorShape(resp map[string]interface{}) {
    if _, ok := resp["rid"]; !ok {
        v.t.Error("missing 'rid' field")
    }
    if _, ok := resp["status_code"]; !ok {
        v.t.Error("missing 'status_code' field")
    }
    if _, ok := resp["error_code"]; !ok {
        v.t.Error("missing 'error_code' field")
    }
    if _, ok := resp["message"]; !ok {
        v.t.Error("missing 'message' field")
    }
}
```

### Python: Test Fixtures

```python
import pytest
from your_app.domain import Product
from backbone.errors import ErrorCodes

class ProductFixtures:
    @staticmethod
    def active_laptop():
        return Product(
            id="prod-laptop-1",
            name="Laptop Pro",
            price=1500.0,
            status="active",
            category="Electronics",
            stock=100
        )

    @staticmethod
    def inactive_furniture():
        return Product(
            id="prod-desk-1",
            name="Wooden Desk",
            price=800.0,
            status="inactive",
            category="Furniture",
            stock=5
        )

    @staticmethod
    def low_stock_phone():
        return Product(
            id="prod-phone-1",
            name="Smartphone",
            price=900.0,
            status="active",
            category="Electronics",
            stock=2
        )

class ErrorCodeValidator:
    @staticmethod
    def assert_code(exception, expected_code):
        assert hasattr(exception, 'code'), "Exception must have 'code' attribute"
        assert exception.code == expected_code, \
            f"Expected code {expected_code}, got {exception.code}"

class ResponseValidator:
    @staticmethod
    def assert_error_shape(response_dict):
        required_fields = ["rid", "status_code", "error_code", "message"]
        for field in required_fields:
            assert field in response_dict, f"Missing required field: {field}"

    @staticmethod
    def assert_success_shape(response_dict):
        # For write operations
        assert "id" in response_dict, "Missing 'id' field"

    @staticmethod
    def assert_list_shape(response_dict):
        # For list operations
        assert "meta" in response_dict, "Missing 'meta' field"
        assert "items" in response_dict, "Missing 'items' field"
        assert "pagination" in response_dict, "Missing 'pagination' field"

# Pytest fixtures
@pytest.fixture
def product_fixtures():
    return ProductFixtures()

@pytest.fixture
def error_validator():
    return ErrorCodeValidator()

@pytest.fixture
def response_validator():
    return ResponseValidator()
```

---

## 7. Integration Testing Examples

### Go: Full HTTP Flow Test

```go
package interfaces

import (
    "bytes"
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "testing"

    "your-app/application/commands"
    "your-app/infrastructure"
    bberrors "github.com/freakjazz/backbone-go/errors"
)

func TestCreateAndGetProduct_FullFlow(t *testing.T) {
    // Arrange: Setup
    repo := infrastructure.NewMockProductRepository()
    createHandler := commands.NewCreateProductCommandHandler(repo)
    getHandler := commands.NewGetProductQueryHandler(repo)

    // Act 1: Create product
    createCmd := commands.CreateProductCommand{
        Name:  "Laptop Pro",
        Price: 1500.0,
    }
    createResult, err := createHandler.Handle(testContext(), createCmd)
    if err != nil {
        t.Fatalf("create failed: %v", err)
    }

    productID := createResult.ID

    // Act 2: Get product
    getCmd := commands.GetProductQuery{ID: productID}
    getResult, err := getHandler.Handle(testContext(), getCmd)
    if err != nil {
        t.Fatalf("get failed: %v", err)
    }

    // Assert
    if getResult.Product.Name != "Laptop Pro" {
        t.Errorf("expected name 'Laptop Pro', got '%s'", getResult.Product.Name)
    }
    if getResult.Product.Price != 1500.0 {
        t.Errorf("expected price 1500.0, got %f", getResult.Product.Price)
    }
}

func TestFilterProductsAndGetFirstOne(t *testing.T) {
    // Arrange
    repo := infrastructure.NewMockProductRepository()

    // Seed test data
    fixtures := &tests.ProductFixtures{}
    repo.Seed(
        fixtures.ActiveLaptop(),
        fixtures.LowStockPhone(),
        fixtures.InactiveFurniture(),
    )

    queryHandler := commands.NewGetProductsQueryHandler(repo)

    // Act: Query for active Electronics
    query := commands.GetProductsQuery{
        Filters:  []string{"status,eq,active,and", "category,eq,Electronics"},
        Page:     1,
        PageSize: 10,
        SortBy:   "price:desc",
    }

    result, err := queryHandler.Handle(testContext(), query)
    if err != nil {
        t.Fatalf("query failed: %v", err)
    }

    // Assert
    if len(result.Products) != 2 {
        t.Errorf("expected 2 products, got %d", len(result.Products))
    }

    // Verify first is most expensive
    if result.Products[0].Name != "Laptop Pro" {
        t.Errorf("expected first product to be Laptop Pro")
    }
}
```

### Python: Full HTTP Flow Test

```python
import json
import pytest
from flask import Flask
from your_app.application.commands import CreateProductCommandHandler, GetProductQueryHandler
from your_app.infrastructure import MockProductRepository
from tests.fixtures import ProductFixtures

class TestProductFlow:
    def setup_method(self):
        self.repo = MockProductRepository()
        self.create_handler = CreateProductCommandHandler(self.repo)
        self.get_handler = GetProductQueryHandler(self.repo)
        self.fixtures = ProductFixtures()

    def test_create_and_get_product_full_flow(self):
        # Act 1: Create
        cmd = CreateProductCommand(name="Laptop Pro", price=1500.0)
        result = self.create_handler.handle(cmd)

        # Assert 1
        assert result.id is not None

        # Act 2: Get
        query = GetProductQuery(product_id=result.id)
        product = self.get_handler.handle(query)

        # Assert 2
        assert product.name == "Laptop Pro"
        assert product.price == 1500.0

    def test_filter_products_and_sort(self):
        # Arrange: Seed data
        self.repo.seed(
            self.fixtures.active_laptop(),
            self.fixtures.low_stock_phone(),
            self.fixtures.inactive_furniture(),
        )

        # Act: Query for active Electronics
        query = GetProductsQuery(
            filters=["status,eq,active,and", "category,eq,Electronics"],
            page=1,
            page_size=10,
            sort_by="price:desc"
        )
        result = self.get_handler.handle(query)

        # Assert
        assert len(result.products) == 2
        assert result.products[0].name == "Laptop Pro"  # Most expensive first
        assert result.total == 2
```

---

## Best Practices Summary

| Practice | Go | Python |
|----------|-----|--------|
| **Mock Repositories** | Use interfaces, in-memory impl | Inheritance, Duck typing |
| **Error Code Testing** | Assert `.Code` property | Assert `.code` attribute |
| **Fixtures** | Struct methods | Pytest fixtures or classes |
| **Async Testing** | No goroutines in tests | Use pytest-asyncio if async |
| **Test Organization** | Test files in same package | Separate `tests/` folder |
| **Assertions** | Manual + assert libraries | pytest assertions |
| **Setup/Teardown** | `setUp()`/`tearDown()` | `setup_method()`/`teardown_method()` |
| **Parametrized Tests** | `t.Run()` subtests | `@pytest.mark.parametrize` |

---

## Installing Testing Utilities

**Go:**
```bash
go get github.com/freakjazz/backbone-go/testing
```

**Python:**
```bash
pip install backbone-python[testing]==0.1.0
```

---

*Next: API Versioning Strategy and Database Agnosticity sections*
