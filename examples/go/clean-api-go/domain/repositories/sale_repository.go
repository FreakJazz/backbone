package repositories

import (
	"context"

	"github.com/freakjazz/clean-api-go/domain/entities"
)

type ISaleRepository interface {
	Save(ctx context.Context, sale *entities.Sale) (*entities.Sale, error)
	FindByProductID(ctx context.Context, productID string, page, pageSize int) ([]*entities.Sale, int, error)
}
