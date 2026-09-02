package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/FreakJazz/backbone/backbone-go/interfaces/responses"
	"github.com/freakjazz/clean-api-go/application/queries"
)

type ProductQueryHandler struct {
	list   *queries.GetProductsQueryHandler
	page   *queries.GetProductsPageQueryHandler
	detail *queries.GetProductByIDQueryHandler
}

func NewProductQueryHandler(
	list *queries.GetProductsQueryHandler,
	page *queries.GetProductsPageQueryHandler,
	detail *queries.GetProductByIDQueryHandler,
) *ProductQueryHandler {
	return &ProductQueryHandler{list: list, page: page, detail: detail}
}

// List godoc
// @Summary      List products
// @Description  Offset-paginated by default (page/page_size). Pass ?cursor=<token> instead to switch to keyset pagination — recommended for deep paging, since it doesn't degrade as the offset grows. The two modes are mutually exclusive: cursor, when present, wins and page/page_size are ignored.
// @Tags         products
// @Produce      json
// @Param        filters   query  []string  false  "Repeated filter tokens e.g. category,eq,Electronics,and &filters=price,gt,500" collectionFormat(multi)
// @Param        page      query  int     false  "Page number, offset mode only (default 1)"
// @Param        page_size query  int     false  "Items per page (default 10)"
// @Param        sort_by   query  string  false  "Sort field and direction e.g. price:desc"
// @Param        cursor    query  string  false  "Opaque token from a previous response's page.next_cursor — switches to keyset pagination"
// @Success      200  {object}  map[string]interface{}
// @Failure      500  {object}  handlers.ErrorResponse
// @Router       /api/v1/products [get]
func (h *ProductQueryHandler) List(w http.ResponseWriter, r *http.Request) {
	cursor := r.URL.Query().Get("cursor")
	if cursor != "" || r.URL.Query().Has("cursor") {
		h.listByCursor(w, r, cursor)
		return
	}

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

// listByCursor serves the keyset-pagination path: no total_count/page (a
// keyset window can't produce a total without an extra COUNT query, which
// would defeat the point) — just the page and, if there's more, a cursor
// for the next one.
func (h *ProductQueryHandler) listByCursor(w http.ResponseWriter, r *http.Request, cursor string) {
	q := queries.GetProductsPageQuery{
		Filters:  r.URL.Query()["filters"],
		SortBy:   r.URL.Query().Get("sort_by"),
		Cursor:   cursor,
		PageSize: intParam(r, "page_size", 10),
	}
	result, errResp := h.page.Handle(r.Context(), q)
	if errResp != nil {
		writeError(w, *errResp)
		return
	}
	resp := responses.CursorPaginatedResponseBuilder.Success(
		result.Items, result.NextCursor, "Products retrieved successfully",
	)
	writeJSON(w, http.StatusOK, resp)
}

// Detail godoc
// @Summary      Get product by ID
// @Description  Returns a single product
// @Tags         products
// @Produce      json
// @Param        id  path  string  true  "Product ID"
// @Success      200  {object}  map[string]interface{}
// @Failure      404  {object}  handlers.ErrorResponse
// @Router       /api/v1/products/{id} [get]
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
