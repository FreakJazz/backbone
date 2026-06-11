package logging_test

import (
	"bytes"
	"encoding/json"
	"strings"
	"testing"

	"github.com/freakjazz/backbone-go/infrastructure/logging"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewLogger(t *testing.T) {
	l := logging.NewLogger("test-service")
	assert.NotNil(t, l)
}

func TestNewEnhancedLogger(t *testing.T) {
	l := logging.NewEnhancedLogger("test-service")
	assert.NotNil(t, l)
}

func TestLoggerOutputJSON(t *testing.T) {
	buf := &bytes.Buffer{}
	l := logging.NewLogger("svc")
	l.SetOutput(buf)
	l.SetLevel(logging.LevelDebug)

	l.Info("hello world", nil)

	var entry map[string]interface{}
	require.NoError(t, json.Unmarshal(bytes.TrimSpace(buf.Bytes()), &entry))

	assert.Equal(t, "INFO", entry["level"])
	assert.Equal(t, "hello world", entry["message"])
	assert.Equal(t, "svc", entry["service"])
	assert.NotEmpty(t, entry["timestamp"])
}

func TestLoggerLevelFiltering(t *testing.T) {
	buf := &bytes.Buffer{}
	l := logging.NewLogger("svc")
	l.SetOutput(buf)
	l.SetLevel(logging.LevelError) // only ERROR and above

	l.Debug("should not appear", nil)
	l.Info("should not appear", nil)
	l.Warning("should not appear", nil)
	l.Error("should appear", nil)

	output := buf.String()
	assert.NotContains(t, output, "should not appear")
	assert.Contains(t, output, "should appear")
}

func TestLoggerWithContext(t *testing.T) {
	buf := &bytes.Buffer{}
	l := logging.NewLogger("svc")
	l.SetOutput(buf)

	scoped := l.WithContext(map[string]interface{}{
		"request_id": "abc-123",
		"user_id":    "user-1",
	})
	scoped.Info("ctx message", nil)

	var entry map[string]interface{}
	require.NoError(t, json.Unmarshal(bytes.TrimSpace(buf.Bytes()), &entry))

	assert.Equal(t, "abc-123", entry["request_id"])
}

func TestEnhancedLoggerFluent(t *testing.T) {
	buf := &bytes.Buffer{}
	l := logging.NewEnhancedLogger("svc")
	l.SetOutput(buf)

	l.WithLayer("application").
		WithComponent("MyHandler").
		WithMethod("Execute").
		WithHandler("MyHandler").
		Info("fluent test", nil)

	var entry map[string]interface{}
	require.NoError(t, json.Unmarshal(bytes.TrimSpace(buf.Bytes()), &entry))

	assert.Equal(t, "application", entry["layer"])
	assert.Equal(t, "MyHandler", entry["component"])
	assert.Equal(t, "Execute", entry["method"])
}

func TestEnhancedLoggerErrorWithCode(t *testing.T) {
	buf := &bytes.Buffer{}
	l := logging.NewEnhancedLogger("svc")
	l.SetOutput(buf)
	l.SetLevel(logging.LevelDebug)

	l.ErrorWithCode("something failed", 10001001, nil)

	var entry map[string]interface{}
	require.NoError(t, json.Unmarshal(bytes.TrimSpace(buf.Bytes()), &entry))

	assert.Equal(t, "ERROR", entry["level"])
	errField, ok := entry["error"].(map[string]interface{})
	require.True(t, ok, "error field should be an object")
	assert.EqualValues(t, 10001001, errField["code"])
}

func TestEnhancedLoggerLogQuery(t *testing.T) {
	buf := &bytes.Buffer{}
	l := logging.NewEnhancedLogger("svc")
	l.SetOutput(buf)
	l.SetLevel(logging.LevelDebug)

	l.LogQuery("SELECT * FROM products WHERE id = $1", []interface{}{"123"}, 12, nil)

	var entry map[string]interface{}
	require.NoError(t, json.Unmarshal(bytes.TrimSpace(buf.Bytes()), &entry))

	query, ok := entry["query"].(map[string]interface{})
	require.True(t, ok, "query field should be present")
	assert.Equal(t, "SELECT * FROM products WHERE id = $1", query["sql"])
	assert.EqualValues(t, 12, query["duration_ms"])
}

func TestLogLevels(t *testing.T) {
	levels := []struct {
		level    logging.LogLevel
		expected string
	}{
		{logging.LevelDebug, "DEBUG"},
		{logging.LevelInfo, "INFO"},
		{logging.LevelWarning, "WARNING"},
		{logging.LevelError, "ERROR"},
		{logging.LevelCritical, "CRITICAL"},
	}

	for _, tc := range levels {
		t.Run(string(tc.level), func(t *testing.T) {
			buf := &bytes.Buffer{}
			l := logging.NewLogger("svc")
			l.SetOutput(buf)
			l.SetLevel(logging.LevelDebug)

			switch tc.level {
			case logging.LevelDebug:
				l.Debug("msg", nil)
			case logging.LevelInfo:
				l.Info("msg", nil)
			case logging.LevelWarning:
				l.Warning("msg", nil)
			case logging.LevelError:
				l.Error("msg", nil)
			case logging.LevelCritical:
				l.Critical("msg", nil)
			}

			assert.True(t, strings.Contains(buf.String(), tc.expected),
				"expected level %s in output: %s", tc.expected, buf.String())
		})
	}
}
