# 🎯 Quick Reference Guide - Backbone Go

## 📦 Installation

```bash
go get github.com/freakjazz/backbone-go
```

---

## 🏗️ Project Structure

```
my-project/
├── go.mod
├── main.go
├── config.yaml
│
├── domain/              # Business logic
│   ├── entities/       # Domain entities
│   └── repositories/   # Repository interfaces
│
├── application/        # Use cases
│   └── services/       # Application services
│
├── infrastructure/     # Technical details
│   ├── persistence/   # Database implementations
│   └── messaging/     # Event handling
│
└── interfaces/         # HTTP/gRPC handlers
    └── http/          # HTTP routes
```

---

## 🚀 Quick Start

### 1. Basic Setup

```go
package main

import (
    "github.com/freakjazz/backbone-go/infrastructure/logging"
    "github.com/freakjazz/backbone-go/infrastructure/config"
)

func main() {
    // Load config
    cfg, _ := config.LoadConfig(".")
    
    // Setup logger
    logger := logging.NewLogger(cfg.AppName)
    
    logger.Info("Application started", nil)
}
```

### 2. Configuration

```yaml
# config.yaml
app_name: "my-service"
app_version: "1.0.0"
environment: "development"

server_port: 8000
log_level: "info"

event_bus_type: "inmemory"  # kafka, redis, inmemory
event_store_path: "./event_store"
```

---

## 🔢 Exception System

### Domain Exceptions (11xxxxxx)

```go
import "github.com/freakjazz/backbone-go/domain/exceptions"

// Basic domain exception
err := exceptions.NewDomainException(
    11001001,
    "Business rule violated",
    map[string]interface{}{"field": "age"},
)

// Business rule violation
err := exceptions.NewBusinessRuleViolationException(
    "User must be 18 or older",
    "ValidateUserAge",
)

// Invalid entity state
err := exceptions.NewInvalidEntityStateException(
    "User is inactive",
    "User",
    "user-123",
    "inactive",
    "active",
)

// Invalid value object
err := exceptions.NewInvalidValueObjectException(
    "Invalid email format",
    "Email",
    "invalid-email",
)
```

### Application Exceptions (10xxxxxx)

```go
import "github.com/freakjazz/backbone-go/application/exceptions"

// Use case exception
err := exceptions.NewUseCaseException(
    "Failed to create user",
    "CreateUserUseCase",
)

// Validation exception
err := exceptions.NewValidationException(
    "Validation failed",
    []exceptions.ValidationError{
        {Field: "email", Message: "Invalid format"},
        {Field: "age", Message: "Must be positive"},
    },
)

// Authorization exception
err := exceptions.NewAuthorizationException(
    "Insufficient permissions",
    "users:write",
    "user-123",
)

// Resource not found
err := exceptions.NewResourceNotFoundException(
    "User not found",
    "User",
    "user-123",
)
```

---

## 🔄 Event System

### Creating Events

```go
import "github.com/freakjazz/backbone-go/domain/ports"

// Base event
event := ports.NewBaseEvent(
    "UserCreated",
    "my-service",
    map[string]interface{}{
        "user_id": 123,
        "email": "user@example.com",
    },
    "users-service",
    "create-user",
)

// Domain event (with aggregate info)
domainEvent := ports.NewDomainEvent(
    "OrderCreated",
    "orders-service",
    map[string]interface{}{"order_id": "ORD-123"},
    "orders-microservice",
    "create-order",
    "ORD-123",     // aggregate_id
    "Order",        // aggregate_type
    1,             // aggregate_version
)

// Integration event (for external services)
integrationEvent := ports.NewIntegrationEvent(
    "PaymentProcessed",
    "payments-service",
    map[string]interface{}{"amount": 99.99},
    "payments-microservice",
    "process-payment",
    "billing-service",  // target_service
)
```

### Publishing Events

```go
import (
    "context"
    "github.com/freakjazz/backbone-go/infrastructure/messaging"
)

// In-memory (for testing)
eventBus := messaging.NewInMemoryEventBus(logger)

// Kafka
eventBus := messaging.NewKafkaEventBus(
    []string{"localhost:9092"},
    logger,
)

// Redis
eventBus := messaging.NewRedisEventBus(
    "localhost:6379",
    "",  // password
    0,   // db
    logger,
)

// Publish
err := eventBus.Publish(context.Background(), event)
```

### Subscribing to Events

```go
// Define handler
handler := func(event *ports.BaseEvent) error {
    logger.Info("Event received", map[string]interface{}{
        "event_name": event.EventName,
        "data": event.Data,
    })
    return nil
}

// Subscribe
err := eventBus.Subscribe(context.Background(), "UserCreated", handler)

// Unsubscribe
err := eventBus.Unsubscribe(context.Background(), "UserCreated")

// Clean up
defer eventBus.Close()
```

---

## 📊 Logging

```go
import "github.com/freakjazz/backbone-go/infrastructure/logging"

logger := logging.NewLogger("my-service")

// Log levels
logger.Debug("Debug message", map[string]interface{}{"key": "value"})
logger.Info("Info message", nil)
logger.Warning("Warning message", map[string]interface{}{"code": 123})
logger.Error("Error occurred", map[string]interface{}{"error": err.Error()})
logger.Critical("Critical error", map[string]interface{}{"system": "down"})

// With context
contextLogger := logger.WithContext(map[string]interface{}{
    "request_id": "req-123",
    "user_id": "user-456",
})
contextLogger.Info("Request processed", nil)
```

