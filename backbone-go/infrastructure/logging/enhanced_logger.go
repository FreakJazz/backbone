// Package logging provides enhanced logging with method, handler, query and layer tracking
package logging

import (
	"encoding/json"
	"fmt"
	"os"
	"runtime"
	"strings"
	"time"
)

// EnhancedLogEntry extends LogEntry with additional context
type EnhancedLogEntry struct {
	Timestamp   time.Time              `json:"timestamp"`
	Level       LogLevel               `json:"level"`
	Service     string                 `json:"service"`
	Component   string                 `json:"component,omitempty"`
	Layer       string                 `json:"layer,omitempty"`
	Method      string                 `json:"method,omitempty"`
	Handler     string                 `json:"handler,omitempty"`
	Message     string                 `json:"message"`
	ExtraData   map[string]interface{} `json:"extra_data,omitempty"`
	Context     map[string]interface{} `json:"context,omitempty"`
	Query       *QueryLog              `json:"query,omitempty"`
	StackTrace  string                 `json:"stack_trace,omitempty"`
	TraceID     string                 `json:"trace_id,omitempty"`
	RequestID   string                 `json:"request_id,omitempty"`
	UserID      string                 `json:"user_id,omitempty"`
	Environment string                 `json:"environment,omitempty"`
	ErrorCode   int                    `json:"error_code,omitempty"`
}

// QueryLog represents query execution information
type QueryLog struct {
	SQL          string                 `json:"sql"`
	Args         []interface{}          `json:"args,omitempty"`
	Duration     int64                  `json:"duration_ms,omitempty"`
	RowsAffected int64                  `json:"rows_affected,omitempty"`
	Error        string                 `json:"error,omitempty"`
	Params       map[string]interface{} `json:"params,omitempty"`
}

// EnhancedLogger provides advanced logging capabilities
type EnhancedLogger struct {
	service     string
	component   string
	layer       string
	method      string
	handler     string
	context     map[string]interface{}
	output      *os.File
	level       LogLevel
	environment string
}

// NewEnhancedLogger creates a new enhanced logger
func NewEnhancedLogger(service string) *EnhancedLogger {
	return &EnhancedLogger{
		service:     service,
		context:     make(map[string]interface{}),
		output:      os.Stdout,
		level:       LevelInfo,
		environment: getEnv("ENVIRONMENT", "development"),
	}
}

// WithLayer sets the layer context
func (l *EnhancedLogger) WithLayer(layer string) *EnhancedLogger {
	newLogger := l.clone()
	newLogger.layer = layer
	return newLogger
}

// WithComponent sets the component context
func (l *EnhancedLogger) WithComponent(component string) *EnhancedLogger {
	newLogger := l.clone()
	newLogger.component = component
	return newLogger
}

// WithMethod sets the method context (automatically detected if not set)
func (l *EnhancedLogger) WithMethod(method string) *EnhancedLogger {
	newLogger := l.clone()
	newLogger.method = method
	return newLogger
}

// WithHandler sets the handler context
func (l *EnhancedLogger) WithHandler(handler string) *EnhancedLogger {
	newLogger := l.clone()
	newLogger.handler = handler
	return newLogger
}

// WithContext adds context information
func (l *EnhancedLogger) WithContext(ctx map[string]interface{}) *EnhancedLogger {
	newLogger := l.clone()
	for k, v := range ctx {
		newLogger.context[k] = v
	}
	return newLogger
}

// clone creates a copy of the logger
func (l *EnhancedLogger) clone() *EnhancedLogger {
	newContext := make(map[string]interface{})
	for k, v := range l.context {
		newContext[k] = v
	}

	return &EnhancedLogger{
		service:     l.service,
		component:   l.component,
		layer:       l.layer,
		method:      l.method,
		handler:     l.handler,
		context:     newContext,
		output:      l.output,
		level:       l.level,
		environment: l.environment,
	}
}

// LogQuery logs a query execution with full details
func (l *EnhancedLogger) LogQuery(sql string, args []interface{}, duration int64, err error) {
	queryLog := &QueryLog{
		SQL:      sql,
		Args:     args,
		Duration: duration,
	}

	if err != nil {
		queryLog.Error = err.Error()
	}

	extra := map[string]interface{}{
		"query_duration_ms": duration,
	}

	if err != nil {
		l.logWithQuery(LevelError, "Query execution failed", extra, queryLog, true)
	} else {
		l.logWithQuery(LevelDebug, "Query executed", extra, queryLog, false)
	}
}

// LogQueryWithParams logs a query with named parameters
func (l *EnhancedLogger) LogQueryWithParams(sql string, args []interface{}, params map[string]interface{}, duration int64, err error) {
	queryLog := &QueryLog{
		SQL:      sql,
		Args:     args,
		Params:   params,
		Duration: duration,
	}

	if err != nil {
		queryLog.Error = err.Error()
	}

	extra := map[string]interface{}{
		"query_duration_ms": duration,
		"params":            params,
	}

	if err != nil {
		l.logWithQuery(LevelError, "Query with params failed", extra, queryLog, true)
	} else {
		l.logWithQuery(LevelDebug, "Query with params executed", extra, queryLog, false)
	}
}

