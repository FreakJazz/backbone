package commands_test

import (
	"context"
	"testing"

	"github.com/freakjazz/backbone-go/examples/clean-api-go/application/commands"
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

func seedProduct(t *testing.T, repo *repositories.MemoryProductRepository, id string) *entities.Product {
	t.Helper()
	p := &entities.Product{
		ID: id, Name: "Laptop Dell", Description: "16GB RAM",
		Price: 1500, Category: "Electronics", Stock: 50, Active: true,
	}
	require.NoError(t, repo.Create(context.Background(), p))
	return p
}

// ── CreateProductCommandHandler ───────────────────────────────────────────────

func TestCreateProduct_Success(t *testing.T) {
	repo := newRepo()
	h := commands.NewCreateProductCommandHandler(repo, newLogger())

	result, err := h.Handle(context.Background(), commands.CreateProductCommand{
		Name: "Wireless Mouse", Description: "Ergonomic", Price: 45.0, Category: "Electronics", Stock: 100,
	})

	require.NoError(t, err)
	require.NotNil(t, result)
	assert.NotEmpty(t, result.ProductID)

	// verify it was actually persisted
	saved, err := repo.FindByID(context.Background(), result.ProductID)
	require.NoError(t, err)
	assert.Equal(t, "Wireless Mouse", saved.Name)
	assert.Equal(t, 45.0, saved.Price)
}

func TestCreateProduct_MissingName(t *testing.T) {
	h := commands.NewCreateProductCommandHandler(newRepo(), newLogger())
	_, err := h.Handle(context.Background(), commands.CreateProductCommand{
		Price: 100, Category: "Electronics", Stock: 10,
	})
	require.Error(t, err)
	assert.Contains(t, err.Error(), "name")
}

func TestCreateProduct_MissingCategory(t *testing.T) {
	h := commands.NewCreateProductCommandHandler(newRepo(), newLogger())
	_, err := h.Handle(context.Background(), commands.CreateProductCommand{
		Name: "Item", Price: 100, Stock: 10,
	})
	require.Error(t, err)
	assert.Contains(t, err.Error(), "category")
}

func TestCreateProduct_InvalidPrice(t *testing.T) {
	h := commands.NewCreateProductCommandHandler(newRepo(), newLogger())
	_, err := h.Handle(context.Background(), commands.CreateProductCommand{
		Name: "Item", Category: "Electronics", Price: -10, Stock: 10,
	})
	require.Error(t, err)
}

func TestCreateProduct_NegativeStock(t *testing.T) {
	h := commands.NewCreateProductCommandHandler(newRepo(), newLogger())
	_, err := h.Handle(context.Background(), commands.CreateProductCommand{
		Name: "Item", Category: "Electronics", Price: 10, Stock: -1,
	})
	require.Error(t, err)
	assert.Contains(t, err.Error(), "stock")
}

func TestCreateProduct_ZeroStock_IsAllowed(t *testing.T) {
	h := commands.NewCreateProductCommandHandler(newRepo(), newLogger())
	result, err := h.Handle(context.Background(), commands.CreateProductCommand{
		Name: "Out-of-Stock Item", Category: "Electronics", Price: 10, Stock: 0,
	})
	require.NoError(t, err)
	assert.NotEmpty(t, result.ProductID)
}

// ── UpdateProductCommandHandler ───────────────────────────────────────────────

func TestUpdateProduct_Success(t *testing.T) {
	repo := newRepo()
	seedProduct(t, repo, "p1")
	h := commands.NewUpdateProductCommandHandler(repo, newLogger())

	result, err := h.Handle(context.Background(), commands.UpdateProductCommand{
		ID: "p1", Name: "Laptop Updated", Price: 1200,
	})

	require.NoError(t, err)
	assert.Equal(t, "p1", result.ProductID)

	updated, _ := repo.FindByID(context.Background(), "p1")
	assert.Equal(t, "Laptop Updated", updated.Name)
	assert.Equal(t, 1200.0, updated.Price)
}

func TestUpdateProduct_PartialUpdate(t *testing.T) {
	repo := newRepo()
	seedProduct(t, repo, "p1")
	h := commands.NewUpdateProductCommandHandler(repo, newLogger())

	_, err := h.Handle(context.Background(), commands.UpdateProductCommand{
		ID: "p1", Stock: 99,
	})
	require.NoError(t, err)

	updated, _ := repo.FindByID(context.Background(), "p1")
	assert.Equal(t, 99, updated.Stock)
	assert.Equal(t, "Laptop Dell", updated.Name) // unchanged
}

func TestUpdateProduct_NotFound(t *testing.T) {
	h := commands.NewUpdateProductCommandHandler(newRepo(), newLogger())
	_, err := h.Handle(context.Background(), commands.UpdateProductCommand{ID: "nonexistent"})
	require.Error(t, err)
	assert.Contains(t, err.Error(), "not found")
}

func TestUpdateProduct_MissingID(t *testing.T) {
	h := commands.NewUpdateProductCommandHandler(newRepo(), newLogger())
	_, err := h.Handle(context.Background(), commands.UpdateProductCommand{})
	require.Error(t, err)
	assert.Contains(t, err.Error(), "ID")
}

func TestUpdateProduct_InvalidPrice(t *testing.T) {
	repo := newRepo()
	seedProduct(t, repo, "p1")
	h := commands.NewUpdateProductCommandHandler(repo, newLogger())

	_, err := h.Handle(context.Background(), commands.UpdateProductCommand{
		ID: "p1", Price: -5,
	})
	require.Error(t, err)
}

// ── DeleteProductCommandHandler ───────────────────────────────────────────────

func TestDeleteProduct_Success(t *testing.T) {
	repo := newRepo()
	seedProduct(t, repo, "p1")
	h := commands.NewDeleteProductCommandHandler(repo, newLogger())

	err := h.Handle(context.Background(), commands.DeleteProductCommand{ID: "p1"})
	require.NoError(t, err)

	exists, _ := repo.ExistsByID(context.Background(), "p1")
	assert.False(t, exists)
}

func TestDeleteProduct_NotFound(t *testing.T) {
	h := commands.NewDeleteProductCommandHandler(newRepo(), newLogger())
	err := h.Handle(context.Background(), commands.DeleteProductCommand{ID: "nonexistent"})
	require.Error(t, err)
	assert.Contains(t, err.Error(), "not found")
}

func TestDeleteProduct_MissingID(t *testing.T) {
	h := commands.NewDeleteProductCommandHandler(newRepo(), newLogger())
	err := h.Handle(context.Background(), commands.DeleteProductCommand{})
	require.Error(t, err)
	assert.Contains(t, err.Error(), "ID")
}

// ── ChangeProductStatusCommandHandler ────────────────────────────────────────

func TestChangeProductStatus_Deactivate(t *testing.T) {
	repo := newRepo()
	seedProduct(t, repo, "p1")
	h := commands.NewChangeProductStatusCommandHandler(repo, newLogger())

	err := h.Handle(context.Background(), commands.ChangeProductStatusCommand{ID: "p1", Active: false})
	require.NoError(t, err)

	p, _ := repo.FindByID(context.Background(), "p1")
	assert.False(t, p.Active)
}

func TestChangeProductStatus_Reactivate(t *testing.T) {
	repo := newRepo()
	p := seedProduct(t, repo, "p1")
	p.Active = false
	repo.Update(context.Background(), p)

	h := commands.NewChangeProductStatusCommandHandler(repo, newLogger())
	err := h.Handle(context.Background(), commands.ChangeProductStatusCommand{ID: "p1", Active: true})
	require.NoError(t, err)

	updated, _ := repo.FindByID(context.Background(), "p1")
	assert.True(t, updated.Active)
}

func TestChangeProductStatus_NotFound(t *testing.T) {
	h := commands.NewChangeProductStatusCommandHandler(newRepo(), newLogger())
	err := h.Handle(context.Background(), commands.ChangeProductStatusCommand{ID: "nonexistent", Active: false})
	require.Error(t, err)
}

func TestChangeProductStatus_MissingID(t *testing.T) {
	h := commands.NewChangeProductStatusCommandHandler(newRepo(), newLogger())
	err := h.Handle(context.Background(), commands.ChangeProductStatusCommand{})
	require.Error(t, err)
	assert.Contains(t, err.Error(), "ID")
}
