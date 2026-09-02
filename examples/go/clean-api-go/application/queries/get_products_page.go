package queries

import (
	"context"
	"strings"

	"github.com/FreakJazz/backbone/backbone-go/domain/specifications"
	bberrors "github.com/FreakJazz/backbone/backbone-go/errors"
	"github.com/FreakJazz/backbone/backbone-go/infrastructure/logging"
	bbex "github.com/FreakJazz/backbone/backbone-go/interfaces/responses"
	"github.com/freakjazz/clean-api-go/domain/entities"
	"github.com/freakjazz/clean-api-go/domain/repositories"
	productspecs "github.com/freakjazz/clean-api-go/domain/specifications"
)

// GetProductsPageQuery is the cursor ("keyset") counterpart to
// GetProductsQuery. It exists as a separate query/handler rather than a
// branch inside GetProductsQueryHandler so the well-tested offset path
// stays untouched — this is purely additive.
type GetProductsPageQuery struct {
	Filters  []string
	SortBy   string
	Cursor   string // "" starts from the beginning
	PageSize int
}

type GetProductsPageResult struct {
	Items      []*entities.Product
	NextCursor string
}

type GetProductsPageQueryHandler struct {
	repo   repositories.IProductRepository
	logger *logging.EnhancedLogger
}

func NewGetProductsPageQueryHandler(repo repositories.IProductRepository) *GetProductsPageQueryHandler {
	return &GetProductsPageQueryHandler{
		repo:   repo,
		logger: logging.NewEnhancedLogger("clean-api-go").WithLayer("application").WithComponent("GetProductsPageQueryHandler").WithMethod("Handle"),
	}
}

func (h *GetProductsPageQueryHandler) Handle(ctx context.Context, q GetProductsPageQuery) (*GetProductsPageResult, *bbex.ErrorResponse) {
	log := h.logger

	for _, f := range q.Filters {
		if err := validateFilterToken(f); err != nil {
			e := bbex.ErrorResponseBuilder.ValidationError(err.Error(), bbex.ErrorOpts{
				Code: bberrors.IfcInvalidFilterFormat.Int(),
			})
			return nil, &e
		}
	}

	// A malformed cursor is a client input error (400), not a server
	// failure (500) — validate it here, before it ever reaches the
	// repository, same as filters above. The repository decodes it again
	// to get the value it actually needs to bind; that's a second pass
	// over a few bytes of base64, not worth threading a decoded value
	// through the interface just to save it.
	if q.Cursor != "" {
		if _, _, err := specifications.DecodeCursor(q.Cursor); err != nil {
			e := bbex.ErrorResponseBuilder.ValidationError(err.Error(), bbex.ErrorOpts{
				Code: bberrors.IfcInvalidRequestBody.Int(),
			})
			return nil, &e
		}
	}

	// Only the Specification half of Criteria is used here — sorting and
	// pagination for the keyset path are driven by sortField/desc/limit
	// below, not by Criteria's own Sorts/Limit/Offset.
	criteria := productspecs.BuildCriteria(q.Filters, 1, 1, "")

	sortField, sortDir := "created_at", "desc"
	if q.SortBy != "" {
		f, d := splitSortBy(q.SortBy)
		if productspecs.ValidSortFields[f] {
			sortField, sortDir = f, d
		}
	}

	products, nextCursor, err := h.repo.FindPageByCursor(ctx, criteria, sortField, sortDir == "desc", q.Cursor, q.PageSize)
	if err != nil {
		log.ErrorWithCode("FindPageByCursor failed", bberrors.InfraDBFailure.Int(), map[string]interface{}{"error": err.Error()})
		e := bbex.ErrorResponseBuilder.InternalServerError(err.Error())
		return nil, &e
	}

	log.Info("Products page listed", map[string]interface{}{
		"filters": q.Filters, "sort_field": sortField, "has_cursor": q.Cursor != "", "returned": len(products),
	})

	return &GetProductsPageResult{Items: products, NextCursor: nextCursor}, nil
}

func splitSortBy(sortBy string) (field, direction string) {
	sortBy = strings.ReplaceAll(sortBy, ":", ",")
	parts := strings.SplitN(sortBy, ",", 2)
	field = strings.TrimSpace(parts[0])
	direction = "desc"
	if len(parts) == 2 && strings.EqualFold(strings.TrimSpace(parts[1]), "asc") {
		direction = "asc"
	}
	return field, direction
}
