// Package usecases contains application use cases
package usecases

import (
	"context"
	"fmt"
	"time"

	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/entities"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/repositories"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
)

// UpdateProductInput is the input for updating a product.
type UpdateProductInput struct {
	ID          string  `json:"id"`
	Name        string  `json:"name"`
	Description string  `json:"description"`
	Price       float64 `json:"price"`
	Category    string  `json:"category"`
	Stock       int     `json:"stock"`
}

// UpdateProductUseCase handles updating an existing product.
type UpdateProductUseCase struct {
	repository repositories.ProductRepository
	logger     *logging.EnhancedLogger
}

// NewUpdateProductUseCase creates a new use case instance.
func NewUpdateProductUseCase(repository repositories.ProductRepository, logger *logging.EnhancedLogger) *UpdateProductUseCase {
	return &UpdateProductUseCase{repository: repository, logger: logger}
}

// Execute validates, applies changes and persists the product.
func (uc *UpdateProductUseCase) Execute(ctx context.Context, input UpdateProductInput) (*entities.Product, error) {
	ucLogger := uc.logger.
		WithLayer("application").
		WithHandler("UpdateProductUseCase").
		WithMethod("Execute").
		WithContext(map[string]interface{}{
			"request_id": ctx.Value("request_id"),
			"product_id": input.ID,
		})

	if input.ID == "" {
		return nil, fmt.Errorf("product ID is required")
	}

	ucLogger.Info("Updating product", map[string]interface{}{
		"name":  input.Name,
		"price": input.Price,
	})

	product, err := uc.repository.FindByID(ctx, input.ID)
	if err != nil {
		ucLogger.Warning("Product not found for update", map[string]interface{}{"error": err.Error()})
		return nil, err
	}

	if input.Name != "" {
		product.Name = input.Name
	}
	if input.Description != "" {
		product.Description = input.Description
	}
	if input.Category != "" {
		product.Category = input.Category
	}
	if input.Price > 0 {
		if err := product.UpdatePrice(input.Price); err != nil {
			return nil, err
		}
	}
	if input.Stock >= 0 {
		if err := product.UpdateStock(input.Stock); err != nil {
			return nil, err
		}
	}
	product.UpdatedAt = time.Now()

	if err := product.Validate(); err != nil {
		ucLogger.ErrorWithCode("Domain validation failed on update", 10003001, map[string]interface{}{
			"error": err.Error(),
		})
		return nil, err
	}

	start := time.Now()
	if err := uc.repository.Update(ctx, product); err != nil {
		ucLogger.ErrorWithCode("Failed to update product", 10003002, map[string]interface{}{
			"error":       err.Error(),
			"duration_ms": time.Since(start).Milliseconds(),
		})
		return nil, err
	}

	ucLogger.Info("Product updated successfully", map[string]interface{}{
		"product_id":  product.ID,
		"duration_ms": time.Since(start).Milliseconds(),
	})
	return product, nil
}
