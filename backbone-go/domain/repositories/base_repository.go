// Package repositories defines domain repository contracts
package repositories

import (
	"context"
)

// IRepository defines the base repository contract
type IRepository interface {
	// Add adds a new entity
	Add(ctx context.Context, entity interface{}) error

	// Update updates an existing entity
	Update(ctx context.Context, entity interface{}) error

	// Remove removes an entity
	Remove(ctx context.Context, entity interface{}) error

	// RemoveByID removes an entity by ID
	RemoveByID(ctx context.Context, id interface{}) error
}

// IReadOnlyRepository defines read-only repository operations
type IReadOnlyRepository interface {
	// FindByID finds an entity by ID
	FindByID(ctx context.Context, id interface{}) (interface{}, error)

	// FindAll finds all entities
	FindAll(ctx context.Context) ([]interface{}, error)

	// Count counts all entities
	Count(ctx context.Context) (int64, error)

	// Exists checks if an entity exists
	Exists(ctx context.Context, id interface{}) (bool, error)
}

// IUnitOfWork defines the unit of work pattern
type IUnitOfWork interface {
	// Begin starts a new transaction
	Begin(ctx context.Context) error

	// Commit commits the current transaction
	Commit(ctx context.Context) error

	// Rollback rolls back the current transaction
	Rollback(ctx context.Context) error

	// IsActive checks if there's an active transaction
	IsActive() bool

	// SaveChanges persists all changes
	SaveChanges(ctx context.Context) error
}

// IQueryBuilder defines query building capabilities
type IQueryBuilder interface {
	// Where adds a where condition
	Where(field string, operator string, value interface{}) IQueryBuilder

	// OrderBy adds ordering
	OrderBy(field string, ascending bool) IQueryBuilder

	// Limit sets the limit
	Limit(limit int) IQueryBuilder

	// Offset sets the offset
	Offset(offset int) IQueryBuilder

	// Execute executes the query
	Execute(ctx context.Context) ([]interface{}, error)

	// Count counts the results
	Count(ctx context.Context) (int64, error)
}

// RepositoryBase provides common repository functionality
type RepositoryBase struct {
	EntityType string
}

// NewRepositoryBase creates a new repository base
func NewRepositoryBase(entityType string) *RepositoryBase {
	return &RepositoryBase{
		EntityType: entityType,
	}
}
