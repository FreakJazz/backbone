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
	seeds := []*entities.Product{
		{ID: "1", Name: "Laptop Pro", Price: 1500.0, Category: "Electronics", Status: "active", Description: "High-performance laptop"},
		{ID: "2", Name: "Wireless Mouse", Price: 29.99, Category: "Electronics", Status: "active", Description: "Ergonomic wireless mouse"},
		{ID: "3", Name: "Standing Desk", Price: 450.0, Category: "Furniture", Status: "active", Description: "Adjustable standing desk"},
		{ID: "4", Name: "Coffee Mug", Price: 12.5, Category: "Kitchen", Status: "active", Description: "Insulated coffee mug"},
		{ID: "5", Name: "Monitor 4K", Price: 699.0, Category: "Electronics", Status: "active", Description: "4K UHD monitor 27 inch"},
		{ID: "6", Name: "Headphones BT", Price: 199.99, Category: "Electronics", Status: "active", Description: "Noise-cancelling bluetooth headphones"},
		{ID: "7", Name: "Keyboard Mech", Price: 89.0, Category: "Electronics", Status: "active", Description: "Mechanical keyboard TKL"},
		{ID: "8", Name: "Desk Chair", Price: 320.0, Category: "Furniture", Status: "active", Description: "Ergonomic office chair"},
		{ID: "9", Name: "Webcam HD", Price: 75.0, Category: "Electronics", Status: "inactive", Description: "1080p HD webcam"},
		{ID: "10", Name: "USB Hub", Price: 35.0, Category: "Electronics", Status: "active", Description: "7-port USB 3.0 hub"},
	}
	for _, p := range seeds {
		s.repo.Save(ctx, p) //nolint:errcheck
	}
}
