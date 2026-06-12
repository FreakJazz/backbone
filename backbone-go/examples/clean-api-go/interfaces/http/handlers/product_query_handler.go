// Package handlers contains HTTP adapters — read side (CQRS).
package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/freakjazz/backbone-go/examples/clean-api-go/application/queries"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/entities"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/interfaces/http/middleware"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
	"github.com/freakjazz/backbone-go/interfaces/responses"
)

// ProductQueryHandler is the thin HTTP adapter for read operations.
// It parses HTTP requests, calls the appropriate query handler,
// and maps results to HTTP responses. Contains NO business logic.
type ProductQueryHandler struct {
	getListHandler  *queries.GetProductsQueryHandler
	getByIDHandler  *queries.GetProductByIDQueryHandler
	logger          *logging.EnhancedLogger
}

// NewProductQueryHandler creates a new HTTP query adapter.
func NewProductQueryHandler(
	getList  *queries.GetProductsQueryHandler,
	getByID  *queries.GetProductByIDQueryHandler,
	logger   *logging.EnhancedLogger,
) *ProductQueryHandler {
	return &ProductQueryHandler{
		getListHandler: getList,
		getByIDHandler: getByID,
		logger:         logger,
	}
}

// GetProducts handles GET /api/v1/products  →  paginated envelope  HTTP 200
//
// Query params (4 generic):
//
//	filters   — repeated: "field,operator,value[,condition]"
//	            operators : eq ne gt gte lt lte contains in between is_null is_not_null
//	            example   : ?filters=category,eq,Electronics,and&filters=price,gt,500
//	page      — int (default 1)
//	page_size — int (default 10)
//	sort_by   — "field:direction"  e.g. price:desc  (default created_at:desc)
func (h *ProductQueryHandler) GetProducts(w http.ResponseWriter, r *http.Request) {
	log := h.log("GetProducts", r)
	log.Info("Handling GetProducts query", nil)

	q := r.URL.Query()
	page, _ := strconv.Atoi(q.Get("page"))
	if page < 1 {
		page = 1
	}
	pageSize, _ := strconv.Atoi(q.Get("page_size"))
	if pageSize < 1 {
		pageSize = 10
	}

	query := queries.GetProductsQuery{
		Filters:  q["filters"],
		Page:     page,
		PageSize: pageSize,
		SortBy:   q.Get("sort_by"),
	}

	result, err := h.getListHandler.Handle(r.Context(), query)
	if err != nil {
		resp := responses.ErrorResponseBuilder.InternalServerError(err.Error(), errOpts(r))
		sendJSON(w, resp.StatusCode, resp)
		return
	}

	items := make([]map[string]interface{}, 0, len(result.Products))
	for _, p := range result.Products {
		items = append(items, productMap(p))
	}

	resp := responses.PaginatedResponseBuilder.Success(
		items, int(result.TotalCount), result.Page, result.PageSize,
		"Products retrieved successfully",
	)

	log.Info("Products retrieved", map[string]interface{}{
		"count": len(items), "total": result.TotalCount,
	})
	sendJSON(w, http.StatusOK, resp)
}

// GetProductByID handles GET /api/v1/products/{id}  →  raw product object  HTTP 200
func (h *ProductQueryHandler) GetProductByID(w http.ResponseWriter, r *http.Request, id string) {
	log := h.log("GetProductByID", r)
	log.Info("Handling GetProductByID query", map[string]interface{}{"product_id": id})

	result, err := h.getByIDHandler.Handle(r.Context(), queries.GetProductByIDQuery{ID: id})
	if err != nil {
		resp := responses.ErrorResponseBuilder.NotFound("Product not found", errOpts(r))
		sendJSON(w, resp.StatusCode, resp)
		return
	}

	log.Info("Product found", map[string]interface{}{"product_id": id})
	sendJSON(w, http.StatusOK, responses.SimpleObjectResponseBuilder.Found(productMap(result.Product)))
}

func (h *ProductQueryHandler) log(method string, r *http.Request) *logging.EnhancedLogger {
	return h.logger.
		WithLayer("interfaces").
		WithHandler("ProductQueryHandler").
		WithMethod(method).
		WithContext(map[string]interface{}{
			"request_id": middleware.RequestIDFromContext(r.Context()),
			"method":     r.Method,
			"path":       r.URL.Path,
		})
}

// sendJSON writes a JSON response — shared by both command and query handlers.
func sendJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

// errOpts builds ErrorOpts from the request context — passes the RID set by
// LoggingMiddleware so every error response carries the same trace identifier
// that appears in the logs.
func errOpts(r *http.Request) responses.ErrorOpts {
	return responses.ErrorOpts{RID: middleware.RequestIDFromContext(r.Context())}
}

// productMap converts a Product entity to a plain map for JSON serialization.
func productMap(p *entities.Product) map[string]interface{} {
	return map[string]interface{}{
		"id":          p.ID,
		"name":        p.Name,
		"description": p.Description,
		"price":       p.Price,
		"category":    p.Category,
		"stock":       p.Stock,
		"active":      p.Active,
		"created_at":  p.CreatedAt,
		"updated_at":  p.UpdatedAt,
	}
}
