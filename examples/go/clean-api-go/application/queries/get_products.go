package queries

import (
	"context"

	bbex "github.com/freakjazz/backbone-go/interfaces/responses"
	"github.com/freakjazz/clean-api-go/domain/repositories"
	productspecs "github.com/freakjazz/clean-api-go/domain/specifications"
)

type GetProductsQuery struct {
	Filters  []string
	SortBy   string
	Page     int
	PageSize int
}

type GetProductsResult struct {
	Items      []map[string]interface{}
	TotalCount int
	Page       int
	PageSize   int
}

type GetProductsQueryHandler struct {
	repo repositories.IProductRepository
}

func NewGetProductsQueryHandler(repo repositories.IProductRepository) *GetProductsQueryHandler {
	return &GetProductsQueryHandler{repo: repo}
}

func (h *GetProductsQueryHandler) Handle(ctx context.Context, q GetProductsQuery) (*GetProductsResult, *bbex.ErrorResponse) {
	criteria := productspecs.BuildCriteria(q.Filters, q.Page, q.PageSize, q.SortBy)

	products, err := h.repo.FindByCriteria(ctx, criteria)
	if err != nil {
		e := bbex.ErrorResponseBuilder.InternalServerError(err.Error())
		return nil, &e
	}
	total, _ := h.repo.Count(ctx, criteria)

	items := make([]map[string]interface{}, len(products))
	for i, p := range products {
		items[i] = p.ToMap()
	}
	return &GetProductsResult{
		Items:      items,
		TotalCount: total,
		Page:       q.Page,
		PageSize:   q.PageSize,
	}, nil
}
