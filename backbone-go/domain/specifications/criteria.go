// Package specifications provides Criteria pattern for flexible queries
package specifications

import (
	"fmt"
	"strings"
)

// SortDirection represents the sort direction
type SortDirection string

const (
	SortAscending  SortDirection = "ASC"
	SortDescending SortDirection = "DESC"
)

// SortCriteria represents sorting criteria
type SortCriteria struct {
	Field     string
	Direction SortDirection
}

// NewSortCriteria creates a new sort criteria
func NewSortCriteria(field string, direction SortDirection) *SortCriteria {
	return &SortCriteria{
		Field:     field,
		Direction: direction,
	}
}

// ToSQL converts sort criteria to SQL ORDER BY clause
func (s *SortCriteria) ToSQL() string {
	return fmt.Sprintf("%s %s", s.Field, s.Direction)
}

// Criteria represents query criteria combining filters, sorting, and pagination
type Criteria struct {
	Specification Specification
	Sorts         []*SortCriteria
	Limit         int
	Offset        int
}

// NewCriteria creates a new criteria
func NewCriteria() *Criteria {
	return &Criteria{
		Sorts: make([]*SortCriteria, 0),
	}
}

// WithSpecification adds a specification filter
func (c *Criteria) WithSpecification(spec Specification) *Criteria {
	c.Specification = spec
	return c
}

// WithSort adds sorting
func (c *Criteria) WithSort(field string, direction SortDirection) *Criteria {
	c.Sorts = append(c.Sorts, NewSortCriteria(field, direction))
	return c
}

// WithLimit sets the limit
func (c *Criteria) WithLimit(limit int) *Criteria {
	c.Limit = limit
	return c
}

// WithOffset sets the offset
func (c *Criteria) WithOffset(offset int) *Criteria {
	c.Offset = offset
	return c
}

// WithPagination sets limit and offset for pagination
func (c *Criteria) WithPagination(page, pageSize int) *Criteria {
	if page < 1 {
		page = 1
	}
	c.Limit = pageSize
	c.Offset = (page - 1) * pageSize
	return c
}

// ToSQL converts criteria to SQL query components
func (c *Criteria) ToSQL() (whereClause string, args []interface{}, orderBy string, limit string) {
	// WHERE clause
	if c.Specification != nil {
		whereClause, args = c.Specification.ToSQL()
	}

	// ORDER BY clause
	if len(c.Sorts) > 0 {
		sortParts := make([]string, len(c.Sorts))
		for i, sort := range c.Sorts {
			sortParts[i] = sort.ToSQL()
		}
		orderBy = strings.Join(sortParts, ", ")
	}

	// LIMIT and OFFSET
	if c.Limit > 0 {
		limit = fmt.Sprintf("LIMIT %d", c.Limit)
		if c.Offset > 0 {
			limit += fmt.Sprintf(" OFFSET %d", c.Offset)
		}
	}

	return whereClause, args, orderBy, limit
}

// GetFullSQL returns the complete SQL string (for logging/debugging)
func (c *Criteria) GetFullSQL(baseQuery string) (string, []interface{}) {
	whereClause, args, orderBy, limit := c.ToSQL()

	query := baseQuery
	if whereClause != "" {
		query += " WHERE " + whereClause
	}
	if orderBy != "" {
		query += " ORDER BY " + orderBy
	}
	if limit != "" {
		query += " " + limit
	}

	return query, args
}

// CriteriaBuilder provides a fluent interface for building criteria
type CriteriaBuilder struct {
	criteria *Criteria
}

// NewCriteriaBuilder creates a new criteria builder
func NewCriteriaBuilder() *CriteriaBuilder {
	return &CriteriaBuilder{
		criteria: NewCriteria(),
	}
}

// Where adds a specification
func (b *CriteriaBuilder) Where(field, operator string, value interface{}) *CriteriaBuilder {
	var spec Specification

	switch operator {
	case "=", "==":
		spec = NewEqualSpecification(field, value)
	case "!=", "<>":
		spec = NewNotEqualSpecification(field, value)
	case ">":
		spec = NewGreaterThanSpecification(field, value)
	case "<":
		spec = NewLessThanSpecification(field, value)
	case "LIKE":
		if strVal, ok := value.(string); ok {
			spec = NewLikeSpecification(field, strVal)
		}
	case "IS NULL":
		spec = NewIsNullSpecification(field)
	default:
		spec = NewEqualSpecification(field, value)
	}

	if b.criteria.Specification == nil {
		b.criteria.Specification = spec
	} else {
		b.criteria.Specification = b.criteria.Specification.And(spec)
	}

	return b
}

// WhereIn adds an IN specification
func (b *CriteriaBuilder) WhereIn(field string, values []interface{}) *CriteriaBuilder {
	spec := NewInSpecification(field, values)

	if b.criteria.Specification == nil {
		b.criteria.Specification = spec
	} else {
		b.criteria.Specification = b.criteria.Specification.And(spec)
	}

	return b
}

// WhereBetween adds a BETWEEN specification
func (b *CriteriaBuilder) WhereBetween(field string, min, max interface{}) *CriteriaBuilder {
	spec := NewBetweenSpecification(field, min, max)

	if b.criteria.Specification == nil {
		b.criteria.Specification = spec
	} else {
		b.criteria.Specification = b.criteria.Specification.And(spec)
	}

	return b
}

// OrWhere adds an OR condition
func (b *CriteriaBuilder) OrWhere(field, operator string, value interface{}) *CriteriaBuilder {
	var spec Specification

	switch operator {
	case "=", "==":
		spec = NewEqualSpecification(field, value)
	case "!=", "<>":
		spec = NewNotEqualSpecification(field, value)
	case ">":
		spec = NewGreaterThanSpecification(field, value)
	case "<":
		spec = NewLessThanSpecification(field, value)
	default:
		spec = NewEqualSpecification(field, value)
	}

	if b.criteria.Specification == nil {
		b.criteria.Specification = spec
	} else {
		b.criteria.Specification = b.criteria.Specification.Or(spec)
	}

	return b
}

// OrderBy adds sorting
func (b *CriteriaBuilder) OrderBy(field string, direction SortDirection) *CriteriaBuilder {
	b.criteria.WithSort(field, direction)
	return b
}

// OrderByAsc adds ascending sort
func (b *CriteriaBuilder) OrderByAsc(field string) *CriteriaBuilder {
	return b.OrderBy(field, SortAscending)
}

// OrderByDesc adds descending sort
func (b *CriteriaBuilder) OrderByDesc(field string) *CriteriaBuilder {
	return b.OrderBy(field, SortDescending)
}

// Limit sets the limit
func (b *CriteriaBuilder) Limit(limit int) *CriteriaBuilder {
	b.criteria.WithLimit(limit)
	return b
}

// Offset sets the offset
func (b *CriteriaBuilder) Offset(offset int) *CriteriaBuilder {
	b.criteria.WithOffset(offset)
	return b
}

// Paginate sets pagination
func (b *CriteriaBuilder) Paginate(page, pageSize int) *CriteriaBuilder {
	b.criteria.WithPagination(page, pageSize)
	return b
}

// Build returns the built criteria
func (b *CriteriaBuilder) Build() *Criteria {
	return b.criteria
}
