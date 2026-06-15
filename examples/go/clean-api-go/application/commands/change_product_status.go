package commands

import (
	"context"

	bberrors "github.com/freakjazz/backbone-go/errors"
	bbex "github.com/freakjazz/backbone-go/interfaces/responses"
	"github.com/freakjazz/clean-api-go/domain/repositories"
)

var validStatuses = map[string]bool{
	"active": true, "inactive": true, "discontinued": true,
}

type ChangeProductStatusCommand struct {
	ProductID string
	Status    string
}

type ChangeProductStatusCommandHandler struct {
	repo repositories.IProductRepository
}

func NewChangeProductStatusCommandHandler(repo repositories.IProductRepository) *ChangeProductStatusCommandHandler {
	return &ChangeProductStatusCommandHandler{repo: repo}
}

func (h *ChangeProductStatusCommandHandler) Handle(ctx context.Context, cmd ChangeProductStatusCommand) (string, *bbex.ErrorResponse) {
	if !validStatuses[cmd.Status] {
		e := bbex.ErrorResponseBuilder.ValidationError("status must be active, inactive, or discontinued",
			bbex.ErrorOpts{
				FieldErrors: map[string]string{"status": "invalid value"},
				Code:        bberrors.IfcInvalidRequestBody.Int(),
			})
		return "", &e
	}

	product, err := h.repo.FindByID(ctx, cmd.ProductID)
	if err != nil || product == nil {
		e := bbex.ErrorResponseBuilder.NotFound("product not found")
		return "", &e
	}

	product.Status = cmd.Status
	if _, err := h.repo.Save(ctx, product); err != nil {
		e := bbex.ErrorResponseBuilder.InternalServerError(err.Error())
		return "", &e
	}
	return product.ID, nil
}
