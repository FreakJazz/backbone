package seeders

import (
	"context"

	"github.com/freakjazz/clean-api-go/domain/entities"
	"github.com/freakjazz/clean-api-go/domain/repositories"
)

type ProductSeeder struct {
	repo repositories.IProductRepository
}

func NewProductSeeder(repo repositories.IProductRepository) *ProductSeeder {
	return &ProductSeeder{repo: repo}
}

// Run seeds a handful of products, skipping any name that already exists —
// backed by a real database that persists across restarts, re-running
// main.go must not try to insert the same name twice (it would trip the
// unique index on lower(name)).
func (s *ProductSeeder) Run(ctx context.Context) {
	seeds := []struct {
		name, category, description, status string
		price                               float64
		stock                               int
	}{
		{"Laptop Pro", "Electronics", "High-performance laptop", "active", 1500.0, 25},
		{"Wireless Mouse", "Electronics", "Ergonomic wireless mouse", "active", 29.99, 200},
		{"Standing Desk", "Furniture", "Adjustable standing desk", "active", 450.0, 15},
		{"Coffee Mug", "Kitchen", "Insulated coffee mug", "active", 12.5, 500},
		{"Monitor 4K", "Electronics", "4K UHD monitor 27 inch", "active", 699.0, 40},
		{"Headphones BT", "Electronics", "Noise-cancelling bluetooth headphones", "active", 199.99, 60},
		{"Keyboard Mech", "Electronics", "Mechanical keyboard TKL", "active", 89.0, 80},
		{"Desk Chair", "Furniture", "Ergonomic office chair", "active", 320.0, 20},
		{"Webcam HD", "Electronics", "1080p HD webcam", "inactive", 75.0, 0},
		{"USB Hub", "Electronics", "7-port USB 3.0 hub", "active", 35.0, 150},
	}
	for _, sd := range seeds {
		if existing, _ := s.repo.FindByName(ctx, sd.name); existing != nil {
			continue
		}
		p := entities.NewProduct(sd.name, sd.price, sd.category, sd.description)
		p.Status = sd.status
		p.Stock = sd.stock
		s.repo.Save(ctx, p) //nolint:errcheck
	}
}
