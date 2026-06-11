// Package handlers contains HTTP adapters — write side (CQRS).
package handlers

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/freakjazz/backbone-go/examples/clean-api-go/application/commands"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
	"github.com/freakjazz/backbone-go/interfaces/responses"
)

// ProductCommandHandler is the thin HTTP adapter for write operations.
// It parses HTTP requests, calls the appropriate command handler,
// and maps results to HTTP responses. Contains NO business logic.
type ProductCommandHandler struct {
	createHandler *commands.CreateProductCommandHandler
	updateHandler *commands.UpdateProductCommandHandler
	deleteHandler *commands.DeleteProductCommandHandler
	statusHandler *commands.ChangeProductStatusCommandHandler
	logger        *logging.EnhancedLogger
}

// NewProductCommandHandler creates a new HTTP command adapter.
func NewProductCommandHandler(
	create *commands.CreateProductCommandHandler,
	update *commands.UpdateProductCommandHandler,
	delete *commands.DeleteProductCommandHandler,
	status *commands.ChangeProductStatusCommandHandler,
	logger *logging.EnhancedLogger,
) *ProductCommandHandler {
	return &ProductCommandHandler{
		createHandler: create,
		updateHandler: update,
		deleteHandler: delete,
		statusHandler: status,
		logger:        logger,
	}
}

// CreateProduct handles POST /api/v1/products → {"id": "uuid"}  HTTP 201
func (h *ProductCommandHandler) CreateProduct(w http.ResponseWriter, r *http.Request) {
	log := h.log("CreateProduct", r)
	log.Info("Handling CreateProduct command", nil)

	var cmd commands.CreateProductCommand
	if err := json.NewDecoder(r.Body).Decode(&cmd); err != nil {
		resp := responses.ErrorResponseBuilder.ValidationError("Invalid JSON payload", nil)
		sendJSON(w, resp.StatusCode, resp)
		return
	}

	result, err := h.createHandler.Handle(r.Context(), cmd)
	if err != nil {
		resp := responses.ErrorResponseBuilder.ValidationError(err.Error(), nil)
		sendJSON(w, resp.StatusCode, resp)
		return
	}

	log.Info("Product created", map[string]interface{}{"product_id": result.ProductID})
	sendJSON(w, http.StatusCreated, responses.ProcessResponseBuilder.Created(result.ProductID))
}

// UpdateProduct handles PUT /api/v1/products/{id} → {"id": "uuid"}  HTTP 200
func (h *ProductCommandHandler) UpdateProduct(w http.ResponseWriter, r *http.Request, id string) {
	log := h.log("UpdateProduct", r)
	log.Info("Handling UpdateProduct command", map[string]interface{}{"product_id": id})

	var body struct {
		Name        string  `json:"name"`
		Description string  `json:"description"`
		Price       float64 `json:"price"`
		Category    string  `json:"category"`
		Stock       int     `json:"stock"`
	}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		resp := responses.ErrorResponseBuilder.ValidationError("Invalid JSON payload", nil)
		sendJSON(w, resp.StatusCode, resp)
		return
	}

	cmd := commands.UpdateProductCommand{
		ID:          id,
		Name:        body.Name,
		Description: body.Description,
		Price:       body.Price,
		Category:    body.Category,
		Stock:       body.Stock,
	}

	result, err := h.updateHandler.Handle(r.Context(), cmd)
	if err != nil {
		if strings.Contains(err.Error(), "not found") {
			resp := responses.ErrorResponseBuilder.NotFound("Product not found")
			sendJSON(w, resp.StatusCode, resp)
			return
		}
		resp := responses.ErrorResponseBuilder.ValidationError(err.Error(), nil)
		sendJSON(w, resp.StatusCode, resp)
		return
	}

	log.Info("Product updated", map[string]interface{}{"product_id": result.ProductID})
	sendJSON(w, http.StatusOK, responses.ProcessResponseBuilder.Updated(result.ProductID))
}

// DeleteProduct handles DELETE /api/v1/products/{id} → {"id": "uuid"}  HTTP 200
func (h *ProductCommandHandler) DeleteProduct(w http.ResponseWriter, r *http.Request, id string) {
	log := h.log("DeleteProduct", r)
	log.Info("Handling DeleteProduct command", map[string]interface{}{"product_id": id})

	cmd := commands.DeleteProductCommand{ID: id}
	if err := h.deleteHandler.Handle(r.Context(), cmd); err != nil {
		if strings.Contains(err.Error(), "not found") {
			resp := responses.ErrorResponseBuilder.NotFound("Product not found")
			sendJSON(w, resp.StatusCode, resp)
			return
		}
		resp := responses.ErrorResponseBuilder.InternalServerError(err.Error())
		sendJSON(w, resp.StatusCode, resp)
		return
	}

	log.Info("Product deleted", map[string]interface{}{"product_id": id})
	sendJSON(w, http.StatusOK, responses.ProcessResponseBuilder.Deleted(id))
}

// ChangeProductStatus handles PATCH /api/v1/products/{id}/status → {"id": "uuid"}  HTTP 200
func (h *ProductCommandHandler) ChangeProductStatus(w http.ResponseWriter, r *http.Request, id string) {
	log := h.log("ChangeProductStatus", r)
	log.Info("Handling ChangeProductStatus command", map[string]interface{}{"product_id": id})

	var body struct {
		Active bool `json:"active"`
	}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		resp := responses.ErrorResponseBuilder.ValidationError("Invalid JSON payload", nil)
		sendJSON(w, resp.StatusCode, resp)
		return
	}

	cmd := commands.ChangeProductStatusCommand{ID: id, Active: body.Active}
	if err := h.statusHandler.Handle(r.Context(), cmd); err != nil {
		if strings.Contains(err.Error(), "not found") {
			resp := responses.ErrorResponseBuilder.NotFound("Product not found")
			sendJSON(w, resp.StatusCode, resp)
			return
		}
		resp := responses.ErrorResponseBuilder.InternalServerError(err.Error())
		sendJSON(w, resp.StatusCode, resp)
		return
	}

	log.Info("Product status changed", map[string]interface{}{"product_id": id, "active": body.Active})
	sendJSON(w, http.StatusOK, responses.ProcessResponseBuilder.Updated(id))
}

func (h *ProductCommandHandler) log(method string, r *http.Request) *logging.EnhancedLogger {
	return h.logger.
		WithLayer("interfaces").
		WithHandler("ProductCommandHandler").
		WithMethod(method).
		WithContext(map[string]interface{}{
			"request_id": r.Context().Value("request_id"),
			"method":     r.Method,
			"path":       r.URL.Path,
		})
}
