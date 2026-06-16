// Package logging provides structured logging functionality
package logging

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

// Formatter serialises a LogEntry to a string for output.
type Formatter interface {
	Format(entry LogEntry) string
}

// levelColors maps log levels to ANSI colour codes for console output.
var levelColors = map[LogLevel]string{
	LevelDebug:    "\033[36m",  // cyan
	LevelInfo:     "\033[32m",  // green
	LevelWarning:  "\033[33m",  // yellow
	LevelError:    "\033[31m",  // red
	LevelCritical: "\033[35m",  // magenta
}

const colorReset = "\033[0m"

// JSONFormatter emits one compact JSON line per entry — ideal for ELK / production.
type JSONFormatter struct{}

func (f *JSONFormatter) Format(entry LogEntry) string {
	b, err := json.Marshal(entry)
	if err != nil {
		return fmt.Sprintf(`{"error":"failed to marshal log entry: %v"}`, err)
	}
	return string(b)
}

// ConsoleFormatter emits a human-readable coloured line — ideal for local development.
//
// Example:
//
//	2026-06-16 10:23:45 [INFO ] users-service | handler | User created  {user_id: 42}
type ConsoleFormatter struct {
	// UseColor controls ANSI colour output (disable when piping to a file).
	UseColor bool
}

func NewConsoleFormatter() *ConsoleFormatter {
	return &ConsoleFormatter{UseColor: true}
}

func (f *ConsoleFormatter) Format(entry LogEntry) string {
	ts := entry.Timestamp.Format("2006-01-02 15:04:05")
	level := fmt.Sprintf("%-8s", string(entry.Level))

	parts := []string{entry.Service}
	if entry.Component != "" {
		parts = append(parts, entry.Component)
	}
	if entry.Layer != "" {
		parts = append(parts, entry.Layer)
	}
	location := strings.Join(parts, " > ")

	line := fmt.Sprintf("%s [%s] %s | %s", ts, level, location, entry.Message)

	if len(entry.ExtraData) > 0 {
		b, _ := json.Marshal(entry.ExtraData)
		line += "  " + string(b)
	}
	if entry.RequestID != "" {
		line += fmt.Sprintf("  rid=%s", entry.RequestID)
	}

	if f.UseColor {
		color := levelColors[entry.Level]
		line = color + line + colorReset
	}
	return line
}

// CompactJSONFormatter is like JSONFormatter but omits zero/empty fields.
// Useful when bandwidth matters (e.g. high-throughput microservices).
type CompactJSONFormatter struct{}

func (f *CompactJSONFormatter) Format(entry LogEntry) string {
	m := map[string]interface{}{
		"ts":      entry.Timestamp.Format(time.RFC3339),
		"level":   string(entry.Level),
		"service": entry.Service,
		"msg":     entry.Message,
	}
	if entry.Component != "" {
		m["component"] = entry.Component
	}
	if entry.Layer != "" {
		m["layer"] = entry.Layer
	}
	if entry.RequestID != "" {
		m["rid"] = entry.RequestID
	}
	if entry.TraceID != "" {
		m["trace_id"] = entry.TraceID
	}
	if entry.UserID != "" {
		m["user_id"] = entry.UserID
	}
	if len(entry.ExtraData) > 0 {
		m["extra"] = entry.ExtraData
	}
	b, _ := json.Marshal(m)
	return string(b)
}