---

## 🔧 Response Builders

### Process Responses (CREATE/UPDATE/DELETE)

```go
import "github.com/freakjazz/backbone-go/interfaces/responses"

// Created (201)
response := responses.ProcessResponseBuilder.Created(
    "User created successfully",
    "user-123-456",
)

// Updated (200)
response := responses.ProcessResponseBuilder.Updated(
    "User updated",
    map[string]interface{}{"id": "user-123"},
)

// Deleted (200)
response := responses.ProcessResponseBuilder.Deleted(
    "User deleted",
    "user-123",
)

// Generic success
response := responses.ProcessResponseBuilder.Success(
    "Operation completed",
    map[string]interface{}{"result": "ok"},
    200,
)
```

### Query Responses (READ/GET)

```go
// List with pagination
users := []map[string]interface{}{
    {"id": "1", "name": "John"},
    {"id": "2", "name": "Jane"},
}

response := responses.QueryResponseBuilder.SuccessWithPagination(
    "Users retrieved",
    users,
    1,    // page
    10,   // page_size
    100,  // total_records
)

// Single resource
response := responses.QueryResponseBuilder.Single(
    "User retrieved",
    map[string]interface{}{"id": "1", "name": "John"},
)

// Empty result
response := responses.QueryResponseBuilder.Empty("No users found")
```

### Error Responses

```go
// From exception
response := responses.ErrorResponseBuilder.FromException(err)

// Bad request (400)
response := responses.ErrorResponseBuilder.BadRequest(
    "Invalid input",
    map[string]interface{}{"field": "email"},
)

// Unauthorized (401)
response := responses.ErrorResponseBuilder.Unauthorized(
    "Authentication required",
)

// Forbidden (403)
response := responses.ErrorResponseBuilder.Forbidden(
    "Access denied",
)

// Not found (404)
response := responses.ErrorResponseBuilder.NotFound(
    "Resource not found",
    "User",
    "user-123",
)

// Internal server error (500)
response := responses.ErrorResponseBuilder.InternalServerError()
```

---

## 📋 Repository Pattern

```go
import (
    "context"
    "github.com/freakjazz/backbone-go/domain/repositories"
)

// Define interface
type UserRepository interface {
    repositories.IRepository
    FindByEmail(ctx context.Context, email string) (*User, error)
}

// Implement
type userRepositoryImpl struct {
    db *sql.DB
}

func (r *userRepositoryImpl) Add(ctx context.Context, entity interface{}) error {
    user := entity.(*User)
    _, err := r.db.ExecContext(ctx, "INSERT INTO users ...", user.ID, user.Name)
    return err
}

func (r *userRepositoryImpl) FindByEmail(ctx context.Context, email string) (*User, error) {
    var user User
    err := r.db.QueryRowContext(ctx, "SELECT * FROM users WHERE email = $1", email).
        Scan(&user.ID, &user.Name, &user.Email)
    if err == sql.ErrNoRows {
        return nil, exceptions.NewResourceNotFoundException("User not found", "User", email)
    }
    return &user, err
}
```

---

## 🧪 Testing

```go
package mypackage_test

import (
    "testing"
    "github.com/stretchr/testify/assert"
)

func TestUserCreation(t *testing.T) {
    // Arrange
    user := NewUser("John", "john@example.com")
    
    // Act
    err := user.Validate()
    
    // Assert
    assert.NoError(t, err)
    assert.Equal(t, "John", user.Name)
}

// Run tests
// go test ./...
// go test -v ./...
// go test -cover ./...
```

---

## 📦 Common Patterns

### Dependency Injection

```go
type App struct {
    logger     logging.Logger
    eventBus   ports.EventBus
    userRepo   UserRepository
    config     *config.Config
}

func NewApp(cfg *config.Config) (*App, error) {
    logger := logging.NewLogger(cfg.AppName)
    eventBus := messaging.NewInMemoryEventBus(logger)
    
    return &App{
        logger:   logger,
        eventBus: eventBus,
        config:   cfg,
    }, nil
}
```

### Context Propagation

```go
func (s *UserService) CreateUser(ctx context.Context, data map[string]interface{}) error {
    // Extract from context
    userID, _ := ctx.Value("user_id").(string)
    requestID, _ := ctx.Value("request_id").(string)
    
    // Use in logging
    s.logger.Info("Creating user", map[string]interface{}{
        "initiated_by": userID,
        "request_id": requestID,
    })
    
    // Pass to repository
    return s.repo.Add(ctx, user)
}
```

---

## 🚀 Production Checklist

- [ ] Load configuration from environment
- [ ] Setup structured logging
- [ ] Configure event bus (Kafka/Redis)
- [ ] Implement health check endpoint
- [ ] Add graceful shutdown
- [ ] Setup monitoring/metrics
- [ ] Configure error tracking
- [ ] Add request tracing
- [ ] Implement rate limiting
- [ ] Setup CI/CD pipeline

---

## 📚 Additional Resources

- [Full Documentation](./README.md)
- [Examples](../examples/)
- [Python vs Go Comparison](./docs/PYTHON_VS_GO.md)
- [Architecture Guide](./docs/ARCHITECTURE.md)
- [GitHub Repository](https://github.com/freakjazz/backbone-go)
