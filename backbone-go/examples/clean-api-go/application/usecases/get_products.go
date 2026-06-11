// Package usecases contains application use cases
package usecases

import (
	"context"
	"time"

	"github.com/freakjazz/backbone-go/application/exceptions"
	"github.com/freakjazz/backbone-go/domain/specifications"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/entities"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/repositories"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
)

// GetProductsInput carries the 4 generic query parameters.
//
//	Filters  — each string: "field,operator,value[,condition]"
//	           operators : eq ne gt gte lt lte contains in between is_null is_not_null
//	           conditions: and (default) | or
//	           examples  : "category,eq,Electronics,and"  "price,gt,500,and"
//	Page     — page number (default 1)
//	PageSize — items per page (default 10)
//	SortBy   — "field:direction" e.g. "price:desc" (default "created_at:desc")
type GetProductsInput struct {
	Filters  []string `json:"filters"`
	Page     int      `json:"page"`
	PageSize int      `json:"page_size"`
	SortBy   string   `json:"sort_by"`
}

// GetProductsOutput is the result of the use case.
type GetProductsOutput struct {
	Products   []*entities.Product
	TotalCount int64
	Page       int
	PageSize   int
}

// GetProductsUseCase handles listing products with dynamic filters.
type GetProductsUseCase struct {
	repository repositories.ProductRepository
	logger     *logging.EnhancedLogger
}

// NewGetProductsUseCase creates a new use case instance.
func NewGetProductsUseCase(repository repositories.ProductRepository, logger *logging.EnhancedLogger) *GetProductsUseCase {
	return &GetProductsUseCase{repository: repository, logger: logger}
}

// Execute applies filters, sorts and pagination via the Specification + Criteria pattern.
func (uc *GetProductsUseCase) Execute(ctx context.Context, input GetProductsInput) (*GetProductsOutput, error) {
	ucLogger := uc.logger.
		WithLayer("application").
		WithHandler("GetProductsUseCase").
		WithMethod("Execute").
		WithContext(map[string]interface{}{
			"request_id": ctx.Value("request_id"),
			"filters":    input.Filters,
			"page":       input.Page,
			"page_size":  input.PageSize,
			"sort_by":    input.SortBy,
		})

	ucLogger.Info("Getting products", nil)

	// Defaults
	page := input.Page
	if page < 1 {
		page = 1
	}
	pageSize := input.PageSize
	if pageSize < 1 {
		pageSize = 10
	}
	if pageSize > 100 {
		pageSize = 100
	}

	sortField, sortDir := specifications.ParseSortBy(input.SortBy)

	// Build Criteria from generic filter params
	start := time.Now()
	criteria := specifications.ParseFilterParams(input.Filters, page, pageSize, sortField, sortDir)

	sql, args := criteria.GetFullSQL("SELECT * FROM products")
	ucLogger.Debug("Criteria built", map[string]interface{}{
		"sql":            sql,
		"args":           args,
		"filters_count":  len(input.Filters),
	})

	// Count
	totalCount, err := uc.repository.Count(ctx, criteria)
	if err != nil {
		ucLogger.ErrorWithCode("Failed to count products", 10002001, map[string]interface{}{"error": err.Error()})
		return nil, exceptions.NewUseCaseException("Failed to count products", "GetProductsUseCase")
	}

	// Fetch
	products, err := uc.repository.FindByCriteria(ctx, criteria)
	if err != nil {
		ucLogger.ErrorWithCode("Failed to get products", 10002002, map[string]interface{}{
			"error":       err.Error(),
			"duration_ms": time.Since(start).Milliseconds(),
		})
		return nil, exceptions.NewUseCaseException("Failed to get products", "GetProductsUseCase")
	}

	ucLogger.Info("Products retrieved", map[string]interface{}{
		"count":       len(products),
		"total":       totalCount,
		"duration_ms": time.Since(start).Milliseconds(),
	})

	return &GetProductsOutput{
		Products:   products,
		TotalCount: totalCount,
		Page:       page,
		PageSize:   pageSize,
	}, nil
}
