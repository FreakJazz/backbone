package queries

import (
	"context"

	bberrors "github.com/freakjazz/backbone-go/errors"
	bbex "github.com/freakjazz/backbone-go/interfaces/responses"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
	"github.com/freakjazz/clean-api-go/domain/repositories"
)

type GetProductByIDQuery struct {
	ProductID string
}

type GetProductByIDQueryHandler struct {
	repo   repositories.IProductRepository
	logger *logging.EnhancedLogger
}

func NewGetProductByIDQueryHandler(repo repositories.IProductRepository) *GetProductByIDQueryHandler {
	return &GetProductByIDQueryHandler{
		repo:   repo,
		logger: logging.NewEnhancedLogger("clean-api-go").WithLayer("application").WithComponent("GetProductByIDQueryHandler"),
	}
}

func (h *GetProductByIDQueryHandler) Handle(ctx context.Context, q GetProductByIDQuery) (map[string]interface{}, *bbex.ErrorResponse) {
	log := h.logger.WithMethod("Handle")

	product, err := h.repo.FindByID(ctx, q.ProductID)
	if err != nil || product == nil {
		log.Warning("Product not found", map[string]interface{}{"id": q.ProductID})
		e := bbex.ErrorResponseBuilder.NotFound("product not found",
			bbex.ErrorOpts{Code: bberrors.AppResourceNotFound.Int()})
		return nil, &e
	}

	log.Info("Product found", map[string]interface{}{"id": product.ID})
	return product.ToMap(), nil
}
