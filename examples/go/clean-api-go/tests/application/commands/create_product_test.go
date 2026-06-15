package commands_test

import (
	"context"
	"testing"

	"github.com/freakjazz/clean-api-go/application/commands"
	"github.com/freakjazz/clean-api-go/infrastructure/repositories"
)

func newRepo() *repositories.MemoryProductRepository {
	return repositories.NewMemoryProductRepository()
}

func TestCreateProduct_Valid(t *testing.T) {
	h := commands.NewCreateProductCommandHandler(newRepo())
	id, err := h.Handle(context.Background(), commands.CreateProductCommand{
		Name: "Laptop Pro", Price: 999.99, Category: "Electronics",
	})
	if err != nil {
		t.Fatalf("expected no error, got %+v", err)
	}
	if id == "" {
		t.Fatal("expected non-empty id")
	}
}

func TestCreateProduct_ShortName(t *testing.T) {
	h := commands.NewCreateProductCommandHandler(newRepo())
	_, err := h.Handle(context.Background(), commands.CreateProductCommand{
		Name: "X", Price: 10, Category: "A",
	})
	if err == nil {
		t.Fatal("expected validation error")
	}
	if err.StatusCode != 400 {
		t.Fatalf("expected 400 got %d", err.StatusCode)
	}
}

func TestCreateProduct_NegativePrice(t *testing.T) {
	h := commands.NewCreateProductCommandHandler(newRepo())
	_, err := h.Handle(context.Background(), commands.CreateProductCommand{
		Name: "Valid Name", Price: -1, Category: "A",
	})
	if err == nil || err.StatusCode != 400 {
		t.Fatal("expected 400 validation error for negative price")
	}
}

func TestCreateProduct_EmptyCategory(t *testing.T) {
	h := commands.NewCreateProductCommandHandler(newRepo())
	_, err := h.Handle(context.Background(), commands.CreateProductCommand{
		Name: "Valid Name", Price: 10, Category: "",
	})
	if err == nil || err.StatusCode != 400 {
		t.Fatal("expected 400 validation error for empty category")
	}
}

func TestCreateProduct_DuplicateName(t *testing.T) {
	repo := newRepo()
	h := commands.NewCreateProductCommandHandler(repo)
	ctx := context.Background()

	_, err := h.Handle(ctx, commands.CreateProductCommand{
		Name: "Laptop Pro", Price: 999, Category: "Electronics",
	})
	if err != nil {
		t.Fatalf("first create failed: %+v", err)
	}

	_, err = h.Handle(ctx, commands.CreateProductCommand{
		Name: "Laptop Pro", Price: 500, Category: "Electronics",
	})
	if err == nil {
		t.Fatal("expected conflict error for duplicate name")
	}
	if err.StatusCode != 409 {
		t.Fatalf("expected 409 got %d: %s", err.StatusCode, err.Message)
	}
}

func TestCreateProduct_DuplicateNameCaseInsensitive(t *testing.T) {
	repo := newRepo()
	h := commands.NewCreateProductCommandHandler(repo)
	ctx := context.Background()

	h.Handle(ctx, commands.CreateProductCommand{Name: "laptop pro", Price: 999, Category: "A"}) //nolint

	_, err := h.Handle(ctx, commands.CreateProductCommand{Name: "LAPTOP PRO", Price: 500, Category: "A"})
	if err == nil || err.StatusCode != 409 {
		t.Fatal("expected 409 conflict for case-insensitive duplicate name")
	}
}
