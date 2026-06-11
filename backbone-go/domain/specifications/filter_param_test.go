package specifications_test

import (
	"testing"

	"github.com/freakjazz/backbone-go/domain/specifications"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// ── ParseSortBy ──────────────────────────────────────────────────────────────

func TestParseSortBy_ColonFormat(t *testing.T) {
	field, dir := specifications.ParseSortBy("price:desc")
	assert.Equal(t, "price", field)
	assert.Equal(t, "desc", dir)
}

func TestParseSortBy_CommaFormat(t *testing.T) {
	field, dir := specifications.ParseSortBy("name,asc")
	assert.Equal(t, "name", field)
	assert.Equal(t, "asc", dir)
}

func TestParseSortBy_FieldOnly(t *testing.T) {
	field, dir := specifications.ParseSortBy("created_at")
	assert.Equal(t, "created_at", field)
	assert.Equal(t, "desc", dir) // default
}

func TestParseSortBy_Empty(t *testing.T) {
	field, dir := specifications.ParseSortBy("")
	assert.Equal(t, "created_at", field)
	assert.Equal(t, "desc", dir)
}

// ── ParseFilterParams ─────────────────────────────────────────────────────────

func TestParseFilterParams_Empty(t *testing.T) {
	criteria := specifications.ParseFilterParams(nil, 1, 10, "created_at", "desc")
	require.NotNil(t, criteria)
	assert.Nil(t, criteria.Specification)
	assert.Equal(t, 10, criteria.Limit)
	assert.Equal(t, 0, criteria.Offset)
}

func TestParseFilterParams_SingleEq(t *testing.T) {
	criteria := specifications.ParseFilterParams(
		[]string{"category,eq,Electronics"},
		1, 10, "created_at", "desc",
	)
	require.NotNil(t, criteria.Specification)
	sql, args := criteria.Specification.ToSQL()
	assert.Contains(t, sql, "category")
	assert.Contains(t, args, "Electronics")
}

func TestParseFilterParams_GreaterThan(t *testing.T) {
	criteria := specifications.ParseFilterParams(
		[]string{"price,gt,500"},
		1, 10, "price", "asc",
	)
	require.NotNil(t, criteria.Specification)
	sql, args := criteria.Specification.ToSQL()
	assert.Contains(t, sql, "price > ?")
	assert.EqualValues(t, int64(500), args[0])
}

func TestParseFilterParams_Between(t *testing.T) {
	criteria := specifications.ParseFilterParams(
		[]string{"price,between,100|2000"},
		1, 10, "price", "asc",
	)
	require.NotNil(t, criteria.Specification)
	sql, args := criteria.Specification.ToSQL()
	assert.Contains(t, sql, "BETWEEN")
	assert.Len(t, args, 2)
}

func TestParseFilterParams_In(t *testing.T) {
	criteria := specifications.ParseFilterParams(
		[]string{"category,in,Electronics|Furniture"},
		1, 10, "name", "asc",
	)
	require.NotNil(t, criteria.Specification)
	sql, _ := criteria.Specification.ToSQL()
	assert.Contains(t, sql, "IN")
}

func TestParseFilterParams_Contains(t *testing.T) {
	criteria := specifications.ParseFilterParams(
		[]string{"name,contains,laptop"},
		1, 10, "name", "asc",
	)
	require.NotNil(t, criteria.Specification)
	sql, args := criteria.Specification.ToSQL()
	assert.Contains(t, sql, "LIKE")
	assert.Equal(t, "laptop", args[0])
}

func TestParseFilterParams_MultipleAndCondition(t *testing.T) {
	criteria := specifications.ParseFilterParams(
		[]string{"category,eq,Electronics,and", "price,gt,500,and"},
		1, 10, "created_at", "desc",
	)
	require.NotNil(t, criteria.Specification)
	sql, _ := criteria.Specification.ToSQL()
	assert.Contains(t, sql, "AND")
}

func TestParseFilterParams_Pagination(t *testing.T) {
	criteria := specifications.ParseFilterParams(nil, 3, 25, "name", "asc")
	assert.Equal(t, 25, criteria.Limit)
	assert.Equal(t, 50, criteria.Offset) // page 3 → offset = (3-1)*25 = 50
}

func TestParseFilterParams_SkipsInvalidFilter(t *testing.T) {
	// A filter with fewer than 3 parts should be skipped, not panic
	criteria := specifications.ParseFilterParams(
		[]string{"bad_filter", "price,gt,500"},
		1, 10, "created_at", "desc",
	)
	require.NotNil(t, criteria)
	// Only the valid filter should produce a specification
	require.NotNil(t, criteria.Specification)
}

func TestParseFilterParams_ScalarConversion(t *testing.T) {
	criteria := specifications.ParseFilterParams(
		[]string{"active,eq,true"},
		1, 10, "created_at", "desc",
	)
	require.NotNil(t, criteria.Specification)
	_, args := criteria.Specification.ToSQL()
	assert.Equal(t, true, args[0])
}

func TestParseFilterParams_IsNull(t *testing.T) {
	criteria := specifications.ParseFilterParams(
		[]string{"description,is_null"},
		1, 10, "created_at", "desc",
	)
	require.NotNil(t, criteria.Specification)
	sql, _ := criteria.Specification.ToSQL()
	assert.Contains(t, sql, "IS NULL")
}
