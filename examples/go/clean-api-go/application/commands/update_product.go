package commands

import (
	"context"
	"strings"

	bberrors "github.com/freakjazz/backbone-go/errors"
	bbex "github.com/freakjazz/backbone-go/interfaces/responses"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
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
	repo   repositories.IProductRepository
	logger *logging.EnhancedLogger
}

func NewUpdateProductCommandHandler(repo repositories.IProductRepository) *UpdateProductCommandHandler {
	return &UpdateProductCommandHandler{
		repo:   repo,
		logger: logging.NewEnhancedLogger("clean-api-go").WithLayer("application").WithComponent("UpdateProductCommandHandler"),
	}
}

func (h *UpdateProductCommandHandler) Handle(ctx context.Context, cmd UpdateProductCommand) (string, *bbex.ErrorResponse) {
	log := h.logger.WithMethod("Handle")

	product, err := h.repo.FindByID(ctx, cmd.ProductID)
	if err != nil || product == nil {
		e := bbex.ErrorResponseBuilder.NotFound("product not found")
		return "", &e
	}

	if cmd.Name != nil {
		name := strings.TrimSpace(*cmd.Name)
		if len(name) < 2 {
			e := bbex.ErrorResponseBuilder.ValidationError("name must be at least 2 characters",
				bbex.ErrorOpts{Code: bberrors.IfcInvalidRequestBody.Int()})
			return "", &e
		}
		if !strings.EqualFold(name, product.Name) {
			existing, _ := h.repo.FindByName(ctx, name)
			if existing != nil {
				e := bbex.ErrorResponseBuilder.Conflict("a product with that name already exists",
					bbex.ErrorOpts{Code: bberrors.AppConflict.Int()})
				return "", &e
			}
		}
		product.Name = name
	}
	if cmd.Price != nil {
		if *cmd.Price <= 0 {
			e := bbex.ErrorResponseBuilder.ValidationError("price must be greater than 0",
				bbex.ErrorOpts{Code: bberrors.IfcInvalidRequestBody.Int()})
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
		log.ErrorWithCode("Save failed", bberrors.InfraDBFailure.Int(), map[string]interface{}{"error": err.Error()})
		e := bbex.ErrorResponseBuilder.InternalServerError(err.Error())
		return "", &e
	}

	log.Info("Product updated", map[string]interface{}{"id": product.ID})
	return product.ID, nil
}
