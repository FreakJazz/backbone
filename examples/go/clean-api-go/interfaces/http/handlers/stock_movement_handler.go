package handlers

import (
	"encoding/json"
	"net/http"

	"github.com/FreakJazz/backbone/backbone-go/interfaces/responses"
	"github.com/freakjazz/clean-api-go/application/commands"
	"github.com/freakjazz/clean-api-go/application/queries"
)

type StockMovementHandler struct {
	register *commands.RegisterStockMovementCommandHandler
	list     *queries.GetStockMovementsQueryHandler
}

func NewStockMovementHandler(register *commands.RegisterStockMovementCommandHandler, list *queries.GetStockMovementsQueryHandler) *StockMovementHandler {
	return &StockMovementHandler{register: register, list: list}
}

// Register godoc
// @Summary      Register a stock movement
// @Description  Adjusts product stock (PostgreSQL) and logs the movement (MongoDB)
// @Tags         stock-movements
// @Accept       json
// @Produce      json
// @Param        body  body  handlers.RegisterStockMovementRequest  true  "Movement data"
// @Success      201  {object}  map[string]string
// @Failure      400  {object}  handlers.ErrorResponse
// @Failure      409  {object}  handlers.ErrorResponse  "would take stock below zero"
// @Router       /api/v1/stock-movements [post]
func (h *StockMovementHandler) Register(w http.ResponseWriter, r *http.Request) {
	var body RegisterStockMovementRequest
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeError(w, responses.ErrorResponseBuilder.ValidationError(errInvalidBody))
		return
	}
	id, errResp := h.register.Handle(r.Context(), commands.RegisterStockMovementCommand{
		ProductID: body.ProductID, Type: body.Type, Quantity: body.Quantity, Reason: body.Reason,
	})
	if errResp != nil {
		writeError(w, *errResp)
		return
	}
	writeJSON(w, http.StatusCreated, responses.ProcessResponseBuilder.Created(id))
}

// List godoc
// @Summary      List stock movements
// @Description  Returns stock movements, optionally filtered by product_id
// @Tags         stock-movements
// @Produce      json
// @Param        product_id  query  string  false  "Filter by product"
// @Param        page        query  int     false  "Page number (default 1)"
// @Param        page_size   query  int     false  "Items per page (default 10)"
// @Success      200  {object}  map[string]interface{}
// @Router       /api/v1/stock-movements [get]
func (h *StockMovementHandler) List(w http.ResponseWriter, r *http.Request) {
	q := queries.GetStockMovementsQuery{
		ProductID: r.URL.Query().Get("product_id"),
		Page:      intParam(r, "page", 1),
		PageSize:  intParam(r, "page_size", 10),
	}
	result, errResp := h.list.Handle(r.Context(), q)
	if errResp != nil {
		writeError(w, *errResp)
		return
	}
	resp := responses.PaginatedResponseBuilder.Success(
		result.Items, result.TotalCount, result.Page, result.PageSize,
		"Stock movements retrieved successfully",
	)
	writeJSON(w, http.StatusOK, resp)
}

type RegisterStockMovementRequest struct {
	ProductID string `json:"product_id" example:"a99ec39f-6a2b-4c05-883d-1973f511b325"`
	Type      string `json:"type"       example:"IN" enums:"IN,OUT,ADJUSTMENT"`
	Quantity  int    `json:"quantity"   example:"10"`
	Reason    string `json:"reason"     example:"restock from supplier"`
}
