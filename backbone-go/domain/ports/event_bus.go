// Package ports defines domain contracts for external dependencies
package ports

import (
	"context"
	"encoding/json"
	"time"

	"github.com/google/uuid"
)

// EventHandler is a function that handles events
type EventHandler func(event *BaseEvent) error

// BaseEvent represents a standard event structure
type BaseEvent struct {
	EventID      string                 `json:"eventId"`
	EventName    string                 `json:"eventName"`
	EventVersion string                 `json:"eventVersion"`
	Source       string                 `json:"source"`
	Timestamp    time.Time              `json:"timestamp"`
	Data         map[string]interface{} `json:"data"`
	Metadata     map[string]interface{} `json:"metadata"`
	CreatedAt    time.Time              `json:"createdAt"`
	UpdatedAt    time.Time              `json:"updatedAt"`
	Status       string                 `json:"status"`
}

// NewBaseEvent creates a new base event
func NewBaseEvent(
	eventName, source string,
	data map[string]interface{},
	microservice, functionality string,
) *BaseEvent {
	now := time.Now().UTC()
	eventID := uuid.New().String()
	correlationID := uuid.New().String()

	return &BaseEvent{
		EventID:      eventID,
		EventName:    eventName,
		EventVersion: "1.0",
		Source:       source,
		Timestamp:    now,
		Data:         data,
		Metadata: map[string]interface{}{
			"microservice":  microservice,
			"functionality": functionality,
			"correlationId": correlationID,
		},
		CreatedAt: now,
		UpdatedAt: now,
		Status:    "created",
	}
}

// MarkAsPublished marks the event as published
func (e *BaseEvent) MarkAsPublished() {
	e.Status = "published"
	e.UpdatedAt = time.Now().UTC()
}

// MarkAsFailed marks the event as failed
func (e *BaseEvent) MarkAsFailed() {
	e.Status = "failed"
	e.UpdatedAt = time.Now().UTC()
}

// MarkAsProcessed marks the event as processed
func (e *BaseEvent) MarkAsProcessed() {
	e.Status = "processed"
	e.UpdatedAt = time.Now().UTC()
}

// ToJSON converts the event to JSON string
func (e *BaseEvent) ToJSON() (string, error) {
	bytes, err := json.MarshalIndent(e, "", "  ")
	if err != nil {
		return "", err
	}
	return string(bytes), nil
}

// IsValid validates that event has all required fields
func (e *BaseEvent) IsValid() bool {
	if e.EventName == "" || e.Source == "" {
		return false
	}

	microservice, ok1 := e.Metadata["microservice"].(string)
	functionality, ok2 := e.Metadata["functionality"].(string)

	return ok1 && ok2 && microservice != "" && functionality != ""
}

// DomainEvent represents a domain event
type DomainEvent struct {
	*BaseEvent
	AggregateID      string `json:"aggregateId,omitempty"`
	AggregateType    string `json:"aggregateType,omitempty"`
	AggregateVersion int    `json:"aggregateVersion,omitempty"`
	EventType        string `json:"eventType"`
}

// NewDomainEvent creates a new domain event
func NewDomainEvent(
	eventName, source string,
	data map[string]interface{},
	microservice, functionality string,
	aggregateID, aggregateType string,
	aggregateVersion int,
) *DomainEvent {
	baseEvent := NewBaseEvent(eventName, source, data, microservice, functionality)
	baseEvent.Metadata["eventType"] = "domain"

	if aggregateID != "" {
		baseEvent.Metadata["aggregateId"] = aggregateID
	}
	if aggregateType != "" {
		baseEvent.Metadata["aggregateType"] = aggregateType
	}
	if aggregateVersion > 0 {
		baseEvent.Metadata["aggregateVersion"] = aggregateVersion
	}

	return &DomainEvent{
		BaseEvent:        baseEvent,
		AggregateID:      aggregateID,
		AggregateType:    aggregateType,
		AggregateVersion: aggregateVersion,
		EventType:        "domain",
	}
}

// IntegrationEvent represents an integration event
type IntegrationEvent struct {
	*BaseEvent
	TargetService string `json:"targetService,omitempty"`
	EventType     string `json:"eventType"`
}

// NewIntegrationEvent creates a new integration event
func NewIntegrationEvent(
	eventName, source string,
	data map[string]interface{},
	microservice, functionality string,
	targetService string,
) *IntegrationEvent {
	baseEvent := NewBaseEvent(eventName, source, data, microservice, functionality)
	baseEvent.Metadata["eventType"] = "integration"

	if targetService != "" {
		baseEvent.Metadata["targetService"] = targetService
	}

	return &IntegrationEvent{
		BaseEvent:     baseEvent,
		TargetService: targetService,
		EventType:     "integration",
	}
}

// EventBus defines the contract for event publishing and subscription
type EventBus interface {
	// Publish publishes an event
	Publish(ctx context.Context, event *BaseEvent) error

	// Subscribe subscribes to events of a given type
	Subscribe(ctx context.Context, eventName string, handler EventHandler) error

	// Unsubscribe removes a subscription
	Unsubscribe(ctx context.Context, eventName string) error

	// Close closes the event bus
	Close() error
}

// EventStore defines the contract for event persistence
type EventStore interface {
	// Save saves an event
	Save(ctx context.Context, event *BaseEvent) error

	// FindByID finds an event by ID
	FindByID(ctx context.Context, eventID string) (*BaseEvent, error)

	// FindByEventName finds events by event name
	FindByEventName(ctx context.Context, eventName string, limit int) ([]*BaseEvent, error)

	// FindBySource finds events by source
	FindBySource(ctx context.Context, source string, limit int) ([]*BaseEvent, error)

	// FindByDateRange finds events in a date range
	FindByDateRange(ctx context.Context, start, end time.Time) ([]*BaseEvent, error)

	// FindByStatus finds events by status
	FindByStatus(ctx context.Context, status string, limit int) ([]*BaseEvent, error)
}
