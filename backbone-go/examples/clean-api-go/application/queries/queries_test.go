package queries_test

import (
	"context"
	"testing"

	"github.com/freakjazz/backbone-go/examples/clean-api-go/application/queries"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/entities"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/infrastructure/repositories"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// helpers ──────────────────────────────────────────────────────────────────────

func newRepo() *repositories.MemoryProductRepository {
	logger := logging.NewEnhancedLogger("test")
	return repositories.NewMemoryProductRepository(logger).(*repositories.MemoryProductRepository)
}

func newLogger() *logging.EnhancedLogger {
	return logging.NewEnhancedLogger("test")
}

func seed(t *testing.T, repo *repositories.MemoryProductRepository, products ...*entities.Product) {
	t.Helper()
	for _, p := range products {
		require.NoError(t, repo.Create(context.Background(), p))
	}
}

func newProduct(id, name, category string, price float64, stock int, active bool) *entities.Product {
	return &entities.Product{
		ID: id, Name: name, Category: category,
		Price: price, Stock: stock, Active: active,
	}
}

// ── GetProductByIDQueryHandler ─────────────────────────────────────────────────

func TestGetProductByID_Found(t *testing.T) {
	repo := newRepo()
	seed(t, repo, newProduct("p1", "Laptop", "Electronics", 1500, 50, true))
	h := queries.NewGetProductByIDQueryHandler(repo, newLogger())

	result, err := h.Handle(context.Background(), queries.GetProductByIDQuery{ID: "p1"})

	require.NoError(t, err)
	require.NotNil(t, result)
	assert.Equal(t, "p1", result.Product.ID)
	assert.Equal(t, "Laptop", result.Product.Name)
}

func TestGetProductByID_NotFound(t *testing.T) {
	h := queries.NewGetProductByIDQueryHandler(newRepo(), newLogger())
	_, err := h.Handle(context.Background(), queries.GetProductByIDQuery{ID: "nonexistent"})
	require.Error(t, err)
}

func TestGetProductByID_EmptyID(t *testing.T) {
	h := queries.NewGetProductByIDQueryHandler(newRepo(), newLogger())
	_, err := h.Handle(context.Background(), queries.GetProductByIDQuery{})
	require.Error(t, err)
	assert.Contains(t, err.Error(), "ID")
}

// ── GetProductsQueryHandler ────────────────────────────────────────────────────

func TestGetProducts_AllResults(t *testing.T) {
	repo := newRepo()
	seed(t, repo,
		newProduct("p1", "Laptop",  "Electronics", 1500, 50, true),
		newProduct("p2", "Mouse",   "Electronics", 45,   200, true),
		newProduct("p3", "Chair",   "Furniture",   350,  30, true),
	)
	h := queries.NewGetProductsQueryHandler(repo, newLogger())

	result, err := h.Handle(context.Background(), queries.GetProductsQuery{
		Page: 1, PageSize: 10,
	})

	require.NoError(t, err)
	assert.Equal(t, int64(3), result.TotalCount)
	assert.Len(t, result.Products, 3)
}

func TestGetProducts_FilterByCategory(t *testing.T) {
	repo := newRepo()
	seed(t, repo,
		newProduct("p1", "Laptop", "Electronics", 1500, 50, true),
		newProduct("p2", "Chair",  "Furniture",   350,  30, true),
		newProduct("p3", "Mouse",  "Electronics", 45,   200, true),
	)
	h := queries.NewGetProductsQueryHandler(repo, newLogger())

	result, err := h.Handle(context.Background(), queries.GetProductsQuery{
		Filters:  []string{"category,eq,Electronics"},
		Page:     1,
		PageSize: 10,
	})

	require.NoError(t, err)
	assert.Equal(t, int64(2), result.TotalCount)
	for _, p := range result.Products {
		assert.Equal(t, "Electronics", p.Category)
	}
}

func TestGetProducts_FilterByPriceGt(t *testing.T) {
	repo := newRepo()
	seed(t, repo,
		newProduct("p1", "Laptop", "Electronics", 1500, 50, true),
		newProduct("p2", "Mouse",  "Electronics", 45,   200, true),
		newProduct("p3", "Chair",  "Furniture",   350,  30, true),
	)
	h := queries.NewGetProductsQueryHandler(repo, newLogger())

	result, err := h.Handle(context.Background(), queries.GetProductsQuery{
		Filters:  []string{"price,gt,100"},
		Page:     1,
		PageSize: 10,
	})

	require.NoError(t, err)
	assert.Equal(t, int64(2), result.TotalCount)
	for _, p := range result.Products {
		assert.Greater(t, p.Price, 100.0)
	}
}

func TestGetProducts_FilterBetween(t *testing.T) {
	repo := newRepo()
	seed(t, repo,
		newProduct("p1", "Laptop", "Electronics", 1500, 50, true),
		newProduct("p2", "Mouse",  "Electronics", 45,   200, true),
		newProduct("p3", "Chair",  "Furniture",   350,  30, true),
	)
	h := queries.NewGetProductsQueryHandler(repo, newLogger())

	result, err := h.Handle(context.Background(), queries.GetProductsQuery{
		Filters:  []string{"price,between,100|1000"},
		Page:     1,
		PageSize: 10,
	})

	require.NoError(t, err)
	assert.Equal(t, int64(1), result.TotalCount)
	assert.Equal(t, 350.0, result.Products[0].Price)
}

func TestGetProducts_MultipleFiltersAnd(t *testing.T) {
	repo := newRepo()
	seed(t, repo,
		newProduct("p1", "Laptop",   "Electronics", 1500, 50, true),
		newProduct("p2", "Mouse",    "Electronics", 45,   200, true),
		newProduct("p3", "Keyboard", "Electronics", 80,   150, true),
		newProduct("p4", "Chair",    "Furniture",   350,  30, true),
	)
	h := queries.NewGetProductsQueryHandler(repo, newLogger())

	result, err := h.Handle(context.Background(), queries.GetProductsQuery{
		Filters:  []string{"category,eq,Electronics,and", "price,gt,50,and"},
		Page:     1,
		PageSize: 10,
	})

	require.NoError(t, err)
	// Laptop (1500) + Keyboard (80) — Mouse (45) excluded
	assert.Equal(t, int64(2), result.TotalCount)
}

func TestGetProducts_EmptyFilters_ReturnsAll(t *testing.T) {
	repo := newRepo()
	seed(t, repo,
		newProduct("p1", "A", "Cat", 10, 1, true),
		newProduct("p2", "B", "Cat", 20, 2, true),
	)
	h := queries.NewGetProductsQueryHandler(repo, newLogger())

	result, err := h.Handle(context.Background(), queries.GetProductsQuery{
		Page: 1, PageSize: 10,
	})

	require.NoError(t, err)
	assert.Equal(t, int64(2), result.TotalCount)
}

func TestGetProducts_Pagination(t *testing.T) {
	repo := newRepo()
	for i := 1; i <= 15; i++ {
		id := string(rune('a' + i - 1))
		seed(t, repo, newProduct(id, "Product "+id, "Cat", float64(i*10), i, true))
	}
	h := queries.NewGetProductsQueryHandler(repo, newLogger())

	// Page 1
	r1, err := h.Handle(context.Background(), queries.GetProductsQuery{Page: 1, PageSize: 5})
	require.NoError(t, err)
	assert.Len(t, r1.Products, 5)
	assert.Equal(t, int64(15), r1.TotalCount)

	// Page 2
	r2, err := h.Handle(context.Background(), queries.GetProductsQuery{Page: 2, PageSize: 5})
	require.NoError(t, err)
	assert.Len(t, r2.Products, 5)

	// Page 3 (last, 5 items)
	r3, err := h.Handle(context.Background(), queries.GetProductsQuery{Page: 3, PageSize: 5})
	require.NoError(t, err)
	assert.Len(t, r3.Products, 5)
}

func TestGetProducts_PageSizeDefaultsTo10(t *testing.T) {
	repo := newRepo()
	for i := 1; i <= 20; i++ {
		id := string(rune('a' + i - 1))
		seed(t, repo, newProduct(id, "P"+id, "Cat", float64(i), i, true))
	}
	h := queries.NewGetProductsQueryHandler(repo, newLogger())

	// PageSize 0 → defaults to 10
	result, err := h.Handle(context.Background(), queries.GetProductsQuery{Page: 1, PageSize: 0})
	require.NoError(t, err)
	assert.Len(t, result.Products, 10)
}

func TestGetProducts_PageSizeCappedAt100(t *testing.T) {
	repo := newRepo()
	for i := 1; i <= 5; i++ {
		id := string(rune('a' + i - 1))
		seed(t, repo, newProduct(id, "P"+id, "Cat", float64(i), i, true))
	}
	h := queries.NewGetProductsQueryHandler(repo, newLogger())

	result, err := h.Handle(context.Background(), queries.GetProductsQuery{Page: 1, PageSize: 500})
	require.NoError(t, err)
	assert.Equal(t, 100, result.PageSize)
}

func TestGetProducts_SortBy(t *testing.T) {
	repo := newRepo()
	seed(t, repo,
		newProduct("p1", "A-Laptop", "Electronics", 1500, 50, true),
		newProduct("p2", "C-Mouse",  "Electronics", 45,   200, true),
		newProduct("p3", "B-Chair",  "Furniture",   350,  30, true),
	)
	h := queries.NewGetProductsQueryHandler(repo, newLogger())

	result, err := h.Handle(context.Background(), queries.GetProductsQuery{
		Page: 1, PageSize: 10, SortBy: "price:asc",
	})

	require.NoError(t, err)
	require.Len(t, result.Products, 3)
	assert.Equal(t, 45.0, result.Products[0].Price)
	assert.Equal(t, 350.0, result.Products[1].Price)
	assert.Equal(t, 1500.0, result.Products[2].Price)
}

func TestGetProducts_EmptyRepository(t *testing.T) {
	h := queries.NewGetProductsQueryHandler(newRepo(), newLogger())
	result, err := h.Handle(context.Background(), queries.GetProductsQuery{Page: 1, PageSize: 10})
	require.NoError(t, err)
	assert.Equal(t, int64(0), result.TotalCount)
	assert.Empty(t, result.Products)
}
