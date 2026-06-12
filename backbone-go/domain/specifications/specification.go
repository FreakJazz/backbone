// Package specifications provides the Specification Pattern for dynamic queries
package specifications

import (
	"fmt"
	"reflect"
	"strings"
)

// Specification defines the contract for query specifications
type Specification interface {
	// IsSatisfiedBy checks if an entity satisfies the specification
	IsSatisfiedBy(entity interface{}) bool

	// ToSQL converts the specification to SQL WHERE clause
	ToSQL() (string, []interface{})

	// And combines this specification with another using AND
	And(other Specification) Specification

	// Or combines this specification with another using OR
	Or(other Specification) Specification

	// Not negates this specification
	Not() Specification
}

// BaseSpecification provides common functionality
type BaseSpecification struct {
	field    string
	operator string
	value    interface{}
}

// ToSQL converts to SQL WHERE clause
func (s *BaseSpecification) ToSQL() (string, []interface{}) {
	return fmt.Sprintf("%s %s ?", s.field, s.operator), []interface{}{s.value}
}

// IsSatisfiedBy evaluates the specification against an entity using its operator.
// Handles = != > >= < <= via the entity_matcher helpers (same package).
func (s *BaseSpecification) IsSatisfiedBy(entity interface{}) bool {
	val, ok := fieldValue(entity, s.field)
	if !ok {
		return false
	}
	switch s.operator {
	case "=":
		return reflect.DeepEqual(val, s.value)
	case "!=":
		return !reflect.DeepEqual(val, s.value)
	case ">":
		return compare(val, s.value) > 0
	case ">=":
		return compare(val, s.value) >= 0
	case "<":
		return compare(val, s.value) < 0
	case "<=":
		return compare(val, s.value) <= 0
	}
	return true
}

// And combines with another specification
func (s *BaseSpecification) And(other Specification) Specification {
	return &AndSpecification{left: s, right: other}
}

// Or combines with another specification
func (s *BaseSpecification) Or(other Specification) Specification {
	return &OrSpecification{left: s, right: other}
}

// Not negates this specification
func (s *BaseSpecification) Not() Specification {
	return &NotSpecification{spec: s}
}

// EqualSpecification checks for equality
type EqualSpecification struct {
	*BaseSpecification
}

// NewEqualSpecification creates an equality specification
func NewEqualSpecification(field string, value interface{}) *EqualSpecification {
	return &EqualSpecification{
		BaseSpecification: &BaseSpecification{
			field:    field,
			operator: "=",
			value:    value,
		},
	}
}

// NotEqualSpecification checks for inequality
type NotEqualSpecification struct {
	*BaseSpecification
}

// NewNotEqualSpecification creates an inequality specification
func NewNotEqualSpecification(field string, value interface{}) *NotEqualSpecification {
	return &NotEqualSpecification{
		BaseSpecification: &BaseSpecification{
			field:    field,
			operator: "!=",
			value:    value,
		},
	}
}

// GreaterThanSpecification checks if field > value
type GreaterThanSpecification struct {
	*BaseSpecification
}

// NewGreaterThanSpecification creates a greater than specification
func NewGreaterThanSpecification(field string, value interface{}) *GreaterThanSpecification {
	return &GreaterThanSpecification{
		BaseSpecification: &BaseSpecification{
			field:    field,
			operator: ">",
			value:    value,
		},
	}
}

// LessThanSpecification checks if field < value
type LessThanSpecification struct {
	*BaseSpecification
}

// NewLessThanSpecification creates a less than specification
func NewLessThanSpecification(field string, value interface{}) *LessThanSpecification {
	return &LessThanSpecification{
		BaseSpecification: &BaseSpecification{
			field:    field,
			operator: "<",
			value:    value,
		},
	}
}

// GreaterThanOrEqualSpecification checks if field >= value
type GreaterThanOrEqualSpecification struct {
	*BaseSpecification
}

