// Package specifications contains domain-specific product specifications
package specifications

import (
	"github.com/freakjazz/backbone-go/domain/specifications"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/entities"
)

// ProductIsActive checks if a product is active
func ProductIsActive() specifications.Specification {
	return specifications.NewEqualSpecification("active", true)
}

// ProductInCategory checks if a product is in a specific category
func ProductInCategory(category string) specifications.Specification {
	return specifications.NewEqualSpecification("category", category)
}

// ProductPriceRange checks if product price is in range
func ProductPriceRange(min, max float64) specifications.Specification {
	return specifications.NewBetweenSpecification("price", min, max)
}

// ProductInStock checks if product is in stock
func ProductInStock() specifications.Specification {
	return specifications.NewGreaterThanSpecification("stock", 0)
}

// ProductByNamePattern searches products by name pattern
func ProductByNamePattern(pattern string) specifications.Specification {
	return specifications.NewLikeSpecification("name", pattern)
}

// IsSatisfiedBy checks if a product satisfies the active specification
func (s ProductIsActive) IsSatisfiedBy(entity interface{}) bool {
	if product, ok := entity.(*entities.Product); ok {
		return product.Active
	}
	return false
}
