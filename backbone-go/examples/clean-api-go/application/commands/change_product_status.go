// Package commands contains write-side application handlers (CQRS).
package commands

import (
	"context"
	"fmt"
	"time"

	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/repositories"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
)

// ChangeProductStatusCommand is the write input for changing a product's status.
type ChangeProductStatusCommand struct {
	ID     string
	Active bool
}

// ChangeProductStatusCommandHandler handles the ChangeProductStatus command.
type ChangeProductStatusCommandHandler struct {
	repository repositories.ProductRepository
	logger     *logging.EnhancedLogger
}

// NewChangeProductStatusCommandHandler creates a new handler instance.
func NewChangeProductStatusCommandHandler(repo repositories.ProductRepository, logger *logging.EnhancedLogger) *ChangeProductStatusCommandHandler {
	return &ChangeProductStatusCommandHandler{repository: repo, logger: logger}
}

// Handle executes the command.
func (h *ChangeProductStatusCommandHandler) Handle(ctx context.Context, cmd ChangeProductStatusCommand) error {
	log := h.logger.
		WithLayer("application").
		WithHandler("ChangeProductStatusCommandHandler").
		WithMethod("Handle").
		WithContext(map[string]interface{}{
			"request_id": ctx.Value("request_id"),
			"product_id": cmd.ID,
			"active":     cmd.Active,
		})

	if cmd.ID == "" {
		return fmt.Errorf("product ID is required")
	}

	product, err := h.repository.FindByID(ctx, cmd.ID)
	if err != nil {
		log.Warning("Product not found", map[string]interface{}{"error": err.Error()})
		return err
	}

	if cmd.Active {
		product.Activate()
	} else {
		product.Deactivate()
	}

	start := time.Now()
	if err := h.repository.Update(ctx, product); err != nil {
		log.ErrorWithCode("Failed to persist status change", 10005001, map[string]interface{}{
			"error": err.Error(), "duration_ms": time.Since(start).Milliseconds(),
		})
		return err
	}

	log.Info("Product status changed", map[string]interface{}{
		"product_id": product.ID, "active": product.Active,
		"duration_ms": time.Since(start).Milliseconds(),
	})
	return nil
}
