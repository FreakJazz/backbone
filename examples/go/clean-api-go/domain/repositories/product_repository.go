package repositories

import (
	"context"

	"github.com/freakjazz/backbone-go/domain/specifications"
	"github.com/freakjazz/clean-api-go/domain/entities"
)

type IProductRepository interface {
	Save(ctx context.Context, product *entities.Product) (*entities.Product, error)
	FindByID(ctx context.Context, id string) (*entities.Product, error)
	FindByCriteria(ctx context.Context, criteria *specifications.Criteria) ([]*entities.Product, error)
	Count(ctx context.Context, criteria *specifications.Criteria) (int, error)
	Delete(ctx context.Context, id string) error
	Exists(ctx context.Context, id string) bool
}
