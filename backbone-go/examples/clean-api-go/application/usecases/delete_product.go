// Package usecases contains application use cases
package usecases

import (
	"context"
	"fmt"
	"time"

	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/repositories"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
)

// DeleteProductUseCase handles deleting a product by ID.
type DeleteProductUseCase struct {
	repository repositories.ProductRepository
	logger     *logging.EnhancedLogger
}

// NewDeleteProductUseCase creates a new use case instance.
func NewDeleteProductUseCase(repository repositories.ProductRepository, logger *logging.EnhancedLogger) *DeleteProductUseCase {
	return &DeleteProductUseCase{repository: repository, logger: logger}
}

// Execute deletes the product or returns an error if not found.
func (uc *DeleteProductUseCase) Execute(ctx context.Context, id string) error {
	ucLogger := uc.logger.
		WithLayer("application").
		WithHandler("DeleteProductUseCase").
		WithMethod("Execute").
		WithContext(map[string]interface{}{
			"request_id": ctx.Value("request_id"),
			"product_id": id,
		})

	if id == "" {
		return fmt.Errorf("product ID is required")
	}

	ucLogger.Info("Deleting product", nil)

	start := time.Now()
	if err := uc.repository.Delete(ctx, id); err != nil {
		ucLogger.ErrorWithCode("Failed to delete product", 10004001, map[string]interface{}{
			"error":       err.Error(),
			"duration_ms": time.Since(start).Milliseconds(),
		})
		return err
	}

	ucLogger.Info("Product deleted successfully", map[string]interface{}{
		"product_id":  id,
		"duration_ms": time.Since(start).Milliseconds(),
	})
	return nil
}