// NewGreaterThanOrEqualSpecification creates a >= specification
func NewGreaterThanOrEqualSpecification(field string, value interface{}) *GreaterThanOrEqualSpecification {
	return &GreaterThanOrEqualSpecification{
		BaseSpecification: &BaseSpecification{
			field:    field,
			operator: ">=",
			value:    value,
		},
	}
}

// LessThanOrEqualSpecification checks if field <= value
type LessThanOrEqualSpecification struct {
	*BaseSpecification
}

// NewLessThanOrEqualSpecification creates a <= specification
func NewLessThanOrEqualSpecification(field string, value interface{}) *LessThanOrEqualSpecification {
	return &LessThanOrEqualSpecification{
		BaseSpecification: &BaseSpecification{
			field:    field,
			operator: "<=",
			value:    value,
		},
	}
}

// InSpecification checks if field is in a list of values
type InSpecification struct {
	field  string
	values []interface{}
}

// NewInSpecification creates an IN specification
func NewInSpecification(field string, values []interface{}) *InSpecification {
	return &InSpecification{
		field:  field,
		values: values,
	}
}

// ToSQL converts to SQL
func (s *InSpecification) ToSQL() (string, []interface{}) {
	placeholders := make([]string, len(s.values))
	for i := range s.values {
		placeholders[i] = "?"
	}
	sql := fmt.Sprintf("%s IN (%s)", s.field, strings.Join(placeholders, ", "))
	return sql, s.values
}

// And combines specifications
func (s *InSpecification) And(other Specification) Specification {
	return &AndSpecification{left: s, right: other}
}

// Or combines specifications
func (s *InSpecification) Or(other Specification) Specification {
	return &OrSpecification{left: s, right: other}
}

// Not negates the specification
func (s *InSpecification) Not() Specification {
	return &NotSpecification{spec: s}
}

// LikeSpecification checks if field matches a pattern
type LikeSpecification struct {
	field   string
	pattern string
}

// NewLikeSpecification creates a LIKE specification
func NewLikeSpecification(field, pattern string) *LikeSpecification {
	return &LikeSpecification{
		field:   field,
		pattern: pattern,
	}
}

// ToSQL converts to SQL
func (s *LikeSpecification) ToSQL() (string, []interface{}) {
	return fmt.Sprintf("%s LIKE ?", s.field), []interface{}{s.pattern}
}

// And combines specifications
func (s *LikeSpecification) And(other Specification) Specification {
	return &AndSpecification{left: s, right: other}
}

// Or combines specifications
func (s *LikeSpecification) Or(other Specification) Specification {
	return &OrSpecification{left: s, right: other}
}

// Not negates the specification
func (s *LikeSpecification) Not() Specification {
	return &NotSpecification{spec: s}
}

// BetweenSpecification checks if field is between two values
type BetweenSpecification struct {
	field string
	min   interface{}
	max   interface{}
}

// NewBetweenSpecification creates a BETWEEN specification
func NewBetweenSpecification(field string, min, max interface{}) *BetweenSpecification {
	return &BetweenSpecification{
		field: field,
		min:   min,
		max:   max,
	}
}

// ToSQL converts to SQL
func (s *BetweenSpecification) ToSQL() (string, []interface{}) {
	return fmt.Sprintf("%s BETWEEN ? AND ?", s.field), []interface{}{s.min, s.max}
}

// And combines specifications
func (s *BetweenSpecification) And(other Specification) Specification {
	return &AndSpecification{left: s, right: other}
}

// Or combines specifications
func (s *BetweenSpecification) Or(other Specification) Specification {
	return &OrSpecification{left: s, right: other}
}

// Not negates the specification
func (s *BetweenSpecification) Not() Specification {
	return &NotSpecification{spec: s}
}

// IsNullSpecification checks if field is NULL
type IsNullSpecification struct {
	field string
}

