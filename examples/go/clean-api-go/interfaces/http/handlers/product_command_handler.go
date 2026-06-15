package handlers

import (
	"encoding/json"
	"net/http"

	"github.com/freakjazz/backbone-go/interfaces/responses"
	"github.com/freakjazz/clean-api-go/application/commands"
)

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

func (h *ProductCommandHandler) Create(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Name        string  `json:"name"`
		Price       float64 `json:"price"`
		Category    string  `json:"category"`
		Description string  `json:"description"`
	}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeError(w, responses.ErrorResponseBuilder.ValidationError("invalid request body"))
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

func (h *ProductCommandHandler) Update(w http.ResponseWriter, r *http.Request, productID string) {
	var body map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeError(w, responses.ErrorResponseBuilder.ValidationError("invalid request body"))
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

func (h *ProductCommandHandler) Delete(w http.ResponseWriter, r *http.Request, productID string) {
	id, errResp := h.delete.Handle(r.Context(), commands.DeleteProductCommand{ProductID: productID})
	if errResp != nil {
		writeError(w, *errResp)
		return
	}
	writeJSON(w, http.StatusOK, responses.ProcessResponseBuilder.Deleted(id))
}

func (h *ProductCommandHandler) ChangeStatus(w http.ResponseWriter, r *http.Request, productID string) {
	var body struct {
		Status string `json:"status"`
	}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeError(w, responses.ErrorResponseBuilder.ValidationError("invalid request body"))
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
