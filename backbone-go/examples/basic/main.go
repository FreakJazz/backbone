// Example usage of backbone-go framework
package main

import (
	"context"
	"fmt"
	"log"

	"github.com/freakjazz/backbone-go/application/exceptions"
	domainExceptions "github.com/freakjazz/backbone-go/domain/exceptions"
	"github.com/freakjazz/backbone-go/domain/ports"
	"github.com/freakjazz/backbone-go/infrastructure/config"
	"github.com/freakjazz/backbone-go/infrastructure/events"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
	"github.com/freakjazz/backbone-go/infrastructure/messaging"
	"github.com/freakjazz/backbone-go/interfaces/responses"
)

func main() {
	fmt.Println("🎯 Backbone-Go Framework Example")
	fmt.Println("==================================")

	// 1. Configuration
	cfg, err := config.LoadConfig(".")
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}
	fmt.Printf("✅ Configuration loaded: %s (env: %s)\n", cfg.AppName, cfg.Environment)

	// 2. Logger
	logger := logging.NewLogger("backbone-example")
	logger.Info("Application started", map[string]interface{}{
		"version": cfg.AppVersion,
	})
	fmt.Println("✅ Logger initialized")

	// 3. Exception System
	fmt.Println("\n📌 Testing Exception System:")
	testExceptions(logger)

	// 4. Response Builders
	fmt.Println("\n📌 Testing Response Builders:")
	testResponseBuilders()

	// 5. Event System
	fmt.Println("\n📌 Testing Event System:")
	testEventSystem(logger, cfg)

	fmt.Println("\n✅ All examples completed successfully!")
}

func testExceptions(logger logging.Logger) {
	// Domain Exception
	domainErr := domainExceptions.NewBusinessRuleViolationException(
		"User age must be between 18 and 120",
		"ValidateUserAge",
	)
	logger.Error("Domain exception example", map[string]interface{}{
		"exception": domainErr.ToDict(),
	})
	fmt.Printf("  - Domain Exception: %s (Code: %d)\n", domainErr.Message, domainErr.Code)

	// Application Exception
	appErr := exceptions.NewValidationException(
		"Validation failed",
		[]exceptions.ValidationError{
			{Field: "email", Message: "Invalid email format", Code: "INVALID_FORMAT"},
			{Field: "age", Message: "Age must be positive", Code: "OUT_OF_RANGE"},
		},
	)
	fmt.Printf("  - Application Exception: %s (Code: %d)\n", appErr.Message, appErr.Code)

	// Resource Not Found
	notFoundErr := exceptions.NewResourceNotFoundException(
		"User not found",
		"User",
		"123",
	)
	fmt.Printf("  - Not Found Exception: %s (Code: %d, HTTP: %d)\n",
		notFoundErr.Message, notFoundErr.Code, notFoundErr.HTTPCode)
}

func testResponseBuilders() {
	// Process Response
	createResponse := responses.ProcessResponseBuilder.Created(
		"User created successfully",
		"uuid-123-456",
	)
	fmt.Printf("  - Create Response: %s (Status: %d)\n", createResponse.Message, createResponse.StatusCode)

	// Query Response
	users := []map[string]interface{}{
		{"id": "1", "name": "John Doe", "email": "john@example.com"},
		{"id": "2", "name": "Jane Smith", "email": "jane@example.com"},
	}
	queryResponse := responses.QueryResponseBuilder.SuccessWithPagination(
		"Users retrieved",
		users,
		1,  // page
		10, // page_size
		25, // total_records
	)
	fmt.Printf("  - Query Response: %d users, page %d/%d\n",
		len(queryResponse.Data),
		queryResponse.Pagination.Page,
		queryResponse.Pagination.TotalPages,
	)

	// Error Response
	errorResponse := responses.ErrorResponseBuilder.NotFound(
		"Resource not found",
		"User",
		"999",
	)
	fmt.Printf("  - Error Response: %s (Status: %d)\n", errorResponse.Message, errorResponse.StatusCode)
}

func testEventSystem(logger logging.Logger, cfg *config.Config) {
	ctx := context.Background()

	// Create in-memory event bus for testing
	eventBus := messaging.NewInMemoryEventBus(logger)
	defer eventBus.Close()

	// Create event store
	eventStore, err := events.NewFileEventStore(cfg.EventStorePath)
	if err != nil {
		logger.Error("Failed to create event store", map[string]interface{}{
			"error": err.Error(),
		})
		return
	}

	// Subscribe to events
	eventBus.Subscribe(ctx, "UserCreated", func(event *ports.BaseEvent) error {
		fmt.Printf("  - Event received: %s (ID: %s)\n", event.EventName, event.EventID)
		fmt.Printf("    Data: %v\n", event.Data)
		return nil
	})

	// Create and publish event
	event := ports.NewBaseEvent(
		"UserCreated",
		"backbone-example",
		map[string]interface{}{
			"user_id": 123,
			"email":   "user@example.com",
			"name":    "John Doe",
		},
		"users-service",
		"create-user",
	)

	// Save to event store
	if err := eventStore.Save(ctx, event); err != nil {
		logger.Error("Failed to save event", map[string]interface{}{
			"error": err.Error(),
		})
	} else {
		fmt.Printf("  - Event saved to store: %s\n", event.EventID)
	}

	// Publish event
	if err := eventBus.Publish(ctx, event); err != nil {
		logger.Error("Failed to publish event", map[string]interface{}{
			"error": err.Error(),
		})
	} else {
		fmt.Printf("  - Event published: %s (Status: %s)\n", event.EventName, event.Status)
	}

	// Create domain event
	domainEvent := ports.NewDomainEvent(
		"OrderCreated",
		"backbone-example",
		map[string]interface{}{
			"order_id": "ORD-123",
			"total":    99.99,
		},
		"orders-service",
		"create-order",
		"ORD-123",
		"Order",
		1,
	)

	fmt.Printf("  - Domain Event created: %s (Aggregate: %s)\n",
		domainEvent.EventName,
		domainEvent.AggregateType,
	)
}
