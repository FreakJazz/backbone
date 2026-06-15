package commands

import (
	"context"

	bberrors "github.com/freakjazz/backbone-go/errors"
	bbex "github.com/freakjazz/backbone-go/interfaces/responses"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
	"github.com/freakjazz/clean-api-go/domain/repositories"
)

var validStatuses = map[string]bool{"active": true, "inactive": true, "discontinued": true}

type ChangeProductStatusCommand struct {
	ProductID string
	Status    string
}

type ChangeProductStatusCommandHandler struct {
	repo   repositories.IProductRepository
	logger *logging.EnhancedLogger
}

func NewChangeProductStatusCommandHandler(repo repositories.IProductRepository) *ChangeProductStatusCommandHandler {
	return &ChangeProductStatusCommandHandler{
		repo:   repo,
		logger: logging.NewEnhancedLogger("clean-api-go").WithLayer("application").WithComponent("ChangeProductStatusCommandHandler"),
	}
}

func (h *ChangeProductStatusCommandHandler) Handle(ctx context.Context, cmd ChangeProductStatusCommand) (string, *bbex.ErrorResponse) {
	log := h.logger.WithMethod("Handle")

	if !validStatuses[cmd.Status] {
		e := bbex.ErrorResponseBuilder.ValidationError("status must be one of: active, inactive, discontinued",
			bbex.ErrorOpts{Code: bberrors.IfcInvalidRequestBody.Int()})
		return "", &e
	}

	product, err := h.repo.FindByID(ctx, cmd.ProductID)
	if err != nil || product == nil {
		e := bbex.ErrorResponseBuilder.NotFound("product not found")
		return "", &e
	}

	product.Status = cmd.Status
	if _, err := h.repo.Save(ctx, product); err != nil {
		log.ErrorWithCode("Save failed", bberrors.InfraDBFailure.Int(), map[string]interface{}{"error": err.Error()})
		e := bbex.ErrorResponseBuilder.InternalServerError(err.Error())
		return "", &e
	}

	log.Info("Product status changed", map[string]interface{}{"id": product.ID, "status": cmd.Status})
	return product.ID, nil
}
