package commands

import (
	"context"
	"strings"

	bberrors "github.com/freakjazz/backbone-go/errors"
	bbex "github.com/freakjazz/backbone-go/interfaces/responses"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
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
	repo   repositories.IProductRepository
	logger *logging.EnhancedLogger
}

func NewCreateProductCommandHandler(repo repositories.IProductRepository) *CreateProductCommandHandler {
	return &CreateProductCommandHandler{
		repo:   repo,
		logger: logging.NewEnhancedLogger("clean-api-go").WithLayer("application").WithComponent("CreateProductCommandHandler"),
	}
}

func (h *CreateProductCommandHandler) Handle(ctx context.Context, cmd CreateProductCommand) (string, *bbex.ErrorResponse) {
	log := h.logger.WithMethod("Handle")

	name := strings.TrimSpace(cmd.Name)
	if len(name) < 2 {
		e := bbex.ErrorResponseBuilder.ValidationError("name must be at least 2 characters",
			bbex.ErrorOpts{Code: bberrors.IfcInvalidRequestBody.Int()})
		return "", &e
	}
	if cmd.Price <= 0 {
		e := bbex.ErrorResponseBuilder.ValidationError("price must be greater than 0",
			bbex.ErrorOpts{Code: bberrors.IfcInvalidRequestBody.Int()})
		return "", &e
	}
	if strings.TrimSpace(cmd.Category) == "" {
		e := bbex.ErrorResponseBuilder.ValidationError("category is required",
			bbex.ErrorOpts{Code: bberrors.IfcInvalidRequestBody.Int()})
		return "", &e
	}

	existing, _ := h.repo.FindByName(ctx, name)
	if existing != nil {
		log.Warning("Duplicate product name", map[string]interface{}{"name": name})
		e := bbex.ErrorResponseBuilder.Conflict("a product with that name already exists",
			bbex.ErrorOpts{Code: bberrors.AppConflict.Int()})
		return "", &e
	}

	product := entities.NewProduct(name, cmd.Price, cmd.Category, cmd.Description)
	saved, err := h.repo.Save(ctx, product)
	if err != nil {
		log.ErrorWithCode("Save failed", bberrors.InfraDBFailure.Int(), map[string]interface{}{"error": err.Error()})
		e := bbex.ErrorResponseBuilder.InternalServerError(err.Error())
		return "", &e
	}

	log.Info("Product created", map[string]interface{}{"id": saved.ID, "name": saved.Name})
	return saved.ID, nil
}
