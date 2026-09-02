package queries

import (
	"context"

	bberrors "github.com/FreakJazz/backbone/backbone-go/errors"
	bbex "github.com/FreakJazz/backbone/backbone-go/interfaces/responses"
	"github.com/FreakJazz/backbone/backbone-go/infrastructure/logging"
	"github.com/freakjazz/clean-api-go/domain/entities"
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
		logger: logging.NewEnhancedLogger("clean-api-go").WithLayer("application").WithComponent("GetProductByIDQueryHandler").WithMethod("Handle"),
	}
}

// Handle returns *entities.Product directly — backbone-go's
// SimpleObjectResponseBuilder.Found accepts any JSON-marshalable value, so
// there's no need to flatten the entity into a map[string]interface{} first
// just to satisfy the response builder's signature.
func (h *GetProductByIDQueryHandler) Handle(ctx context.Context, q GetProductByIDQuery) (*entities.Product, *bbex.ErrorResponse) {
	log := h.logger

	product, err := h.repo.FindByID(ctx, q.ProductID)
	if err != nil || product == nil {
		log.Warning("Product not found", map[string]interface{}{"id": q.ProductID})
		e := bbex.ErrorResponseBuilder.NotFound("product not found",
			bbex.ErrorOpts{Code: bberrors.AppResourceNotFound.Int()})
		return nil, &e
	}

	log.Info("Product found", map[string]interface{}{"id": product.ID})
	return product, nil
}
