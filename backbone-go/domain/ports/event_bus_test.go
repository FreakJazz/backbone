package ports_test

import (
	"testing"

	"github.com/freakjazz/backbone-go/domain/ports"
	"github.com/stretchr/testify/assert"
)

func TestNewBaseEvent(t *testing.T) {
	event := ports.NewBaseEvent(
		"UserCreated",
		"test-service",
		map[string]interface{}{"user_id": 123},
		"users-service",
		"create-user",
	)

	assert.NotNil(t, event)
	assert.NotEmpty(t, event.EventID)
	assert.Equal(t, "UserCreated", event.EventName)
	assert.Equal(t, "test-service", event.Source)
	assert.Equal(t, "1.0", event.EventVersion)
	assert.Equal(t, "created", event.Status)
	assert.Equal(t, 123, event.Data["user_id"])
	assert.Equal(t, "users-service", event.Metadata["microservice"])
	assert.Equal(t, "create-user", event.Metadata["functionality"])
}

func TestEventIsValid(t *testing.T) {
	tests := []struct {
		name     string
		event    *ports.BaseEvent
		expected bool
	}{
		{
			name: "Valid event",
			event: ports.NewBaseEvent(
				"TestEvent",
				"test-service",
				map[string]interface{}{},
				"test-microservice",
				"test-functionality",
			),
			expected: true,
		},
		{
			name: "Missing event name",
			event: &ports.BaseEvent{
				Source: "test-service",
				Metadata: map[string]interface{}{
					"microservice":  "test-microservice",
					"functionality": "test-functionality",
				},
			},
			expected: false,
		},
		{
			name: "Missing source",
			event: &ports.BaseEvent{
				EventName: "TestEvent",
				Metadata: map[string]interface{}{
					"microservice":  "test-microservice",
					"functionality": "test-functionality",
				},
			},
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			assert.Equal(t, tt.expected, tt.event.IsValid())
		})
	}
}

func TestEventStatusTransitions(t *testing.T) {
	event := ports.NewBaseEvent(
		"TestEvent",
		"test-service",
		map[string]interface{}{},
		"test-microservice",
		"test-functionality",
	)

	assert.Equal(t, "created", event.Status)

	event.MarkAsPublished()
	assert.Equal(t, "published", event.Status)

	event.MarkAsFailed()
	assert.Equal(t, "failed", event.Status)

	event.MarkAsProcessed()
	assert.Equal(t, "processed", event.Status)
}

func TestEventToJSON(t *testing.T) {
	event := ports.NewBaseEvent(
		"TestEvent",
		"test-service",
		map[string]interface{}{"key": "value"},
		"test-microservice",
		"test-functionality",
	)

	jsonStr, err := event.ToJSON()
	assert.NoError(t, err)
	assert.NotEmpty(t, jsonStr)
	assert.Contains(t, jsonStr, "TestEvent")
	assert.Contains(t, jsonStr, "test-service")
	assert.Contains(t, jsonStr, "key")
}

func TestNewDomainEvent(t *testing.T) {
	event := ports.NewDomainEvent(
		"OrderCreated",
		"orders-service",
		map[string]interface{}{"order_id": "ORD-123"},
		"orders-microservice",
		"create-order",
		"ORD-123",
		"Order",
		1,
	)

	assert.NotNil(t, event)
	assert.Equal(t, "OrderCreated", event.EventName)
	assert.Equal(t, "ORD-123", event.AggregateID)
	assert.Equal(t, "Order", event.AggregateType)
	assert.Equal(t, 1, event.AggregateVersion)
	assert.Equal(t, "domain", event.EventType)
	assert.Equal(t, "domain", event.Metadata["eventType"])
}

func TestNewIntegrationEvent(t *testing.T) {
	event := ports.NewIntegrationEvent(
		"UserNotification",
		"notifications-service",
		map[string]interface{}{"message": "Welcome"},
		"notifications-microservice",
		"send-notification",
		"email-service",
	)

	assert.NotNil(t, event)
	assert.Equal(t, "UserNotification", event.EventName)
	assert.Equal(t, "email-service", event.TargetService)
	assert.Equal(t, "integration", event.EventType)
	assert.Equal(t, "integration", event.Metadata["eventType"])
}
