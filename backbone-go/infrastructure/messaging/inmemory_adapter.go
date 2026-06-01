// Package messaging provides in-memory event bus for testing
package messaging

import (
	"context"
	"fmt"
	"sync"

	"github.com/freakjazz/backbone-go/domain/ports"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
)

// InMemoryEventBus implements EventBus using in-memory channels
// Useful for testing and development
type InMemoryEventBus struct {
	handlers map[string][]ports.EventHandler
	logger   logging.Logger
	mu       sync.RWMutex
}

// NewInMemoryEventBus creates a new in-memory event bus
func NewInMemoryEventBus(logger logging.Logger) *InMemoryEventBus {
	return &InMemoryEventBus{
		handlers: make(map[string][]ports.EventHandler),
		logger:   logger,
	}
}

// Publish publishes an event in-memory
func (b *InMemoryEventBus) Publish(ctx context.Context, event *ports.BaseEvent) error {
	if !event.IsValid() {
		return fmt.Errorf("invalid event: missing required fields")
	}

	b.mu.RLock()
	handlers, exists := b.handlers[event.EventName]
	b.mu.RUnlock()

	if !exists || len(handlers) == 0 {
		b.logger.Warning("No handlers registered for event", map[string]interface{}{
			"event_name": event.EventName,
			"event_id":   event.EventID,
		})
		event.MarkAsPublished()
		return nil
	}

	// Execute all handlers
	event.MarkAsPublished()
	for _, handler := range handlers {
		if err := handler(event); err != nil {
			b.logger.Error("Handler failed", map[string]interface{}{
				"event_name": event.EventName,
				"event_id":   event.EventID,
				"error":      err.Error(),
			})
			event.MarkAsFailed()
			return fmt.Errorf("handler failed: %w", err)
		}
	}

	event.MarkAsProcessed()
	b.logger.Info("Event processed", map[string]interface{}{
		"event_name": event.EventName,
		"event_id":   event.EventID,
		"handlers":   len(handlers),
	})

	return nil
}

// Subscribe subscribes to events of a given type
func (b *InMemoryEventBus) Subscribe(ctx context.Context, eventName string, handler ports.EventHandler) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	b.handlers[eventName] = append(b.handlers[eventName], handler)

	b.logger.Info("Subscribed to event", map[string]interface{}{
		"event_name": eventName,
	})

	return nil
}

// Unsubscribe removes all subscriptions for an event
func (b *InMemoryEventBus) Unsubscribe(ctx context.Context, eventName string) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	delete(b.handlers, eventName)

	b.logger.Info("Unsubscribed from event", map[string]interface{}{
		"event_name": eventName,
	})

	return nil
}

// Close closes the event bus (no-op for in-memory)
func (b *InMemoryEventBus) Close() error {
	b.mu.Lock()
	defer b.mu.Unlock()

	b.handlers = make(map[string][]ports.EventHandler)
	b.logger.Info("In-memory event bus closed", nil)
	return nil
}

// GetHandlerCount returns the number of handlers for an event
func (b *InMemoryEventBus) GetHandlerCount(eventName string) int {
	b.mu.RLock()
	defer b.mu.RUnlock()

	return len(b.handlers[eventName])
}
