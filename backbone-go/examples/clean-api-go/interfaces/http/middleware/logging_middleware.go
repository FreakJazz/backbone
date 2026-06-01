// Package middleware contains HTTP middleware
package middleware

import (
	"context"
	"net/http"
	"time"

	"github.com/freakjazz/backbone-go/infrastructure/logging"
	"github.com/google/uuid"
)

// LoggingMiddleware logs HTTP requests and responses
func LoggingMiddleware(logger *logging.EnhancedLogger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()

			// Generate request ID
			requestID := uuid.New().String()

			// Add request ID to context
			ctx := context.WithValue(r.Context(), "request_id", requestID)
			r = r.WithContext(ctx)

			// Logger con contexto de request
			reqLogger := logger.
				WithLayer("interfaces").
				WithComponent("HTTPMiddleware").
				WithMethod("LoggingMiddleware").
				WithContext(map[string]interface{}{
					"request_id": requestID,
				})

			// Log request
			reqLogger.Info("Incoming HTTP request", map[string]interface{}{
				"method":     r.Method,
				"path":       r.URL.Path,
				"query":      r.URL.RawQuery,
				"remote_ip":  r.RemoteAddr,
				"user_agent": r.UserAgent(),
			})

			// Create custom response writer to capture status code
			rw := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}

			// Call next handler
			next.ServeHTTP(rw, r)

			// Calculate duration
			duration := time.Since(start).Milliseconds()

			// Log response
			reqLogger.Info("HTTP request completed", map[string]interface{}{
				"method":      r.Method,
				"path":        r.URL.Path,
				"status_code": rw.statusCode,
				"duration_ms": duration,
			})
		})
	}
}

// responseWriter wraps http.ResponseWriter to capture status code
type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

// WriteHeader captures the status code
func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}
