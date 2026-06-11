// Package seeders contains data seeders — Infrastructure layer.
package seeders

import (
	"context"
	"time"

	domainRepos "github.com/freakjazz/backbone-go/examples/clean-api-go/domain/repositories"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/entities"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
)

var seedProducts = []struct {
	id, name, description, category string
	price                           float64
	stock                           int
}{
	{"1", "Laptop Dell XPS 15",    "High performance laptop with 16GB RAM", "Electronics", 1500.00, 50},
	{"2", "iPhone 14 Pro",          "Latest iPhone with advanced camera",    "Electronics", 1200.00, 100},
	{"3", "Office Chair Ergonomic", "Comfortable ergonomic office chair",    "Furniture",   350.00,  30},
	{"4", "Standing Desk",          "Adjustable height standing desk",       "Furniture",   600.00,  20},
	{"5", "Wireless Mouse",         "Ergonomic wireless mouse",              "Electronics", 45.00,   200},
}

// ProductSeeder seeds demo products into the repository.
type ProductSeeder struct {
	repository domainRepos.ProductRepository
	logger     *logging.EnhancedLogger
}

// NewProductSeeder creates a new seeder.
func NewProductSeeder(repo domainRepos.ProductRepository, logger *logging.EnhancedLogger) *ProductSeeder {
	return &ProductSeeder{repository: repo, logger: logger}
}

// Run seeds all demo products.
func (s *ProductSeeder) Run(ctx context.Context) {
	s.logger.Info("Running product seeder...", nil)
	now := time.Now()
	seeded := 0

	for _, d := range seedProducts {
		p := &entities.Product{
			ID:          d.id,
			Name:        d.name,
			Description: d.description,
			Price:       d.price,
			Category:    d.category,
			Stock:       d.stock,
			Active:      true,
			CreatedAt:   now,
			UpdatedAt:   now,
		}
		if err := s.repository.Create(ctx, p); err != nil {
			s.logger.Warning("Failed to seed product", map[string]interface{}{
				"id": d.id, "error": err.Error(),
			})
			continue
		}
		seeded++
	}

	s.logger.Info("Product seeder completed", map[string]interface{}{"seeded": seeded})
}
