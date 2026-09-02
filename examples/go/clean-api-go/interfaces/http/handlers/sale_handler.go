package handlers

import (
	"encoding/json"
	"net/http"

	"github.com/FreakJazz/backbone/backbone-go/interfaces/responses"
	"github.com/freakjazz/clean-api-go/application/commands"
	"github.com/freakjazz/clean-api-go/application/queries"
)

type SaleHandler struct {
	register *commands.RegisterSaleCommandHandler
	list     *queries.GetSalesQueryHandler
}

func NewSaleHandler(register *commands.RegisterSaleCommandHandler, list *queries.GetSalesQueryHandler) *SaleHandler {
	return &SaleHandler{register: register, list: list}
}

// Register godoc
// @Summary      Register a sale
// @Description  Decrements product stock (PostgreSQL) and logs the sale (MongoDB)
// @Tags         sales
// @Accept       json
// @Produce      json
// @Param        body  body  handlers.RegisterSaleRequest  true  "Sale data"
// @Success      201  {object}  map[string]string
// @Failure      400  {object}  handlers.ErrorResponse
// @Failure      409  {object}  handlers.ErrorResponse  "insufficient stock"
// @Router       /api/v1/sales [post]
func (h *SaleHandler) Register(w http.ResponseWriter, r *http.Request) {
	var body RegisterSaleRequest
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeError(w, responses.ErrorResponseBuilder.ValidationError(errInvalidBody))
		return
	}
	id, errResp := h.register.Handle(r.Context(), commands.RegisterSaleCommand{
		ProductID: body.ProductID, Quantity: body.Quantity,
	})
	if errResp != nil {
		writeError(w, *errResp)
		return
	}
	writeJSON(w, http.StatusCreated, responses.ProcessResponseBuilder.Created(id))
}

// List godoc
// @Summary      List sales
// @Description  Returns sales, optionally filtered by product_id
// @Tags         sales
// @Produce      json
// @Param        product_id  query  string  false  "Filter by product"
// @Param        page        query  int     false  "Page number (default 1)"
// @Param        page_size   query  int     false  "Items per page (default 10)"
// @Success      200  {object}  map[string]interface{}
// @Router       /api/v1/sales [get]
func (h *SaleHandler) List(w http.ResponseWriter, r *http.Request) {
	q := queries.GetSalesQuery{
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
		"Sales retrieved successfully",
	)
	writeJSON(w, http.StatusOK, resp)
}

type RegisterSaleRequest struct {
	ProductID string `json:"product_id" example:"a99ec39f-6a2b-4c05-883d-1973f511b325"`
	Quantity  int    `json:"quantity"   example:"2"`
}
