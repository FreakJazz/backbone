package commands

import (
	"context"
	"strings"

	bberrors "github.com/freakjazz/backbone-go/errors"
	bbex "github.com/freakjazz/backbone-go/interfaces/responses"
	"github.com/freakjazz/clean-api-go/domain/repositories"
)

type UpdateProductCommand struct {
	ProductID   string
	Name        *string
	Price       *float64
	Category    *string
	Description *string
}

type UpdateProductCommandHandler struct {
	repo repositories.IProductRepository
}

func NewUpdateProductCommandHandler(repo repositories.IProductRepository) *UpdateProductCommandHandler {
	return &UpdateProductCommandHandler{repo: repo}
}

func (h *UpdateProductCommandHandler) Handle(ctx context.Context, cmd UpdateProductCommand) (string, *bbex.ErrorResponse) {
	product, err := h.repo.FindByID(ctx, cmd.ProductID)
	if err != nil || product == nil {
		e := bbex.ErrorResponseBuilder.NotFound("product not found")
		return "", &e
	}

	if cmd.Name != nil {
		if len(strings.TrimSpace(*cmd.Name)) < 2 {
			e := bbex.ErrorResponseBuilder.ValidationError("name must be at least 2 characters",
				bbex.ErrorOpts{
					FieldErrors: map[string]string{"name": "min length 2"},
					Code:        bberrors.IfcInvalidRequestBody.Int(),
				})
			return "", &e
		}
		product.Name = strings.TrimSpace(*cmd.Name)
	}
	if cmd.Price != nil {
		if *cmd.Price <= 0 {
			e := bbex.ErrorResponseBuilder.ValidationError("price must be greater than 0",
				bbex.ErrorOpts{
					FieldErrors: map[string]string{"price": "must be > 0"},
					Code:        bberrors.IfcInvalidRequestBody.Int(),
				})
			return "", &e
		}
		product.Price = *cmd.Price
	}
	if cmd.Category != nil {
		product.Category = *cmd.Category
	}
	if cmd.Description != nil {
		product.Description = *cmd.Description
	}

	if _, err := h.repo.Save(ctx, product); err != nil {
		e := bbex.ErrorResponseBuilder.InternalServerError(err.Error())
		return "", &e
	}
	return product.ID, nil
}
