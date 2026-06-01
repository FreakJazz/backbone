// Example of using Specification Pattern and Enhanced Logging
package main

import (
	"context"
	"fmt"
	"time"

	"github.com/freakjazz/backbone-go/domain/specifications"
	"github.com/freakjazz/backbone-go/infrastructure/logging"
)

func main() {
	fmt.Println("🔍 Specification Pattern & Enhanced Logging Example")
	fmt.Println("====================================================\n")

	// Setup enhanced logger
	logger := logging.NewEnhancedLogger("specification-example")
	logger.SetLevel(logging.LevelDebug)

	// Example 1: Simple Specifications
	fmt.Println("1️⃣  Simple Specifications:")
	exampleSimpleSpecifications(logger)

	// Example 2: Combined Specifications
	fmt.Println("\n2️⃣  Combined Specifications (AND/OR):")
	exampleCombinedSpecifications(logger)

	// Example 3: Criteria Pattern
	fmt.Println("\n3️⃣  Criteria Pattern with Pagination:")
	exampleCriteriaPattern(logger)

	// Example 4: Query Object Pattern
	fmt.Println("\n4️⃣  Query Object Pattern:")
	exampleQueryObjectPattern(logger)

	// Example 5: Complex Query with Logging
	fmt.Println("\n5️⃣  Complex Query with Enhanced Logging:")
	exampleComplexQueryWithLogging(logger)

	// Example 6: Query Execution Simulation
	fmt.Println("\n6️⃣  Query Execution with Error Tracking:")
	exampleQueryExecution(logger)
}

func exampleSimpleSpecifications(logger *logging.EnhancedLogger) {
	// Create logger with layer context
	domainLogger := logger.WithLayer("domain").WithComponent("UserRepository")

	// Equal specification
	spec1 := specifications.NewEqualSpecification("status", "active")
	sql1, args1 := spec1.ToSQL()
	domainLogger.Debug("Equal specification created", map[string]interface{}{
		"sql":  sql1,
		"args": args1,
	})
	fmt.Printf("  Equal: %s | Args: %v\n", sql1, args1)

	// Greater than specification
	spec2 := specifications.NewGreaterThanSpecification("age", 18)
	sql2, args2 := spec2.ToSQL()
	domainLogger.Debug("Greater than specification created", map[string]interface{}{
		"sql":  sql2,
		"args": args2,
	})
	fmt.Printf("  Greater than: %s | Args: %v\n", sql2, args2)

	// IN specification
	spec3 := specifications.NewInSpecification("role", []interface{}{"admin", "manager", "user"})
	sql3, args3 := spec3.ToSQL()
	domainLogger.Debug("IN specification created", map[string]interface{}{
		"sql":  sql3,
		"args": args3,
	})
	fmt.Printf("  IN: %s | Args: %v\n", sql3, args3)

	// BETWEEN specification
	spec4 := specifications.NewBetweenSpecification("salary", 30000, 80000)
	sql4, args4 := spec4.ToSQL()
	domainLogger.Debug("BETWEEN specification created", map[string]interface{}{
		"sql":  sql4,
		"args": args4,
	})
	fmt.Printf("  BETWEEN: %s | Args: %v\n", sql4, args4)
}

