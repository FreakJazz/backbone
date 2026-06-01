# 🔍 Specification Pattern & Criteria Pattern

Sistema completo de consultas dinámicas mediante **Specification Pattern**, **Criteria Pattern** y **Query Object Pattern** con logging mejorado que rastrea método, handler, query y capa de error.

## 🎯 Características

- ✅ **Specification Pattern** completo con 8 especificaciones básicas
- ✅ **Criteria Pattern** con ordenamiento y paginación
- ✅ **Query Object Pattern** para encapsular queries completas
- ✅ **Composición** de especificaciones (AND, OR, NOT)
- ✅ **Type-safe** queries sin concatenación de strings
- ✅ **Generación SQL** automática con placeholders
- ✅ **Enhanced Logging** con contexto de capa, método, handler y queries
- ✅ **Stack traces** automáticos para errores
- ✅ **Error codes** integrados
- ✅ **JSON output** para ELK Stack

## 📦 Uso Rápido

### 1. Especificaciones Simples

```go
import "github.com/freakjazz/backbone-go/domain/specifications"

// Igualdad
spec := specifications.NewEqualSpecification("status", "active")
sql, args := spec.ToSQL()
// Output: "status = ?" | Args: ["active"]

// Mayor que
spec := specifications.NewGreaterThanSpecification("age", 18)
sql, args := spec.ToSQL()
// Output: "age > ?" | Args: [18]

// IN
spec := specifications.NewInSpecification("role", []interface{}{"admin", "user"})
sql, args := spec.ToSQL()
// Output: "role IN (?, ?)" | Args: ["admin", "user"]

// BETWEEN
spec := specifications.NewBetweenSpecification("salary", 30000, 80000)
sql, args := spec.ToSQL()
// Output: "salary BETWEEN ? AND ?" | Args: [30000, 80000]
```

### 2. Composición de Especificaciones

```go
// AND: age > 18 AND status = 'active'
spec1 := specifications.NewGreaterThanSpecification("age", 18)
spec2 := specifications.NewEqualSpecification("status", "active")
combined := spec1.And(spec2)

sql, args := combined.ToSQL()
// Output: "(age > ? AND status = ?)" | Args: [18, "active"]

// OR: role = 'admin' OR role = 'manager'
spec1 := specifications.NewEqualSpecification("role", "admin")
spec2 := specifications.NewEqualSpecification("role", "manager")
combined := spec1.Or(spec2)

sql, args := combined.ToSQL()
// Output: "(role = ? OR role = ?)" | Args: ["admin", "manager"]

// NOT: NOT deleted = true
spec := specifications.NewEqualSpecification("deleted", true).Not()
sql, args := spec.ToSQL()
// Output: "NOT (deleted = ?)" | Args: [true]
```

### 3. Criteria Pattern con Builder

```go
criteria := specifications.NewCriteriaBuilder().
    Where("status", "=", "active").
    Where("age", ">", 18).
    WhereIn("department", []interface{}{"IT", "Sales"}).
    WhereBetween("salary", 50000, 100000).
    OrderByDesc("created_at").
    OrderByAsc("name").
    Paginate(2, 20).  // Página 2, 20 items por página
    Build()

// Obtener SQL completo
fullSQL, args := criteria.GetFullSQL("SELECT * FROM users")
// Output: SELECT * FROM users WHERE ((status = ? AND age > ?) AND department IN (?, ?)) AND salary BETWEEN ? AND ?) ORDER BY created_at DESC, name ASC LIMIT 20 OFFSET 20
```

### 4. Query Object Pattern

```go
query := specifications.NewQueryBuilder("SELECT * FROM employees").
    Where("status", "=", "active").
    AndWhere("department", "=", "IT").
    WhereBetween("salary", 50000, 100000).
    OrderByDesc("salary").
    Paginate(1, 50).
    WithParam("report_type", "employee_listing").
    WithParam("source", "api").
    Build()

sql, args := query.GetSQL()
params := query.GetParams()

// Para logging
fmt.Println(query.String())
// Output: SQL: SELECT * FROM employees WHERE... | Args: [...] | Params: {...}
```

## 📊 Enhanced Logging

### Logger con Contexto Completo

```go
import "github.com/freakjazz/backbone-go/infrastructure/logging"

// Crear logger con contexto de capa, componente y método
logger := logging.NewEnhancedLogger("user-service").
    WithLayer("infrastructure").
    WithComponent("UserRepository").
    WithMethod("FindByCriteria").
    WithContext(map[string]interface{}{
        "request_id": "req-123",
        "user_id": "user-abc",
        "trace_id": "trace-xyz",
    })
```

### Logging de Queries

```go
// Logging de query con SQL, args, duración y error
sql := "SELECT * FROM users WHERE status = ? AND age > ?"
args := []interface{}{"active", 18}
durationMs := int64(15)
err := nil  // o error real

logger.LogQuery(sql, args, durationMs, err)
```

