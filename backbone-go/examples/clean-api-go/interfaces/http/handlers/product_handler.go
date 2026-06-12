// Package handlers contains HTTP handlers
package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"
	"strings"

	"github.com/freakjazz/backbone-go/examples/clean-api-go/application/usecases"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/domain/entities"
	"github.com/freakjazz/backbone-go/examples/clean-api-go/interfaces/http/middleware"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
	"github.com/freakjazz/backbone-go/interfaces/responses"
)

// ProductHandler handles all product HTTP requests.
type ProductHandler struct {
	createUseCase       *usecases.CreateProductUseCase
	getListUseCase      *usecases.GetProductsUseCase
	getByIDUseCase      *usecases.GetProductByIDUseCase
	updateUseCase       *usecases.UpdateProductUseCase
	deleteUseCase       *usecases.DeleteProductUseCase
	changeStatusUseCase *usecases.ChangeProductStatusUseCase
	logger              *logging.EnhancedLogger
}

// NewProductHandler creates a new product handler.
func NewProductHandler(
	create *usecases.CreateProductUseCase,
	getList *usecases.GetProductsUseCase,
	getByID *usecases.GetProductByIDUseCase,
	update *usecases.UpdateProductUseCase,
	del *usecases.DeleteProductUseCase,
	changeStatus *usecases.ChangeProductStatusUseCase,
	logger *logging.EnhancedLogger,
) *ProductHandler {
	return &ProductHandler{
		createUseCase:       create,
		getListUseCase:      getList,
		getByIDUseCase:      getByID,
		updateUseCase:       update,
		deleteUseCase:       del,
		changeStatusUseCase: changeStatus,
		logger:              logger,
	}
}

// ----------------------------------------------------------------------------
// POST /api/products
// ----------------------------------------------------------------------------

func (h *ProductHandler) CreateProduct(w http.ResponseWriter, r *http.Request) {
	log := h.log("CreateProduct", r)
	log.Info("Handling create product request", nil)
	opts := errOpts(r)

	var input usecases.CreateProductInput
	if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
		log.ErrorWithCode(msgInvalidJSON, 13001001, map[string]interface{}{"error": err.Error()})
		resp := responses.ErrorResponseBuilder.ValidationError(msgInvalidJSON, opts)
		h.sendJSON(w, resp.StatusCode, resp)
		return
	}

	output, err := h.createUseCase.Execute(r.Context(), input)
	if err != nil {
		log.ErrorWithCode("Create use case failed", 13001002, map[string]interface{}{"error": err.Error()})
		resp := responses.ErrorResponseBuilder.ValidationError(err.Error(), opts)
		h.sendJSON(w, resp.StatusCode, resp)
		return
	}

	log.Info("Product created", map[string]interface{}{"product_id": output.Product.ID})
	h.sendJSON(w, http.StatusCreated, responses.ProcessResponseBuilder.Created(output.Product.ID))
}

// ----------------------------------------------------------------------------
// GET /api/products
// ----------------------------------------------------------------------------

func (h *ProductHandler) GetProducts(w http.ResponseWriter, r *http.Request) {
	log := h.log("GetProducts", r)
	log.Info("Handling get products request", nil)

	input := h.parseQueryParameters(r)

	output, err := h.getListUseCase.Execute(r.Context(), input)
	if err != nil {
		log.ErrorWithCode("Get list use case failed", 13001003, map[string]interface{}{"error": err.Error()})
		resp := responses.ErrorResponseBuilder.InternalServerError("", errOpts(r))
		h.sendJSON(w, resp.StatusCode, resp)
		return
	}

	items := make([]map[string]interface{}, 0, len(output.Products))
	for _, p := range output.Products {
		items = append(items, productToMap(p))
	}

	resp := responses.PaginatedResponseBuilder.Success(
		items,
		int(output.TotalCount),
		output.Page,
		output.PageSize,
		"Products retrieved successfully",
	)

	log.Info("Products retrieved", map[string]interface{}{
		"count": len(items), "total": output.TotalCount,
	})
	h.sendJSON(w, http.StatusOK, resp)
}

// ----------------------------------------------------------------------------
// GET /api/products/{id}
// ----------------------------------------------------------------------------

// GetProductByID returns the raw product object — no envelope wrapper.
func (h *ProductHandler) GetProductByID(w http.ResponseWriter, r *http.Request, id string) {
	log := h.log("GetProductByID", r)
	log.Info("Handling get product by ID", map[string]interface{}{"product_id": id})

	product, err := h.getByIDUseCase.Execute(r.Context(), id)
	if err != nil {
		resp := responses.ErrorResponseBuilder.NotFound(msgProductNotFound, errOpts(r))
		h.sendJSON(w, resp.StatusCode, resp)
		return
	}

	h.sendJSON(w, http.StatusOK, responses.SimpleObjectResponseBuilder.Found(productToMap(product)))
}

// ----------------------------------------------------------------------------
// PUT /api/products/{id}
// ----------------------------------------------------------------------------

