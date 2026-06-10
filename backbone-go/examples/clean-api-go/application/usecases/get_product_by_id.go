// Package usecases contains application use cases
package usecases

import (
	"context"
	"fmt"

	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/entities"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/repositories"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
)

// GetProductByIDUseCase handles fetching a single product by ID.
type GetProductByIDUseCase struct {
	repository repositories.ProductRepository
	logger     *logging.EnhancedLogger
}

// NewGetProductByIDUseCase creates a new use case instance.
func NewGetProductByIDUseCase(repository repositories.ProductRepository, logger *logging.EnhancedLogger) *GetProductByIDUseCase {
	return &GetProductByIDUseCase{repository: repository, logger: logger}
}

// Execute returns the product or an error if not found.
func (uc *GetProductByIDUseCase) Execute(ctx context.Context, id string) (*entities.Product, error) {
	ucLogger := uc.logger.
		WithLayer("application").
		WithHandler("GetProductByIDUseCase").
		WithMethod("Execute").
		WithContext(map[string]interface{}{
			"request_id": ctx.Value("request_id"),
			"product_id": id,
		})

	if id == "" {
		return nil, fmt.Errorf("product ID is required")
	}

	ucLogger.Info("Fetching product by ID", nil)

	product, err := uc.repository.FindByID(ctx, id)
	if err != nil {
		ucLogger.Warning("Product not found", map[string]interface{}{"error": err.Error()})
		return nil, err
	}

	ucLogger.Info("Product retrieved", map[string]interface{}{"product_id": product.ID})
	return product, nil
}
