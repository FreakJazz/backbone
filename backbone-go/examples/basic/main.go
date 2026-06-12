// Basic usage example for backbone-go framework.
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
	fmt.Println("backbone-go — basic example")
	fmt.Println("============================")

	cfg, err := config.LoadConfig(".")
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}
	fmt.Printf("Config loaded: %s (env: %s)\n", cfg.AppName, cfg.Environment)

	logger := logging.NewLogger("backbone-example")
	logger.Info("Application started", map[string]interface{}{"version": cfg.AppVersion})

	fmt.Println("\n-- Exception system --")
	testExceptions(logger)

	fmt.Println("\n-- Response builders --")
	testResponseBuilders()

	fmt.Println("\n-- Event system --")
	testEventSystem(logger, cfg)

	fmt.Println("\nAll examples completed.")
}

func testExceptions(logger logging.Logger) {
	domainErr := domainExceptions.NewBusinessRuleViolationException(
		"User age must be between 18 and 120",
		"ValidateUserAge",
	)
	logger.Error("Domain exception", map[string]interface{}{"exception": domainErr.ToDict()})
	fmt.Printf("  Domain:      %s (code: %d)\n", domainErr.Message, domainErr.Code)

	appErr := exceptions.NewValidationException("Validation failed",
		[]exceptions.ValidationError{
			{Field: "email", Message: "Invalid format", Code: "INVALID_FORMAT"},
		},
	)
	fmt.Printf("  Validation:  %s (code: %d)\n", appErr.Message, appErr.Code)

	notFound := exceptions.NewResourceNotFoundException("User not found", "User", "123")
	fmt.Printf("  Not found:   %s (code: %d, http: %d)\n", notFound.Message, notFound.Code, notFound.HTTPCode)
}

func testResponseBuilders() {
	const exampleID = "uuid-123"

	// Write operations → {"id": "uuid"}
	created := responses.ProcessResponseBuilder.Created(exampleID)
	fmt.Printf("  Created:  id=%s\n", created.ID)

	updated := responses.ProcessResponseBuilder.Updated(exampleID)
	fmt.Printf("  Updated:  id=%s\n", updated.ID)

	deleted := responses.ProcessResponseBuilder.Deleted(exampleID)
	fmt.Printf("  Deleted:  id=%s\n", deleted.ID)

	// Read single → raw object
	userObj := responses.SimpleObjectResponseBuilder.Found(map[string]interface{}{
		"id": "1", "name": "John Doe",
	})
	fmt.Printf("  Found:    id=%s\n", userObj["id"])

	// Read list → paginated envelope
	items := []map[string]interface{}{
		{"id": "1", "name": "John"},
		{"id": "2", "name": "Jane"},
	}
	list := responses.PaginatedResponseBuilder.Success(items, 25, 1, 10, "Users retrieved")
	fmt.Printf("  List:     %d items, total=%d\n", len(list.Items), list.Pagination.TotalCount)

	// Error
	errResp := responses.ErrorResponseBuilder.NotFound("User not found")
	fmt.Printf("  Error:    status=%d code=%d\n", errResp.StatusCode, errResp.ErrorCode)
}

func testEventSystem(logger logging.Logger, cfg *config.Config) {
	ctx := context.Background()

	bus := messaging.NewInMemoryEventBus(logger)
	defer bus.Close()

	store, err := events.NewFileEventStore(cfg.EventStorePath)
	if err != nil {
		logger.Error("Failed to create event store", map[string]interface{}{"error": err.Error()})
		return
	}

	bus.Subscribe(ctx, "UserCreated", func(e *ports.BaseEvent) error {
		fmt.Printf("  Event received: %s (id: %s)\n", e.EventName, e.EventID)
		return nil
	})

	event := ports.NewBaseEvent(
		"UserCreated", "backbone-example",
		map[string]interface{}{"user_id": 123, "email": "user@example.com"},
		"users-service", "create-user",
	)

	if err := store.Save(ctx, event); err != nil {
		logger.Error("Failed to save event", map[string]interface{}{"error": err.Error()})
	} else {
		fmt.Printf("  Event saved: %s\n", event.EventID)
	}

	if err := bus.Publish(ctx, event); err != nil {
		logger.Error("Failed to publish event", map[string]interface{}{"error": err.Error()})
	}

	domainEvent := ports.NewDomainEvent(
		"OrderCreated", "backbone-example",
		map[string]interface{}{"order_id": "ORD-123", "total": 99.99},
		"orders-service", "create-order",
		"ORD-123", "Order", 1,
	)
	fmt.Printf("  Domain event: %s (aggregate: %s)\n", domainEvent.EventName, domainEvent.AggregateType)
}