func exampleCombinedSpecifications(logger *logging.EnhancedLogger) {
	domainLogger := logger.WithLayer("domain").WithComponent("EmployeeRepository")

	// AND: age > 18 AND status = 'active'
	spec1 := specifications.NewGreaterThanSpecification("age", 18)
	spec2 := specifications.NewEqualSpecification("status", "active")
	combinedAND := spec1.And(spec2)

	sqlAND, argsAND := combinedAND.ToSQL()
	domainLogger.Info("AND specification created", map[string]interface{}{
		"sql":  sqlAND,
		"args": argsAND,
	})
	fmt.Printf("  AND: %s | Args: %v\n", sqlAND, argsAND)

	// OR: role = 'admin' OR role = 'manager'
	spec3 := specifications.NewEqualSpecification("role", "admin")
	spec4 := specifications.NewEqualSpecification("role", "manager")
	combinedOR := spec3.Or(spec4)

	sqlOR, argsOR := combinedOR.ToSQL()
	domainLogger.Info("OR specification created", map[string]interface{}{
		"sql":  sqlOR,
		"args": argsOR,
	})
	fmt.Printf("  OR: %s | Args: %v\n", sqlOR, argsOR)

	// Complex: (age > 18 AND status = 'active') OR role = 'admin'
	complexSpec := combinedAND.Or(specifications.NewEqualSpecification("role", "admin"))
	sqlComplex, argsComplex := complexSpec.ToSQL()
	domainLogger.Info("Complex specification created", map[string]interface{}{
		"sql":  sqlComplex,
		"args": argsComplex,
	})
	fmt.Printf("  Complex: %s | Args: %v\n", sqlComplex, argsComplex)

	// NOT specification
	notSpec := specifications.NewEqualSpecification("deleted", true).Not()
	sqlNot, argsNot := notSpec.ToSQL()
	domainLogger.Info("NOT specification created", map[string]interface{}{
		"sql":  sqlNot,
		"args": argsNot,
	})
	fmt.Printf("  NOT: %s | Args: %v\n", sqlNot, argsNot)
}

func exampleCriteriaPattern(logger *logging.EnhancedLogger) {
	infraLogger := logger.WithLayer("infrastructure").WithComponent("UserQuery")

	// Build criteria with fluent interface
	criteria := specifications.NewCriteriaBuilder().
		Where("status", "=", "active").
		Where("age", ">", 18).
		WhereIn("department", []interface{}{"IT", "Sales", "Marketing"}).
		OrderByDesc("created_at").
		OrderByAsc("name").
		Paginate(2, 20). // Page 2, 20 items per page
		Build()

	// Get SQL components
	whereClause, args, orderBy, limit := criteria.ToSQL()

	infraLogger.Info("Criteria built", map[string]interface{}{
		"where_clause": whereClause,
		"args":         args,
		"order_by":     orderBy,
		"limit":        limit,
	})

	fmt.Printf("  WHERE: %s\n", whereClause)
	fmt.Printf("  Args: %v\n", args)
	fmt.Printf("  ORDER BY: %s\n", orderBy)
	fmt.Printf("  LIMIT: %s\n", limit)

	// Get full SQL
	baseQuery := "SELECT * FROM users"
	fullSQL, fullArgs := criteria.GetFullSQL(baseQuery)

	infraLogger.Debug("Full query generated", map[string]interface{}{
		"full_sql":  fullSQL,
		"full_args": fullArgs,
	})

	fmt.Printf("\n  Full SQL: %s\n", fullSQL)
	fmt.Printf("  Full Args: %v\n", fullArgs)
}

func exampleQueryObjectPattern(logger *logging.EnhancedLogger) {
	appLogger := logger.WithLayer("application").WithHandler("GetActiveUsersHandler")

	// Build query using QueryBuilder
	query := specifications.NewQueryBuilder("SELECT * FROM users").
		Where("status", "=", "active").
		AndWhere("age", ">", 21).
		WhereIn("country", []interface{}{"USA", "Canada", "Mexico"}).
		OrderByDesc("registration_date").
		Paginate(1, 50).
		WithParam("source", "web-app").
		WithParam("request_type", "user_list").
		Build()

	sql, args := query.GetSQL()
	params := query.GetParams()

	appLogger.Info("Query object built", map[string]interface{}{
		"sql":    sql,
		"args":   args,
		"params": params,
	})

	fmt.Printf("  SQL: %s\n", sql)
	fmt.Printf("  Args: %v\n", args)
	fmt.Printf("  Params: %v\n", params)
	fmt.Printf("  String: %s\n", query.String())
}

