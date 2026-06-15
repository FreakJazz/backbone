package messaging_test

import (
	"context"
	"sync"
	"testing"
	"time"

	"github.com/freakjazz/backbone-go/domain/ports"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
	"github.com/freakjazz/backbone-go/infrastructure/messaging"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func newEvent(name string) *ports.BaseEvent {
	return ports.NewBaseEvent(
		name, "test-service",
		map[string]interface{}{"key": "value"},
		"test-service", "test-op",
	)
}

func TestInMemoryEventBus_PublishAndSubscribe(t *testing.T) {
	logger := logging.NewLogger("test")
	bus := messaging.NewInMemoryEventBus(logger)
	defer bus.Close()

	ctx := context.Background()
	received := make(chan *ports.BaseEvent, 1)

	err := bus.Subscribe(ctx, "UserCreated", func(e *ports.BaseEvent) error {
		received <- e
		return nil
	})
	require.NoError(t, err)

	event := newEvent("UserCreated")
	require.NoError(t, bus.Publish(ctx, event))

	select {
	case e := <-received:
		assert.Equal(t, "UserCreated", e.EventName)
	case <-time.After(500 * time.Millisecond):
		t.Fatal("event not received within timeout")
	}
}

func TestInMemoryEventBus_MultipleSubscribers(t *testing.T) {
	logger := logging.NewLogger("test")
	bus := messaging.NewInMemoryEventBus(logger)
	defer bus.Close()

	ctx := context.Background()
	var mu sync.Mutex
	count := 0

	for i := 0; i < 3; i++ {
		require.NoError(t, bus.Subscribe(ctx, "OrderPlaced", func(e *ports.BaseEvent) error {
			mu.Lock()
			count++
			mu.Unlock()
			return nil
		}))
	}

	require.NoError(t, bus.Publish(ctx, newEvent("OrderPlaced")))
	time.Sleep(100 * time.Millisecond)

	mu.Lock()
	assert.Equal(t, 3, count)
	mu.Unlock()
}

func TestInMemoryEventBus_UnrelatedEventNotDelivered(t *testing.T) {
	logger := logging.NewLogger("test")
	bus := messaging.NewInMemoryEventBus(logger)
	defer bus.Close()

	ctx := context.Background()
	received := make(chan struct{}, 1)

	require.NoError(t, bus.Subscribe(ctx, "ProductCreated", func(e *ports.BaseEvent) error {
		received <- struct{}{}
		return nil
	}))

	require.NoError(t, bus.Publish(ctx, newEvent("OrderPlaced")))
	time.Sleep(100 * time.Millisecond)

	assert.Empty(t, received)
}

func TestInMemoryEventBus_Unsubscribe(t *testing.T) {
	logger := logging.NewLogger("test")
	bus := messaging.NewInMemoryEventBus(logger)
	defer bus.Close()

	ctx := context.Background()
	count := 0

	require.NoError(t, bus.Subscribe(ctx, "TestEvent", func(e *ports.BaseEvent) error {
		count++
		return nil
	}))

	require.NoError(t, bus.Publish(ctx, newEvent("TestEvent")))
	time.Sleep(50 * time.Millisecond)
	assert.Equal(t, 1, count)

	require.NoError(t, bus.Unsubscribe(ctx, "TestEvent"))
	require.NoError(t, bus.Publish(ctx, newEvent("TestEvent")))
	time.Sleep(50 * time.Millisecond)
	assert.Equal(t, 1, count) // still 1 — handler was removed
}

func TestInMemoryEventBus_HandlerCount(t *testing.T) {
	logger := logging.NewLogger("test")
	bus := messaging.NewInMemoryEventBus(logger)
	defer bus.Close()

	ctx := context.Background()

	noop := func(e *ports.BaseEvent) error { return nil }
	_ = bus.Subscribe(ctx, "Evt", noop)
	_ = bus.Subscribe(ctx, "Evt", noop)
	_ = bus.Subscribe(ctx, "Other", noop)

	assert.Equal(t, 2, bus.GetHandlerCount("Evt"))
	assert.Equal(t, 1, bus.GetHandlerCount("Other"))
}
