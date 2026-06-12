// Package middleware contains HTTP middleware
package middleware

import (
	"context"
	"net/http"
	"time"

	"github.com/freakjazz/backbone-go/infrastructure/logging"
	"github.com/google/uuid"
)

// ctxKey is an unexported type for context keys in this package.
// Using a private type prevents collisions with keys from other packages
// that happen to use the same string — a common source of subtle bugs.
type ctxKey uint8

const ctxRequestID ctxKey = 0

// RequestIDFromContext returns the request trace ID set by LoggingMiddleware.
// Returns an empty string if no ID is present (e.g. in unit tests).
func RequestIDFromContext(ctx context.Context) string {
	if v, ok := ctx.Value(ctxRequestID).(string); ok {
		return v
	}
	return ""
}

// LoggingMiddleware logs HTTP requests and responses.
// It also generates a UUID request trace ID and stores it in the context
// so all downstream handlers and use-cases can attach it to logs and error responses.
func LoggingMiddleware(logger *logging.EnhancedLogger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()

			requestID := uuid.New().String()
			ctx := context.WithValue(r.Context(), ctxRequestID, requestID)
			r = r.WithContext(ctx)

			reqLogger := logger.
				WithLayer("interfaces").
				WithComponent("HTTPMiddleware").
				WithMethod("LoggingMiddleware").
				WithContext(map[string]interface{}{
					"request_id": requestID,
				})

			reqLogger.Info("Incoming HTTP request", map[string]interface{}{
				"method":     r.Method,
				"path":       r.URL.Path,
				"query":      r.URL.RawQuery,
				"remote_ip":  r.RemoteAddr,
				"user_agent": r.UserAgent(),
			})

			rw := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}
			next.ServeHTTP(rw, r)

			reqLogger.Info("HTTP request completed", map[string]interface{}{
				"method":      r.Method,
				"path":        r.URL.Path,
				"status_code": rw.statusCode,
				"duration_ms": time.Since(start).Milliseconds(),
			})
		})
	}
}

type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}
