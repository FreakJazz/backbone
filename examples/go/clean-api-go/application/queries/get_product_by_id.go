package queries

import (
	"context"

	bbex "github.com/freakjazz/backbone-go/interfaces/responses"
	"github.com/freakjazz/clean-api-go/domain/repositories"
)

type GetProductByIDQuery struct {
	ProductID string
}

type GetProductByIDQueryHandler struct {
	repo repositories.IProductRepository
}

func NewGetProductByIDQueryHandler(repo repositories.IProductRepository) *GetProductByIDQueryHandler {
	return &GetProductByIDQueryHandler{repo: repo}
}

func (h *GetProductByIDQueryHandler) Handle(ctx context.Context, q GetProductByIDQuery) (map[string]interface{}, *bbex.ErrorResponse) {
	product, err := h.repo.FindByID(ctx, q.ProductID)
	if err != nil || product == nil {
		e := bbex.ErrorResponseBuilder.NotFound("product not found")
		return nil, &e
	}
	return product.ToMap(), nil
}
