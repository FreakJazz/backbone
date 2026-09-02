package repositories

import (
	"context"

	"github.com/freakjazz/clean-api-go/domain/entities"
)

type IStockMovementRepository interface {
	Save(ctx context.Context, movement *entities.StockMovement) (*entities.StockMovement, error)
	FindByProductID(ctx context.Context, productID string, page, pageSize int) ([]*entities.StockMovement, int, error)
}
