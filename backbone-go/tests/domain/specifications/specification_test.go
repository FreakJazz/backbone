package specifications_test

import (
	"testing"

	"github.com/freakjazz/backbone-go/domain/specifications"
	"github.com/stretchr/testify/assert"
)

func TestEqualSpecification(t *testing.T) {
	spec := specifications.NewEqualSpecification("name", "John")

	sql, args := spec.ToSQL()

	assert.Equal(t, "name = ?", sql)
	assert.Equal(t, []interface{}{"John"}, args)
}

func TestNotEqualSpecification(t *testing.T) {
	spec := specifications.NewNotEqualSpecification("status", "deleted")

	sql, args := spec.ToSQL()

	assert.Equal(t, "status != ?", sql)
	assert.Equal(t, []interface{}{"deleted"}, args)
}

func TestGreaterThanSpecification(t *testing.T) {
	spec := specifications.NewGreaterThanSpecification("age", 18)

	sql, args := spec.ToSQL()

	assert.Equal(t, "age > ?", sql)
	assert.Equal(t, []interface{}{18}, args)
}

func TestLessThanSpecification(t *testing.T) {
	spec := specifications.NewLessThanSpecification("price", 100.50)

	sql, args := spec.ToSQL()

	assert.Equal(t, "price < ?", sql)
	assert.Equal(t, []interface{}{100.50}, args)
}

func TestInSpecification(t *testing.T) {
	values := []interface{}{"admin", "manager", "user"}
	spec := specifications.NewInSpecification("role", values)

	sql, args := spec.ToSQL()

	assert.Equal(t, "role IN (?, ?, ?)", sql)
	assert.Equal(t, values, args)
}

func TestLikeSpecification(t *testing.T) {
	spec := specifications.NewLikeSpecification("email", "%@example.com")

	sql, args := spec.ToSQL()

	assert.Equal(t, "email LIKE ?", sql)
	assert.Equal(t, []interface{}{"%@example.com"}, args)
}

func TestBetweenSpecification(t *testing.T) {
	spec := specifications.NewBetweenSpecification("salary", 30000, 80000)

	sql, args := spec.ToSQL()

	assert.Equal(t, "salary BETWEEN ? AND ?", sql)
	assert.Equal(t, []interface{}{30000, 80000}, args)
}

func TestIsNullSpecification(t *testing.T) {
	spec := specifications.NewIsNullSpecification("deleted_at")

	sql, args := spec.ToSQL()

	assert.Equal(t, "deleted_at IS NULL", sql)
	assert.Empty(t, args)
}

func TestAndSpecification(t *testing.T) {
	spec1 := specifications.NewEqualSpecification("status", "active")
	spec2 := specifications.NewGreaterThanSpecification("age", 18)

	combined := spec1.And(spec2)
	sql, args := combined.ToSQL()

	assert.Contains(t, sql, "status = ?")
	assert.Contains(t, sql, "age > ?")
	assert.Contains(t, sql, "AND")
	assert.Equal(t, []interface{}{"active", 18}, args)
}

func TestOrSpecification(t *testing.T) {
	spec1 := specifications.NewEqualSpecification("role", "admin")
	spec2 := specifications.NewEqualSpecification("role", "manager")

	combined := spec1.Or(spec2)
	sql, args := combined.ToSQL()

	assert.Contains(t, sql, "role = ?")
	assert.Contains(t, sql, "OR")
	assert.Equal(t, []interface{}{"admin", "manager"}, args)
}

func TestNotSpecification(t *testing.T) {
	spec := specifications.NewEqualSpecification("deleted", true)
	notSpec := spec.Not()

	sql, args := notSpec.ToSQL()

	assert.Contains(t, sql, "NOT")
	assert.Contains(t, sql, "deleted = ?")
	assert.Equal(t, []interface{}{true}, args)
}