func (h *ProductHandler) UpdateProduct(w http.ResponseWriter, r *http.Request, id string) {
	log := h.log("UpdateProduct", r)
	log.Info("Handling update product request", map[string]interface{}{"product_id": id})
	opts := errOpts(r)

	var input usecases.UpdateProductInput
	if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
		resp := responses.ErrorResponseBuilder.ValidationError(msgInvalidJSON, opts)
		h.sendJSON(w, resp.StatusCode, resp)
		return
	}
	input.ID = id

	product, err := h.updateUseCase.Execute(r.Context(), input)
	if err != nil {
		if strings.Contains(err.Error(), errNotFound) {
			resp := responses.ErrorResponseBuilder.NotFound(msgProductNotFound, opts)
			h.sendJSON(w, resp.StatusCode, resp)
			return
		}
		resp := responses.ErrorResponseBuilder.ValidationError(err.Error(), opts)
		h.sendJSON(w, resp.StatusCode, resp)
		return
	}

	log.Info("Product updated", map[string]interface{}{"product_id": product.ID})
	h.sendJSON(w, http.StatusOK, responses.ProcessResponseBuilder.Updated(product.ID))
}

// ----------------------------------------------------------------------------
// DELETE /api/products/{id}
// ----------------------------------------------------------------------------

func (h *ProductHandler) DeleteProduct(w http.ResponseWriter, r *http.Request, id string) {
	log := h.log("DeleteProduct", r)
	log.Info("Handling delete product request", map[string]interface{}{"product_id": id})
	opts := errOpts(r)

	if err := h.deleteUseCase.Execute(r.Context(), id); err != nil {
		if strings.Contains(err.Error(), errNotFound) {
			resp := responses.ErrorResponseBuilder.NotFound(msgProductNotFound, opts)
			h.sendJSON(w, resp.StatusCode, resp)
			return
		}
		resp := responses.ErrorResponseBuilder.InternalServerError("", opts)
		h.sendJSON(w, resp.StatusCode, resp)
		return
	}

	log.Info("Product deleted", map[string]interface{}{"product_id": id})
	h.sendJSON(w, http.StatusOK, responses.ProcessResponseBuilder.Deleted(id))
}

// ----------------------------------------------------------------------------
// PATCH /api/products/{id}/status
// ----------------------------------------------------------------------------

func (h *ProductHandler) ChangeProductStatus(w http.ResponseWriter, r *http.Request, id string) {
	log := h.log("ChangeProductStatus", r)
	log.Info("Handling change product status", map[string]interface{}{"product_id": id})
	opts := errOpts(r)

	var body struct {
		Active bool `json:"active"`
	}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		resp := responses.ErrorResponseBuilder.ValidationError(msgInvalidJSON, opts)
		h.sendJSON(w, resp.StatusCode, resp)
		return
	}

	input := usecases.ChangeProductStatusInput{ID: id, Active: body.Active}
	if err := h.changeStatusUseCase.Execute(r.Context(), input); err != nil {
		if strings.Contains(err.Error(), errNotFound) {
			resp := responses.ErrorResponseBuilder.NotFound(msgProductNotFound, opts)
			h.sendJSON(w, resp.StatusCode, resp)
			return
		}
		resp := responses.ErrorResponseBuilder.InternalServerError("", opts)
		h.sendJSON(w, resp.StatusCode, resp)
		return
	}

	log.Info("Product status changed", map[string]interface{}{"product_id": id, "active": body.Active})
	h.sendJSON(w, http.StatusOK, responses.ProcessResponseBuilder.Updated(id))
}

// ----------------------------------------------------------------------------
// helpers
// ----------------------------------------------------------------------------

func (h *ProductHandler) log(method string, r *http.Request) *logging.EnhancedLogger {
	return h.logger.
		WithLayer("interfaces").
		WithHandler("ProductHandler").
		WithMethod(method).
		WithContext(map[string]interface{}{
			"request_id": middleware.RequestIDFromContext(r.Context()),
			"method":     r.Method,
			"path":       r.URL.Path,
		})
}

func (h *ProductHandler) sendJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

// parseQueryParameters reads the 4 generic query params:
//
//	filters   — repeated, each: "field,operator,value[,condition]"
//	            operators : eq ne gt gte lt lte contains in between is_null is_not_null
//	            conditions: and (default) | or
//	            examples  : ?filters=category,eq,Electronics,and&filters=price,gt,500
//	page      — int (default 1)
//	page_size — int (default 10)
//	sort_by   — "field:direction"  e.g. price:desc  (default created_at:desc)
func (h *ProductHandler) parseQueryParameters(r *http.Request) usecases.GetProductsInput {
	q := r.URL.Query()

	page, _ := strconv.Atoi(q.Get("page"))
	if page < 1 {
		page = 1
	}
	pageSize, _ := strconv.Atoi(q.Get("page_size"))
	if pageSize < 1 {
		pageSize = 10
	}

	return usecases.GetProductsInput{
		Filters:  q["filters"], // all values of the repeated "filters" param
		Page:     page,
		PageSize: pageSize,
		SortBy:   q.Get("sort_by"),
	}
}

// productToMap converts a Product entity to a plain map for JSON responses.
func productToMap(p *entities.Product) map[string]interface{} {
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
