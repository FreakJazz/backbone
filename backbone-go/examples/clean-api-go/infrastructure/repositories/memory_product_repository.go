// Package repositories contains infrastructure repository implementations
package repositories

import (
	"context"
	"fmt"
	"reflect"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/freakjazz/backbone-go/domain/specifications"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/entities"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/repositories"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
)

const errProductNotFound = "product not found"

// MemoryProductRepository implements ProductRepository using in-memory storage
type MemoryProductRepository struct {
	products map[string]*entities.Product
	mu       sync.RWMutex
	logger   *logging.EnhancedLogger
}

// NewMemoryProductRepository creates a new in-memory repository
func NewMemoryProductRepository(logger *logging.EnhancedLogger) repositories.ProductRepository {
	return &MemoryProductRepository{
		products: make(map[string]*entities.Product),
		logger:   logger,
	}
}

// Create creates a new product
func (r *MemoryProductRepository) Create(ctx context.Context, product *entities.Product) error {
	repoLogger := r.logger.
		WithLayer("infrastructure").
		WithComponent("MemoryProductRepository").
		WithMethod("Create")

	start := time.Now()

	r.mu.Lock()
	defer r.mu.Unlock()

	if _, exists := r.products[product.ID]; exists {
		duration := time.Since(start).Milliseconds()
		repoLogger.ErrorWithCode("Product already exists", 12001001, map[string]interface{}{
			"product_id":  product.ID,
			"duration_ms": duration,
		})
		return fmt.Errorf("product with ID %s already exists", product.ID)
	}

	r.products[product.ID] = product

	duration := time.Since(start).Milliseconds()
	repoLogger.Info("Product created", map[string]interface{}{
		"product_id":  product.ID,
		"duration_ms": duration,
	})

	return nil
}

// FindByID finds a product by ID
func (r *MemoryProductRepository) FindByID(ctx context.Context, id string) (*entities.Product, error) {
	repoLogger := r.logger.
		WithLayer("infrastructure").
		WithComponent("MemoryProductRepository").
		WithMethod("FindByID")

	start := time.Now()

	r.mu.RLock()
	defer r.mu.RUnlock()

	product, exists := r.products[id]
	duration := time.Since(start).Milliseconds()

	if !exists {
		repoLogger.Warning("Product not found", map[string]interface{}{
			"product_id":  id,
			"duration_ms": duration,
		})
		return nil, fmt.Errorf(errProductNotFound)
	}

	repoLogger.Debug("Product found", map[string]interface{}{
		"product_id":  id,
		"duration_ms": duration,
	})

	return product, nil
}

// FindAll finds all products
func (r *MemoryProductRepository) FindAll(ctx context.Context) ([]*entities.Product, error) {
	repoLogger := r.logger.
		WithLayer("infrastructure").
		WithComponent("MemoryProductRepository").
		WithMethod("FindAll")

	start := time.Now()

	r.mu.RLock()
	defer r.mu.RUnlock()

	products := make([]*entities.Product, 0, len(r.products))
	for _, product := range r.products {
		products = append(products, product)
	}

	duration := time.Since(start).Milliseconds()
	repoLogger.Info("All products retrieved", map[string]interface{}{
		"count":       len(products),
		"duration_ms": duration,
	})

	return products, nil
}

// FindByCriteria finds products matching criteria with Specification Pattern
func (r *MemoryProductRepository) FindByCriteria(ctx context.Context, criteria *specifications.Criteria) ([]*entities.Product, error) {
	repoLogger := r.logger.
		WithLayer("infrastructure").
		WithComponent("MemoryProductRepository").
		WithMethod("FindByCriteria")

	start := time.Now()

	// Simular SQL query logging
	sql, args := criteria.GetFullSQL("SELECT * FROM products")
	repoLogger.Debug("Executing query with criteria", map[string]interface{}{
		"sql":  sql,
		"args": args,
	})

	r.mu.RLock()
	defer r.mu.RUnlock()

	// En memoria: aplicar filtros manualmente
	results := make([]*entities.Product, 0)
	for _, product := range r.products {
		if r.matchesCriteria(product, criteria) {
			results = append(results, product)
		}
	}

	// Aplicar ordenamiento por cada sort criteria
	for i := len(criteria.Sorts) - 1; i >= 0; i-- {
		s := criteria.Sorts[i]
		sort.SliceStable(results, func(a, b int) bool {
			av := r.fieldFloat(results[a], s.Field)
			bv := r.fieldFloat(results[b], s.Field)
			if s.Direction == specifications.SortDescending {
				return av > bv
			}
			return av < bv
		})
	}

	// Aplicar paginación
	results = r.applyPagination(results, criteria)

	duration := time.Since(start).Milliseconds()

	// Log de query completo con duración
	repoLogger.LogQuery(sql, args, duration, nil)

	repoLogger.Info("Products found by criteria", map[string]interface{}{
		"count":       len(results),
		"duration_ms": duration,
	})

	return results, nil
}

