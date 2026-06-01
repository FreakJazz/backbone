// Package repositories defines domain repository interfaces
package repositories

import (
	"context"

	"github.com/freakjazz/backbone-go/domain/specifications"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/entities"
)

// ProductRepository defines the contract for product persistence
type ProductRepository interface {
	// Create creates a new product
	Create(ctx context.Context, product *entities.Product) error

	// FindByID finds a product by ID
	FindByID(ctx context.Context, id string) (*entities.Product, error)

	// FindAll finds all products
	FindAll(ctx context.Context) ([]*entities.Product, error)

	// FindByCriteria finds products matching criteria with Specification Pattern
	FindByCriteria(ctx context.Context, criteria *specifications.Criteria) ([]*entities.Product, error)

	// Count counts products matching criteria
	Count(ctx context.Context, criteria *specifications.Criteria) (int64, error)

	// Update updates a product
	Update(ctx context.Context, product *entities.Product) error

	// Delete deletes a product by ID
	Delete(ctx context.Context, id string) error

	// ExistsByID checks if a product exists
	ExistsByID(ctx context.Context, id string) (bool, error)
}
