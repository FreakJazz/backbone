package commands

import (
	"context"
	"strings"

	bberrors "github.com/freakjazz/backbone-go/errors"
	bbex "github.com/freakjazz/backbone-go/interfaces/responses"
	"github.com/freakjazz/clean-api-go/domain/entities"
	"github.com/freakjazz/clean-api-go/domain/repositories"
)

type CreateProductCommand struct {
	Name        string
	Price       float64
	Category    string
	Description string
}

type CreateProductCommandHandler struct {
	repo repositories.IProductRepository
}

func NewCreateProductCommandHandler(repo repositories.IProductRepository) *CreateProductCommandHandler {
	return &CreateProductCommandHandler{repo: repo}
}

func (h *CreateProductCommandHandler) Handle(ctx context.Context, cmd CreateProductCommand) (string, *bbex.ErrorResponse) {
	if strings.TrimSpace(cmd.Name) == "" || len(strings.TrimSpace(cmd.Name)) < 2 {
		e := bbex.ErrorResponseBuilder.ValidationError("name must be at least 2 characters",
			bbex.ErrorOpts{
				FieldErrors: map[string]string{"name": "min length 2"},
				Code:        bberrors.IfcInvalidRequestBody.Int(),
			})
		return "", &e
	}
	if cmd.Price <= 0 {
		e := bbex.ErrorResponseBuilder.ValidationError("price must be greater than 0",
			bbex.ErrorOpts{
				FieldErrors: map[string]string{"price": "must be > 0"},
				Code:        bberrors.IfcInvalidRequestBody.Int(),
			})
		return "", &e
	}
	if strings.TrimSpace(cmd.Category) == "" {
		e := bbex.ErrorResponseBuilder.ValidationError("category is required",
			bbex.ErrorOpts{
				FieldErrors: map[string]string{"category": "required"},
				Code:        bberrors.IfcInvalidRequestBody.Int(),
			})
		return "", &e
	}

	product := entities.NewProduct(
		strings.TrimSpace(cmd.Name),
		cmd.Price,
		cmd.Category,
		cmd.Description,
	)
	saved, err := h.repo.Save(ctx, product)
	if err != nil {
		e := bbex.ErrorResponseBuilder.InternalServerError(err.Error())
		return "", &e
	}
	return saved.ID, nil
}
