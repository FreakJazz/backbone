package commands_test

import (
	"context"
	"testing"

	"github.com/freakjazz/clean-api-go/application/commands"
	"github.com/freakjazz/clean-api-go/domain/entities"
	"github.com/freakjazz/clean-api-go/infrastructure/repositories"
)

func seedProduct(repo *repositories.MemoryProductRepository, name string, price float64, category string) *entities.Product {
	p := entities.NewProduct(name, price, category, "")
	saved, _ := repo.Save(context.Background(), p)
	return saved
}

func TestUpdateProduct_Valid(t *testing.T) {
	repo := newRepo()
	p := seedProduct(repo, "Old Name", 100, "Electronics")
	h := commands.NewUpdateProductCommandHandler(repo)

	newName := "New Name"
	newPrice := 200.0
	id, err := h.Handle(context.Background(), commands.UpdateProductCommand{
		ProductID: p.ID, Name: &newName, Price: &newPrice,
	})
	if err != nil {
		t.Fatalf("expected no error, got %+v", err)
	}
	if id != p.ID {
		t.Fatalf("expected id %s got %s", p.ID, id)
	}
}

func TestUpdateProduct_NotFound(t *testing.T) {
	h := commands.NewUpdateProductCommandHandler(newRepo())
	_, err := h.Handle(context.Background(), commands.UpdateProductCommand{ProductID: "nonexistent"})
	if err == nil || err.StatusCode != 404 {
		t.Fatal("expected 404 not found")
	}
}

func TestUpdateProduct_DuplicateName(t *testing.T) {
	repo := newRepo()
	seedProduct(repo, "Laptop Pro", 999, "Electronics")
	p2 := seedProduct(repo, "Mouse", 29, "Electronics")
	h := commands.NewUpdateProductCommandHandler(repo)

	conflictName := "Laptop Pro"
	_, err := h.Handle(context.Background(), commands.UpdateProductCommand{
		ProductID: p2.ID, Name: &conflictName,
	})
	if err == nil || err.StatusCode != 409 {
		t.Fatalf("expected 409 conflict, got %v", err)
	}
}

func TestUpdateProduct_SameNameAllowed(t *testing.T) {
	repo := newRepo()
	p := seedProduct(repo, "Laptop Pro", 999, "Electronics")
	h := commands.NewUpdateProductCommandHandler(repo)

	sameName := "Laptop Pro"
	_, err := h.Handle(context.Background(), commands.UpdateProductCommand{
		ProductID: p.ID, Name: &sameName,
	})
	if err != nil {
		t.Fatalf("updating with same name should be allowed, got %+v", err)
	}
}
