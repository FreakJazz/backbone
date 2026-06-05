// @title Product API
// @version 1.0
// @description Clean Architecture API Example with Backbone Framework
// @contact.name API Support
// @license.name MIT
// @host localhost:8080
// @basePath /api
// @schemes http

// Package main contains the main application setup
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

	"github.com/freakjazz/backbone-go/examples/clean-api-go/application/usecases"
	_ "github.com/freakjazz/backbone-go/examples/clean-api-go/docs"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/entities"
	domainRepositories "github.com/freakjazz/backbone-go/examples/clean-api-go/domain/repositories"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/infrastructure/repositories"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/interfaces/http/handlers"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/interfaces/http/middleware"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
	httpSwagger "github.com/swaggo/http-swagger"
)

func main() {
	fmt.Println("🚀 Starting Clean API Example - Go")
	fmt.Println("====================================")

	// Setup logger
	logger := logging.NewEnhancedLogger("product-api")
	logger.SetLevel(logging.LevelDebug)

	logger.Info("Initializing application", map[string]interface{}{
		"version": "1.0.0",
		"env":     "development",
	})

	// Setup dependencies (Dependency Injection)
	productRepo := repositories.NewMemoryProductRepository(logger)

	// Create use cases
	createProductUseCase := usecases.NewCreateProductUseCase(productRepo, logger)
	getProductsUseCase := usecases.NewGetProductsUseCase(productRepo, logger)

	// Create handlers
	productHandler := handlers.NewProductHandler(
		createProductUseCase,
		getProductsUseCase,
		logger,
	)

	// Seed data for demo
	seedData(productRepo, logger)

	// Setup HTTP server
	mux := http.NewServeMux()

	// Apply middleware
	handler := middleware.LoggingMiddleware(logger)(mux)

	// Register routes
	mux.HandleFunc("/api/products", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodPost:
			productHandler.CreateProduct(w, r)
		case http.MethodGet:
			productHandler.GetProducts(w, r)
		default:
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		}
	})

	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"healthy","service":"product-api"}`))
	})

	// Swagger documentation routes
	mux.Handle("/swagger/", httpSwagger.WrapHandler)

	server := &http.Server{
		Addr:         ":8080",
		Handler:      handler,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	}

	// Start server in goroutine
	go func() {
		logger.Info("HTTP server starting", map[string]interface{}{
			"address": server.Addr,
			"port":    8080,
		})

		fmt.Println("\n✅ Server running on http://localhost:8080")
		fmt.Println("\n📝 API Endpoints:")
		fmt.Println("  POST   http://localhost:8080/api/products")
		fmt.Println("  GET    http://localhost:8080/api/products")
		fmt.Println("  GET    http://localhost:8080/health")
		fmt.Println("\n🔍 Example with filters:")
		fmt.Println("  curl \"http://localhost:8080/api/products?category=Electronics&min_price=500&max_price=2000&page=1&page_size=10\"")
		fmt.Println("\n💡 Press Ctrl+C to stop")

		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Critical("Server failed to start", map[string]interface{}{
				"error": err.Error(),
			})
			log.Fatal(err)
		}
	}()

	// Graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Info("Shutting down server...", nil)

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		logger.Error("Server forced to shutdown", map[string]interface{}{
			"error": err.Error(),
		})
	}

	logger.Info("Server stopped gracefully", nil)
	fmt.Println("👋 Server stopped")
}

// seedData seeds initial data for demo
func seedData(repo domainRepositories.ProductRepository, logger *logging.EnhancedLogger) {
	ctx := context.Background()

	logger.Info("Seeding demo data...", nil)

	products := []*entities.Product{
		{
			ID:          "1",
			Name:        "Laptop Dell XPS 15",
			Description: "High performance laptop with 16GB RAM",
			Price:       1500.00,
			Category:    "Electronics",
			Stock:       50,
			Active:      true,
			CreatedAt:   time.Now(),
			UpdatedAt:   time.Now(),
		},
		{
			ID:          "2",
			Name:        "iPhone 14 Pro",
			Description: "Latest iPhone with advanced camera",
			Price:       1200.00,
			Category:    "Electronics",
			Stock:       100,
			Active:      true,
			CreatedAt:   time.Now(),
			UpdatedAt:   time.Now(),
		},
		{
			ID:          "3",
			Name:        "Office Chair Ergonomic",
			Description: "Comfortable ergonomic office chair",
			Price:       350.00,
			Category:    "Furniture",
			Stock:       30,
			Active:      true,
			CreatedAt:   time.Now(),
			UpdatedAt:   time.Now(),
		},
		{
			ID:          "4",
			Name:        "Standing Desk",
			Description: "Adjustable height standing desk",
			Price:       600.00,
			Category:    "Furniture",
			Stock:       20,
			Active:      true,
			CreatedAt:   time.Now(),
			UpdatedAt:   time.Now(),
		},
		{
			ID:          "5",
			Name:        "Wireless Mouse",
			Description: "Ergonomic wireless mouse",
			Price:       45.00,
			Category:    "Electronics",
			Stock:       200,
			Active:      true,
			CreatedAt:   time.Now(),
			UpdatedAt:   time.Now(),
		},
	}

	for _, product := range products {
		if err := repo.Create(ctx, product); err != nil {
			logger.Warning("Failed to seed product", map[string]interface{}{
				"product_id": product.ID,
				"error":      err.Error(),
			})
		}
	}

	logger.Info("Demo data seeded successfully", map[string]interface{}{
		"count": len(products),
	})
}
