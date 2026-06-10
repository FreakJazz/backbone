// @title Product API
// @version 1.0
// @description Clean Architecture API Example with Backbone Framework
// @host localhost:8080
// @basePath /api
// @schemes http

package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strings"
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
	fmt.Println("Starting Clean API Example - backbone-go")
	fmt.Println("=========================================")

	logger := logging.NewEnhancedLogger("product-api")
	logger.SetLevel(logging.LevelDebug)

	logger.Info("Initializing application", map[string]interface{}{
		"version": "1.0.0",
		"env":     "development",
	})

	// Dependency injection
	productRepo := repositories.NewMemoryProductRepository(logger)

	createUC := usecases.NewCreateProductUseCase(productRepo, logger)
	getListUC := usecases.NewGetProductsUseCase(productRepo, logger)
	getByIDUC := usecases.NewGetProductByIDUseCase(productRepo, logger)
	updateUC := usecases.NewUpdateProductUseCase(productRepo, logger)
	deleteUC := usecases.NewDeleteProductUseCase(productRepo, logger)
	changeStatusUC := usecases.NewChangeProductStatusUseCase(productRepo, logger)

	productHandler := handlers.NewProductHandler(
		createUC, getListUC, getByIDUC, updateUC, deleteUC, changeStatusUC, logger,
	)

	seedData(productRepo, logger)

	mux := http.NewServeMux()

	// Wrap with logging middleware
	handler := middleware.LoggingMiddleware(logger)(mux)

	// -------------------------------------------------------------------------
	// Routes
	//
	// Go 1.21 net/http has no native {id} params — we dispatch manually.
	//
	//  POST   /api/products              → CreateProduct
	//  GET    /api/products              → GetProducts (list + filters)
	//  GET    /api/products/{id}         → GetProductByID
	//  PUT    /api/products/{id}         → UpdateProduct
	//  DELETE /api/products/{id}         → DeleteProduct
	//  PATCH  /api/products/{id}/status  → ChangeProductStatus
	// -------------------------------------------------------------------------

	mux.HandleFunc("/api/products", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodPost:
			productHandler.CreateProduct(w, r)
		case http.MethodGet:
			productHandler.GetProducts(w, r)
		default:
			http.Error(w, `{"error":"method not allowed"}`, http.StatusMethodNotAllowed)
		}
	})

	mux.HandleFunc("/api/products/", func(w http.ResponseWriter, r *http.Request) {
		// strip "/api/products/" prefix and split remaining path
		tail := strings.TrimPrefix(r.URL.Path, "/api/products/")
		parts := strings.SplitN(tail, "/", 2)
		id := parts[0]

		if id == "" {
			http.Error(w, `{"error":"product ID required"}`, http.StatusBadRequest)
			return
		}

		// /api/products/{id}/status
		if len(parts) == 2 && parts[1] == "status" {
			if r.Method != http.MethodPatch {
				http.Error(w, `{"error":"method not allowed"}`, http.StatusMethodNotAllowed)
				return
			}
			productHandler.ChangeProductStatus(w, r, id)
			return
		}

		// /api/products/{id}
		switch r.Method {
		case http.MethodGet:
			productHandler.GetProductByID(w, r, id)
		case http.MethodPut:
			productHandler.UpdateProduct(w, r, id)
		case http.MethodDelete:
			productHandler.DeleteProduct(w, r, id)
		default:
			http.Error(w, `{"error":"method not allowed"}`, http.StatusMethodNotAllowed)
		}
	})

	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"healthy","service":"product-api"}`))
	})

	mux.Handle("/swagger/", httpSwagger.WrapHandler)

	server := &http.Server{
		Addr:         ":8080",
		Handler:      handler,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	}

	go func() {
		logger.Info("HTTP server starting", map[string]interface{}{"port": 8080})

		fmt.Println("\nServer running on http://localhost:8080")
		fmt.Println("\nAPI Endpoints:")
		fmt.Println("  POST   /api/products              - Create product")
		fmt.Println("  GET    /api/products              - List products (filters + pagination)")
		fmt.Println("  GET    /api/products/{id}         - Get product by ID")
		fmt.Println("  PUT    /api/products/{id}         - Update product")
		fmt.Println("  DELETE /api/products/{id}         - Delete product")
		fmt.Println("  PATCH  /api/products/{id}/status  - Activate / deactivate product")
		fmt.Println("  GET    /health")
		fmt.Println("  GET    /swagger/")
		fmt.Println("\nFilters: ?category=Electronics&min_price=100&max_price=2000&in_stock=true&page=1&page_size=10")
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

func seedData(repo domainRepositories.ProductRepository, logger *logging.EnhancedLogger) {
	ctx := context.Background()
	logger.Info("Seeding demo data...", nil)

	products := []*entities.Product{
		{ID: "1", Name: "Laptop Dell XPS 15", Description: "High performance laptop with 16GB RAM", Price: 1500.00, Category: "Electronics", Stock: 50, Active: true, CreatedAt: time.Now(), UpdatedAt: time.Now()},
		{ID: "2", Name: "iPhone 14 Pro", Description: "Latest iPhone with advanced camera", Price: 1200.00, Category: "Electronics", Stock: 100, Active: true, CreatedAt: time.Now(), UpdatedAt: time.Now()},
		{ID: "3", Name: "Office Chair Ergonomic", Description: "Comfortable ergonomic office chair", Price: 350.00, Category: "Furniture", Stock: 30, Active: true, CreatedAt: time.Now(), UpdatedAt: time.Now()},
		{ID: "4", Name: "Standing Desk", Description: "Adjustable height standing desk", Price: 600.00, Category: "Furniture", Stock: 20, Active: true, CreatedAt: time.Now(), UpdatedAt: time.Now()},
		{ID: "5", Name: "Wireless Mouse", Description: "Ergonomic wireless mouse", Price: 45.00, Category: "Electronics", Stock: 200, Active: true, CreatedAt: time.Now(), UpdatedAt: time.Now()},
	}

	for _, p := range products {
		if err := repo.Create(ctx, p); err != nil {
			logger.Warning("Failed to seed product", map[string]interface{}{"id": p.ID, "error": err.Error()})
		}
	}

	logger.Info("Demo data seeded", map[string]interface{}{"count": len(products)})
}
