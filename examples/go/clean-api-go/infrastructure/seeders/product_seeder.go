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

func (s *ProductSeeder) Run(ctx context.Context) {
	seeds := []struct {
		name, category, description, status string
		price                               float64
	}{
		{"Laptop Pro", "Electronics", "High-performance laptop", "active", 1500.0},
		{"Wireless Mouse", "Electronics", "Ergonomic wireless mouse", "active", 29.99},
		{"Standing Desk", "Furniture", "Adjustable standing desk", "active", 450.0},
		{"Coffee Mug", "Kitchen", "Insulated coffee mug", "active", 12.5},
		{"Monitor 4K", "Electronics", "4K UHD monitor 27 inch", "active", 699.0},
		{"Headphones BT", "Electronics", "Noise-cancelling bluetooth headphones", "active", 199.99},
		{"Keyboard Mech", "Electronics", "Mechanical keyboard TKL", "active", 89.0},
		{"Desk Chair", "Furniture", "Ergonomic office chair", "active", 320.0},
		{"Webcam HD", "Electronics", "1080p HD webcam", "inactive", 75.0},
		{"USB Hub", "Electronics", "7-port USB 3.0 hub", "active", 35.0},
	}
	for _, s2 := range seeds {
		p := entities.NewProduct(s2.name, s2.price, s2.category, s2.description)
		p.Status = s2.status
		s.repo.Save(ctx, p) //nolint:errcheck
	}
}
