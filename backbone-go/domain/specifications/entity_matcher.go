// Package specifications — entity-level evaluation for Specification pattern.
// Allows in-memory repositories to filter entities without a real database.
package specifications

import (
	"reflect"
	"strings"
)

// fieldValue extracts a field value from a struct by name (case-insensitive).
func fieldValue(entity interface{}, fieldName string) (interface{}, bool) {
	v := reflect.ValueOf(entity)
	if v.Kind() == reflect.Ptr {
		v = v.Elem()
	}
	if v.Kind() != reflect.Struct {
		return nil, false
	}

	// exact match first
	f := v.FieldByName(fieldName)
	if f.IsValid() {
		return f.Interface(), true
	}

	// case-insensitive match
	t := v.Type()
	for i := 0; i < t.NumField(); i++ {
		if strings.EqualFold(t.Field(i).Name, fieldName) {
			return v.Field(i).Interface(), true
		}
	}
	return nil, false
}

// toFloat64 converts a numeric value to float64 for comparison.
func toFloat64(v interface{}) (float64, bool) {
	switch n := v.(type) {
	case int:
		return float64(n), true
	case int32:
		return float64(n), true
	case int64:
		return float64(n), true
	case float32:
		return float64(n), true
	case float64:
		return n, true
	}
	return 0, false
}

// compare compares two values using a numeric or string ordering.
// Returns -1, 0, or 1 like strings.Compare.
func compare(a, b interface{}) int {
	fa, aIsNum := toFloat64(a)
	fb, bIsNum := toFloat64(b)
	if aIsNum && bIsNum {
		switch {
		case fa < fb:
			return -1
		case fa > fb:
			return 1
		default:
			return 0
		}
	}
	sa := strings.ToLower(reflect.ValueOf(a).String())
	sb := strings.ToLower(reflect.ValueOf(b).String())
	return strings.Compare(sa, sb)
}

// IsSatisfiedBy evaluates the specification against a struct entity using reflection.
// Override the stub in BaseSpecification.
func (s *EqualSpecification) IsSatisfiedBy(entity interface{}) bool {
	val, ok := fieldValue(entity, s.field)
	if !ok {
		return false
	}
	return reflect.DeepEqual(val, s.value)
}

// IsSatisfiedBy for NotEqual.
func (s *NotEqualSpecification) IsSatisfiedBy(entity interface{}) bool {
	val, ok := fieldValue(entity, s.field)
	if !ok {
		return false
	}
	return !reflect.DeepEqual(val, s.value)
}

// IsSatisfiedBy for GreaterThan.
func (s *GreaterThanSpecification) IsSatisfiedBy(entity interface{}) bool {
	val, ok := fieldValue(entity, s.field)
	if !ok {
		return false
	}
	return compare(val, s.value) > 0
}

// IsSatisfiedBy for GreaterThanOrEqual.
func (s *GreaterThanOrEqualSpecification) IsSatisfiedBy(entity interface{}) bool {
	val, ok := fieldValue(entity, s.field)
	if !ok {
		return false
	}
	return compare(val, s.value) >= 0
}

// IsSatisfiedBy for LessThan.
func (s *LessThanSpecification) IsSatisfiedBy(entity interface{}) bool {
	val, ok := fieldValue(entity, s.field)
	if !ok {
		return false
	}
	return compare(val, s.value) < 0
}

// IsSatisfiedBy for LessThanOrEqual.
func (s *LessThanOrEqualSpecification) IsSatisfiedBy(entity interface{}) bool {
	val, ok := fieldValue(entity, s.field)
	if !ok {
		return false
	}
	return compare(val, s.value) <= 0
}

// IsSatisfiedBy for Like (substring match, case-insensitive).
func (s *LikeSpecification) IsSatisfiedBy(entity interface{}) bool {
	val, ok := fieldValue(entity, s.field)
	if !ok {
		return false
	}
	pattern := strings.ToLower(strings.Trim(s.pattern, "%"))
	return strings.Contains(strings.ToLower(reflect.ValueOf(val).String()), pattern)
}

// IsSatisfiedBy for In.
func (s *InSpecification) IsSatisfiedBy(entity interface{}) bool {
	val, ok := fieldValue(entity, s.field)
	if !ok {
		return false
	}
	for _, v := range s.values {
		if reflect.DeepEqual(val, v) {
			return true
		}
	}
	return false
}

// IsSatisfiedBy for Between.
func (s *BetweenSpecification) IsSatisfiedBy(entity interface{}) bool {
	val, ok := fieldValue(entity, s.field)
	if !ok {
		return false
	}
	return compare(val, s.min) >= 0 && compare(val, s.max) <= 0
}

// IsSatisfiedBy for IsNull.
func (s *IsNullSpecification) IsSatisfiedBy(entity interface{}) bool {
	val, ok := fieldValue(entity, s.field)
	if !ok {
		return true
	}
	v := reflect.ValueOf(val)
	return !v.IsValid() || (v.Kind() == reflect.Ptr && v.IsNil())
}

