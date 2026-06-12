// Package specifications provides Criteria pattern for flexible queries
package specifications

import (
	"strconv"
	"strings"
)

// FilterParam represents a single filter condition received from query params.
//
// URL format (repeated param):
//
//	?filters=field,operator,value[,condition]
//
// Operators : eq  ne  gt  gte  lt  lte  contains  in  between  is_null  is_not_null
// Conditions: and (default) | or
//
// Examples:
//
//	filters=category,eq,Electronics,and
//	filters=price,gt,500,and
//	filters=price,between,100|2000
//	filters=name,contains,laptop
//	filters=stock,gt,0,or
type FilterParam struct {
	Field     string      // entity field name
	Operator  string      // eq | ne | gt | gte | lt | lte | contains | in | between | is_null | is_not_null
	Value     interface{} // scalar, or []interface{} for "in"/"between"
	Condition string      // "and" (default) | "or"
}

// ParseFilterParams converts a slice of "field,operator,value[,condition]" strings
// into a *Criteria ready to pass to a repository.
//
// Pagination and sorting are set separately via page, pageSize and sortBy.
func ParseFilterParams(filters []string, page, pageSize int, sortField, sortDir string) *Criteria {
	builder := NewCriteriaBuilder()

	for _, f := range filters {
		fp := parseOneFilter(f)
		if fp == nil {
			continue
		}
		applyFilter(builder, fp)
	}

	// Sorting
	if sortField == "" {
		sortField = "created_at"
	}
	switch strings.ToLower(sortDir) {
	case "asc":
		builder.OrderByAsc(sortField)
	default:
		builder.OrderByDesc(sortField)
	}

	// Pagination
	builder.Paginate(page, pageSize)

	return builder.Build()
}

// ParseSortBy parses "field:direction" or "field,direction" or just "field".
// Returns (field, direction).
func ParseSortBy(sortBy string) (string, string) {
	if sortBy == "" {
		return "created_at", "desc"
	}
	// support both "field:dir" and "field,dir"
	sortBy = strings.ReplaceAll(sortBy, ":", ",")
	parts := strings.SplitN(sortBy, ",", 2)
	field := strings.TrimSpace(parts[0])
	dir := "desc"
	if len(parts) == 2 {
		dir = strings.ToLower(strings.TrimSpace(parts[1]))
	}
	return field, dir
}

// parseOneFilter parses a single "field,operator,value[,condition]" string.
// is_null and is_not_null operators do not require a value: "field,is_null" is valid.
func parseOneFilter(s string) *FilterParam {
	parts := strings.SplitN(s, ",", 4)
	if len(parts) < 2 {
		return nil
	}
	op := strings.ToLower(strings.TrimSpace(parts[1]))
	if op != "is_null" && op != "is_not_null" && len(parts) < 3 {
		return nil
	}

	fp := &FilterParam{
		Field:     strings.TrimSpace(parts[0]),
		Operator:  strings.ToLower(strings.TrimSpace(parts[1])),
		Condition: "and",
	}

	if len(parts) == 4 {
		cond := strings.ToLower(strings.TrimSpace(parts[3]))
		if cond == "or" {
			fp.Condition = "or"
		}
	}

	rawValue := ""
	if len(parts) > 2 {
		rawValue = strings.TrimSpace(parts[2])
	}

	switch fp.Operator {
	case "in":
		// values separated by "|"
		vals := strings.Split(rawValue, "|")
		parsed := make([]interface{}, 0, len(vals))
		for _, v := range vals {
			parsed = append(parsed, parseScalar(strings.TrimSpace(v)))
		}
		fp.Value = parsed
	case "between":
		// exactly two values separated by "|"
		vals := strings.SplitN(rawValue, "|", 2)
		if len(vals) == 2 {
			fp.Value = []interface{}{parseScalar(strings.TrimSpace(vals[0])), parseScalar(strings.TrimSpace(vals[1]))}
		}
	case "is_null", "is_not_null":
		fp.Value = nil
	default:
		fp.Value = parseScalar(rawValue)
	}

	return fp
}

// applyFilter adds a FilterParam to the CriteriaBuilder using the correct condition.
func applyFilter(b *CriteriaBuilder, fp *FilterParam) {
	op := operatorToSQL(fp.Operator)

	switch fp.Operator {
	case "in":
		values, _ := fp.Value.([]interface{})
		if fp.Condition == "or" {
			b.OrWhereIn(fp.Field, values)
		} else {
			b.WhereIn(fp.Field, values)
		}
	case "between":
		values, _ := fp.Value.([]interface{})
		if len(values) == 2 {
			if fp.Condition == "or" {
				b.OrWhereBetween(fp.Field, values[0], values[1])
			} else {
				b.WhereBetween(fp.Field, values[0], values[1])
			}
		}
	default:
		if fp.Condition == "or" {
			b.OrWhere(fp.Field, op, fp.Value)
		} else {
			b.Where(fp.Field, op, fp.Value)
		}
	}
}

// operatorToSQL maps FilterParam operators to CriteriaBuilder operators.
func operatorToSQL(op string) string {
	switch op {
	case "eq":
		return "="
	case "ne":
		return "!="
	case "gt":
		return ">"
	case "gte":
		return ">="
	case "lt":
		return "<"
	case "lte":
		return "<="
	case "contains", "like":
		return "LIKE"
	case "is_null":
		return "IS NULL"
	case "is_not_null":
		return "IS NOT NULL"
	default:
		return "="
	}
}

// parseScalar converts a string to bool, int, float64 or keeps it as string.
func parseScalar(s string) interface{} {
	if s == "" || s == "null" || s == "none" {
		return nil
	}
	if s == "true" {
		return true
	}
	if s == "false" {
		return false
	}
	if i, err := strconv.ParseInt(s, 10, 64); err == nil {
		return i
	}
	if f, err := strconv.ParseFloat(s, 64); err == nil {
		return f
	}
	return s
}