**Output JSON:**
```json
{
  "timestamp": "2026-06-01T10:30:45Z",
  "level": "DEBUG",
  "service": "user-service",
  "component": "UserRepository",
  "layer": "infrastructure",
  "method": "FindByCriteria",
  "message": "Query executed",
  "query": {
    "sql": "SELECT * FROM users WHERE status = ? AND age > ?",
    "args": ["active", 18],
    "duration_ms": 15
  },
  "context": {
    "request_id": "req-123",
    "user_id": "user-abc",
    "trace_id": "trace-xyz"
  },
  "trace_id": "trace-xyz",
  "request_id": "req-123",
  "user_id": "user-abc",
  "environment": "development"
}
```

### Logging de Queries con Parámetros

```go
logger.LogQueryWithParams(sql, args, params, durationMs, err)
```

### Logging de Errores con Código

```go
logger.ErrorWithCode("Database connection failed", 12001001, map[string]interface{}{
    "host": "localhost",
    "port": 5432,
    "error_type": "connection_timeout",
})
```

**Output JSON con Stack Trace:**
```json
{
  "timestamp": "2026-06-01T10:30:45Z",
  "level": "ERROR",
  "service": "user-service",
  "component": "UserRepository",
  "layer": "infrastructure",
  "method": "FindByCriteria",
  "message": "Database connection failed",
  "extra_data": {
    "host": "localhost",
    "port": 5432,
    "error_type": "connection_timeout"
  },
  "stack_trace": "goroutine 1 [running]:\n...",
  "error_code": 12001001,
  "environment": "production"
}
```

## 🎯 Especificaciones Disponibles

| Especificación | Constructor | SQL Generado |
|----------------|-------------|--------------|
| Equal | `NewEqualSpecification("name", "John")` | `name = ?` |
| NotEqual | `NewNotEqualSpecification("status", "deleted")` | `status != ?` |
| GreaterThan | `NewGreaterThanSpecification("age", 18)` | `age > ?` |
| LessThan | `NewLessThanSpecification("price", 100)` | `price < ?` |
| In | `NewInSpecification("role", []interface{}{"admin", "user"})` | `role IN (?, ?)` |
| Like | `NewLikeSpecification("email", "%@example.com")` | `email LIKE ?` |
| Between | `NewBetweenSpecification("salary", 30000, 80000)` | `salary BETWEEN ? AND ?` |
| IsNull | `NewIsNullSpecification("deleted_at")` | `deleted_at IS NULL` |

## 🚀 Ejemplo Completo

```go
package main

import (
    "context"
    "time"
    
    "github.com/freakjazz/backbone-go/domain/specifications"
    "github.com/freakjazz/backbone-go/infrastructure/logging"
)

func main() {
    // Setup logger
    logger := logging.NewEnhancedLogger("employee-service")
    
    // Application layer con contexto completo
    handler := NewSearchEmployeesHandler(logger)
    handler.Execute(context.Background())
}

type SearchEmployeesHandler struct {
    logger *logging.EnhancedLogger
}

func (h *SearchEmployeesHandler) Execute(ctx context.Context) error {
    // Logger con contexto de handler
    handlerLogger := h.logger.
        WithLayer("application").
        WithHandler("SearchEmployeesHandler").
        WithMethod("Execute").
        WithContext(map[string]interface{}{
            "request_id": ctx.Value("request_id"),
            "user_id": ctx.Value("user_id"),
        })
    
    handlerLogger.Info("Starting employee search", nil)
    
    // Construir query dinámico
    query := specifications.NewQueryBuilder("SELECT * FROM employees").
        Where("status", "=", "active").
        Where("department", "=", "IT").
        Where("salary", ">=", 50000).
        WhereBetween("years_experience", 2, 10).
        OrderByDesc("salary").
        Paginate(1, 50).
        WithParam("report_type", "employee_listing").
        Build()
    
    handlerLogger.Debug("Query built", map[string]interface{}{
        "query": query.String(),
    })
    
    // Ejecutar query (simulado)
    start := time.Now()
    sql, args := query.GetSQL()
    // db.Query(sql, args...)
    duration := time.Since(start).Milliseconds()
    
    handlerLogger.LogQuery(sql, args, duration, nil)
    
    handlerLogger.Info("Search completed", map[string]interface{}{
        "results_count": 25,
        "duration_ms": duration,
    })
    
    return nil
}
```

## 📝 Tests

```bash
# Ejecutar tests de specifications
go test ./domain/specifications/... -v

# Ejecutar ejemplo completo
go run examples/specifications/main.go
```

## 🎓 Documentación Completa

Ver [docs/QUERY_PATTERNS.md](../docs/QUERY_PATTERNS.md) para documentación completa con todos los patrones de uso y ejemplos avanzados.

## 📊 Beneficios

1. **Type Safety**: Detecta errores en tiempo de compilación
2. **Reutilización**: Las especificaciones se pueden combinar
3. **Testing**: Fácil de probar sin base de datos
4. **Logging Completo**: Visibilidad total de queries y errores
5. **Debugging**: Stack traces y contexto facilitan debugging
6. **Monitoreo**: JSON output compatible con ELK/Splunk
7. **Mantenibilidad**: Código limpio y organizado

## 🔗 Referencias

- [Specification Pattern (Martin Fowler)](https://martinfowler.com/apsupp/spec.pdf)
- [Query Object Pattern](https://martinfowler.com/eaaCatalog/queryObject.html)
- [Domain-Driven Design](https://domainlanguage.com/ddd/)