// NewIsNullSpecification creates an IS NULL specification
func NewIsNullSpecification(field string) *IsNullSpecification {
	return &IsNullSpecification{field: field}
}

// ToSQL converts to SQL
func (s *IsNullSpecification) ToSQL() (string, []interface{}) {
	return fmt.Sprintf("%s IS NULL", s.field), []interface{}{}
}

// And combines specifications
func (s *IsNullSpecification) And(other Specification) Specification {
	return &AndSpecification{left: s, right: other}
}

// Or combines specifications
func (s *IsNullSpecification) Or(other Specification) Specification {
	return &OrSpecification{left: s, right: other}
}

// Not negates the specification
func (s *IsNullSpecification) Not() Specification {
	return &NotSpecification{spec: s}
}

// AndSpecification combines two specifications with AND
type AndSpecification struct {
	left  Specification
	right Specification
}

// ToSQL converts to SQL
func (s *AndSpecification) ToSQL() (string, []interface{}) {
	leftSQL, leftArgs := s.left.ToSQL()
	rightSQL, rightArgs := s.right.ToSQL()

	sql := fmt.Sprintf("(%s AND %s)", leftSQL, rightSQL)
	args := append(leftArgs, rightArgs...)

	return sql, args
}

// IsSatisfiedBy checks if entity satisfies both specifications
func (s *AndSpecification) IsSatisfiedBy(entity interface{}) bool {
	return s.left.IsSatisfiedBy(entity) && s.right.IsSatisfiedBy(entity)
}

// And combines specifications
func (s *AndSpecification) And(other Specification) Specification {
	return &AndSpecification{left: s, right: other}
}

// Or combines specifications
func (s *AndSpecification) Or(other Specification) Specification {
	return &OrSpecification{left: s, right: other}
}

// Not negates the specification
func (s *AndSpecification) Not() Specification {
	return &NotSpecification{spec: s}
}

// OrSpecification combines two specifications with OR
type OrSpecification struct {
	left  Specification
	right Specification
}

// ToSQL converts to SQL
func (s *OrSpecification) ToSQL() (string, []interface{}) {
	leftSQL, leftArgs := s.left.ToSQL()
	rightSQL, rightArgs := s.right.ToSQL()

	sql := fmt.Sprintf("(%s OR %s)", leftSQL, rightSQL)
	args := append(leftArgs, rightArgs...)

	return sql, args
}

// IsSatisfiedBy checks if entity satisfies either specification
func (s *OrSpecification) IsSatisfiedBy(entity interface{}) bool {
	return s.left.IsSatisfiedBy(entity) || s.right.IsSatisfiedBy(entity)
}

// And combines specifications
func (s *OrSpecification) And(other Specification) Specification {
	return &AndSpecification{left: s, right: other}
}

// Or combines specifications
func (s *OrSpecification) Or(other Specification) Specification {
	return &OrSpecification{left: s, right: other}
}

// Not negates the specification
func (s *OrSpecification) Not() Specification {
	return &NotSpecification{spec: s}
}

// NotSpecification negates a specification
type NotSpecification struct {
	spec Specification
}

// ToSQL converts to SQL
func (s *NotSpecification) ToSQL() (string, []interface{}) {
	sql, args := s.spec.ToSQL()
	return fmt.Sprintf("NOT (%s)", sql), args
}

// IsSatisfiedBy checks if entity does NOT satisfy the specification
func (s *NotSpecification) IsSatisfiedBy(entity interface{}) bool {
	return !s.spec.IsSatisfiedBy(entity)
}

// And combines specifications
func (s *NotSpecification) And(other Specification) Specification {
	return &AndSpecification{left: s, right: other}
}

// Or combines specifications
func (s *NotSpecification) Or(other Specification) Specification {
	return &OrSpecification{left: s, right: other}
}

// Not negates the specification (double negation)
func (s *NotSpecification) Not() Specification {
	return s.spec // Double negation cancels out
}
