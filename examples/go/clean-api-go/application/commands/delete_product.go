package commands

import (
	"context"

	bbex "github.com/freakjazz/backbone-go/interfaces/responses"
	"github.com/freakjazz/clean-api-go/domain/repositories"
)

type DeleteProductCommand struct {
	ProductID string
}

type DeleteProductCommandHandler struct {
	repo repositories.IProductRepository
}

func NewDeleteProductCommandHandler(repo repositories.IProductRepository) *DeleteProductCommandHandler {
	return &DeleteProductCommandHandler{repo: repo}
}

func (h *DeleteProductCommandHandler) Handle(ctx context.Context, cmd DeleteProductCommand) (string, *bbex.ErrorResponse) {
	if !h.repo.Exists(ctx, cmd.ProductID) {
		e := bbex.ErrorResponseBuilder.NotFound("product not found")
		return "", &e
	}
	if err := h.repo.Delete(ctx, cmd.ProductID); err != nil {
		e := bbex.ErrorResponseBuilder.InternalServerError(err.Error())
		return "", &e
	}
	return cmd.ProductID, nil
}
