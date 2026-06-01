// Package messaging provides event bus adapters
package messaging

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"

	"github.com/freakjazz/backbone-go/domain/ports"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
	"github.com/segmentio/kafka-go"
)

// KafkaEventBus implements EventBus using Apache Kafka
type KafkaEventBus struct {
	brokers      []string
	writer       *kafka.Writer
	readers      map[string]*kafka.Reader
	handlers     map[string]ports.EventHandler
	logger       logging.Logger
	mu           sync.RWMutex
	stopChannels map[string]chan struct{}
}

// NewKafkaEventBus creates a new Kafka event bus
func NewKafkaEventBus(brokers []string, logger logging.Logger) *KafkaEventBus {
	return &KafkaEventBus{
		brokers:      brokers,
		readers:      make(map[string]*kafka.Reader),
		handlers:     make(map[string]ports.EventHandler),
		logger:       logger,
		stopChannels: make(map[string]chan struct{}),
		writer: &kafka.Writer{
			Addr:                   kafka.TCP(brokers...),
			Balancer:               &kafka.LeastBytes{},
			AllowAutoTopicCreation: true,
		},
	}
}

// Publish publishes an event to Kafka
func (b *KafkaEventBus) Publish(ctx context.Context, event *ports.BaseEvent) error {
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

	message := kafka.Message{
		Topic: event.EventName,
		Key:   []byte(event.EventID),
		Value: []byte(eventJSON),
		Headers: []kafka.Header{
			{Key: "event-id", Value: []byte(event.EventID)},
			{Key: "event-name", Value: []byte(event.EventName)},
			{Key: "source", Value: []byte(event.Source)},
		},
	}

	err = b.writer.WriteMessages(ctx, message)
	if err != nil {
		b.logger.Error("Failed to publish event to Kafka", map[string]interface{}{
			"event_name": event.EventName,
			"event_id":   event.EventID,
			"error":      err.Error(),
		})
		event.MarkAsFailed()
		return fmt.Errorf("failed to publish event: %w", err)
	}

	event.MarkAsPublished()
	b.logger.Info("Event published to Kafka", map[string]interface{}{
		"event_name": event.EventName,
		"event_id":   event.EventID,
		"topic":      event.EventName,
	})

	return nil
}

// Subscribe subscribes to events of a given type
func (b *KafkaEventBus) Subscribe(ctx context.Context, eventName string, handler ports.EventHandler) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	if _, exists := b.handlers[eventName]; exists {
		return fmt.Errorf("handler already registered for event: %s", eventName)
	}

	reader := kafka.NewReader(kafka.ReaderConfig{
		Brokers: b.brokers,
		Topic:   eventName,
		GroupID: fmt.Sprintf("%s-group", eventName),
	})

	b.readers[eventName] = reader
	b.handlers[eventName] = handler
	stopChan := make(chan struct{})
	b.stopChannels[eventName] = stopChan

	// Start consuming messages in a goroutine
	go b.consumeMessages(ctx, eventName, reader, handler, stopChan)

	b.logger.Info("Subscribed to event", map[string]interface{}{
		"event_name": eventName,
	})

	return nil
}

// consumeMessages consumes messages from Kafka
func (b *KafkaEventBus) consumeMessages(
	ctx context.Context,
	eventName string,
	reader *kafka.Reader,
	handler ports.EventHandler,
	stopChan chan struct{},
) {
	for {
		select {
		case <-stopChan:
			b.logger.Info("Stopping consumer", map[string]interface{}{
				"event_name": eventName,
			})
			return
		case <-ctx.Done():
			return
		default:
			message, err := reader.ReadMessage(ctx)
			if err != nil {
				b.logger.Error("Failed to read message", map[string]interface{}{
					"event_name": eventName,
					"error":      err.Error(),
				})
				continue
			}

			var event ports.BaseEvent
			if err := json.Unmarshal(message.Value, &event); err != nil {
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
func (b *KafkaEventBus) Unsubscribe(ctx context.Context, eventName string) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	reader, exists := b.readers[eventName]
	if !exists {
		return fmt.Errorf("no subscription found for event: %s", eventName)
	}

	// Stop the consumer
	if stopChan, ok := b.stopChannels[eventName]; ok {
		close(stopChan)
		delete(b.stopChannels, eventName)
	}

	if err := reader.Close(); err != nil {
		return fmt.Errorf("failed to close reader: %w", err)
	}

	delete(b.readers, eventName)
	delete(b.handlers, eventName)

	b.logger.Info("Unsubscribed from event", map[string]interface{}{
		"event_name": eventName,
	})

	return nil
}

// Close closes the event bus
func (b *KafkaEventBus) Close() error {
	b.mu.Lock()
	defer b.mu.Unlock()

	// Close all readers
	for eventName, reader := range b.readers {
		if stopChan, ok := b.stopChannels[eventName]; ok {
			close(stopChan)
		}
		reader.Close()
	}

	// Close writer
	if err := b.writer.Close(); err != nil {
		return fmt.Errorf("failed to close writer: %w", err)
	}

	b.logger.Info("Kafka event bus closed", nil)
	return nil
}
