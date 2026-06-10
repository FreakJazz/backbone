// Package logging provides enhanced logging with method, handler, query and layer tracking
package logging

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"runtime"
	"strings"
	"time"
)

// ErrorLog matches the Python "error" field in log entries.
type ErrorLog struct {
	Type       string `json:"type"`
	Message    string `json:"message"`
	Code       int    `json:"code,omitempty"`
	StackTrace string `json:"stack_trace,omitempty"`
}

// QueryLog represents query execution information.
type QueryLog struct {
	SQL          string                 `json:"sql"`
	Args         []interface{}          `json:"args,omitempty"`
	Duration     int64                  `json:"duration_ms,omitempty"`
	RowsAffected int64                  `json:"rows_affected,omitempty"`
	Error        string                 `json:"error,omitempty"`
	Params       map[string]interface{} `json:"params,omitempty"`
}

// EnhancedLogEntry is the unified log entry shape (same as Python backbone).
//
// JSON output:
//
//	{
//	  "timestamp": "...",
//	  "level": "INFO",
//	  "service": "...",
//	  "component": "...",
//	  "layer": "...",
//	  "method": "...",
//	  "message": "...",
//	  "request_id": "...",
//	  "trace_id": "...",
//	  "user_id": "...",
//	  "environment": "...",
//	  "extra_data": {},
//	  "context": {},
//	  "error": { "type": "...", "message": "...", "code": 0, "stack_trace": "..." },
//	  "query": { ... }
//	}
type EnhancedLogEntry struct {
	Timestamp   time.Time              `json:"timestamp"`
	Level       LogLevel               `json:"level"`
	Service     string                 `json:"service"`
	Component   string                 `json:"component,omitempty"`
	Layer       string                 `json:"layer,omitempty"`
	Method      string                 `json:"method,omitempty"`
	Message     string                 `json:"message"`
	RequestID   string                 `json:"request_id,omitempty"`
	TraceID     string                 `json:"trace_id,omitempty"`
	UserID      string                 `json:"user_id,omitempty"`
	Environment string                 `json:"environment,omitempty"`
	ExtraData   map[string]interface{} `json:"extra_data,omitempty"`
	Context     map[string]interface{} `json:"context,omitempty"`
	Error       *ErrorLog              `json:"error,omitempty"`
	Query       *QueryLog              `json:"query,omitempty"`
}

// EnhancedLogger provides advanced logging capabilities.
type EnhancedLogger struct {
	service     string
	component   string
	layer       string
	method      string
	handler     string
	context     map[string]interface{}
	output      io.Writer
	level       LogLevel
	environment string
}

// NewEnhancedLogger creates a new enhanced logger.
func NewEnhancedLogger(service string) *EnhancedLogger {
	return &EnhancedLogger{
		service:     service,
		context:     make(map[string]interface{}),
		output:      os.Stdout,
		level:       LevelInfo,
		environment: getEnv("ENVIRONMENT", "development"),
	}
}

// WithLayer returns a new logger scoped to a layer.
func (l *EnhancedLogger) WithLayer(layer string) *EnhancedLogger {
	c := l.clone()
	c.layer = layer
	return c
}

// WithComponent returns a new logger scoped to a component.
func (l *EnhancedLogger) WithComponent(component string) *EnhancedLogger {
	c := l.clone()
	c.component = component
	return c
}

// WithMethod returns a new logger scoped to a method.
func (l *EnhancedLogger) WithMethod(method string) *EnhancedLogger {
	c := l.clone()
	c.method = method
	return c
}

// WithHandler returns a new logger scoped to a handler.
func (l *EnhancedLogger) WithHandler(handler string) *EnhancedLogger {
	c := l.clone()
	c.handler = handler
	return c
}

// WithContext returns a new logger with additional context fields.
func (l *EnhancedLogger) WithContext(ctx map[string]interface{}) *EnhancedLogger {
	c := l.clone()
	for k, v := range ctx {
		c.context[k] = v
	}
	return c
}

// SetLevel sets the minimum log level.
func (l *EnhancedLogger) SetLevel(level LogLevel) {
	l.level = level
}

// SetOutput sets the output writer.
func (l *EnhancedLogger) SetOutput(w io.Writer) {
	l.output = w
}

func (l *EnhancedLogger) clone() *EnhancedLogger {
	ctx := make(map[string]interface{}, len(l.context))
	for k, v := range l.context {
		ctx[k] = v
	}
	return &EnhancedLogger{
		service:     l.service,
		component:   l.component,
		layer:       l.layer,
		method:      l.method,
		handler:     l.handler,
		context:     ctx,
		output:      l.output,
		level:       l.level,
		environment: l.environment,
	}
}

// --- logging methods ---

