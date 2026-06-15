package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/freakjazz/backbone-go/interfaces/responses"
	"github.com/freakjazz/clean-api-go/application/queries"
)

type ProductQueryHandler struct {
	list   *queries.GetProductsQueryHandler
	detail *queries.GetProductByIDQueryHandler
}

func NewProductQueryHandler(
	list *queries.GetProductsQueryHandler,
	detail *queries.GetProductByIDQueryHandler,
) *ProductQueryHandler {
	return &ProductQueryHandler{list: list, detail: detail}
}

func (h *ProductQueryHandler) List(w http.ResponseWriter, r *http.Request) {
	q := queries.GetProductsQuery{
		Filters:  r.URL.Query()["filters"],
		SortBy:   r.URL.Query().Get("sort_by"),
		Page:     intParam(r, "page", 1),
		PageSize: intParam(r, "page_size", 10),
	}
	result, errResp := h.list.Handle(r.Context(), q)
	if errResp != nil {
		writeError(w, *errResp)
		return
	}
	resp := responses.PaginatedResponseBuilder.Success(
		result.Items, result.TotalCount, result.Page, result.PageSize,
		"Products retrieved successfully",
	)
	writeJSON(w, http.StatusOK, resp)
}

func (h *ProductQueryHandler) Detail(w http.ResponseWriter, r *http.Request, productID string) {
	data, errResp := h.detail.Handle(r.Context(), queries.GetProductByIDQuery{ProductID: productID})
	if errResp != nil {
		writeError(w, *errResp)
		return
	}
	writeJSON(w, http.StatusOK, responses.SimpleObjectResponseBuilder.Found(data))
}

// ── helpers ──────────────────────────────────────────────────────────────────

func writeJSON(w http.ResponseWriter, status int, v interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v) //nolint:errcheck
}

func writeError(w http.ResponseWriter, e responses.ErrorResponse) {
	writeJSON(w, e.StatusCode, e)
}

func intParam(r *http.Request, key string, def int) int {
	if v := r.URL.Query().Get(key); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			return n
		}
	}
	return def
}
