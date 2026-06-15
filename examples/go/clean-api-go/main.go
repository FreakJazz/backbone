// Clean API Go — backbone Clean Architecture + CQRS example.
//
// Setup:
//
//	go mod tidy
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
package main

import (
	"context"
	"log"
	"net/http"

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
	v1.RegisterRoutes(mux, cmdHandler, qryHandler)

	log.Println("clean-api-go running on :8080")
	log.Println("  GET  /api/v1/products?filters=category,eq,Electronics&page=1&page_size=5&sort_by=price:desc")
	if err := http.ListenAndServe(":8080", mux); err != nil {
		log.Fatal(err)
	}
}
