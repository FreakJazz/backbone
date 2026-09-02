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

type RegisterSaleCommand struct {
	ProductID string
	Quantity  int
}

// RegisterSaleCommandHandler coordinates two independent stores for one
// business action: PostgreSQL owns the authoritative stock count, MongoDB
// owns the append-only sales log. There is no distributed transaction here
// — stock is decremented first (the step that can legitimately fail, e.g.
// insufficient stock) and the sale is recorded only after that succeeds. If
// the Mongo insert itself fails, stock has already moved and this returns
// an error without rolling it back; a production system would reconcile
// that gap with an outbox/saga instead of a bare two-step call.
type RegisterSaleCommandHandler struct {
	products repositories.IProductRepository
	sales    repositories.ISaleRepository
	logger   *logging.EnhancedLogger
}

func NewRegisterSaleCommandHandler(products repositories.IProductRepository, sales repositories.ISaleRepository) *RegisterSaleCommandHandler {
	return &RegisterSaleCommandHandler{
		products: products,
		sales:    sales,
		logger:   logging.NewEnhancedLogger("clean-api-go").WithLayer("application").WithComponent("RegisterSaleCommandHandler").WithMethod("Handle"),
	}
}

func (h *RegisterSaleCommandHandler) Handle(ctx context.Context, cmd RegisterSaleCommand) (string, *bbex.ErrorResponse) {
	log := h.logger

	if cmd.Quantity <= 0 {
		e := bbex.ErrorResponseBuilder.ValidationError("quantity must be greater than 0",
			bbex.ErrorOpts{Code: bberrors.IfcInvalidRequestBody.Int()})
		return "", &e
	}

	product, err := h.products.FindByID(ctx, cmd.ProductID)
	if err != nil || product == nil {
		e := bbex.ErrorResponseBuilder.NotFound("product not found")
		return "", &e
	}

	if _, err := h.products.AdjustStock(ctx, cmd.ProductID, -cmd.Quantity); err != nil {
		if errors.Is(err, repositories.ErrInsufficientStock) {
			e := bbex.ErrorResponseBuilder.Conflict("insufficient stock for this sale",
				bbex.ErrorOpts{Code: bberrors.AppConflict.Int()})
			return "", &e
		}
		log.ErrorWithCode("AdjustStock failed", bberrors.InfraDBFailure.Int(), map[string]interface{}{"error": err.Error()})
		e := bbex.ErrorResponseBuilder.InternalServerError(err.Error())
		return "", &e
	}

	sale := entities.NewSale(cmd.ProductID, cmd.Quantity, product.Price)
	saved, err := h.sales.Save(ctx, sale)
	if err != nil {
		// Stock was already decremented in Postgres — flagged here rather
		// than silently swallowed, since this is exactly the inconsistency
		// window a saga/outbox pattern exists to close.
		log.ErrorWithCode("Sale record failed after stock was decremented — data inconsistency", bberrors.InfraDBFailure.Int(), map[string]interface{}{
			"product_id": cmd.ProductID, "quantity": cmd.Quantity, "error": err.Error(),
		})
		e := bbex.ErrorResponseBuilder.InternalServerError("sale could not be recorded; stock was already adjusted")
		return "", &e
	}

	log.Info("Sale registered", map[string]interface{}{"sale_id": saved.ID, "product_id": cmd.ProductID, "quantity": cmd.Quantity})
	return saved.ID, nil
}