func TestComplexSpecification(t *testing.T) {
	// (age > 18 AND status = 'active') OR role = 'admin'
	spec1 := specifications.NewGreaterThanSpecification("age", 18)
	spec2 := specifications.NewEqualSpecification("status", "active")
	spec3 := specifications.NewEqualSpecification("role", "admin")

	combined := spec1.And(spec2).Or(spec3)
	sql, args := combined.ToSQL()

	assert.Contains(t, sql, "age > ?")
	assert.Contains(t, sql, "status = ?")
	assert.Contains(t, sql, "role = ?")
	assert.Contains(t, sql, "AND")
	assert.Contains(t, sql, "OR")
	assert.Equal(t, []interface{}{18, "active", "admin"}, args)
}

func TestCriteriaBuilder(t *testing.T) {
	criteria := specifications.NewCriteriaBuilder().
		Where("status", "=", "active").
		Where("age", ">", 18).
		OrderByDesc("created_at").
		Limit(10).
		Offset(20).
		Build()

	whereClause, args, orderBy, limit := criteria.ToSQL()

	assert.NotEmpty(t, whereClause)
	assert.Contains(t, whereClause, "status = ?")
	assert.Contains(t, whereClause, "age > ?")
	assert.Equal(t, []interface{}{"active", 18}, args)
	assert.Equal(t, "created_at DESC", orderBy)
	assert.Equal(t, "LIMIT 10 OFFSET 20", limit)
}

func TestCriteriaPagination(t *testing.T) {
	criteria := specifications.NewCriteriaBuilder().
		Where("status", "=", "active").
		Paginate(2, 25). // Page 2, 25 items per page
		Build()

	_, _, _, limit := criteria.ToSQL()

	assert.Equal(t, "LIMIT 25 OFFSET 25", limit)
}

func TestCriteriaMultipleSorting(t *testing.T) {
	criteria := specifications.NewCriteriaBuilder().
		OrderByDesc("priority").
		OrderByAsc("created_at").
		OrderByAsc("name").
		Build()

	_, _, orderBy, _ := criteria.ToSQL()

	assert.Equal(t, "priority DESC, created_at ASC, name ASC", orderBy)
}

func TestQueryBuilder(t *testing.T) {
	query := specifications.NewQueryBuilder("SELECT * FROM users").
		Where("status", "=", "active").
		AndWhere("age", ">", 18).
		OrderByDesc("created_at").
		Limit(10).
		WithParam("source", "api").
		Build()

	sql, args := query.GetSQL()
	params := query.GetParams()

	assert.Contains(t, sql, "SELECT * FROM users")
	assert.Contains(t, sql, "WHERE")
	assert.Contains(t, sql, "ORDER BY")
	assert.Contains(t, sql, "LIMIT")
	assert.NotEmpty(t, args)
	assert.Equal(t, "api", params["source"])
}

func TestQueryBuilderWhereIn(t *testing.T) {
	query := specifications.NewQueryBuilder("SELECT * FROM users").
		WhereIn("role", []interface{}{"admin", "manager"}).
		Build()

	sql, args := query.GetSQL()

	assert.Contains(t, sql, "role IN (?, ?)")
	assert.Equal(t, []interface{}{"admin", "manager"}, args)
}

func TestQueryBuilderWhereBetween(t *testing.T) {
	query := specifications.NewQueryBuilder("SELECT * FROM employees").
		WhereBetween("salary", 30000, 80000).
		Build()

	sql, args := query.GetSQL()

	assert.Contains(t, sql, "salary BETWEEN ? AND ?")
	assert.Equal(t, []interface{}{30000, 80000}, args)
}

func TestGetFullSQL(t *testing.T) {
	criteria := specifications.NewCriteriaBuilder().
		Where("status", "=", "active").
		OrderByAsc("name").
		Limit(5).
		Build()

	fullSQL, args := criteria.GetFullSQL("SELECT * FROM users")

	assert.Contains(t, fullSQL, "SELECT * FROM users")
	assert.Contains(t, fullSQL, "WHERE status = ?")
	assert.Contains(t, fullSQL, "ORDER BY name ASC")
	assert.Contains(t, fullSQL, "LIMIT 5")
	assert.Equal(t, []interface{}{"active"}, args)
}
