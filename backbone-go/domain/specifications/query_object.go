// Package specifications provides Query Object Pattern
package specifications

import (
	"context"
	"fmt"
)

// QueryObject represents a complete query with all its parameters
type QueryObject struct {
	BaseQuery string
	Criteria  *Criteria
	params    map[string]interface{}
}

// NewQueryObject creates a new query object
func NewQueryObject(baseQuery string) *QueryObject {
	return &QueryObject{
		BaseQuery: baseQuery,
		Criteria:  NewCriteria(),
		params:    make(map[string]interface{}),
	}
}

// WithCriteria sets the criteria
func (q *QueryObject) WithCriteria(criteria *Criteria) *QueryObject {
	q.Criteria = criteria
	return q
}

// WithParam adds a named parameter
func (q *QueryObject) WithParam(name string, value interface{}) *QueryObject {
	q.params[name] = value
	return q
}

// GetSQL returns the complete SQL query and arguments
func (q *QueryObject) GetSQL() (string, []interface{}) {
	return q.Criteria.GetFullSQL(q.BaseQuery)
}

// GetParams returns all parameters
func (q *QueryObject) GetParams() map[string]interface{} {
	return q.params
}

// String returns a string representation for logging
func (q *QueryObject) String() string {
	sql, args := q.GetSQL()
	return fmt.Sprintf("SQL: %s | Args: %v | Params: %v", sql, args, q.params)
}

// QueryExecutor defines the interface for executing queries
type QueryExecutor interface {
	// Execute executes the query and returns results
	Execute(ctx context.Context, query *QueryObject) ([]interface{}, error)

	// ExecuteOne executes the query and returns a single result
	ExecuteOne(ctx context.Context, query *QueryObject) (interface{}, error)

	// ExecuteCount executes a count query
	ExecuteCount(ctx context.Context, query *QueryObject) (int64, error)
}

// QueryBuilder provides a fluent interface for building complete queries
type QueryBuilder struct {
	query *QueryObject
}

// NewQueryBuilder creates a new query builder
func NewQueryBuilder(baseQuery string) *QueryBuilder {
	return &QueryBuilder{
		query: NewQueryObject(baseQuery),
	}
}

// Where adds a WHERE condition
func (b *QueryBuilder) Where(field, operator string, value interface{}) *QueryBuilder {
	criteriaBuilder := NewCriteriaBuilder()
	criteriaBuilder.Where(field, operator, value)
	b.query.Criteria = criteriaBuilder.Build()
	return b
}

// AndWhere adds an AND condition
func (b *QueryBuilder) AndWhere(field, operator string, value interface{}) *QueryBuilder {
	if b.query.Criteria.Specification == nil {
		return b.Where(field, operator, value)
	}

	var spec Specification
	switch operator {
	case "=":
		spec = NewEqualSpecification(field, value)
	case "!=":
		spec = NewNotEqualSpecification(field, value)
	case ">":
		spec = NewGreaterThanSpecification(field, value)
	case "<":
		spec = NewLessThanSpecification(field, value)
	default:
		spec = NewEqualSpecification(field, value)
	}

	b.query.Criteria.Specification = b.query.Criteria.Specification.And(spec)
	return b
}

// OrWhere adds an OR condition
func (b *QueryBuilder) OrWhere(field, operator string, value interface{}) *QueryBuilder {
	if b.query.Criteria.Specification == nil {
		return b.Where(field, operator, value)
	}

	var spec Specification
	switch operator {
	case "=":
		spec = NewEqualSpecification(field, value)
	case "!=":
		spec = NewNotEqualSpecification(field, value)
	case ">":
		spec = NewGreaterThanSpecification(field, value)
	case "<":
		spec = NewLessThanSpecification(field, value)
	default:
		spec = NewEqualSpecification(field, value)
	}

	b.query.Criteria.Specification = b.query.Criteria.Specification.Or(spec)
	return b
}

// WhereIn adds an IN condition
func (b *QueryBuilder) WhereIn(field string, values []interface{}) *QueryBuilder {
	spec := NewInSpecification(field, values)

	if b.query.Criteria.Specification == nil {
		b.query.Criteria.Specification = spec
	} else {
		b.query.Criteria.Specification = b.query.Criteria.Specification.And(spec)
	}

	return b
}

// WhereBetween adds a BETWEEN condition
func (b *QueryBuilder) WhereBetween(field string, min, max interface{}) *QueryBuilder {
	spec := NewBetweenSpecification(field, min, max)

	if b.query.Criteria.Specification == nil {
		b.query.Criteria.Specification = spec
	} else {
		b.query.Criteria.Specification = b.query.Criteria.Specification.And(spec)
	}

	return b
}

// OrderBy adds sorting
func (b *QueryBuilder) OrderBy(field string, direction SortDirection) *QueryBuilder {
	b.query.Criteria.WithSort(field, direction)
	return b
}

// OrderByAsc adds ascending sort
func (b *QueryBuilder) OrderByAsc(field string) *QueryBuilder {
	return b.OrderBy(field, SortAscending)
}

// OrderByDesc adds descending sort
func (b *QueryBuilder) OrderByDesc(field string) *QueryBuilder {
	return b.OrderBy(field, SortDescending)
}

// Limit sets the limit
func (b *QueryBuilder) Limit(limit int) *QueryBuilder {
	b.query.Criteria.WithLimit(limit)
	return b
}

// Offset sets the offset
func (b *QueryBuilder) Offset(offset int) *QueryBuilder {
	b.query.Criteria.WithOffset(offset)
	return b
}

// Paginate sets pagination
func (b *QueryBuilder) Paginate(page, pageSize int) *QueryBuilder {
	b.query.Criteria.WithPagination(page, pageSize)
	return b
}

// WithParam adds a named parameter
func (b *QueryBuilder) WithParam(name string, value interface{}) *QueryBuilder {
	b.query.WithParam(name, value)
	return b
}

// Build returns the built query object
func (b *QueryBuilder) Build() *QueryObject {
	return b.query
}

// GetSQL returns the SQL and arguments
func (b *QueryBuilder) GetSQL() (string, []interface{}) {
	return b.query.GetSQL()
}
