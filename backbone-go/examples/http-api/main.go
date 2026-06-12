// HTTP API example using backbone-go with net/http.
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

type App struct {
	logger     logging.Logger
	eventBus   ports.EventBus
	eventStore ports.EventStore
	config     *config.Config
}

func main() {
	cfg, err := config.LoadConfig(".")
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	logger := logging.NewLogger(cfg.AppName)
	logger.Info("Starting HTTP API", map[string]interface{}{
		"version": cfg.AppVersion,
		"env":     cfg.Environment,
		"port":    cfg.ServerPort,
	})

	bus := messaging.NewInMemoryEventBus(logger)
	defer bus.Close()

	store, err := events.NewFileEventStore(cfg.EventStorePath)
	if err != nil {
		log.Fatalf("Failed to create event store: %v", err)
	}

	app := &App{logger: logger, eventBus: bus, eventStore: store, config: cfg}

	mux := http.NewServeMux()
	app.setupRoutes(mux)

	server := &http.Server{
		Addr:         fmt.Sprintf("%s:%d", cfg.ServerHost, cfg.ServerPort),
		Handler:      loggingMiddleware(logger, mux),
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	go func() {
		logger.Info("Server listening", map[string]interface{}{"address": server.Addr})
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Error("Server error", map[string]interface{}{"error": err.Error()})
			os.Exit(1)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := server.Shutdown(ctx); err != nil {
		logger.Error("Forced shutdown", map[string]interface{}{"error": err.Error()})
	}
	logger.Info("Server stopped", nil)
}

func (app *App) setupRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/health", app.healthCheck)
	mux.HandleFunc("/api/v1/users", app.handleUsers)
	mux.HandleFunc("/api/v1/users/", app.handleUserByID)
	mux.HandleFunc("/api/v1/machines", app.handleMachines)
	mux.HandleFunc("/api/v1/machines/", app.handleMachineByID)
}

func (app *App) healthCheck(w http.ResponseWriter, r *http.Request) {
	data := responses.SimpleObjectResponseBuilder.Found(map[string]interface{}{
		"service":     app.config.AppName,
		"version":     app.config.AppVersion,
		"environment": app.config.Environment,
		"status":      "healthy",
		"timestamp":   time.Now().UTC().Format(time.RFC3339),
	})
	writeJSON(w, http.StatusOK, data)
}

func (app *App) handleUsers(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		app.listUsers(w, r)
	case http.MethodPost:
		app.createUser(w, r)
	default:
		resp := responses.ErrorResponseBuilder.ValidationError("Method not allowed")
		writeJSON(w, http.StatusMethodNotAllowed, resp)
	}
}

func (app *App) listUsers(w http.ResponseWriter, r *http.Request) {
	page, _ := strconv.Atoi(r.URL.Query().Get("page"))
	if page < 1 {
		page = 1
	}
	pageSize, _ := strconv.Atoi(r.URL.Query().Get("page_size"))
	if pageSize < 1 {
		pageSize = 10
	}

	users := []map[string]interface{}{
		{"id": "1", "name": "John Doe",   "email": "john@example.com", "status": "active"},
		{"id": "2", "name": "Jane Smith", "email": "jane@example.com", "status": "active"},
	}

	resp := responses.PaginatedResponseBuilder.Success(users, 100, page, pageSize, "Users retrieved successfully")
	app.logger.Info("Users listed", map[string]interface{}{"page": page, "count": len(users)})
	writeJSON(w, http.StatusOK, resp)
}

func (app *App) createUser(w http.ResponseWriter, r *http.Request) {
	var body map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		resp := responses.ErrorResponseBuilder.ValidationError("Invalid request body")
		writeJSON(w, http.StatusBadRequest, resp)
		return
	}

	if name, ok := body["name"].(string); !ok || name == "" {
		resp := responses.ErrorResponseBuilder.ValidationError("Name is required",
			responses.ErrorOpts{FieldErrors: map[string]string{"name": "required"}})
		writeJSON(w, http.StatusBadRequest, resp)
		return
	}

	if age, ok := body["age"].(float64); ok && age < 18 {
		err := domainExceptions.NewBusinessRuleViolationException("User must be 18 or older", "ValidateUserAge")
		resp := responses.ErrorResponseBuilder.FromException(err)
		writeJSON(w, err.HTTPCode, resp)
		return
	}

	userID := "user-123-456"
	event := ports.NewBaseEvent("UserCreated", app.config.AppName,
		map[string]interface{}{"user_id": userID, "name": body["name"]},
		"users-service", "create-user",
	)

	ctx := context.Background()
	if err := app.eventStore.Save(ctx, event); err != nil {
		app.logger.Error("Failed to save event", map[string]interface{}{"error": err.Error()})
	}
	if err := app.eventBus.Publish(ctx, event); err != nil {
		app.logger.Error("Failed to publish event", map[string]interface{}{"error": err.Error()})
	}

	app.logger.Info("User created", map[string]interface{}{"user_id": userID})
	writeJSON(w, http.StatusCreated, responses.ProcessResponseBuilder.Created(userID))
}

func (app *App) handleUserByID(w http.ResponseWriter, r *http.Request) {
	userID := r.URL.Path[len("/api/v1/users/"):]
	switch r.Method {
	case http.MethodGet:
		app.getUser(w, r, userID)
	case http.MethodPut:
		app.updateUser(w, r, userID)
	case http.MethodDelete:
		app.deleteUser(w, r, userID)
	default:
		resp := responses.ErrorResponseBuilder.ValidationError("Method not allowed")
		writeJSON(w, http.StatusMethodNotAllowed, resp)
	}
}

func (app *App) getUser(w http.ResponseWriter, r *http.Request, userID string) {
	user := responses.SimpleObjectResponseBuilder.Found(map[string]interface{}{
		"id": userID, "name": "John Doe", "email": "john@example.com", "status": "active",
	})
	writeJSON(w, http.StatusOK, user)
}

func (app *App) updateUser(w http.ResponseWriter, r *http.Request, userID string) {
	var body map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		resp := responses.ErrorResponseBuilder.ValidationError("Invalid request body")
		writeJSON(w, http.StatusBadRequest, resp)
		return
	}
	writeJSON(w, http.StatusOK, responses.ProcessResponseBuilder.Updated(userID))
}

func (app *App) deleteUser(w http.ResponseWriter, r *http.Request, userID string) {
	writeJSON(w, http.StatusOK, responses.ProcessResponseBuilder.Deleted(userID))
}

func (app *App) handleMachines(w http.ResponseWriter, r *http.Request) {
	resp := responses.PaginatedResponseBuilder.Empty("No machines found")
	writeJSON(w, http.StatusOK, resp)
}

func (app *App) handleMachineByID(w http.ResponseWriter, r *http.Request) {
	machineID := r.URL.Path[len("/api/v1/machines/"):]
	resp := responses.ErrorResponseBuilder.NotFound("Machine " + machineID + " not found")
	writeJSON(w, http.StatusNotFound, resp)
}

func writeJSON(w http.ResponseWriter, statusCode int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	json.NewEncoder(w).Encode(data)
}

func loggingMiddleware(logger logging.Logger, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		logger.Info("HTTP request", map[string]interface{}{
			"method":      r.Method,
			"path":        r.URL.Path,
			"duration_ms": time.Since(start).Milliseconds(),
		})
	})
}
