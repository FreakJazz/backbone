// Package usecases contains application use cases
package usecases

import (
	"context"
	"fmt"
	"time"

	"github.com/freakjazz/backbone-go/application/exceptions"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/entities"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/repositories"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
)

// CreateProductInput represents the input for creating a product
type CreateProductInput struct {
	Name        string  `json:"name"`
	Description string  `json:"description"`
	Price       float64 `json:"price"`
	Category    string  `json:"category"`
	Stock       int     `json:"stock"`
}

// CreateProductOutput represents the output of product creation
type CreateProductOutput struct {
	Product *entities.Product `json:"product"`
}

// CreateProductUseCase handles product creation
type CreateProductUseCase struct {
	repository repositories.ProductRepository
	logger     *logging.EnhancedLogger
}

// NewCreateProductUseCase creates a new use case instance
func NewCreateProductUseCase(repository repositories.ProductRepository, logger *logging.EnhancedLogger) *CreateProductUseCase {
	return &CreateProductUseCase{
		repository: repository,
		logger:     logger,
	}
}

// Execute executes the use case
func (uc *CreateProductUseCase) Execute(ctx context.Context, input CreateProductInput) (*CreateProductOutput, error) {
	// Logger con contexto de aplicación
	useCaseLogger := uc.logger.
		WithLayer("application").
		WithHandler("CreateProductUseCase").
		WithMethod("Execute").
		WithContext(map[string]interface{}{
			"request_id": ctx.Value("request_id"),
			"user_id":    ctx.Value("user_id"),
		})

	useCaseLogger.Info("Creating product", map[string]interface{}{
		"name":     input.Name,
		"category": input.Category,
		"price":    input.Price,
	})

	// Validar input
	if err := uc.validateInput(input); err != nil {
		useCaseLogger.ErrorWithCode("Invalid input", 10001001, map[string]interface{}{
			"error": err.Error(),
		})
		return nil, err
	}

	// Crear entidad de dominio
	product, err := entities.NewProduct(
		input.Name,
		input.Description,
		input.Category,
		input.Price,
		input.Stock,
	)
	if err != nil {
		useCaseLogger.ErrorWithCode("Domain validation failed", 10001002, map[string]interface{}{
			"error": err.Error(),
		})
		return nil, exceptions.NewValidationException(
			"Product validation failed",
			[]exceptions.ValidationError{
				{Field: "product", Message: err.Error()},
			},
		)
	}

	// Guardar en repositorio
	start := time.Now()
	if err := uc.repository.Create(ctx, product); err != nil {
		duration := time.Since(start).Milliseconds()
		useCaseLogger.ErrorWithCode("Failed to save product", 10001003, map[string]interface{}{
			"error":       err.Error(),
			"duration_ms": duration,
		})
		return nil, exceptions.NewUseCaseException(
			"Failed to create product",
			"CreateProductUseCase",
		)
	}

	duration := time.Since(start).Milliseconds()
	useCaseLogger.Info("Product created successfully", map[string]interface{}{
		"product_id":  product.ID,
		"duration_ms": duration,
	})

	return &CreateProductOutput{
		Product: product,
	}, nil
}

func (uc *CreateProductUseCase) validateInput(input CreateProductInput) error {
	if input.Name == "" {
		return fmt.Errorf("name is required")
	}
	if input.Category == "" {
		return fmt.Errorf("category is required")
	}
	if input.Price <= 0 {
		return fmt.Errorf("price must be greater than 0")
	}
	if input.Stock < 0 {
		return fmt.Errorf("stock cannot be negative")
	}
	return nil
}
