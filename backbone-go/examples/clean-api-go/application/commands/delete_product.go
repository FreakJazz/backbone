// Package commands contains write-side application handlers (CQRS).
package commands

import (
	"context"
	"fmt"
	"time"

	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/repositories"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
)

// DeleteProductCommand is the write input for deleting a product.
type DeleteProductCommand struct {
	ID string
}

// DeleteProductCommandHandler handles the DeleteProduct command.
type DeleteProductCommandHandler struct {
	repository repositories.ProductRepository
	logger     *logging.EnhancedLogger
}

// NewDeleteProductCommandHandler creates a new handler instance.
func NewDeleteProductCommandHandler(repo repositories.ProductRepository, logger *logging.EnhancedLogger) *DeleteProductCommandHandler {
	return &DeleteProductCommandHandler{repository: repo, logger: logger}
}

// Handle executes the command.
func (h *DeleteProductCommandHandler) Handle(ctx context.Context, cmd DeleteProductCommand) error {
	log := h.logger.
		WithLayer("application").
		WithHandler("DeleteProductCommandHandler").
		WithMethod("Handle").
		WithContext(map[string]interface{}{"request_id": ctx.Value("request_id"), "product_id": cmd.ID})

	if cmd.ID == "" {
		return fmt.Errorf("product ID is required")
	}

	log.Info("Deleting product", nil)

	start := time.Now()
	if err := h.repository.Delete(ctx, cmd.ID); err != nil {
		log.ErrorWithCode("Failed to delete product", 10004001, map[string]interface{}{
			"error": err.Error(), "duration_ms": time.Since(start).Milliseconds(),
		})
		return err
	}

	log.Info("Product deleted", map[string]interface{}{
		"product_id": cmd.ID, "duration_ms": time.Since(start).Milliseconds(),
	})
	return nil
}
