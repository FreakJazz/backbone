package repositories

import (
	"context"
	"errors"

	"github.com/FreakJazz/backbone/backbone-go/domain/specifications"
	"github.com/freakjazz/clean-api-go/domain/entities"
)

// ErrInsufficientStock is returned by AdjustStock when applying delta would
// take stock below zero. Callers translate it into a 409 Conflict.
var ErrInsufficientStock = errors.New("insufficient stock")

type IProductRepository interface {
	Save(ctx context.Context, product *entities.Product) (*entities.Product, error)
	FindByID(ctx context.Context, id string) (*entities.Product, error)
	FindByName(ctx context.Context, name string) (*entities.Product, error)
	// FindByCriteria returns the page of products matching criteria together
	// with the total match count (ignoring pagination). The Postgres
	// implementation computes both in a single round trip via
	// COUNT(*) OVER(), rather than a separate SELECT and COUNT query — the
	// difference that matters once the table has millions of rows and every
	// extra round trip costs real latency.
	FindByCriteria(ctx context.Context, criteria *specifications.Criteria) (products []*entities.Product, total int, err error)

	// FindPageByCursor returns up to limit products matching criteria's
	// filters (its Sorts/Limit/Offset are ignored — sortField/desc/limit
	// govern this call), ordered by sortField then id, starting strictly
	// after the row identified by afterCursor (an opaque token from
	// specifications.EncodeCursor — "" to start from the beginning).
	// Returns the page and, when there may be more rows, a cursor for the
	// next page ("" when this is the last page).
	//
	// Unlike FindByCriteria's LIMIT/OFFSET, this never degrades as the
	// client pages deeper into a large result set: the Postgres
	// implementation seeks directly via the (sortField, id) ordering
	// instead of scanning and discarding every skipped row, which is what
	// OFFSET does no matter how large the offset gets.
	FindPageByCursor(ctx context.Context, criteria *specifications.Criteria, sortField string, desc bool, afterCursor string, limit int) (products []*entities.Product, nextCursor string, err error)

	Delete(ctx context.Context, id string) error
	Exists(ctx context.Context, id string) bool

	// AdjustStock atomically applies delta (positive or negative) to a
	// product's stock. The production (Postgres) implementation does this
	// in a single UPDATE ... WHERE stock + delta >= 0 statement, so two
	// concurrent sales can never oversell the same unit. Returns
	// ErrInsufficientStock rather than a generic error so callers can map
	// it to 409.
	AdjustStock(ctx context.Context, id string, delta int) (newStock int, err error)
}
