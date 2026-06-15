// Clean API Go — backbone Clean Architecture + CQRS example.
//
// Setup:
//
//	go mod tidy
//	swag init
//	go run main.go
//
// Endpoints:
//
//	GET    /api/v1/products
//	GET    /api/v1/products/{id}
//	POST   /api/v1/products
//	PUT    /api/v1/products/{id}
//	DELETE /api/v1/products/{id}
//	PATCH  /api/v1/products/{id}/status
//	GET    /docs/index.html  → Swagger UI

// @title           Clean API Go
// @version         1.0
// @description     backbone — Clean Architecture + CQRS example with net/http
// @host            localhost:8005
// @BasePath        /
package main

import (
	"context"
	"log"
	"net/http"

	// ── Swagger ───────────────────────────────────────────────────────────────
	_ "github.com/freakjazz/clean-api-go/docs"
	httpSwagger "github.com/swaggo/http-swagger"

	// ── Commands ──────────────────────────────────────────────────────────────
	"github.com/freakjazz/clean-api-go/application/commands"
	// ── Queries ───────────────────────────────────────────────────────────────
	"github.com/freakjazz/clean-api-go/application/queries"
	// ── Infrastructure ────────────────────────────────────────────────────────
	memrepo "github.com/freakjazz/clean-api-go/infrastructure/repositories"
	"github.com/freakjazz/clean-api-go/infrastructure/seeders"
	// ── HTTP adapters ─────────────────────────────────────────────────────────
	"github.com/freakjazz/clean-api-go/interfaces/http/handlers"
	v1 "github.com/freakjazz/clean-api-go/interfaces/http/v1"
)

func main() {
	ctx := context.Background()

	// 1. Infrastructure
	repo := memrepo.NewMemoryProductRepository()
	seeders.NewProductSeeder(repo).Run(ctx)

	// 2. Commands (write side)
	createCmd := commands.NewCreateProductCommandHandler(repo)
	updateCmd := commands.NewUpdateProductCommandHandler(repo)
	deleteCmd := commands.NewDeleteProductCommandHandler(repo)
	statusCmd := commands.NewChangeProductStatusCommandHandler(repo)

	// 3. Queries (read side)
	listQry   := queries.NewGetProductsQueryHandler(repo)
	detailQry := queries.NewGetProductByIDQueryHandler(repo)

	// 4. HTTP adapters
	cmdHandler := handlers.NewProductCommandHandler(createCmd, updateCmd, deleteCmd, statusCmd)
	qryHandler := handlers.NewProductQueryHandler(listQry, detailQry)

	// 5. Routes
	mux := http.NewServeMux()

	// Swagger UI
	mux.HandleFunc("/docs/", httpSwagger.WrapHandler)

	// Root info
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/" {
			http.NotFound(w, r)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"service":"clean-api-go","docs":"http://localhost:8005/docs/index.html","api":"/api/v1/products"}`))
	})

	v1.RegisterRoutes(mux, cmdHandler, qryHandler)

	log.Println("clean-api-go running on :8005")
	log.Println("  Swagger UI → http://localhost:8005/docs/index.html")
	log.Println("  GET  /api/v1/products?filters=category,eq,Electronics&page=1&page_size=5&sort_by=price:desc")
	if err := http.ListenAndServe(":8005", mux); err != nil {
		log.Fatal(err)
	}
}
