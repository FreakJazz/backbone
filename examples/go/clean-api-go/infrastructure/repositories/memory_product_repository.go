package repositories

import (
	"context"
	"fmt"
	"sort"
	"strings"
	"sync"

	"github.com/freakjazz/backbone-go/domain/specifications"
	"github.com/freakjazz/clean-api-go/domain/entities"
	domainrepos "github.com/freakjazz/clean-api-go/domain/repositories"
)

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

func (r *MemoryProductRepository) FindByCriteria(_ context.Context, criteria *specifications.Criteria) ([]*entities.Product, error) {
	r.mu.RLock()
	all := make([]*entities.Product, 0, len(r.store))
	for _, p := range r.store {
		all = append(all, p)
	}
	r.mu.RUnlock()

	filtered := r.applySpec(all, criteria)
	filtered = r.applySort(filtered, criteria)

	// Pagination via Limit/Offset
	offset := criteria.Offset
	limit := criteria.Limit
	if limit <= 0 {
		limit = 10
	}
	if offset >= len(filtered) {
		return []*entities.Product{}, nil
	}
	end := offset + limit
	if end > len(filtered) {
		end = len(filtered)
	}
	return filtered[offset:end], nil
}

func (r *MemoryProductRepository) Count(_ context.Context, criteria *specifications.Criteria) (int, error) {
	r.mu.RLock()
	all := make([]*entities.Product, 0, len(r.store))
	for _, p := range r.store {
		all = append(all, p)
	}
	r.mu.RUnlock()
	return len(r.applySpec(all, criteria)), nil
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
	}
	return ""
}
