// Package commands contains write-side application handlers (CQRS).
package commands

import (
	"context"
	"fmt"
	"time"

	"github.com/freakjazz/backbone-go/application/exceptions"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/entities"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/repositories"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
)

// CreateProductCommand is the write input for creating a product.
type CreateProductCommand struct {
	Name        string  `json:"name"`
	Description string  `json:"description"`
	Price       float64 `json:"price"`
	Category    string  `json:"category"`
	Stock       int     `json:"stock"`
}

// CreateProductResult is the write output.
type CreateProductResult struct {
	ProductID string
}

// CreateProductCommandHandler handles the CreateProduct command.
type CreateProductCommandHandler struct {
	repository repositories.ProductRepository
	logger     *logging.EnhancedLogger
}

// NewCreateProductCommandHandler creates a new handler instance.
func NewCreateProductCommandHandler(repo repositories.ProductRepository, logger *logging.EnhancedLogger) *CreateProductCommandHandler {
	return &CreateProductCommandHandler{repository: repo, logger: logger}
}

// Handle executes the command.
func (h *CreateProductCommandHandler) Handle(ctx context.Context, cmd CreateProductCommand) (*CreateProductResult, error) {
	log := h.logger.
		WithLayer("application").
		WithHandler("CreateProductCommandHandler").
		WithMethod("Handle").
		WithContext(map[string]interface{}{"request_id": ctx.Value("request_id")})

	if err := h.validate(cmd); err != nil {
		log.ErrorWithCode("Validation failed", 10001001, map[string]interface{}{"error": err.Error()})
		return nil, err
	}

	product, err := entities.NewProduct(cmd.Name, cmd.Description, cmd.Category, cmd.Price, cmd.Stock)
	if err != nil {
		log.ErrorWithCode("Domain validation failed", 10001002, map[string]interface{}{"error": err.Error()})
		return nil, exceptions.NewValidationException("Product validation failed",
			[]exceptions.ValidationError{{Field: "product", Message: err.Error()}})
	}

	start := time.Now()
	if err := h.repository.Create(ctx, product); err != nil {
		log.ErrorWithCode("Failed to persist product", 10001003, map[string]interface{}{
			"error": err.Error(), "duration_ms": time.Since(start).Milliseconds(),
		})
		return nil, exceptions.NewUseCaseException("Failed to create product", "CreateProductCommandHandler")
	}

	log.Info("Product created", map[string]interface{}{
		"product_id": product.ID, "duration_ms": time.Since(start).Milliseconds(),
	})
	return &CreateProductResult{ProductID: product.ID}, nil
}

func (h *CreateProductCommandHandler) validate(cmd CreateProductCommand) error {
	if cmd.Name == "" {
		return fmt.Errorf("name is required")
	}
	if cmd.Category == "" {
		return fmt.Errorf("category is required")
	}
	if cmd.Price <= 0 {
		return fmt.Errorf("price must be greater than 0")
	}
	if cmd.Stock < 0 {
		return fmt.Errorf("stock cannot be negative")
	}
	return nil
}
