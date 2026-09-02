package queries

import (
	"context"

	bberrors "github.com/FreakJazz/backbone/backbone-go/errors"
	"github.com/FreakJazz/backbone/backbone-go/infrastructure/logging"
	bbex "github.com/FreakJazz/backbone/backbone-go/interfaces/responses"
	"github.com/freakjazz/clean-api-go/domain/entities"
	"github.com/freakjazz/clean-api-go/domain/repositories"
)

type GetSalesQuery struct {
	ProductID string
	Page      int
	PageSize  int
}

// Items is []*entities.Sale rather than []map[string]interface{} — see
// GetProductsResult's doc comment for why.
type GetSalesResult struct {
	Items      []*entities.Sale
	TotalCount int
	Page       int
	PageSize   int
}

type GetSalesQueryHandler struct {
	repo   repositories.ISaleRepository
	logger *logging.EnhancedLogger
}

func NewGetSalesQueryHandler(repo repositories.ISaleRepository) *GetSalesQueryHandler {
	return &GetSalesQueryHandler{
		repo:   repo,
		logger: logging.NewEnhancedLogger("clean-api-go").WithLayer("application").WithComponent("GetSalesQueryHandler").WithMethod("Handle"),
	}
}

func (h *GetSalesQueryHandler) Handle(ctx context.Context, q GetSalesQuery) (*GetSalesResult, *bbex.ErrorResponse) {
	log := h.logger

	sales, total, err := h.repo.FindByProductID(ctx, q.ProductID, q.Page, q.PageSize)
	if err != nil {
		log.ErrorWithCode("FindByProductID failed", bberrors.InfraDBFailure.Int(), map[string]interface{}{"error": err.Error()})
		e := bbex.ErrorResponseBuilder.InternalServerError(err.Error())
		return nil, &e
	}

	return &GetSalesResult{Items: sales, TotalCount: total, Page: q.Page, PageSize: q.PageSize}, nil
}
