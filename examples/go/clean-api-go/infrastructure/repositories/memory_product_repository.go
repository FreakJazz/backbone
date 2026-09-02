package repositories

import (
	"context"
	"fmt"
	"sort"
	"strings"
	"sync"

	"github.com/FreakJazz/backbone/backbone-go/domain/specifications"
	"github.com/freakjazz/clean-api-go/domain/entities"
	domainrepos "github.com/freakjazz/clean-api-go/domain/repositories"
)

// MemoryProductRepository is a fast, dependency-free fake of
// IProductRepository used by the unit tests under tests/application — it is
// not wired into main.go. Production uses PostgresProductRepository
// (infrastructure/repositories/postgres_product_repository.go).
type MemoryProductRepository struct {
	mu    sync.RWMutex
	store map[string]*entities.Product
}

var _ domainrepos.IProductRepository = (*MemoryProductRepository)(nil)

func NewMemoryProductRepository() *MemoryProductRepository {
	return &MemoryProductRepository{store: make(map[string]*entities.Product)}
}

func (r *MemoryProductRepository) Save(_ context.Context, p *entities.Product) (*entities.Product, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.store[p.ID] = p
	return p, nil
}

func (r *MemoryProductRepository) FindByID(_ context.Context, id string) (*entities.Product, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	if p, ok := r.store[id]; ok {
		return p, nil
	}
	return nil, fmt.Errorf("not found")
}

// FindByCriteria filters+sorts the whole store once and slices the page out
// of it, returning len(filtered) as the total — a single pass, mirroring
// PostgresProductRepository's single-round-trip contract instead of the
// filter-twice pattern a naive FindByCriteria+Count split would need.
func (r *MemoryProductRepository) FindByCriteria(_ context.Context, criteria *specifications.Criteria) ([]*entities.Product, int, error) {
	r.mu.RLock()
	all := make([]*entities.Product, 0, len(r.store))
	for _, p := range r.store {
		all = append(all, p)
	}
	r.mu.RUnlock()

	filtered := r.applySpec(all, criteria)
	filtered = r.applySort(filtered, criteria)
	total := len(filtered)

	offset := criteria.Offset
	limit := criteria.Limit
	if limit <= 0 {
		limit = 10
	}
	if offset >= total {
		return []*entities.Product{}, total, nil
	}
	end := offset + limit
	if end > total {
		end = total
	}
	return filtered[offset:end], total, nil
}

// FindPageByCursor mirrors PostgresProductRepository's keyset contract using
// the same full filter+sort pass FindByCriteria already does, then finds
// afterCursor's row by id and slices the next `limit` items after it — an
// O(n) scan here, since the fake has no index to seek with, but the
// contract callers see (same ordering, same tiebreak-by-id, same
// next-cursor semantics) is identical to the real Postgres implementation.
func (r *MemoryProductRepository) FindPageByCursor(_ context.Context, criteria *specifications.Criteria, sortField string, desc bool, afterCursor string, limit int) ([]*entities.Product, string, error) {
	if limit <= 0 {
		limit = specifications.DefaultPageSize
	}

	r.mu.RLock()
	all := make([]*entities.Product, 0, len(r.store))
	for _, p := range r.store {
		all = append(all, p)
	}
	r.mu.RUnlock()

	filtered := r.applySpec(all, criteria)
	sort.SliceStable(filtered, func(i, j int) bool {
		vi, vj := fieldStr(filtered[i], sortField), fieldStr(filtered[j], sortField)
		if vi != vj {
			if desc {
				return vi > vj
			}
			return vi < vj
		}
		return filtered[i].ID < filtered[j].ID // tiebreak matches (sortField, id) in the real query
	})

	start := 0
	if afterCursor != "" {
		_, afterID, err := specifications.DecodeCursor(afterCursor)
		if err != nil {
			return nil, "", err
		}
		found := false
		for i, p := range filtered {
			if p.ID == afterID {
				start = i + 1
				found = true
				break
			}
		}
		if !found {
			return []*entities.Product{}, "", nil
		}
	}
	if start >= len(filtered) {
		return []*entities.Product{}, "", nil
	}

	end := start + limit
	hasMore := end < len(filtered)
	if end > len(filtered) {
		end = len(filtered)
	}
	page := filtered[start:end]

	nextCursor := ""
	if hasMore && len(page) > 0 {
		last := page[len(page)-1]
		var err error
		nextCursor, err = specifications.EncodeCursor(cursorValueFor(sortField, last), last.ID)
		if err != nil {
			return nil, "", err
		}
	}
	return page, nextCursor, nil
}

func (r *MemoryProductRepository) FindByName(_ context.Context, name string) (*entities.Product, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	lower := strings.ToLower(name)
	for _, p := range r.store {
		if strings.ToLower(p.Name) == lower {
			return p, nil
		}
	}
	return nil, nil
}

func (r *MemoryProductRepository) Delete(_ context.Context, id string) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	delete(r.store, id)
	return nil
}

func (r *MemoryProductRepository) Exists(_ context.Context, id string) bool {
	r.mu.RLock()
	defer r.mu.RUnlock()
	_, ok := r.store[id]
	return ok
}

// AdjustStock mirrors PostgresProductRepository's atomicity contract closely
// enough for unit tests: the whole check-and-write happens under the same
// write lock, so no other goroutine touching this fake can observe a
// negative stock in between.
func (r *MemoryProductRepository) AdjustStock(_ context.Context, id string, delta int) (int, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	p, ok := r.store[id]
	if !ok {
		return 0, fmt.Errorf("product not found")
	}
	if p.Stock+delta < 0 {
		return 0, domainrepos.ErrInsufficientStock
	}
	p.Stock += delta
	return p.Stock, nil
}

// applySpec filters using criteria.Specification.IsSatisfiedBy on the struct.
// backbone-go's entity_matcher uses reflection with case-insensitive field matching.
func (r *MemoryProductRepository) applySpec(products []*entities.Product, criteria *specifications.Criteria) []*entities.Product {
	if criteria == nil || criteria.Specification == nil {
		return products
	}
	out := make([]*entities.Product, 0, len(products))
	for _, p := range products {
		if criteria.Specification.IsSatisfiedBy(p) {
			out = append(out, p)
		}
	}
	return out
}

// applySort sorts using criteria.Sorts ([]*SortCriteria with Field + Direction).
func (r *MemoryProductRepository) applySort(products []*entities.Product, criteria *specifications.Criteria) []*entities.Product {
	if criteria == nil || len(criteria.Sorts) == 0 {
		return products
	}
	s := criteria.Sorts[0] // primary sort
	desc := strings.EqualFold(string(s.Direction), "desc")

	sort.SliceStable(products, func(i, j int) bool {
		vi := fieldStr(products[i], s.Field)
		vj := fieldStr(products[j], s.Field)
		if desc {
			return vi > vj
		}
		return vi < vj
	})
	return products
}

func fieldStr(p *entities.Product, field string) string {
	switch strings.ToLower(field) {
	case "name":
		return p.Name
	case "category":
		return p.Category
	case "status":
		return p.Status
	case "price":
		return fmt.Sprintf("%020.6f", p.Price)
	case "stock":
		return fmt.Sprintf("%020d", p.Stock)
	case "created_at":
		return p.CreatedAt.Format("20060102150405.000000000")
	}
	return ""
}
