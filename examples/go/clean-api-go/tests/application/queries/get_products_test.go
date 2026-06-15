package queries_test

import (
	"context"
	"testing"

	"github.com/freakjazz/clean-api-go/application/queries"
	"github.com/freakjazz/clean-api-go/domain/entities"
	"github.com/freakjazz/clean-api-go/infrastructure/repositories"
)

func seedRepo() *repositories.MemoryProductRepository {
	repo := repositories.NewMemoryProductRepository()
	ctx := context.Background()
	products := []*entities.Product{
		entities.NewProduct("Laptop Pro", 1500, "Electronics", ""),
		entities.NewProduct("Monitor 4K", 699, "Electronics", ""),
		entities.NewProduct("Standing Desk", 450, "Furniture", ""),
		entities.NewProduct("Coffee Mug", 12, "Kitchen", ""),
		entities.NewProduct("USB Hub", 35, "Electronics", ""),
	}
	for _, p := range products {
		repo.Save(ctx, p) //nolint
	}
	return repo
}

func TestGetProducts_All(t *testing.T) {
	h := queries.NewGetProductsQueryHandler(seedRepo())
	result, err := h.Handle(context.Background(), queries.GetProductsQuery{Page: 1, PageSize: 10})
	if err != nil {
		t.Fatalf("unexpected error: %+v", err)
	}
	if result.TotalCount != 5 {
		t.Fatalf("expected 5 items, got %d", result.TotalCount)
	}
}

func TestGetProducts_FilterByCategory(t *testing.T) {
	h := queries.NewGetProductsQueryHandler(seedRepo())
	result, err := h.Handle(context.Background(), queries.GetProductsQuery{
		Filters:  []string{"category,eq,Electronics"},
		Page:     1,
		PageSize: 10,
	})
	if err != nil {
		t.Fatalf("unexpected error: %+v", err)
	}
	if result.TotalCount != 3 {
		t.Fatalf("expected 3 Electronics, got %d", result.TotalCount)
	}
}

func TestGetProducts_MultipleFilters(t *testing.T) {
	h := queries.NewGetProductsQueryHandler(seedRepo())
	// Electronics AND price > 500
	result, err := h.Handle(context.Background(), queries.GetProductsQuery{
		Filters:  []string{"category,eq,Electronics,and", "price,gt,500"},
		Page:     1,
		PageSize: 10,
	})
	if err != nil {
		t.Fatalf("unexpected error: %+v", err)
	}
	if result.TotalCount != 2 { // Laptop 1500 + Monitor 699
		t.Fatalf("expected 2, got %d", result.TotalCount)
	}
}

func TestGetProducts_Pagination(t *testing.T) {
	h := queries.NewGetProductsQueryHandler(seedRepo())
	result, err := h.Handle(context.Background(), queries.GetProductsQuery{Page: 1, PageSize: 2})
	if err != nil {
		t.Fatalf("unexpected error: %+v", err)
	}
	if len(result.Items) != 2 {
		t.Fatalf("expected page of 2, got %d", len(result.Items))
	}
	if result.TotalCount != 5 {
		t.Fatalf("expected total 5, got %d", result.TotalCount)
	}
}

func TestGetProducts_SortByPriceDesc(t *testing.T) {
	h := queries.NewGetProductsQueryHandler(seedRepo())
	result, err := h.Handle(context.Background(), queries.GetProductsQuery{
		SortBy: "price:desc", Page: 1, PageSize: 10,
	})
	if err != nil {
		t.Fatalf("unexpected error: %+v", err)
	}
	items := result.Items
	if len(items) < 2 {
		t.Fatal("expected multiple items")
	}
	first := items[0]["price"].(float64)
	second := items[1]["price"].(float64)
	if first < second {
		t.Fatalf("expected descending price: first=%.2f second=%.2f", first, second)
	}
}
