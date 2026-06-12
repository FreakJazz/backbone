// Package commands contains write-side application handlers (CQRS).
package commands

import (
	"context"
	"fmt"
	"time"

	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/repositories"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
)

// UpdateProductCommand is the write input for updating a product.
type UpdateProductCommand struct {
	ID          string
	Name        string
	Description string
	Price       float64
	Category    string
	Stock       int
}

// UpdateProductResult is the write output.
type UpdateProductResult struct {
	ProductID string
}

// UpdateProductCommandHandler handles the UpdateProduct command.
type UpdateProductCommandHandler struct {
	repository repositories.ProductRepository
	logger     *logging.EnhancedLogger
}

// NewUpdateProductCommandHandler creates a new handler instance.
func NewUpdateProductCommandHandler(repo repositories.ProductRepository, logger *logging.EnhancedLogger) *UpdateProductCommandHandler {
	return &UpdateProductCommandHandler{repository: repo, logger: logger}
}

// Handle executes the command.
func (h *UpdateProductCommandHandler) Handle(ctx context.Context, cmd UpdateProductCommand) (*UpdateProductResult, error) {
	log := h.logger.
		WithLayer("application").
		WithHandler("UpdateProductCommandHandler").
		WithMethod("Handle").
		WithContext(map[string]interface{}{"request_id": ctx.Value("request_id"), "product_id": cmd.ID})

	if cmd.ID == "" {
		return nil, fmt.Errorf("product ID is required")
	}

	product, err := h.repository.FindByID(ctx, cmd.ID)
	if err != nil {
		log.Warning("Product not found", map[string]interface{}{"error": err.Error()})
		return nil, err
	}

	if cmd.Name != "" {
		product.Name = cmd.Name
	}
	if cmd.Description != "" {
		product.Description = cmd.Description
	}
	if cmd.Category != "" {
		product.Category = cmd.Category
	}
	if cmd.Price != 0 {
		if err := product.UpdatePrice(cmd.Price); err != nil {
			return nil, err
		}
	}
	if cmd.Stock >= 0 {
		if err := product.UpdateStock(cmd.Stock); err != nil {
			return nil, err
		}
	}

	if err := product.Validate(); err != nil {
		log.ErrorWithCode("Domain validation failed", 10003001, map[string]interface{}{"error": err.Error()})
		return nil, err
	}

	start := time.Now()
	if err := h.repository.Update(ctx, product); err != nil {
		log.ErrorWithCode("Failed to persist update", 10003002, map[string]interface{}{
			"error": err.Error(), "duration_ms": time.Since(start).Milliseconds(),
		})
		return nil, err
	}

	log.Info("Product updated", map[string]interface{}{
		"product_id": product.ID, "duration_ms": time.Since(start).Milliseconds(),
	})
	return &UpdateProductResult{ProductID: product.ID}, nil
}
