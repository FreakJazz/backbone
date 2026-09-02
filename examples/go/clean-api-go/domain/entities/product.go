package entities

import (
	"time"

	"github.com/google/uuid"
)

// Product lives in PostgreSQL. Stock is the single source of truth for
// availability — Sale and StockMovement (both in Mongo) only ever move it
// through IProductRepository.AdjustStock, never by writing it directly.
type Product struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Price       float64   `json:"price"`
	Category    string    `json:"category"`
	Status      string    `json:"status"`
	Description string    `json:"description"`
	Stock       int       `json:"stock"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// NewProduct keeps its original 4-arg signature for backward compatibility
// with existing call sites/tests. Stock defaults to 0 — set it explicitly
// on the returned Product when a non-zero initial stock is needed.
func NewProduct(name string, price float64, category, description string) *Product {
	now := time.Now().UTC()
	return &Product{
		ID:          uuid.New().String(),
		Name:        name,
		Price:       price,
		Category:    category,
		Status:      "active",
		Description: description,
		CreatedAt:   now,
		UpdatedAt:   now,
	}
}