func exampleComplexQueryWithLogging(logger *logging.EnhancedLogger) {
	// Simulate a use case handler
	handlerLogger := logger.
		WithLayer("application").
		WithHandler("SearchEmployeesHandler").
		WithMethod("Execute").
		WithContext(map[string]interface{}{
			"request_id": "req-12345",
			"user_id":    "user-abc",
			"trace_id":   "trace-xyz",
		})

	handlerLogger.Info("Starting employee search", map[string]interface{}{
		"search_criteria": "active employees in IT department",
	})

	// Build complex query
	query := specifications.NewQueryBuilder("SELECT * FROM employees").
		Where("status", "=", "active").
		AndWhere("department", "=", "IT").
		AndWhere("salary", ">", 50000).
		WhereBetween("years_experience", 2, 10).
		OrderByDesc("salary").
		OrderByAsc("last_name").
		Paginate(1, 25).
		WithParam("report_type", "employee_listing").
		Build()

	sql, args := query.GetSQL()

	handlerLogger.Debug("Query constructed", map[string]interface{}{
		"query": query.String(),
	})

	// Simulate query execution timing
	start := time.Now()
	time.Sleep(15 * time.Millisecond) // Simulate query execution
	duration := time.Since(start).Milliseconds()

	handlerLogger.LogQuery(sql, args, duration, nil)

	handlerLogger.Info("Employee search completed", map[string]interface{}{
		"results_count":  25,
		"execution_time": duration,
		"cache_hit":      false,
	})

	fmt.Printf("  ✅ Query executed in %dms\n", duration)
}

func exampleQueryExecution(logger *logging.EnhancedLogger) {
	// Simulate repository layer with error tracking
	repoLogger := logger.
		WithLayer("infrastructure").
		WithComponent("PostgresUserRepository").
		WithMethod("FindByCriteria")

	ctx := context.Background()

	// Successful query
	query1 := specifications.NewQueryBuilder("SELECT * FROM users").
		Where("id", "=", 123).
		Build()

	sql1, args1 := query1.GetSQL()

	repoLogger.Info("Executing query", map[string]interface{}{
		"query_type": "find_by_id",
	})

	start := time.Now()
	// Simulate successful execution
	time.Sleep(8 * time.Millisecond)
	duration := time.Since(start).Milliseconds()

	repoLogger.LogQuery(sql1, args1, duration, nil)
	fmt.Printf("  ✅ Successful query (8ms)\n")

	// Failed query with error
	query2 := specifications.NewQueryBuilder("SELECT * FROM invalid_table").
		Where("id", "=", 999).
		Build()

	sql2, args2 := query2.GetSQL()

	start = time.Now()
	// Simulate failed execution
	time.Sleep(5 * time.Millisecond)
	duration = time.Since(start).Milliseconds()
	err := fmt.Errorf("table 'invalid_table' does not exist")

	repoLogger.LogQuery(sql2, args2, duration, err)
	repoLogger.ErrorWithCode("Query execution failed", 12001001, map[string]interface{}{
		"table":      "invalid_table",
		"error_type": "table_not_found",
		"query":      sql2,
	})

	fmt.Printf("  ❌ Failed query with error tracking\n")

	// Complex query with params
	query3 := specifications.NewQueryBuilder("SELECT u.*, d.name as dept_name FROM users u JOIN departments d ON u.dept_id = d.id").
		Where("u.status", "=", "active").
		WhereIn("d.name", []interface{}{"Engineering", "Product"}).
		OrderByDesc("u.created_at").
		Paginate(1, 100).
		WithParam("include_departments", true).
		WithParam("filter_type", "active_with_dept").
		Build()

	sql3, args3 := query3.GetSQL()
	params3 := query3.GetParams()

	start = time.Now()
	time.Sleep(25 * time.Millisecond)
	duration = time.Since(start).Milliseconds()

	repoLogger.LogQueryWithParams(sql3, args3, params3, duration, nil)
	fmt.Printf("  ✅ Complex query with params (25ms)\n")

	_ = ctx // Use context
}
