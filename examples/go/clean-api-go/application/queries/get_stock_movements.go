package queries

import (
	"context"

	bberrors "github.com/FreakJazz/backbone/backbone-go/errors"
	"github.com/FreakJazz/backbone/backbone-go/infrastructure/logging"
	bbex "github.com/FreakJazz/backbone/backbone-go/interfaces/responses"
	"github.com/freakjazz/clean-api-go/domain/entities"
	"github.com/freakjazz/clean-api-go/domain/repositories"
)

type GetStockMovementsQuery struct {
	ProductID string
	Page      int
	PageSize  int
}

// Items is []*entities.StockMovement rather than []map[string]interface{}
// — see GetProductsResult's doc comment for why.
type GetStockMovementsResult struct {
	Items      []*entities.StockMovement
	TotalCount int
	Page       int
	PageSize   int
}

type GetStockMovementsQueryHandler struct {
	repo   repositories.IStockMovementRepository
	logger *logging.EnhancedLogger
}

func NewGetStockMovementsQueryHandler(repo repositories.IStockMovementRepository) *GetStockMovementsQueryHandler {
	return &GetStockMovementsQueryHandler{
		repo:   repo,
		logger: logging.NewEnhancedLogger("clean-api-go").WithLayer("application").WithComponent("GetStockMovementsQueryHandler").WithMethod("Handle"),
	}
}

func (h *GetStockMovementsQueryHandler) Handle(ctx context.Context, q GetStockMovementsQuery) (*GetStockMovementsResult, *bbex.ErrorResponse) {
	log := h.logger

	movements, total, err := h.repo.FindByProductID(ctx, q.ProductID, q.Page, q.PageSize)
	if err != nil {
		log.ErrorWithCode("FindByProductID failed", bberrors.InfraDBFailure.Int(), map[string]interface{}{"error": err.Error()})
		e := bbex.ErrorResponseBuilder.InternalServerError(err.Error())
		return nil, &e
	}

	return &GetStockMovementsResult{Items: movements, TotalCount: total, Page: q.Page, PageSize: q.PageSize}, nil
}
