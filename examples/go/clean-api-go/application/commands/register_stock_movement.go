package commands

import (
	"context"
	"errors"

	bberrors "github.com/FreakJazz/backbone/backbone-go/errors"
	"github.com/FreakJazz/backbone/backbone-go/infrastructure/logging"
	bbex "github.com/FreakJazz/backbone/backbone-go/interfaces/responses"
	"github.com/freakjazz/clean-api-go/domain/entities"
	"github.com/freakjazz/clean-api-go/domain/repositories"
)

type RegisterStockMovementCommand struct {
	ProductID string
	Type      string // IN | OUT | ADJUSTMENT
	Quantity  int    // IN/OUT: must be > 0. ADJUSTMENT: signed delta, may be negative.
	Reason    string
}

type RegisterStockMovementCommandHandler struct {
	products  repositories.IProductRepository
	movements repositories.IStockMovementRepository
	logger    *logging.EnhancedLogger
}

func NewRegisterStockMovementCommandHandler(products repositories.IProductRepository, movements repositories.IStockMovementRepository) *RegisterStockMovementCommandHandler {
	return &RegisterStockMovementCommandHandler{
		products:  products,
		movements: movements,
		logger:    logging.NewEnhancedLogger("clean-api-go").WithLayer("application").WithComponent("RegisterStockMovementCommandHandler").WithMethod("Handle"),
	}
}

func (h *RegisterStockMovementCommandHandler) Handle(ctx context.Context, cmd RegisterStockMovementCommand) (string, *bbex.ErrorResponse) {
	log := h.logger

	movType := entities.MovementType(cmd.Type)
	var delta, quantity int
	switch movType {
	case entities.MovementIn:
		if cmd.Quantity <= 0 {
			e := bbex.ErrorResponseBuilder.ValidationError("quantity must be greater than 0 for IN movements",
				bbex.ErrorOpts{Code: bberrors.IfcInvalidRequestBody.Int()})
			return "", &e
		}
		delta, quantity = cmd.Quantity, cmd.Quantity
	case entities.MovementOut:
		if cmd.Quantity <= 0 {
			e := bbex.ErrorResponseBuilder.ValidationError("quantity must be greater than 0 for OUT movements",
				bbex.ErrorOpts{Code: bberrors.IfcInvalidRequestBody.Int()})
			return "", &e
		}
		delta, quantity = -cmd.Quantity, cmd.Quantity
	case entities.MovementAdjustment:
		if cmd.Quantity == 0 {
			e := bbex.ErrorResponseBuilder.ValidationError("quantity must be non-zero for ADJUSTMENT movements",
				bbex.ErrorOpts{Code: bberrors.IfcInvalidRequestBody.Int()})
			return "", &e
		}
		delta, quantity = cmd.Quantity, abs(cmd.Quantity)
	default:
		e := bbex.ErrorResponseBuilder.ValidationError("type must be one of: IN, OUT, ADJUSTMENT",
			bbex.ErrorOpts{Code: bberrors.IfcInvalidRequestBody.Int()})
		return "", &e
	}

	if !h.products.Exists(ctx, cmd.ProductID) {
		e := bbex.ErrorResponseBuilder.NotFound("product not found")
		return "", &e
	}

	if _, err := h.products.AdjustStock(ctx, cmd.ProductID, delta); err != nil {
		if errors.Is(err, repositories.ErrInsufficientStock) {
			e := bbex.ErrorResponseBuilder.Conflict("movement would take stock below zero",
				bbex.ErrorOpts{Code: bberrors.AppConflict.Int()})
			return "", &e
		}
		log.ErrorWithCode("AdjustStock failed", bberrors.InfraDBFailure.Int(), map[string]interface{}{"error": err.Error()})
		e := bbex.ErrorResponseBuilder.InternalServerError(err.Error())
		return "", &e
	}

	movement := entities.NewStockMovement(cmd.ProductID, movType, quantity, delta, cmd.Reason)
	saved, err := h.movements.Save(ctx, movement)
	if err != nil {
		log.ErrorWithCode("Movement record failed after stock was adjusted — data inconsistency", bberrors.InfraDBFailure.Int(), map[string]interface{}{
			"product_id": cmd.ProductID, "delta": delta, "error": err.Error(),
		})
		e := bbex.ErrorResponseBuilder.InternalServerError("movement could not be recorded; stock was already adjusted")
		return "", &e
	}

	log.Info("Stock movement registered", map[string]interface{}{"movement_id": saved.ID, "product_id": cmd.ProductID, "delta": delta})
	return saved.ID, nil
}

func abs(n int) int {
	if n < 0 {
		return -n
	}
	return n
}
