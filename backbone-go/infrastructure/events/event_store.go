// Package events provides event store implementation
package events

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/freakjazz/backbone-go/domain/ports"
)

// FileEventStore implements EventStore using JSON files
type FileEventStore struct {
	basePath string
}

// NewFileEventStore creates a new file-based event store
func NewFileEventStore(basePath string) (*FileEventStore, error) {
	if err := os.MkdirAll(basePath, 0755); err != nil {
		return nil, fmt.Errorf("failed to create event store directory: %w", err)
	}

	return &FileEventStore{
		basePath: basePath,
	}, nil
}

// Save saves an event to file
func (s *FileEventStore) Save(ctx context.Context, event *ports.BaseEvent) error {
	// Create date-based directory structure
	dateDir := filepath.Join(s.basePath, event.CreatedAt.Format("2006-01-02"))
	if err := os.MkdirAll(dateDir, 0755); err != nil {
		return fmt.Errorf("failed to create date directory: %w", err)
	}

	// Write event to file
	filename := filepath.Join(dateDir, fmt.Sprintf("%s.json", event.EventID))
	eventJSON, err := json.MarshalIndent(event, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal event: %w", err)
	}

	if err := os.WriteFile(filename, eventJSON, 0644); err != nil {
		return fmt.Errorf("failed to write event file: %w", err)
	}

	return nil
}

// FindByID finds an event by ID
func (s *FileEventStore) FindByID(ctx context.Context, eventID string) (*ports.BaseEvent, error) {
	// Search through date directories
	entries, err := os.ReadDir(s.basePath)
	if err != nil {
		return nil, fmt.Errorf("failed to read event store: %w", err)
	}

	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}

		filename := filepath.Join(s.basePath, entry.Name(), fmt.Sprintf("%s.json", eventID))
		if data, err := os.ReadFile(filename); err == nil {
			var event ports.BaseEvent
			if err := json.Unmarshal(data, &event); err != nil {
				return nil, fmt.Errorf("failed to unmarshal event: %w", err)
			}
			return &event, nil
		}
	}

	return nil, fmt.Errorf("event not found: %s", eventID)
}

// FindByEventName finds events by event name
func (s *FileEventStore) FindByEventName(ctx context.Context, eventName string, limit int) ([]*ports.BaseEvent, error) {
	var events []*ports.BaseEvent

	err := filepath.Walk(s.basePath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if info.IsDir() || filepath.Ext(path) != ".json" {
			return nil
		}

		data, err := os.ReadFile(path)
		if err != nil {
			return err
		}

		var event ports.BaseEvent
		if err := json.Unmarshal(data, &event); err != nil {
			return err
		}

		if event.EventName == eventName {
			events = append(events, &event)
			if limit > 0 && len(events) >= limit {
				return filepath.SkipDir
			}
		}

		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to search events: %w", err)
	}

	return events, nil
}

// FindBySource finds events by source
func (s *FileEventStore) FindBySource(ctx context.Context, source string, limit int) ([]*ports.BaseEvent, error) {
	var events []*ports.BaseEvent

	err := filepath.Walk(s.basePath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if info.IsDir() || filepath.Ext(path) != ".json" {
			return nil
		}

		data, err := os.ReadFile(path)
		if err != nil {
			return err
		}

		var event ports.BaseEvent
		if err := json.Unmarshal(data, &event); err != nil {
			return err
		}

		if event.Source == source {
			events = append(events, &event)
			if limit > 0 && len(events) >= limit {
				return filepath.SkipDir
			}
		}

		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to search events: %w", err)
	}

	return events, nil
}

// FindByDateRange finds events in a date range
func (s *FileEventStore) FindByDateRange(ctx context.Context, start, end time.Time) ([]*ports.BaseEvent, error) {
	var events []*ports.BaseEvent

	current := start
	for current.Before(end) || current.Equal(end) {
		dateDir := filepath.Join(s.basePath, current.Format("2006-01-02"))

		entries, err := os.ReadDir(dateDir)
		if err != nil {
			if os.IsNotExist(err) {
				current = current.AddDate(0, 0, 1)
				continue
			}
			return nil, fmt.Errorf("failed to read date directory: %w", err)
		}

		for _, entry := range entries {
			if entry.IsDir() || filepath.Ext(entry.Name()) != ".json" {
				continue
			}

			data, err := os.ReadFile(filepath.Join(dateDir, entry.Name()))
			if err != nil {
				continue
			}

			var event ports.BaseEvent
			if err := json.Unmarshal(data, &event); err != nil {
				continue
			}

			if (event.CreatedAt.After(start) || event.CreatedAt.Equal(start)) &&
				(event.CreatedAt.Before(end) || event.CreatedAt.Equal(end)) {
				events = append(events, &event)
			}
		}

		current = current.AddDate(0, 0, 1)
	}

	return events, nil
}

// FindByStatus finds events by status
func (s *FileEventStore) FindByStatus(ctx context.Context, status string, limit int) ([]*ports.BaseEvent, error) {
	var events []*ports.BaseEvent

	err := filepath.Walk(s.basePath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if info.IsDir() || filepath.Ext(path) != ".json" {
			return nil
		}

		data, err := os.ReadFile(path)
		if err != nil {
			return err
		}

		var event ports.BaseEvent
		if err := json.Unmarshal(data, &event); err != nil {
			return err
		}

		if event.Status == status {
			events = append(events, &event)
			if limit > 0 && len(events) >= limit {
				return filepath.SkipDir
			}
		}

		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to search events: %w", err)
	}

	return events, nil
}