// Count counts products matching criteria
func (r *MemoryProductRepository) Count(ctx context.Context, criteria *specifications.Criteria) (int64, error) {
	repoLogger := r.logger.
		WithLayer("infrastructure").
		WithComponent("MemoryProductRepository").
		WithMethod("Count")

	start := time.Now()

	r.mu.RLock()
	defer r.mu.RUnlock()

	count := int64(0)
	for _, product := range r.products {
		if r.matchesCriteria(product, criteria) {
			count++
		}
	}

	duration := time.Since(start).Milliseconds()
	repoLogger.Debug("Count query executed", map[string]interface{}{
		"count":       count,
		"duration_ms": duration,
	})

	return count, nil
}

// Update updates a product
func (r *MemoryProductRepository) Update(ctx context.Context, product *entities.Product) error {
	repoLogger := r.logger.
		WithLayer("infrastructure").
		WithComponent("MemoryProductRepository").
		WithMethod("Update")

	start := time.Now()

	r.mu.Lock()
	defer r.mu.Unlock()

	if _, exists := r.products[product.ID]; !exists {
		duration := time.Since(start).Milliseconds()
		repoLogger.ErrorWithCode("Product not found for update", 12001002, map[string]interface{}{
			"product_id":  product.ID,
			"duration_ms": duration,
		})
		return fmt.Errorf(errProductNotFound)
	}

	product.UpdatedAt = time.Now()
	r.products[product.ID] = product

	duration := time.Since(start).Milliseconds()
	repoLogger.Info("Product updated", map[string]interface{}{
		"product_id":  product.ID,
		"duration_ms": duration,
	})

	return nil
}

// Delete deletes a product by ID
func (r *MemoryProductRepository) Delete(ctx context.Context, id string) error {
	repoLogger := r.logger.
		WithLayer("infrastructure").
		WithComponent("MemoryProductRepository").
		WithMethod("Delete")

	start := time.Now()

	r.mu.Lock()
	defer r.mu.Unlock()

	if _, exists := r.products[id]; !exists {
		duration := time.Since(start).Milliseconds()
		repoLogger.ErrorWithCode("Product not found for deletion", 12001003, map[string]interface{}{
			"product_id":  id,
			"duration_ms": duration,
		})
		return fmt.Errorf(errProductNotFound)
	}

	delete(r.products, id)

	duration := time.Since(start).Milliseconds()
	repoLogger.Info("Product deleted", map[string]interface{}{
		"product_id":  id,
		"duration_ms": duration,
	})

	return nil
}

// ExistsByID checks if a product exists
func (r *MemoryProductRepository) ExistsByID(ctx context.Context, id string) (bool, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	_, exists := r.products[id]
	return exists, nil
}

// fieldFloat returns the numeric value of a product field for sorting.
// Falls back to 0 for non-numeric fields (use fieldStr for string sorting).
func (r *MemoryProductRepository) fieldFloat(p *entities.Product, field string) float64 {
	v := reflect.ValueOf(p).Elem().FieldByNameFunc(func(name string) bool {
		return strings.EqualFold(name, field)
	})
	if !v.IsValid() {
		return 0
	}
	switch v.Kind() {
	case reflect.Float32, reflect.Float64:
		return v.Float()
	case reflect.Int, reflect.Int32, reflect.Int64:
		return float64(v.Int())
	}
	return 0
}

// matchesCriteria evaluates a product against the specification using IsSatisfiedBy.
func (r *MemoryProductRepository) matchesCriteria(product *entities.Product, criteria *specifications.Criteria) bool {
	if criteria.Specification == nil {
		return true
	}
	return criteria.Specification.IsSatisfiedBy(product)
}

// applyPagination applies pagination to results
func (r *MemoryProductRepository) applyPagination(products []*entities.Product, criteria *specifications.Criteria) []*entities.Product {
	if criteria.Limit == 0 {
		return products
	}

	start := criteria.Offset
	end := start + criteria.Limit

	if start >= len(products) {
		return []*entities.Product{}
	}

	if end > len(products) {
		end = len(products)
	}

	return products[start:end]
}
