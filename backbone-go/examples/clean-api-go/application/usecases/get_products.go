// Package usecases contains application use cases
package usecases

import (
	"context"
	"time"

	"github.com/freakjazz/backbone-go/application/exceptions"
	"github.com/freakjazz/backbone-go/domain/specifications"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/entities"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/repositories"
	productSpecs "github.com/freakjazz/backbone-go/examples/clean-api-go/domain/specifications"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
)

// GetProductsInput represents the input for getting products with filters
type GetProductsInput struct {
	Category    string  `json:"category"`
	MinPrice    float64 `json:"min_price"`
	MaxPrice    float64 `json:"max_price"`
	InStock     bool    `json:"in_stock"`
	Active      bool    `json:"active"`
	NamePattern string  `json:"name_pattern"`
	Page        int     `json:"page"`
	PageSize    int     `json:"page_size"`
	SortBy      string  `json:"sort_by"`
	SortOrder   string  `json:"sort_order"`
}

// GetProductsOutput represents the output of getting products
type GetProductsOutput struct {
	Products    []*entities.Product `json:"products"`
	TotalCount  int64               `json:"total_count"`
	Page        int                 `json:"page"`
	PageSize    int                 `json:"page_size"`
	TotalPages  int                 `json:"total_pages"`
	HasNext     bool                `json:"has_next"`
	HasPrevious bool                `json:"has_previous"`
}

// GetProductsUseCase handles getting products with filters
type GetProductsUseCase struct {
	repository repositories.ProductRepository
	logger     *logging.EnhancedLogger
}

// NewGetProductsUseCase creates a new use case instance
func NewGetProductsUseCase(repository repositories.ProductRepository, logger *logging.EnhancedLogger) *GetProductsUseCase {
	return &GetProductsUseCase{
		repository: repository,
		logger:     logger,
	}
}

// Execute executes the use case with Specification Pattern
func (uc *GetProductsUseCase) Execute(ctx context.Context, input GetProductsInput) (*GetProductsOutput, error) {
	// Logger con contexto de aplicación
	useCaseLogger := uc.logger.
		WithLayer("application").
		WithHandler("GetProductsUseCase").
		WithMethod("Execute").
		WithContext(map[string]interface{}{
			"request_id": ctx.Value("request_id"),
			"user_id":    ctx.Value("user_id"),
		})

	useCaseLogger.Info("Getting products with filters", map[string]interface{}{
		"category":  input.Category,
		"min_price": input.MinPrice,
		"max_price": input.MaxPrice,
		"in_stock":  input.InStock,
		"page":      input.Page,
		"page_size": input.PageSize,
	})

	// Construir criteria con Specification Pattern
	start := time.Now()
	criteria := uc.buildCriteria(input)

	// Log de la query construida
	useCaseLogger.Debug("Query criteria built", map[string]interface{}{
		"filters_applied": uc.getAppliedFilters(input),
	})

	// Obtener total count
	totalCount, err := uc.repository.Count(ctx, criteria)
	if err != nil {
		useCaseLogger.ErrorWithCode("Failed to count products", 10002001, map[string]interface{}{
			"error": err.Error(),
		})
		return nil, exceptions.NewUseCaseException(
			"Failed to count products",
			"GetProductsUseCase",
		)
	}

	// Obtener productos
	products, err := uc.repository.FindByCriteria(ctx, criteria)
	if err != nil {
		duration := time.Since(start).Milliseconds()
		useCaseLogger.ErrorWithCode("Failed to get products", 10002002, map[string]interface{}{
			"error":       err.Error(),
			"duration_ms": duration,
		})
		return nil, exceptions.NewUseCaseException(
			"Failed to get products",
			"GetProductsUseCase",
		)
	}

	duration := time.Since(start).Milliseconds()

	// Calcular paginación
	totalPages := int(totalCount) / input.PageSize
	if int(totalCount)%input.PageSize > 0 {
		totalPages++
	}

	output := &GetProductsOutput{
		Products:    products,
		TotalCount:  totalCount,
		Page:        input.Page,
		PageSize:    input.PageSize,
		TotalPages:  totalPages,
		HasNext:     input.Page < totalPages,
		HasPrevious: input.Page > 1,
	}

	useCaseLogger.Info("Products retrieved successfully", map[string]interface{}{
		"count":       len(products),
		"total_count": totalCount,
		"duration_ms": duration,
	})

	return output, nil
}

// buildCriteria construye el criteria con Specification Pattern
func (uc *GetProductsUseCase) buildCriteria(input GetProductsInput) *specifications.Criteria {
	builder := specifications.NewCriteriaBuilder()

	// Filtro de activo por defecto
	if input.Active {
		builder.Where("active", "=", true)
	}

	// Filtro por categoría
	if input.Category != "" {
		spec := productSpecs.ProductInCategory(input.Category)
		sql, args := spec.ToSQL()
		uc.logger.Debug("Category filter applied", map[string]interface{}{
			"category": input.Category,
			"sql":      sql,
			"args":     args,
		})
		builder.Where("category", "=", input.Category)
	}

	// Filtro por rango de precio
	if input.MinPrice > 0 && input.MaxPrice > 0 {
		builder.WhereBetween("price", input.MinPrice, input.MaxPrice)
	} else if input.MinPrice > 0 {
		builder.Where("price", ">=", input.MinPrice)
	} else if input.MaxPrice > 0 {
		builder.Where("price", "<=", input.MaxPrice)
	}

	// Filtro por stock
	if input.InStock {
		builder.Where("stock", ">", 0)
	}

	// Filtro por nombre (pattern)
	if input.NamePattern != "" {
		// Para LIKE necesitamos agregar los %
		pattern := "%" + input.NamePattern + "%"
		// Nota: En implementación real con DB, usarías LIKE
		builder.Where("name", "LIKE", pattern)
	}

	// Ordenamiento
	sortBy := input.SortBy
	if sortBy == "" {
		sortBy = "created_at"
	}

	if input.SortOrder == "asc" {
		builder.OrderByAsc(sortBy)
	} else {
		builder.OrderByDesc(sortBy)
	}

	// Paginación
	page := input.Page
	if page < 1 {
		page = 1
	}
	pageSize := input.PageSize
	if pageSize < 1 {
		pageSize = 10
	}
	if pageSize > 100 {
		pageSize = 100 // Límite máximo
	}

	builder.Paginate(page, pageSize)

	return builder.Build()
}

// getAppliedFilters retorna los filtros aplicados para logging
func (uc *GetProductsUseCase) getAppliedFilters(input GetProductsInput) []string {
	filters := []string{}
	if input.Category != "" {
		filters = append(filters, "category")
	}
	if input.MinPrice > 0 || input.MaxPrice > 0 {
		filters = append(filters, "price_range")
	}
	if input.InStock {
		filters = append(filters, "in_stock")
	}
	if input.NamePattern != "" {
		filters = append(filters, "name_pattern")
	}
	return filters
}
