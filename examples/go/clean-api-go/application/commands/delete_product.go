package commands

import (
	"context"

	bberrors "github.com/FreakJazz/backbone/backbone-go/errors"
	bbex "github.com/FreakJazz/backbone/backbone-go/interfaces/responses"
	"github.com/FreakJazz/backbone/backbone-go/infrastructure/logging"
	"github.com/freakjazz/clean-api-go/domain/repositories"
)

type DeleteProductCommand struct {
	ProductID string
}

type DeleteProductCommandHandler struct {
	repo   repositories.IProductRepository
	logger *logging.EnhancedLogger
}

func NewDeleteProductCommandHandler(repo repositories.IProductRepository) *DeleteProductCommandHandler {
	return &DeleteProductCommandHandler{
		repo:   repo,
		logger: logging.NewEnhancedLogger("clean-api-go").WithLayer("application").WithComponent("DeleteProductCommandHandler").WithMethod("Handle"),
	}
}

func (h *DeleteProductCommandHandler) Handle(ctx context.Context, cmd DeleteProductCommand) (string, *bbex.ErrorResponse) {
	log := h.logger

	if !h.repo.Exists(ctx, cmd.ProductID) {
		e := bbex.ErrorResponseBuilder.NotFound("product not found")
		return "", &e
	}
	if err := h.repo.Delete(ctx, cmd.ProductID); err != nil {
		log.ErrorWithCode("Delete failed", bberrors.InfraDBFailure.Int(), map[string]interface{}{"error": err.Error()})
		e := bbex.ErrorResponseBuilder.InternalServerError(err.Error())
		return "", &e
	}

	log.Info("Product deleted", map[string]interface{}{"id": cmd.ProductID})
	return cmd.ProductID, nil
}
