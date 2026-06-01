// Package messaging provides Redis Pub/Sub event bus adapter
package messaging

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"

	"github.com/freakjazz/backbone-go/domain/ports"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
	"github.com/go-redis/redis/v8"
)

// RedisEventBus implements EventBus using Redis Pub/Sub
type RedisEventBus struct {
	client       *redis.Client
	pubsub       map[string]*redis.PubSub
	handlers     map[string]ports.EventHandler
	logger       logging.Logger
	mu           sync.RWMutex
	stopChannels map[string]chan struct{}
}

// NewRedisEventBus creates a new Redis event bus
func NewRedisEventBus(addr string, password string, db int, logger logging.Logger) *RedisEventBus {
	client := redis.NewClient(&redis.Options{
		Addr:     addr,
		Password: password,
		DB:       db,
	})

	return &RedisEventBus{
		client:       client,
		pubsub:       make(map[string]*redis.PubSub),
		handlers:     make(map[string]ports.EventHandler),
		logger:       logger,
		stopChannels: make(map[string]chan struct{}),
	}
}

// Publish publishes an event to Redis
func (b *RedisEventBus) Publish(ctx context.Context, event *ports.BaseEvent) error {
	if !event.IsValid() {
		return fmt.Errorf("invalid event: missing required fields")
	}

	eventJSON, err := event.ToJSON()
	if err != nil {
		b.logger.Error("Failed to serialize event", map[string]interface{}{
			"event_name": event.EventName,
			"error":      err.Error(),
		})
		event.MarkAsFailed()
		return fmt.Errorf("failed to serialize event: %w", err)
	}

	channel := fmt.Sprintf("events:%s", event.EventName)
	if err := b.client.Publish(ctx, channel, eventJSON).Err(); err != nil {
		b.logger.Error("Failed to publish event to Redis", map[string]interface{}{
			"event_name": event.EventName,
			"event_id":   event.EventID,
			"error":      err.Error(),
		})
		event.MarkAsFailed()
		return fmt.Errorf("failed to publish event: %w", err)
	}

	event.MarkAsPublished()
	b.logger.Info("Event published to Redis", map[string]interface{}{
		"event_name": event.EventName,
		"event_id":   event.EventID,
		"channel":    channel,
	})

	return nil
}

// Subscribe subscribes to events of a given type
func (b *RedisEventBus) Subscribe(ctx context.Context, eventName string, handler ports.EventHandler) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	if _, exists := b.handlers[eventName]; exists {
		return fmt.Errorf("handler already registered for event: %s", eventName)
	}

	channel := fmt.Sprintf("events:%s", eventName)
	pubsub := b.client.Subscribe(ctx, channel)

	b.pubsub[eventName] = pubsub
	b.handlers[eventName] = handler
	stopChan := make(chan struct{})
	b.stopChannels[eventName] = stopChan

	// Start consuming messages in a goroutine
	go b.consumeMessages(ctx, eventName, pubsub, handler, stopChan)

	b.logger.Info("Subscribed to event", map[string]interface{}{
		"event_name": eventName,
		"channel":    channel,
	})

	return nil
}

// consumeMessages consumes messages from Redis Pub/Sub
func (b *RedisEventBus) consumeMessages(
	ctx context.Context,
	eventName string,
	pubsub *redis.PubSub,
	handler ports.EventHandler,
	stopChan chan struct{},
) {
	ch := pubsub.Channel()

	for {
		select {
		case <-stopChan:
			b.logger.Info("Stopping consumer", map[string]interface{}{
				"event_name": eventName,
			})
			return
		case <-ctx.Done():
			return
		case message := <-ch:
			var event ports.BaseEvent
			if err := json.Unmarshal([]byte(message.Payload), &event); err != nil {
				b.logger.Error("Failed to deserialize event", map[string]interface{}{
					"event_name": eventName,
					"error":      err.Error(),
				})
				continue
			}

			if err := handler(&event); err != nil {
				b.logger.Error("Handler failed", map[string]interface{}{
					"event_name": eventName,
					"event_id":   event.EventID,
					"error":      err.Error(),
				})
				event.MarkAsFailed()
			} else {
				event.MarkAsProcessed()
				b.logger.Info("Event processed", map[string]interface{}{
					"event_name": eventName,
					"event_id":   event.EventID,
				})
			}
		}
	}
}

// Unsubscribe removes a subscription
func (b *RedisEventBus) Unsubscribe(ctx context.Context, eventName string) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	pubsub, exists := b.pubsub[eventName]
	if !exists {
		return fmt.Errorf("no subscription found for event: %s", eventName)
	}

	// Stop the consumer
	if stopChan, ok := b.stopChannels[eventName]; ok {
		close(stopChan)
		delete(b.stopChannels, eventName)
	}

	if err := pubsub.Close(); err != nil {
		return fmt.Errorf("failed to close pubsub: %w", err)
	}

	delete(b.pubsub, eventName)
	delete(b.handlers, eventName)

	b.logger.Info("Unsubscribed from event", map[string]interface{}{
		"event_name": eventName,
	})

	return nil
}

// Close closes the event bus
func (b *RedisEventBus) Close() error {
	b.mu.Lock()
	defer b.mu.Unlock()

	// Close all pubsubs
	for eventName, pubsub := range b.pubsub {
		if stopChan, ok := b.stopChannels[eventName]; ok {
			close(stopChan)
		}
		pubsub.Close()
	}

	// Close Redis client
	if err := b.client.Close(); err != nil {
		return fmt.Errorf("failed to close Redis client: %w", err)
	}

	b.logger.Info("Redis event bus closed", nil)
	return nil
}
