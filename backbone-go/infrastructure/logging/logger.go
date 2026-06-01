// Package logging provides structured logging functionality
package logging

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"time"
)

// LogLevel represents the log level
type LogLevel string

const (
	LevelDebug    LogLevel = "DEBUG"
	LevelInfo     LogLevel = "INFO"
	LevelWarning  LogLevel = "WARNING"
	LevelError    LogLevel = "ERROR"
	LevelCritical LogLevel = "CRITICAL"
)

// Logger defines the logging interface
type Logger interface {
	Debug(message string, extra map[string]interface{})
	Info(message string, extra map[string]interface{})
	Warning(message string, extra map[string]interface{})
	Error(message string, extra map[string]interface{})
	Critical(message string, extra map[string]interface{})
	WithContext(ctx map[string]interface{}) Logger
}

// LogEntry represents a structured log entry
type LogEntry struct {
	Timestamp   time.Time              `json:"timestamp"`
	Level       LogLevel               `json:"level"`
	Service     string                 `json:"service"`
	Component   string                 `json:"component,omitempty"`
	Layer       string                 `json:"layer,omitempty"`
	Message     string                 `json:"message"`
	ExtraData   map[string]interface{} `json:"extra_data,omitempty"`
	Context     map[string]interface{} `json:"context,omitempty"`
	TraceID     string                 `json:"trace_id,omitempty"`
	RequestID   string                 `json:"request_id,omitempty"`
	UserID      string                 `json:"user_id,omitempty"`
	Environment string                 `json:"environment,omitempty"`
}

// StructuredLogger implements the Logger interface
type StructuredLogger struct {
	service     string
	component   string
	layer       string
	context     map[string]interface{}
	output      io.Writer
	level       LogLevel
	environment string
}

// NewLogger creates a new structured logger
func NewLogger(service string) *StructuredLogger {
	return &StructuredLogger{
		service:     service,
		context:     make(map[string]interface{}),
		output:      os.Stdout,
		level:       LevelInfo,
		environment: getEnv("ENVIRONMENT", "development"),
	}
}

// NewLoggerWithConfig creates a logger with custom configuration
func NewLoggerWithConfig(service, component, layer string, level LogLevel) *StructuredLogger {
	return &StructuredLogger{
		service:     service,
		component:   component,
		layer:       layer,
		context:     make(map[string]interface{}),
		output:      os.Stdout,
		level:       level,
		environment: getEnv("ENVIRONMENT", "development"),
	}
}

// SetOutput sets the output writer
func (l *StructuredLogger) SetOutput(output io.Writer) {
	l.output = output
}

// SetLevel sets the minimum log level
func (l *StructuredLogger) SetLevel(level LogLevel) {
	l.level = level
}

// WithContext returns a new logger with additional context
func (l *StructuredLogger) WithContext(ctx map[string]interface{}) Logger {
	newContext := make(map[string]interface{})
	for k, v := range l.context {
		newContext[k] = v
	}
	for k, v := range ctx {
		newContext[k] = v
	}

	return &StructuredLogger{
		service:     l.service,
		component:   l.component,
		layer:       l.layer,
		context:     newContext,
		output:      l.output,
		level:       l.level,
		environment: l.environment,
	}
}

// Debug logs a debug message
func (l *StructuredLogger) Debug(message string, extra map[string]interface{}) {
	if l.shouldLog(LevelDebug) {
		l.log(LevelDebug, message, extra)
	}
}

// Info logs an info message
func (l *StructuredLogger) Info(message string, extra map[string]interface{}) {
	if l.shouldLog(LevelInfo) {
		l.log(LevelInfo, message, extra)
	}
}

// Warning logs a warning message
func (l *StructuredLogger) Warning(message string, extra map[string]interface{}) {
	if l.shouldLog(LevelWarning) {
		l.log(LevelWarning, message, extra)
	}
}

// Error logs an error message
func (l *StructuredLogger) Error(message string, extra map[string]interface{}) {
	if l.shouldLog(LevelError) {
		l.log(LevelError, message, extra)
	}
}

// Critical logs a critical message
func (l *StructuredLogger) Critical(message string, extra map[string]interface{}) {
	if l.shouldLog(LevelCritical) {
		l.log(LevelCritical, message, extra)
	}
}

// log writes a log entry
func (l *StructuredLogger) log(level LogLevel, message string, extra map[string]interface{}) {
	entry := LogEntry{
		Timestamp:   time.Now().UTC(),
		Level:       level,
		Service:     l.service,
		Component:   l.component,
		Layer:       l.layer,
		Message:     message,
		ExtraData:   extra,
		Context:     l.context,
		Environment: l.environment,
	}

	// Add trace and request IDs from context
	if traceID, ok := l.context["trace_id"].(string); ok {
		entry.TraceID = traceID
	}
	if requestID, ok := l.context["request_id"].(string); ok {
		entry.RequestID = requestID
	}
	if userID, ok := l.context["user_id"].(string); ok {
		entry.UserID = userID
	}

	// Serialize to JSON
	bytes, err := json.Marshal(entry)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to serialize log entry: %v\n", err)
		return
	}

	fmt.Fprintln(l.output, string(bytes))
}

// shouldLog checks if the log level should be logged
func (l *StructuredLogger) shouldLog(level LogLevel) bool {
	levels := map[LogLevel]int{
		LevelDebug:    0,
		LevelInfo:     1,
		LevelWarning:  2,
		LevelError:    3,
		LevelCritical: 4,
	}

	return levels[level] >= levels[l.level]
}

// getEnv gets an environment variable with a default value
func getEnv(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}

// LoggerFactory creates loggers with consistent configuration
type LoggerFactory struct {
	defaultService string
	defaultLevel   LogLevel
}

// NewLoggerFactory creates a new logger factory
func NewLoggerFactory(service string, level LogLevel) *LoggerFactory {
	return &LoggerFactory{
		defaultService: service,
		defaultLevel:   level,
	}
}

// CreateLogger creates a new logger
func (f *LoggerFactory) CreateLogger(component string) Logger {
	return NewLoggerWithConfig(f.defaultService, component, "", f.defaultLevel)
}

// CreateLayerLogger creates a logger for a specific layer
func (f *LoggerFactory) CreateLayerLogger(component, layer string) Logger {
	return NewLoggerWithConfig(f.defaultService, component, layer, f.defaultLevel)
}
