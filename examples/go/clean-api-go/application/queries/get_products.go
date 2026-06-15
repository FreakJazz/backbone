package queries

import (
	"context"
	"fmt"
	"strings"

	bberrors "github.com/freakjazz/backbone-go/errors"
	bbex "github.com/freakjazz/backbone-go/interfaces/responses"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
	"github.com/freakjazz/clean-api-go/domain/repositories"
	productspecs "github.com/freakjazz/clean-api-go/domain/specifications"
)

type GetProductsQuery struct {
	Filters  []string
	SortBy   string
	Page     int
	PageSize int
}

type GetProductsResult struct {
	Items      []map[string]interface{}
	TotalCount int
	Page       int
	PageSize   int
}

type GetProductsQueryHandler struct {
	repo   repositories.IProductRepository
	logger *logging.EnhancedLogger
}

func NewGetProductsQueryHandler(repo repositories.IProductRepository) *GetProductsQueryHandler {
	return &GetProductsQueryHandler{
		repo:   repo,
		logger: logging.NewEnhancedLogger("clean-api-go").WithLayer("application").WithComponent("GetProductsQueryHandler"),
	}
}

func (h *GetProductsQueryHandler) Handle(ctx context.Context, q GetProductsQuery) (*GetProductsResult, *bbex.ErrorResponse) {
	log := h.logger.WithMethod("Handle")

	// Validate filter format before building criteria
	for _, f := range q.Filters {
		if err := validateFilterToken(f); err != nil {
			log.ErrorWithCode("Invalid filter token", bberrors.IfcInvalidFilterFormat.Int(), map[string]interface{}{
				"filter": f, "error": err.Error(),
			})
			e := bbex.ErrorResponseBuilder.ValidationError(err.Error(), bbex.ErrorOpts{
				Code: bberrors.IfcInvalidFilterFormat.Int(),
			})
			return nil, &e
		}
	}

	criteria := productspecs.BuildCriteria(q.Filters, q.Page, q.PageSize, q.SortBy)

	products, err := h.repo.FindByCriteria(ctx, criteria)
	if err != nil {
		log.ErrorWithCode("FindByCriteria failed", bberrors.InfraDBFailure.Int(), map[string]interface{}{"error": err.Error()})
		e := bbex.ErrorResponseBuilder.InternalServerError(err.Error())
		return nil, &e
	}
	total, _ := h.repo.Count(ctx, criteria)

	items := make([]map[string]interface{}, len(products))
	for i, p := range products {
		items[i] = p.ToMap()
	}

	log.Info("Products listed", map[string]interface{}{
		"filters": q.Filters, "total": total, "page": q.Page, "page_size": q.PageSize,
	})

	return &GetProductsResult{
		Items:      items,
		TotalCount: total,
		Page:       q.Page,
		PageSize:   q.PageSize,
	}, nil
}

// validateFilterToken returns an error if the token does not conform to
// "field,operator,value[,condition]". Null-check operators ("is_null","is_not_null")
// do not require a value part.
func validateFilterToken(token string) error {
	parts := strings.SplitN(strings.TrimSpace(token), ",", 4)
	if len(parts) < 2 {
		return fmt.Errorf("invalid filter %q — expected format: field,operator,value[,condition]", token)
	}
	op := strings.ToLower(strings.TrimSpace(parts[1]))
	validOps := map[string]bool{
		"eq": true, "ne": true, "gt": true, "gte": true, "lt": true, "lte": true,
		"contains": true, "in": true, "between": true, "is_null": true, "is_not_null": true,
	}
	if !validOps[op] {
		return fmt.Errorf("unknown operator %q in filter %q — supported: eq ne gt gte lt lte contains in between is_null is_not_null", op, token)
	}
	if op != "is_null" && op != "is_not_null" && len(parts) < 3 {
		return fmt.Errorf("missing value in filter %q — expected format: field,operator,value", token)
	}
	return nil
}
