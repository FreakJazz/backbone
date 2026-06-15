package queries_test

import (
	"context"
	"testing"

	"github.com/freakjazz/clean-api-go/application/queries"
	"github.com/freakjazz/clean-api-go/domain/entities"
	"github.com/freakjazz/clean-api-go/infrastructure/repositories"
)

func TestGetProductByID_Found(t *testing.T) {
	repo := repositories.NewMemoryProductRepository()
	p := entities.NewProduct("Laptop", 999, "Electronics", "")
	repo.Save(context.Background(), p) //nolint

	h := queries.NewGetProductByIDQueryHandler(repo)
	data, err := h.Handle(context.Background(), queries.GetProductByIDQuery{ProductID: p.ID})
	if err != nil {
		t.Fatalf("expected no error, got %+v", err)
	}
	if data["id"] != p.ID {
		t.Fatalf("expected id %s, got %v", p.ID, data["id"])
	}
	if data["name"] != "Laptop" {
		t.Fatalf("expected name Laptop, got %v", data["name"])
	}
}

func TestGetProductByID_NotFound(t *testing.T) {
	h := queries.NewGetProductByIDQueryHandler(repositories.NewMemoryProductRepository())
	_, err := h.Handle(context.Background(), queries.GetProductByIDQuery{ProductID: "nonexistent"})
	if err == nil || err.StatusCode != 404 {
		t.Fatal("expected 404 not found")
	}
}
