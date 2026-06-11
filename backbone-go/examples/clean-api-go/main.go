// Application entry point — DI container + server start.
//
// main() responsibilities (nothing else):
//  1. Instantiate infrastructure (repositories)
//  2. Run seeders
//  3. Wire command handlers   (write side — CQRS)
//  4. Wire query handlers     (read  side — CQRS)
//  5. Wire HTTP adapters      (interfaces layer)
//  6. Register versioned routes
//  7. Start server

package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	_ "github.com/freakjazz/backbone-go/examples/clean-api-go/docs"

	// Infrastructure
	"github.com/freakjazz/backbone-go/examples/clean-api-go/infrastructure/repositories"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/infrastructure/seeders"

	// Commands (write side)
	"github.com/freakjazz/backbone-go/examples/clean-api-go/application/commands"

	// Queries (read side)
	"github.com/freakjazz/backbone-go/examples/clean-api-go/application/queries"

	// HTTP adapters (split by CQRS side)
	"github.com/freakjazz/backbone-go/examples/clean-api-go/interfaces/http/handlers"
	v1 "github.com/freakjazz/backbone-go/examples/clean-api-go/interfaces/http/v1"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/interfaces/http/middleware"

	"github.com/freakjazz/backbone-go/infrastructure/logging"
	httpSwagger "github.com/swaggo/http-swagger"
)

func main() {
	fmt.Println("Starting Clean API — backbone-go (Clean Architecture + CQRS)")
	fmt.Println("=============================================================")

	logger := logging.NewEnhancedLogger("product-api")
	logger.SetLevel(logging.LevelDebug)
	logger.Info("Initializing application", map[string]interface{}{"version": "1.0.0"})

	// -------------------------------------------------------------------------
	// 1. Infrastructure
	// -------------------------------------------------------------------------
	productRepo := repositories.NewMemoryProductRepository(logger)

	// -------------------------------------------------------------------------
	// 2. Seeders
	// -------------------------------------------------------------------------
	seeders.NewProductSeeder(productRepo, logger).Run(context.Background())

	// -------------------------------------------------------------------------
	// 3. Command handlers  (write side)
	// -------------------------------------------------------------------------
	createCmd := commands.NewCreateProductCommandHandler(productRepo, logger)
	updateCmd := commands.NewUpdateProductCommandHandler(productRepo, logger)
	deleteCmd := commands.NewDeleteProductCommandHandler(productRepo, logger)
	statusCmd := commands.NewChangeProductStatusCommandHandler(productRepo, logger)

	// -------------------------------------------------------------------------
	// 4. Query handlers  (read side)
	// -------------------------------------------------------------------------
	getListQry  := queries.NewGetProductsQueryHandler(productRepo, logger)
	getByIDQry  := queries.NewGetProductByIDQueryHandler(productRepo, logger)

	// -------------------------------------------------------------------------
	// 5. HTTP adapters  (split by CQRS side)
	// -------------------------------------------------------------------------
	cmdHandler := handlers.NewProductCommandHandler(createCmd, updateCmd, deleteCmd, statusCmd, logger)
	qryHandler := handlers.NewProductQueryHandler(getListQry, getByIDQry, logger)

	// -------------------------------------------------------------------------
	// 6. Routes  (versioned)
	// -------------------------------------------------------------------------
	mux := http.NewServeMux()
	v1.RegisterRoutes(mux, cmdHandler, qryHandler)

	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"healthy","service":"product-api"}`))
	})
	mux.Handle("/swagger/", httpSwagger.WrapHandler)

	// -------------------------------------------------------------------------
	// 7. Server
	// -------------------------------------------------------------------------
	server := &http.Server{
		Addr:         ":8080",
		Handler:      middleware.LoggingMiddleware(logger)(mux),
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	}

	go func() {
		logger.Info("HTTP server starting", map[string]interface{}{"port": 8080})
		fmt.Println("\nServer  → http://localhost:8080")
		fmt.Println("Swagger → http://localhost:8080/swagger/")
		fmt.Println("\nEndpoints (v1):")
		fmt.Println("  POST   /api/v1/products")
		fmt.Println("  GET    /api/v1/products?filters=category,eq,Electronics,and&filters=price,gt,500&page=1&page_size=10&sort_by=price:desc")
		fmt.Println("  GET    /api/v1/products/{id}")
		fmt.Println("  PUT    /api/v1/products/{id}")
		fmt.Println("  DELETE /api/v1/products/{id}")
		fmt.Println("  PATCH  /api/v1/products/{id}/status")
		fmt.Println("  GET    /health")
		fmt.Println("\nPress Ctrl+C to stop")

		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Critical("Server failed to start", map[string]interface{}{"error": err.Error()})
			log.Fatal(err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Info("Shutting down server...", nil)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := server.Shutdown(ctx); err != nil {
		logger.Error("Forced shutdown", map[string]interface{}{"error": err.Error()})
	}
	logger.Info("Server stopped gracefully", nil)
	fmt.Println("Server stopped")
}
