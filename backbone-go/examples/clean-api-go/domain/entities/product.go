// Package entities contains domain entities
package entities

import (
	"time"

	"github.com/google/uuid"
)

// Product represents a product entity in the domain
type Product struct {
	ID          string
	Name        string
	Description string
	Price       float64
	Category    string
	Stock       int
	Active      bool
	CreatedAt   time.Time
	UpdatedAt   time.Time
}

// NewProduct creates a new product with validation
func NewProduct(name, description, category string, price float64, stock int) (*Product, error) {
	product := &Product{
		ID:          uuid.New().String(),
		Name:        name,
		Description: description,
		Price:       price,
		Category:    category,
		Stock:       stock,
		Active:      true,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	if err := product.Validate(); err != nil {
		return nil, err
	}

	return product, nil
}

// Validate validates the product
func (p *Product) Validate() error {
	if p.Name == "" || len(p.Name) < 3 {
		return &ValidationError{
			Field:   "name",
			Message: "Product name must be at least 3 characters",
			Code:    11001001,
		}
	}

	if p.Price <= 0 {
		return &ValidationError{
			Field:   "price",
			Message: "Product price must be greater than 0",
			Code:    11001002,
		}
	}

	if p.Stock < 0 {
		return &ValidationError{
			Field:   "stock",
			Message: "Product stock cannot be negative",
			Code:    11001003,
		}
	}

	if p.Category == "" {
		return &ValidationError{
			Field:   "category",
			Message: "Product category is required",
			Code:    11001004,
		}
	}

	return nil
}

// UpdateStock updates the stock quantity
func (p *Product) UpdateStock(quantity int) error {
	if quantity < 0 {
		return &ValidationError{
			Field:   "stock",
			Message: "Stock quantity cannot be negative",
			Code:    11001003,
		}
	}

	p.Stock = quantity
	p.UpdatedAt = time.Now()
	return nil
}

// UpdatePrice updates the price
func (p *Product) UpdatePrice(price float64) error {
	if price <= 0 {
		return &ValidationError{
			Field:   "price",
			Message: "Product price must be greater than 0",
			Code:    11001002,
		}
	}

	p.Price = price
	p.UpdatedAt = time.Now()
	return nil
}

// Deactivate marks the product as inactive
func (p *Product) Deactivate() {
	p.Active = false
	p.UpdatedAt = time.Now()
}

// Activate marks the product as active
func (p *Product) Activate() {
	p.Active = true
	p.UpdatedAt = time.Now()
}

// IsInStock checks if product is in stock
func (p *Product) IsInStock() bool {
	return p.Stock > 0
}

// ValidationError represents a domain validation error
type ValidationError struct {
	Field   string
	Message string
	Code    int
}

// Error implements the error interface
func (e *ValidationError) Error() string {
	return e.Message
}
