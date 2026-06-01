// HTTP API example using backbone-go with net/http
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	domainExceptions "github.com/freakjazz/backbone-go/domain/exceptions"
	"github.com/freakjazz/backbone-go/domain/ports"
	"github.com/freakjazz/backbone-go/infrastructure/config"
	"github.com/freakjazz/backbone-go/infrastructure/events"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
	"github.com/freakjazz/backbone-go/infrastructure/messaging"
	"github.com/freakjazz/backbone-go/interfaces/responses"
)

// App holds application dependencies
type App struct {
	logger     logging.Logger
	eventBus   ports.EventBus
	eventStore ports.EventStore
	config     *config.Config
}

func main() {
	// Load configuration
	cfg, err := config.LoadConfig(".")
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	// Setup logger
	logger := logging.NewLogger(cfg.AppName)
	logger.Info("Starting HTTP API server", map[string]interface{}{
		"version":     cfg.AppVersion,
		"environment": cfg.Environment,
		"port":        cfg.ServerPort,
	})

	// Setup event bus
	eventBus := messaging.NewInMemoryEventBus(logger)
	defer eventBus.Close()

	// Setup event store
	eventStore, err := events.NewFileEventStore(cfg.EventStorePath)
	if err != nil {
		log.Fatalf("Failed to create event store: %v", err)
	}

	// Create app instance
	app := &App{
		logger:     logger,
		eventBus:   eventBus,
		eventStore: eventStore,
		config:     cfg,
	}

	// Setup routes
	mux := http.NewServeMux()
	app.setupRoutes(mux)

	// Create server
	server := &http.Server{
		Addr:         fmt.Sprintf("%s:%d", cfg.ServerHost, cfg.ServerPort),
		Handler:      loggingMiddleware(logger, mux),
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Start server in a goroutine
	go func() {
		logger.Info("Server listening", map[string]interface{}{
			"address": server.Addr,
		})
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Error("Server error", map[string]interface{}{
				"error": err.Error(),
			})
			os.Exit(1)
		}
	}()

	// Graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Info("Shutting down server...", nil)

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		logger.Error("Server forced to shutdown", map[string]interface{}{
			"error": err.Error(),
		})
	}

	logger.Info("Server stopped", nil)
}

// setupRoutes configures HTTP routes
func (app *App) setupRoutes(mux *http.ServeMux) {
	// Health check
	mux.HandleFunc("/health", app.healthCheck)

	// API routes
	mux.HandleFunc("/api/v1/users", app.handleUsers)
	mux.HandleFunc("/api/v1/users/", app.handleUserByID)
	mux.HandleFunc("/api/v1/machines", app.handleMachines)
	mux.HandleFunc("/api/v1/machines/", app.handleMachineByID)
}

// healthCheck endpoint
func (app *App) healthCheck(w http.ResponseWriter, r *http.Request) {
	response := responses.ProcessResponseBuilder.Status(
		"Service is healthy",
		map[string]interface{}{
			"service":     app.config.AppName,
			"version":     app.config.AppVersion,
			"environment": app.config.Environment,
			"timestamp":   time.Now().UTC().Format(time.RFC3339),
		},
	)

	writeJSON(w, http.StatusOK, response)
}

// handleUsers handles user listing and creation
func (app *App) handleUsers(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		app.listUsers(w, r)
	case http.MethodPost:
		app.createUser(w, r)
	default:
		response := responses.ErrorResponseBuilder.BadRequest(
			"Method not allowed",
			map[string]interface{}{"allowed_methods": []string{"GET", "POST"}},
		)
		writeJSON(w, http.StatusMethodNotAllowed, response)
	}
}

// listUsers lists all users with pagination
func (app *App) listUsers(w http.ResponseWriter, r *http.Request) {
	// Parse query parameters
	page, _ := strconv.Atoi(r.URL.Query().Get("page"))
	if page < 1 {
		page = 1
	}
	pageSize, _ := strconv.Atoi(r.URL.Query().Get("page_size"))
	if pageSize < 1 {
		pageSize = 10
	}

	// Mock data
	users := []map[string]interface{}{
		{"id": "1", "name": "John Doe", "email": "john@example.com", "status": "active"},
		{"id": "2", "name": "Jane Smith", "email": "jane@example.com", "status": "active"},
	}

	response := responses.QueryResponseBuilder.SuccessWithPagination(
		"Users retrieved successfully",
		users,
		page,
		pageSize,
		100, // total records
	)

	app.logger.Info("Users listed", map[string]interface{}{
		"page":      page,
		"page_size": pageSize,
		"count":     len(users),
	})

	writeJSON(w, http.StatusOK, response)
}