// Debug logs a debug message.
func (l *EnhancedLogger) Debug(message string, extra map[string]interface{}) {
	if l.shouldLog(LevelDebug) {
		l.write(LevelDebug, message, extra, nil, nil, false)
	}
}

// Info logs an info message.
func (l *EnhancedLogger) Info(message string, extra map[string]interface{}) {
	if l.shouldLog(LevelInfo) {
		l.write(LevelInfo, message, extra, nil, nil, false)
	}
}

// Warning logs a warning message.
func (l *EnhancedLogger) Warning(message string, extra map[string]interface{}) {
	if l.shouldLog(LevelWarning) {
		l.write(LevelWarning, message, extra, nil, nil, false)
	}
}

// Error logs an error message with stack trace.
func (l *EnhancedLogger) Error(message string, extra map[string]interface{}) {
	if l.shouldLog(LevelError) {
		l.write(LevelError, message, extra, nil, nil, true)
	}
}

// ErrorWithCode logs an error with an error code.
func (l *EnhancedLogger) ErrorWithCode(message string, errorCode int, extra map[string]interface{}) {
	if l.shouldLog(LevelError) {
		errLog := &ErrorLog{
			Type:    "Error",
			Message: message,
			Code:    errorCode,
		}
		errLog.StackTrace = l.getStackTrace()
		l.write(LevelError, message, extra, nil, errLog, false)
	}
}

// Critical logs a critical message with stack trace.
func (l *EnhancedLogger) Critical(message string, extra map[string]interface{}) {
	if l.shouldLog(LevelCritical) {
		l.write(LevelCritical, message, extra, nil, nil, true)
	}
}

// LogQuery logs a query execution.
func (l *EnhancedLogger) LogQuery(sql string, args []interface{}, duration int64, err error) {
	q := &QueryLog{SQL: sql, Args: args, Duration: duration}
	if err != nil {
		q.Error = err.Error()
		l.write(LevelError, "Query execution failed", map[string]interface{}{
			"query_duration_ms": duration,
		}, q, nil, true)
	} else {
		l.write(LevelDebug, "Query executed", map[string]interface{}{
			"query_duration_ms": duration,
		}, q, nil, false)
	}
}

// LogQueryWithParams logs a query with named parameters.
func (l *EnhancedLogger) LogQueryWithParams(sql string, args []interface{}, params map[string]interface{}, duration int64, err error) {
	q := &QueryLog{SQL: sql, Args: args, Params: params, Duration: duration}
	if err != nil {
		q.Error = err.Error()
		l.write(LevelError, "Query with params failed", map[string]interface{}{
			"query_duration_ms": duration,
		}, q, nil, true)
	} else {
		l.write(LevelDebug, "Query with params executed", map[string]interface{}{
			"query_duration_ms": duration,
		}, q, nil, false)
	}
}

// write is the internal write method.
func (l *EnhancedLogger) write(
	level LogLevel,
	message string,
	extra map[string]interface{},
	query *QueryLog,
	errLog *ErrorLog,
	includeStack bool,
) {
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
		Message:     message,
		ExtraData:   extra,
		Context:     l.context,
		Query:       query,
		Environment: l.environment,
	}

	// Promote IDs from context to top-level fields.
	if v, ok := l.context["request_id"].(string); ok {
		entry.RequestID = v
	}
	if v, ok := l.context["trace_id"].(string); ok {
		entry.TraceID = v
	}
	if v, ok := l.context["user_id"].(string); ok {
		entry.UserID = v
	}

	if errLog != nil {
		entry.Error = errLog
	} else if includeStack {
		entry.Error = &ErrorLog{
			Type:       "Error",
			Message:    message,
			StackTrace: l.getStackTrace(),
		}
	}

	bytes, err := json.Marshal(entry)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to serialize log entry: %v\n", err)
		return
	}
	fmt.Fprintln(l.output, string(bytes))
}

func (l *EnhancedLogger) getCallerMethod() string {
	pc, _, _, ok := runtime.Caller(4)
	if !ok {
		return "unknown"
	}
	fn := runtime.FuncForPC(pc)
	if fn == nil {
		return "unknown"
	}
	parts := strings.Split(fn.Name(), "/")
	last := parts[len(parts)-1]
	methodParts := strings.Split(last, ".")
	if len(methodParts) > 1 {
		return methodParts[len(methodParts)-1]
	}
	return last
}

func (l *EnhancedLogger) getStackTrace() string {
	buf := make([]byte, 4096)
	n := runtime.Stack(buf, false)
	return string(buf[:n])
}

func (l *EnhancedLogger) shouldLog(level LogLevel) bool {
	order := map[LogLevel]int{
		LevelDebug:    0,
		LevelInfo:     1,
		LevelWarning:  2,
		LevelError:    3,
		LevelCritical: 4,
	}
	return order[level] >= order[l.level]
}
