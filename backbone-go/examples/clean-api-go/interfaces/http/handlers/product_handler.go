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
// @Summary Create a new product
// @Description Create a new product in the system
// @Tags products
// @Accept json
// @Produce json
// @Param product body CreateProductRequest true "Product object"
// @Success 201 {object} CreateProductResponse "Product created successfully"
// @Failure 400 {object} ErrorResponse "Bad request"
// @Failure 500 {object} ErrorResponse "Internal server error"
// @Router /products [post]
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
		h.sendJSON(w, response.StatusCode, response)
		return
	}

	// Execute use case
	output, err := h.createUseCase.Execute(r.Context(), input)
	if err != nil {
		handlerLogger.ErrorWithCode("Use case failed", 13001002, map[string]interface{}{
			"error": err.Error(),
		})
		response := responses.ErrorResponseBuilder.FromException(err)
		h.sendJSON(w, response.StatusCode, response)
		return
	}

	// Success response
	response := responses.ProcessResponseBuilder.Created(
		"Product created successfully",
		output.Product.ID,
	)

	handlerLogger.Info("Product created successfully", map[string]interface{}{
		"product_id": output.Product.ID,
	})

	h.sendJSON(w, response.StatusCode, response)
}

// GetProducts handles getting products with filters
// @Summary Get products with filters
// @Description Retrieve products with optional filtering, sorting and pagination
// @Tags products
// @Accept json
// @Produce json
// @Param category query string false "Filter by category"
// @Param min_price query number false "Minimum price filter"
// @Param max_price query number false "Maximum price filter"
// @Param in_stock query boolean false "Filter by stock availability"
// @Param name query string false "Search by name pattern"
// @Param page query integer false "Page number (default 1)"
// @Param page_size query integer false "Page size (default 10)"
// @Param sort_by query string false "Sort field (default created_at)"
// @Param sort_order query string false "Sort order: asc or desc (default desc)"
// @Success 200 {object} GetProductsResponse "Products retrieved successfully"
// @Failure 500 {object} ErrorResponse "Internal server error"
// @Router /products [get]
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
		h.sendJSON(w, response.StatusCode, response)
		return
	}

	// Convert products to response data
	productsData := make([]map[string]interface{}, 0, len(output.Products))
	for _, product := range output.Products {
		productsData = append(productsData, map[string]interface{}{
			"id":          product.ID,
			"name":        product.Name,
			"description": product.Description,
			"price":       product.Price,
			"category":    product.Category,
			"stock":       product.Stock,
			"active":      product.Active,
			"created_at":  product.CreatedAt,
			"updated_at":  product.UpdatedAt,
		})
	}

	// Success response with pagination
	response := responses.QueryResponseBuilder.SuccessWithPagination(
		"Products retrieved successfully",
		productsData,
		output.Page,
		output.PageSize,
		int(output.TotalCount),
	)

	handlerLogger.Info("Products retrieved successfully", map[string]interface{}{
		"count":       len(output.Products),
		"total_count": output.TotalCount,
		"page":        output.Page,
	})

	h.sendJSON(w, response.StatusCode, response)
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
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

// CreateProductRequest represents the request body for creating a product
type CreateProductRequest struct {
	Name        string  `json:"name" example:"Laptop Dell XPS 15"`
	Description string  `json:"description" example:"High performance laptop"`
	Price       float64 `json:"price" example:"1500.00"`
	Category    string  `json:"category" example:"Electronics"`
	Stock       int     `json:"stock" example:"50"`
}

// Product represents a product in the response
type Product struct {
	ID          string  `json:"id"`
	Name        string  `json:"name"`
	Description string  `json:"description"`
	Price       float64 `json:"price"`
	Category    string  `json:"category"`
	Stock       int     `json:"stock"`
	Active      bool    `json:"active"`
	CreatedAt   string  `json:"created_at"`
	UpdatedAt   string  `json:"updated_at"`
}

// CreateProductResponse represents the response for creating a product
type CreateProductResponse struct {
	Status     string `json:"status"`
	StatusCode int    `json:"status_code"`
	Message    string `json:"message"`
	Data       struct {
		ID string `json:"id"`
	} `json:"data"`
}

// GetProductsResponse represents the response for getting products
type GetProductsResponse struct {
	Status     string    `json:"status"`
	StatusCode int       `json:"status_code"`
	Message    string    `json:"message"`
	Data       []Product `json:"data"`
	Pagination struct {
		Page         int `json:"page"`
		PageSize     int `json:"page_size"`
		TotalRecords int `json:"total_records"`
		TotalPages   int `json:"total_pages"`
	} `json:"pagination"`
}

// ErrorResponse represents an error response
type ErrorResponse struct {
	Status       string                 `json:"status"`
	StatusCode   int                    `json:"status_code"`
	Message      string                 `json:"message"`
	ErrorDetails map[string]interface{} `json:"error_details,omitempty"`
}