// createUser creates a new user
func (app *App) createUser(w http.ResponseWriter, r *http.Request) {
	var userData map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&userData); err != nil {
		response := responses.ErrorResponseBuilder.BadRequest(
			"Invalid request body",
			map[string]interface{}{"error": err.Error()},
		)
		writeJSON(w, http.StatusBadRequest, response)
		return
	}

	// Validate
	if name, ok := userData["name"].(string); !ok || name == "" {
		response := responses.ErrorResponseBuilder.BadRequest(
			"Name is required",
			map[string]interface{}{"field": "name"},
		)
		writeJSON(w, http.StatusBadRequest, response)
		return
	}

	// Business rule validation example
	if age, ok := userData["age"].(float64); ok && age < 18 {
		err := domainExceptions.NewBusinessRuleViolationException(
			"User must be 18 or older",
			"ValidateUserAge",
		)
		response := responses.ErrorResponseBuilder.FromException(err)
		writeJSON(w, err.HTTPCode, response)
		return
	}

	// Create user (mock)
	userID := "user-123-456"

	// Publish event
	event := ports.NewBaseEvent(
		"UserCreated",
		app.config.AppName,
		map[string]interface{}{
			"user_id": userID,
			"name":    userData["name"],
			"email":   userData["email"],
		},
		"users-service",
		"create-user",
	)

	ctx := context.Background()
	if err := app.eventStore.Save(ctx, event); err != nil {
		app.logger.Error("Failed to save event", map[string]interface{}{
			"error": err.Error(),
		})
	}

	if err := app.eventBus.Publish(ctx, event); err != nil {
		app.logger.Error("Failed to publish event", map[string]interface{}{
			"error": err.Error(),
		})
	}

	response := responses.ProcessResponseBuilder.Created(
		"User created successfully",
		userID,
	)

	app.logger.Info("User created", map[string]interface{}{
		"user_id": userID,
		"name":    userData["name"],
	})

	writeJSON(w, http.StatusCreated, response)
}

// handleUserByID handles user by ID operations
func (app *App) handleUserByID(w http.ResponseWriter, r *http.Request) {
	// Extract ID from path
	userID := r.URL.Path[len("/api/v1/users/"):]

	switch r.Method {
	case http.MethodGet:
		app.getUser(w, r, userID)
	case http.MethodPut:
		app.updateUser(w, r, userID)
	case http.MethodDelete:
		app.deleteUser(w, r, userID)
	default:
		response := responses.ErrorResponseBuilder.BadRequest(
			"Method not allowed",
			map[string]interface{}{"allowed_methods": []string{"GET", "PUT", "DELETE"}},
		)
		writeJSON(w, http.StatusMethodNotAllowed, response)
	}
}

// getUser retrieves a user by ID
func (app *App) getUser(w http.ResponseWriter, r *http.Request, userID string) {
	// Mock data
	user := map[string]interface{}{
		"id":     userID,
		"name":   "John Doe",
		"email":  "john@example.com",
		"status": "active",
	}

	response := responses.QueryResponseBuilder.Single(
		"User retrieved successfully",
		user,
	)

	writeJSON(w, http.StatusOK, response)
}

// updateUser updates a user
func (app *App) updateUser(w http.ResponseWriter, r *http.Request, userID string) {
	var userData map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&userData); err != nil {
		response := responses.ErrorResponseBuilder.BadRequest(
			"Invalid request body",
			map[string]interface{}{"error": err.Error()},
		)
		writeJSON(w, http.StatusBadRequest, response)
		return
	}

	response := responses.ProcessResponseBuilder.Updated(
		"User updated successfully",
		map[string]interface{}{"id": userID},
	)

	writeJSON(w, http.StatusOK, response)
}

// deleteUser deletes a user
func (app *App) deleteUser(w http.ResponseWriter, r *http.Request, userID string) {
	response := responses.ProcessResponseBuilder.Deleted(
		"User deleted successfully",
		userID,
	)

	writeJSON(w, http.StatusOK, response)
}

// handleMachines handles machine operations
func (app *App) handleMachines(w http.ResponseWriter, r *http.Request) {
	// Similar to users...
	response := responses.QueryResponseBuilder.Empty("No machines found")
	writeJSON(w, http.StatusOK, response)
}

// handleMachineByID handles machine by ID operations
func (app *App) handleMachineByID(w http.ResponseWriter, r *http.Request) {
	machineID := r.URL.Path[len("/api/v1/machines/"):]
	response := responses.ErrorResponseBuilder.NotFound(
		"Machine not found",
		"Machine",
		machineID,
	)
	writeJSON(w, http.StatusNotFound, response)
}

// writeJSON writes a JSON response
func writeJSON(w http.ResponseWriter, statusCode int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteStatus(statusCode)
	json.NewEncoder(w).Encode(data)
}

// loggingMiddleware logs HTTP requests
func loggingMiddleware(logger logging.Logger, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Call the next handler
		next.ServeHTTP(w, r)

		logger.Info("HTTP request", map[string]interface{}{
			"method":   r.Method,
			"path":     r.URL.Path,
			"duration": time.Since(start).Milliseconds(),
			"remote":   r.RemoteAddr,
		})
	})
}
