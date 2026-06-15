package entities

import "github.com/google/uuid"

type Product struct {
	ID          string  `json:"id"`
	Name        string  `json:"name"`
	Price       float64 `json:"price"`
	Category    string  `json:"category"`
	Status      string  `json:"status"`
	Description string  `json:"description,omitempty"`
}

func NewProduct(name string, price float64, category, description string) *Product {
	return &Product{
		ID:          uuid.New().String(),
		Name:        name,
		Price:       price,
		Category:    category,
		Status:      "active",
		Description: description,
	}
}

func (p *Product) ToMap() map[string]interface{} {
	return map[string]interface{}{
		"id":          p.ID,
		"name":        p.Name,
		"price":       p.Price,
		"category":    p.Category,
		"status":      p.Status,
		"description": p.Description,
	}
}
