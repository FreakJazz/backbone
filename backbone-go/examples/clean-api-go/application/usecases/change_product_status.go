// Package usecases contains application use cases
package usecases

import (
	"context"
	"fmt"
	"time"

	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/repositories"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
)

// ChangeProductStatusInput is the input for changing a product's active status.
type ChangeProductStatusInput struct {
	ID     string `json:"id"`
	Active bool   `json:"active"`
}

// ChangeProductStatusUseCase handles activating or deactivating a product.
type ChangeProductStatusUseCase struct {
	repository repositories.ProductRepository
	logger     *logging.EnhancedLogger
}

// NewChangeProductStatusUseCase creates a new use case instance.
func NewChangeProductStatusUseCase(repository repositories.ProductRepository, logger *logging.EnhancedLogger) *ChangeProductStatusUseCase {
	return &ChangeProductStatusUseCase{repository: repository, logger: logger}
}

// Execute changes the active status of a product.
func (uc *ChangeProductStatusUseCase) Execute(ctx context.Context, input ChangeProductStatusInput) error {
	ucLogger := uc.logger.
		WithLayer("application").
		WithHandler("ChangeProductStatusUseCase").
		WithMethod("Execute").
		WithContext(map[string]interface{}{
			"request_id": ctx.Value("request_id"),
			"product_id": input.ID,
			"active":     input.Active,
		})

	if input.ID == "" {
		return fmt.Errorf("product ID is required")
	}

	ucLogger.Info("Changing product status", nil)

	product, err := uc.repository.FindByID(ctx, input.ID)
	if err != nil {
		ucLogger.Warning("Product not found", map[string]interface{}{"error": err.Error()})
		return err
	}

	if input.Active {
		product.Activate()
	} else {
		product.Deactivate()
	}

	start := time.Now()
	if err := uc.repository.Update(ctx, product); err != nil {
		ucLogger.ErrorWithCode("Failed to persist status change", 10005001, map[string]interface{}{
			"error":       err.Error(),
			"duration_ms": time.Since(start).Milliseconds(),
		})
		return err
	}

	ucLogger.Info("Product status changed", map[string]interface{}{
		"product_id":  product.ID,
		"active":      product.Active,
		"duration_ms": time.Since(start).Milliseconds(),
	})
	return nil
}
