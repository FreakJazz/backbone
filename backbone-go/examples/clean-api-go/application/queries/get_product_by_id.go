// Package queries contains read-side application handlers (CQRS).
package queries

import (
	"context"
	"fmt"

	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/entities"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/repositories"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
)

// GetProductByIDQuery is the read input for fetching a single product.
type GetProductByIDQuery struct {
	ID string
}

// GetProductByIDResult is the read output.
type GetProductByIDResult struct {
	Product *entities.Product
}

// GetProductByIDQueryHandler handles the GetProductByID query.
type GetProductByIDQueryHandler struct {
	repository repositories.ProductRepository
	logger     *logging.EnhancedLogger
}

// NewGetProductByIDQueryHandler creates a new handler instance.
func NewGetProductByIDQueryHandler(repo repositories.ProductRepository, logger *logging.EnhancedLogger) *GetProductByIDQueryHandler {
	return &GetProductByIDQueryHandler{repository: repo, logger: logger}
}

// Handle executes the query.
func (h *GetProductByIDQueryHandler) Handle(ctx context.Context, query GetProductByIDQuery) (*GetProductByIDResult, error) {
	log := h.logger.
		WithLayer("application").
		WithHandler("GetProductByIDQueryHandler").
		WithMethod("Handle").
		WithContext(map[string]interface{}{
			"request_id": ctx.Value("request_id"),
			"product_id": query.ID,
		})

	if query.ID == "" {
		return nil, fmt.Errorf("product ID is required")
	}

	log.Info("Fetching product by ID", nil)

	product, err := h.repository.FindByID(ctx, query.ID)
	if err != nil {
		log.Warning("Product not found", map[string]interface{}{"error": err.Error()})
		return nil, err
	}

	log.Info("Product found", map[string]interface{}{"product_id": product.ID})
	return &GetProductByIDResult{Product: product}, nil
}
