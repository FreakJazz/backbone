// Package handlers contains HTTP handlers
package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/freakjazz/backbone-go/examples/clean-api-go/application/usecases"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
	"github.com/freakjazz/backbone-go/interfaces/responses"
)

// ProductHandler handles product HTTP requests
type ProductHandler struct {
	createUseCase *usecases.CreateProductUseCase
	getUseCase    *usecases.GetProductsUseCase
	logger        *logging.EnhancedLogger
}

// NewProductHandler creates a new product handler
func NewProductHandler(
	createUseCase *usecases.CreateProductUseCase,
	getUseCase *usecases.GetProductsUseCase,
	logger *logging.EnhancedLogger,
) *ProductHandler {
	return &ProductHandler{
		createUseCase: createUseCase,
		getUseCase:    getUseCase,
		logger:        logger,
	}
}

// CreateProduct handles product creation
func (h *ProductHandler) CreateProduct(w http.ResponseWriter, r *http.Request) {
	handlerLogger := h.logger.
		WithLayer("interfaces").
		WithHandler("ProductHandler").
		WithMethod("CreateProduct").
		WithContext(map[string]interface{}{
			"request_id": r.Context().Value("request_id"),
			"method":     r.Method,
			"path":       r.URL.Path,
		})

	handlerLogger.Info("Handling create product request", nil)

	// Parse request body
	var input usecases.CreateProductInput
	if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
		handlerLogger.ErrorWithCode("Invalid JSON payload", 13001001, map[string]interface{}{
			"error": err.Error(),
		})
		response := responses.ErrorResponseBuilder.BadRequest("Invalid JSON payload", map[string]interface{}{
			"error": err.Error(),
		})
		h.sendJSON(w, response.Status, response)
		return
	}

	// Execute use case
	output, err := h.createUseCase.Execute(r.Context(), input)
	if err != nil {
		handlerLogger.ErrorWithCode("Use case failed", 13001002, map[string]interface{}{
			"error": err.Error(),
		})
		response := responses.ErrorResponseBuilder.FromException(err)
		h.sendJSON(w, response.Status, response)
		return
	}

	// Success response
	response := responses.ProcessResponseBuilder.Created(
		"Product created successfully",
		map[string]interface{}{
			"product": output.Product,
		},
	)

	handlerLogger.Info("Product created successfully", map[string]interface{}{
		"product_id": output.Product.ID,
	})

	h.sendJSON(w, response.Status, response)
}

// GetProducts handles getting products with filters
func (h *ProductHandler) GetProducts(w http.ResponseWriter, r *http.Request) {
	handlerLogger := h.logger.
		WithLayer("interfaces").
		WithHandler("ProductHandler").
		WithMethod("GetProducts").
		WithContext(map[string]interface{}{
			"request_id": r.Context().Value("request_id"),
			"method":     r.Method,
			"path":       r.URL.Path,
		})

	handlerLogger.Info("Handling get products request", nil)

	// Parse query parameters
	input := h.parseQueryParameters(r)

	handlerLogger.Debug("Query parameters parsed", map[string]interface{}{
		"category":  input.Category,
		"min_price": input.MinPrice,
		"max_price": input.MaxPrice,
		"in_stock":  input.InStock,
		"page":      input.Page,
		"page_size": input.PageSize,
	})

	// Execute use case
	output, err := h.getUseCase.Execute(r.Context(), input)
	if err != nil {
		handlerLogger.ErrorWithCode("Use case failed", 13001003, map[string]interface{}{
			"error": err.Error(),
		})
		response := responses.ErrorResponseBuilder.FromException(err)
		h.sendJSON(w, response.Status, response)
		return
	}

	// Success response with pagination
	response := responses.QueryResponseBuilder.SuccessWithPagination(
		"Products retrieved successfully",
		output.Products,
		output.Page,
		output.PageSize,
		output.TotalCount,
	)

	handlerLogger.Info("Products retrieved successfully", map[string]interface{}{
		"count":       len(output.Products),
		"total_count": output.TotalCount,
		"page":        output.Page,
	})

	h.sendJSON(w, response.Status, response)
}

// parseQueryParameters parses query parameters for filtering
func (h *ProductHandler) parseQueryParameters(r *http.Request) usecases.GetProductsInput {
	query := r.URL.Query()

	// Parse numeric parameters
	minPrice, _ := strconv.ParseFloat(query.Get("min_price"), 64)
	maxPrice, _ := strconv.ParseFloat(query.Get("max_price"), 64)
	page, _ := strconv.Atoi(query.Get("page"))
	if page < 1 {
		page = 1
	}
	pageSize, _ := strconv.Atoi(query.Get("page_size"))
	if pageSize < 1 {
		pageSize = 10
	}

	// Parse boolean parameters
	inStock := query.Get("in_stock") == "true"
	active := query.Get("active") != "false" // Active por defecto

	return usecases.GetProductsInput{
		Category:    query.Get("category"),
		MinPrice:    minPrice,
		MaxPrice:    maxPrice,
		InStock:     inStock,
		Active:      active,
		NamePattern: query.Get("name"),
		Page:        page,
		PageSize:    pageSize,
		SortBy:      query.Get("sort_by"),
		SortOrder:   query.Get("sort_order"),
	}
}

// sendJSON sends a JSON response
func (h *ProductHandler) sendJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteStatus(status)
	json.NewEncoder(w).Encode(data)
}
