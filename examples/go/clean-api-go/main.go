// Clean API Go — backbone Clean Architecture + CQRS example, backed by real
// databases: PostgreSQL for the product catalog (consistency-critical
// stock) and MongoDB for sales/stock-movement transaction logs (append-only,
// schema-light).
//
// Setup:
//
//	docker compose -f ../../docker-compose.yml up -d
//	cp .env.example .env
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
//	POST   /api/v1/sales                    — decrements stock (Postgres) + logs sale (Mongo)
//	GET    /api/v1/sales?product_id=...
//	POST   /api/v1/stock-movements          — adjusts stock (Postgres) + logs movement (Mongo)
//	GET    /api/v1/stock-movements?product_id=...
//	GET    /docs/index.html  → Swagger UI

// @title           Clean API Go
// @version         1.0
// @description     backbone — Clean Architecture + CQRS example with net/http, PostgreSQL and MongoDB
// @host            localhost:8005
// @BasePath        /
package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"time"

	// ── Swagger ───────────────────────────────────────────────────────────────
	_ "github.com/freakjazz/clean-api-go/docs"
	"github.com/joho/godotenv"
	httpSwagger "github.com/swaggo/http-swagger"

	// ── Commands ──────────────────────────────────────────────────────────────
	"github.com/freakjazz/clean-api-go/application/commands"
	// ── Queries ───────────────────────────────────────────────────────────────
	"github.com/freakjazz/clean-api-go/application/queries"
	// ── Infrastructure ────────────────────────────────────────────────────────
	"github.com/freakjazz/clean-api-go/infrastructure/database"
	repos "github.com/freakjazz/clean-api-go/infrastructure/repositories"
	"github.com/freakjazz/clean-api-go/infrastructure/seeders"
	// ── HTTP adapters ─────────────────────────────────────────────────────────
	"github.com/freakjazz/clean-api-go/interfaces/http/handlers"
	v1 "github.com/freakjazz/clean-api-go/interfaces/http/v1"
)

func main() {
	_ = godotenv.Load() // optional — falls back to real env vars / defaults if .env is absent

	ctx := context.Background()

	postgresDSN := getEnv("POSTGRES_DSN", "postgres://backbone:backbone@localhost:5433/backbone_products?sslmode=disable")
	mongoURI := getEnv("MONGO_URI", "mongodb://backbone:backbone@localhost:27018")
	mongoDB := getEnv("MONGO_DB", "backbone_transactions")
	port := getEnv("PORT", "8005")

	// 1. PostgreSQL — product catalog
	pgPool, err := database.ConnectPostgres(ctx, postgresDSN)
	if err != nil {
		log.Fatalf("postgres: %v", err)
	}
	defer pgPool.Close()
	if err := database.MigrateProducts(ctx, pgPool); err != nil {
		log.Fatalf("postgres migrate: %v", err)
	}
	log.Println("connected to PostgreSQL:", postgresDSN)

	// 2. MongoDB — sales & stock-movement transaction logs
	mongoClient, err := database.ConnectMongo(ctx, mongoURI)
	if err != nil {
		log.Fatalf("mongo: %v", err)
	}
	defer mongoClient.Disconnect(context.Background()) //nolint:errcheck
	mongoDatabase := mongoClient.Database(mongoDB)
	if err := database.EnsureIndexes(ctx, mongoDatabase); err != nil {
		log.Fatalf("mongo indexes: %v", err)
	}
	log.Println("connected to MongoDB:", mongoURI, "db:", mongoDB)

	// 3. Repositories
	productRepo := repos.NewPostgresProductRepository(pgPool)
	saleRepo := repos.NewMongoSaleRepository(mongoDatabase)
	movementRepo := repos.NewMongoStockMovementRepository(mongoDatabase)

	seedCtx, cancel := context.WithTimeout(ctx, 10*time.Second)
	seeders.NewProductSeeder(productRepo).Run(seedCtx)
	cancel()

	// 4. Commands (write side)
	createCmd := commands.NewCreateProductCommandHandler(productRepo)
	updateCmd := commands.NewUpdateProductCommandHandler(productRepo)
	deleteCmd := commands.NewDeleteProductCommandHandler(productRepo)
	statusCmd := commands.NewChangeProductStatusCommandHandler(productRepo)
	saleCmd := commands.NewRegisterSaleCommandHandler(productRepo, saleRepo)
	movementCmd := commands.NewRegisterStockMovementCommandHandler(productRepo, movementRepo)

	// 5. Queries (read side)
	listQry := queries.NewGetProductsQueryHandler(productRepo)
	pageQry := queries.NewGetProductsPageQueryHandler(productRepo)
	detailQry := queries.NewGetProductByIDQueryHandler(productRepo)
	salesQry := queries.NewGetSalesQueryHandler(saleRepo)
	movementsQry := queries.NewGetStockMovementsQueryHandler(movementRepo)

	// 6. HTTP adapters
	cmdHandler := handlers.NewProductCommandHandler(createCmd, updateCmd, deleteCmd, statusCmd)
	qryHandler := handlers.NewProductQueryHandler(listQry, pageQry, detailQry)
	saleHandler := handlers.NewSaleHandler(saleCmd, salesQry)
	movementHandler := handlers.NewStockMovementHandler(movementCmd, movementsQry)

	// 7. Routes
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

	v1.RegisterRoutes(mux, cmdHandler, qryHandler, saleHandler, movementHandler)

	log.Println("clean-api-go running on :" + port)
	log.Println("  Swagger UI → http://localhost:8005/docs/index.html")
	log.Println("  GET  /api/v1/products?filters=category,eq,Electronics&page=1&page_size=5&sort_by=price:desc")
	log.Println("  POST /api/v1/sales             {\"product_id\":\"...\",\"quantity\":2}")
	log.Println("  POST /api/v1/stock-movements   {\"product_id\":\"...\",\"type\":\"IN\",\"quantity\":10,\"reason\":\"restock\"}")
	if err := http.ListenAndServe(":"+port, mux); err != nil {
		log.Fatal(err)
	}
}

func getEnv(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}
