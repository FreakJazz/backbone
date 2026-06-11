// Package queries contains read-side application handlers (CQRS).
package queries

import (
	"context"
	"time"

	"github.com/freakjazz/backbone-go/application/exceptions"
	"github.com/freakjazz/backbone-go/domain/specifications"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/entities"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/repositories"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
)

// GetProductsQuery is the read input for listing products.
//
// Query params (4 generic):
//
//	Filters  — repeated: "field,operator,value[,condition]"
//	           operators : eq ne gt gte lt lte contains in between is_null is_not_null
//	           conditions: and (default) | or
//	           examples  : "category,eq,Electronics,and"  "price,gt,500"
//	Page     — page number (default 1)
//	PageSize — items per page (default 10)
//	SortBy   — "field:direction"  e.g. "price:desc"  (default "created_at:desc")
type GetProductsQuery struct {
	Filters  []string
	Page     int
	PageSize int
	SortBy   string
}

// GetProductsResult is the read output.
type GetProductsResult struct {
	Products   []*entities.Product
	TotalCount int64
	Page       int
	PageSize   int
}

// GetProductsQueryHandler handles the GetProducts query.
type GetProductsQueryHandler struct {
	repository repositories.ProductRepository
	logger     *logging.EnhancedLogger
}

// NewGetProductsQueryHandler creates a new handler instance.
func NewGetProductsQueryHandler(repo repositories.ProductRepository, logger *logging.EnhancedLogger) *GetProductsQueryHandler {
	return &GetProductsQueryHandler{repository: repo, logger: logger}
}

// Handle executes the query.
func (h *GetProductsQueryHandler) Handle(ctx context.Context, query GetProductsQuery) (*GetProductsResult, error) {
	log := h.logger.
		WithLayer("application").
		WithHandler("GetProductsQueryHandler").
		WithMethod("Handle").
		WithContext(map[string]interface{}{
			"request_id":    ctx.Value("request_id"),
			"filters_count": len(query.Filters),
			"page":          query.Page,
			"page_size":     query.PageSize,
		})

	page := query.Page
	if page < 1 {
		page = 1
	}
	pageSize := query.PageSize
	if pageSize < 1 {
		pageSize = 10
	}
	if pageSize > 100 {
		pageSize = 100
	}

	sortField, sortDir := specifications.ParseSortBy(query.SortBy)
	criteria := specifications.ParseFilterParams(query.Filters, page, pageSize, sortField, sortDir)

	sql, args := criteria.GetFullSQL("SELECT * FROM products")
	log.Debug("Query criteria built", map[string]interface{}{"sql": sql, "args": args})

	start := time.Now()

	totalCount, err := h.repository.Count(ctx, criteria)
	if err != nil {
		log.ErrorWithCode("Failed to count products", 10002001, map[string]interface{}{"error": err.Error()})
		return nil, exceptions.NewUseCaseException("Failed to count products", "GetProductsQueryHandler")
	}

	products, err := h.repository.FindByCriteria(ctx, criteria)
	if err != nil {
		log.ErrorWithCode("Failed to fetch products", 10002002, map[string]interface{}{
			"error": err.Error(), "duration_ms": time.Since(start).Milliseconds(),
		})
		return nil, exceptions.NewUseCaseException("Failed to get products", "GetProductsQueryHandler")
	}

	log.Info("Products retrieved", map[string]interface{}{
		"count": len(products), "total": totalCount,
		"duration_ms": time.Since(start).Milliseconds(),
	})

	return &GetProductsResult{
		Products:   products,
		TotalCount: totalCount,
		Page:       page,
		PageSize:   pageSize,
	}, nil
}