// Debug logs a debug message
func (l *EnhancedLogger) Debug(message string, extra map[string]interface{}) {
	if l.shouldLog(LevelDebug) {
		l.logWithQuery(LevelDebug, message, extra, nil, false)
	}
}

// Info logs an info message
func (l *EnhancedLogger) Info(message string, extra map[string]interface{}) {
	if l.shouldLog(LevelInfo) {
		l.logWithQuery(LevelInfo, message, extra, nil, false)
	}
}

// Warning logs a warning message
func (l *EnhancedLogger) Warning(message string, extra map[string]interface{}) {
	if l.shouldLog(LevelWarning) {
		l.logWithQuery(LevelWarning, message, extra, nil, false)
	}
}

// Error logs an error message with stack trace
func (l *EnhancedLogger) Error(message string, extra map[string]interface{}) {
	if l.shouldLog(LevelError) {
		l.logWithQuery(LevelError, message, extra, nil, true)
	}
}

// ErrorWithCode logs an error with error code
func (l *EnhancedLogger) ErrorWithCode(message string, errorCode int, extra map[string]interface{}) {
	if extra == nil {
		extra = make(map[string]interface{})
	}
	extra["error_code"] = errorCode

	if l.shouldLog(LevelError) {
		l.logWithQueryAndCode(LevelError, message, extra, nil, true, errorCode)
	}
}

// Critical logs a critical message with stack trace
func (l *EnhancedLogger) Critical(message string, extra map[string]interface{}) {
	if l.shouldLog(LevelCritical) {
		l.logWithQuery(LevelCritical, message, extra, nil, true)
	}
}

// logWithQuery writes a log entry with optional query and stack trace
func (l *EnhancedLogger) logWithQuery(level LogLevel, message string, extra map[string]interface{}, query *QueryLog, includeStackTrace bool) {
	l.logWithQueryAndCode(level, message, extra, query, includeStackTrace, 0)
}

// logWithQueryAndCode writes a log entry with error code
func (l *EnhancedLogger) logWithQueryAndCode(level LogLevel, message string, extra map[string]interface{}, query *QueryLog, includeStackTrace bool, errorCode int) {
	// Auto-detect method if not set
	method := l.method
	if method == "" {
		method = l.getCallerMethod()
	}

	entry := EnhancedLogEntry{
		Timestamp:   time.Now().UTC(),
		Level:       level,
		Service:     l.service,
		Component:   l.component,
		Layer:       l.layer,
		Method:      method,
		Handler:     l.handler,
		Message:     message,
		ExtraData:   extra,
		Context:     l.context,
		Query:       query,
		Environment: l.environment,
		ErrorCode:   errorCode,
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

	// Add stack trace for errors
	if includeStackTrace {
		entry.StackTrace = l.getStackTrace()
	}

	// Serialize to JSON
	bytes, err := json.Marshal(entry)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to serialize log entry: %v\n", err)
		return
	}

	fmt.Fprintln(l.output, string(bytes))
}

// getCallerMethod automatically detects the calling method name
func (l *EnhancedLogger) getCallerMethod() string {
	pc, _, _, ok := runtime.Caller(4) // Skip 4 frames to get to the actual caller
	if !ok {
		return "unknown"
	}

	fn := runtime.FuncForPC(pc)
	if fn == nil {
		return "unknown"
	}

	fullName := fn.Name()
	parts := strings.Split(fullName, "/")
	if len(parts) > 0 {
		// Get last part and remove package prefix
		lastPart := parts[len(parts)-1]
		methodParts := strings.Split(lastPart, ".")
		if len(methodParts) > 1 {
			return methodParts[len(methodParts)-1]
		}
		return lastPart
	}

	return fullName
}

// getStackTrace captures the current stack trace
func (l *EnhancedLogger) getStackTrace() string {
	buf := make([]byte, 4096)
	n := runtime.Stack(buf, false)
	return string(buf[:n])
}

// shouldLog checks if the log level should be logged
func (l *EnhancedLogger) shouldLog(level LogLevel) bool {
	levels := map[LogLevel]int{
		LevelDebug:    0,
		LevelInfo:     1,
		LevelWarning:  2,
		LevelError:    3,
		LevelCritical: 4,
	}

	return levels[level] >= levels[l.level]
}

// SetLevel sets the minimum log level
func (l *EnhancedLogger) SetLevel(level LogLevel) {
	l.level = level
}

// SetOutput sets the output file
func (l *EnhancedLogger) SetOutput(output *os.File) {
	l.output = output
}
