package handlers

import (
	"encoding/json"
	"net/http"

	"github.com/freakjazz/backbone-go/interfaces/responses"
	"github.com/freakjazz/clean-api-go/application/commands"
)

const errInvalidBody = "invalid request body"

type ProductCommandHandler struct {
	create *commands.CreateProductCommandHandler
	update *commands.UpdateProductCommandHandler
	delete *commands.DeleteProductCommandHandler
	status *commands.ChangeProductStatusCommandHandler
}

func NewProductCommandHandler(
	create *commands.CreateProductCommandHandler,
	update *commands.UpdateProductCommandHandler,
	delete *commands.DeleteProductCommandHandler,
	status *commands.ChangeProductStatusCommandHandler,
) *ProductCommandHandler {
	return &ProductCommandHandler{create: create, update: update, delete: delete, status: status}
}

// Create godoc
// @Summary      Create product
// @Description  Creates a new product
// @Tags         products
// @Accept       json
// @Produce      json
// @Param        body  body  handlers.CreateProductRequest  true  "Product data"
// @Success      201  {object}  map[string]string
// @Failure      400  {object}  handlers.ErrorResponse
// @Router       /api/v1/products [post]
func (h *ProductCommandHandler) Create(w http.ResponseWriter, r *http.Request) {
	var body CreateProductRequest
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeError(w, responses.ErrorResponseBuilder.ValidationError(errInvalidBody))
		return
	}
	id, errResp := h.create.Handle(r.Context(), commands.CreateProductCommand{
		Name: body.Name, Price: body.Price, Category: body.Category, Description: body.Description,
	})
	if errResp != nil {
		writeError(w, *errResp)
		return
	}
	writeJSON(w, http.StatusCreated, responses.ProcessResponseBuilder.Created(id))
}

// Update godoc
// @Summary      Update product
// @Description  Updates an existing product (partial update supported)
// @Tags         products
// @Accept       json
// @Produce      json
// @Param        id    path  string                         true  "Product ID"
// @Param        body  body  handlers.UpdateProductRequest  true  "Fields to update"
// @Success      200  {object}  map[string]string
// @Failure      400  {object}  handlers.ErrorResponse
// @Failure      404  {object}  handlers.ErrorResponse
// @Router       /api/v1/products/{id} [put]
func (h *ProductCommandHandler) Update(w http.ResponseWriter, r *http.Request, productID string) {
	var body map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeError(w, responses.ErrorResponseBuilder.ValidationError(errInvalidBody))
		return
	}
	cmd := commands.UpdateProductCommand{ProductID: productID}
	if v, ok := body["name"].(string); ok {
		cmd.Name = &v
	}
	if v, ok := body["price"].(float64); ok {
		cmd.Price = &v
	}
	if v, ok := body["category"].(string); ok {
		cmd.Category = &v
	}
	if v, ok := body["description"].(string); ok {
		cmd.Description = &v
	}
	id, errResp := h.update.Handle(r.Context(), cmd)
	if errResp != nil {
		writeError(w, *errResp)
		return
	}
	writeJSON(w, http.StatusOK, responses.ProcessResponseBuilder.Updated(id))
}

// Delete godoc
// @Summary      Delete product
// @Description  Deletes a product by ID
// @Tags         products
// @Produce      json
// @Param        id  path  string  true  "Product ID"
// @Success      200  {object}  map[string]string
// @Failure      404  {object}  handlers.ErrorResponse
// @Router       /api/v1/products/{id} [delete]
func (h *ProductCommandHandler) Delete(w http.ResponseWriter, r *http.Request, productID string) {
	id, errResp := h.delete.Handle(r.Context(), commands.DeleteProductCommand{ProductID: productID})
	if errResp != nil {
		writeError(w, *errResp)
		return
	}
	writeJSON(w, http.StatusOK, responses.ProcessResponseBuilder.Deleted(id))
}

// ChangeStatus godoc
// @Summary      Change product status
// @Description  Changes product status (active | inactive | discontinued)
// @Tags         products
// @Accept       json
// @Produce      json
// @Param        id    path  string                          true  "Product ID"
// @Param        body  body  handlers.ChangeStatusRequest    true  "New status"
// @Success      200  {object}  map[string]string
// @Failure      400  {object}  handlers.ErrorResponse
// @Failure      404  {object}  handlers.ErrorResponse
// @Router       /api/v1/products/{id}/status [patch]
func (h *ProductCommandHandler) ChangeStatus(w http.ResponseWriter, r *http.Request, productID string) {
	var body ChangeStatusRequest
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeError(w, responses.ErrorResponseBuilder.ValidationError(errInvalidBody))
		return
	}
	id, errResp := h.status.Handle(r.Context(), commands.ChangeProductStatusCommand{
		ProductID: productID, Status: body.Status,
	})
	if errResp != nil {
		writeError(w, *errResp)
		return
	}
	writeJSON(w, http.StatusOK, responses.ProcessResponseBuilder.Updated(id))
}

// ── request DTOs (used by swag for schema generation) ────────────────────────

type CreateProductRequest struct {
	Name        string  `json:"name"        example:"Laptop Pro"`
	Price       float64 `json:"price"       example:"999.99"`
	Category    string  `json:"category"    example:"Electronics"`
	Description string  `json:"description" example:"High-performance laptop"`
}

type UpdateProductRequest struct {
	Name        *string  `json:"name"        example:"Laptop Pro"`
	Price       *float64 `json:"price"       example:"999.99"`
	Category    *string  `json:"category"    example:"Electronics"`
	Description *string  `json:"description" example:"Updated description"`
}

type ChangeStatusRequest struct {
	Status string `json:"status" example:"inactive" enums:"active,inactive,discontinued"`
}
