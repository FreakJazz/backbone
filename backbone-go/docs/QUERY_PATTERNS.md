# 🔍 Query Patterns & Enhanced Logging

## Specification Pattern

### Características

- ✅ **Consultas dinámicas** tipo-seguras
- ✅ **Composición** de especificaciones (AND, OR, NOT)
- ✅ **Generación SQL** automática
- ✅ **Reutilización** de lógica de filtrado
- ✅ **Testing** simplificado

### Uso Básico

```go
import "github.com/freakjazz/backbone-go/domain/specifications"

// Especificaciones simples
activeSpec := specifications.NewEqualSpecification("status", "active")
ageSpec := specifications.NewGreaterThanSpecification("age", 18)

// Combinar con AND
combined := activeSpec.And(ageSpec)

// Generar SQL
sql, args := combined.ToSQL()
// Output: (status = ? AND age > ?) | Args: ["active", 18]
```

### Especificaciones Disponibles

| Especificación | Ejemplo | SQL Generado |
|----------------|---------|--------------|
| `Equal` | `NewEqualSpecification("name", "John")` | `name = ?` |
| `NotEqual` | `NewNotEqualSpecification("status", "deleted")` | `status != ?` |
| `GreaterThan` | `NewGreaterThanSpecification("age", 18)` | `age > ?` |
| `LessThan` | `NewLessThanSpecification("price", 100)` | `price < ?` |
| `In` | `NewInSpecification("role", []interface{}{"admin", "user"})` | `role IN (?, ?)` |
| `Like` | `NewLikeSpecification("email", "%@example.com")` | `email LIKE ?` |
| `Between` | `NewBetweenSpecification("salary", 30000, 80000)` | `salary BETWEEN ? AND ?` |
| `IsNull` | `NewIsNullSpecification("deleted_at")` | `deleted_at IS NULL` |

---

## Criteria Pattern

### Uso con Builder

```go
criteria := specifications.NewCriteriaBuilder().
    Where("status", "=", "active").
    Where("age", ">", 18).
    WhereIn("department", []interface{}{"IT", "Sales"}).
    OrderByDesc("created_at").
    OrderByAsc("name").
    Paginate(2, 20).  // Página 2, 20 por página
    Build()

// Obtener SQL completo
fullSQL, args := criteria.GetFullSQL("SELECT * FROM users")
```

**Resultado:**
```sql
SELECT * FROM users 
WHERE (status = ? AND age > ? AND department IN (?, ?)) 
ORDER BY created_at DESC, name ASC 
LIMIT 20 OFFSET 20
```

---

## Query Object Pattern

### Construcción de Queries

```go
query := specifications.NewQueryBuilder("SELECT * FROM employees").
    Where("status", "=", "active").
    AndWhere("department", "=", "IT").
    WhereBetween("salary", 50000, 100000).
    OrderByDesc("salary").
    Paginate(1, 50).
    WithParam("report_type", "employee_listing").
    Build()

sql, args := query.GetSQL()
params := query.GetParams()

// Logging completo
fmt.Println(query.String())
// Output: SQL: SELECT * FROM employees WHERE... | Args: [...] | Params: {...}
```

---

## 📊 Enhanced Logging

### Características del Logger Mejorado

- ✅ **Información de Capa** (domain, application, infrastructure, interfaces)
- ✅ **Método y Handler** automáticamente detectados
- ✅ **Query Logging** con SQL, args, duración, errores
- ✅ **Stack Traces** para errores
- ✅ **Context-aware** con trace_id, request_id, user_id
- ✅ **Error Codes** integrados con el sistema de excepciones
- ✅ **JSON output** para ELK Stack

### Uso del Enhanced Logger

```go
import "github.com/freakjazz/backbone-go/infrastructure/logging"

// Crear logger
logger := logging.NewEnhancedLogger("my-service")

// Con contexto de capa y componente
repoLogger := logger.
    WithLayer("infrastructure").
    WithComponent("UserRepository").
    WithMethod("FindByCriteria")

// Logging normal
repoLogger.Info("Finding users", map[string]interface{}{
    "criteria": "active users",
})

// Logging de queries
repoLogger.LogQuery(sql, args, durationMs, err)

// Logging con error code
repoLogger.ErrorWithCode("Database connection failed", 12001001, map[string]interface{}{
    "host": "localhost",
    "port": 5432,
})
```

### Ejemplo de Output JSON

```json
{
  "timestamp": "2026-06-01T10:30:45Z",
  "level": "ERROR",
  "service": "user-service",
  "component": "UserRepository",
  "layer": "infrastructure",
  "method": "FindByCriteria",
  "handler": "GetUsersHandler",
  "message": "Query execution failed",
  "extra_data": {
    "table": "users",
    "error_type": "connection_timeout"
  },
  "query": {
    "sql": "SELECT * FROM users WHERE status = ? AND age > ?",
    "args": ["active", 18],
    "duration_ms": 5243,
    "error": "connection timeout after 5s"
  },
  "context": {
    "request_id": "req-12345",
    "user_id": "user-abc",
    "trace_id": "trace-xyz"
  },
  "stack_trace": "goroutine 1 [running]:\n...",
  "trace_id": "trace-xyz",
  "request_id": "req-12345",
  "user_id": "user-abc",
  "environment": "production",
  "error_code": 12001001
}
```

---

## 🎯 Patrones de Uso por Capa

### Domain Layer

```go
domainLogger := logger.
    WithLayer("domain").
    WithComponent("UserEntity")

domainLogger.Info("User entity created", map[string]interface{}{
    "user_id": user.ID,
    "email": user.Email,
})
```

### Application Layer

```go
appLogger := logger.
    WithLayer("application").
    WithHandler("CreateUserHandler").
    WithMethod("Execute").
    WithContext(map[string]interface{}{
        "request_id": requestID,
        "user_id": currentUserID,
    })

appLogger.Info("Processing user creation", map[string]interface{}{
    "email": input.Email,
})
```

### Infrastructure Layer

```go
infraLogger := logger.
    WithLayer("infrastructure").
    WithComponent("PostgresUserRepository").
    WithMethod("Save")

start := time.Now()
// Execute query...
duration := time.Since(start).Milliseconds()

infraLogger.LogQuery(sql, args, duration, err)
```

### Interface Layer

```go
interfaceLogger := logger.
    WithLayer("interfaces").
    WithHandler("UserHTTPHandler").
    WithMethod("CreateUser")

interfaceLogger.Info("HTTP request received", map[string]interface{}{
    "method": "POST",
    "path": "/api/v1/users",
})
```

---

## 🔥 Ejemplo Completo de Uso

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
    
    // Application layer
    handler := NewSearchEmployeesHandler(logger)
    handler.Execute(context.Background(), SearchCriteria{
        Department: "IT",
        MinSalary: 50000,
        Status: "active",
    })
}

type SearchEmployeesHandler struct {
    logger *logging.EnhancedLogger
    repo   EmployeeRepository
}

func (h *SearchEmployeesHandler) Execute(ctx context.Context, criteria SearchCriteria) error {
    // Logger con contexto completo
    handlerLogger := h.logger.
        WithLayer("application").
        WithHandler("SearchEmployeesHandler").
        WithMethod("Execute").
        WithContext(map[string]interface{}{
            "request_id": ctx.Value("request_id"),
            "user_id": ctx.Value("user_id"),
        })
    
    handlerLogger.Info("Starting employee search", map[string]interface{}{
        "criteria": criteria,
    })
    
    // Construir query con Specification Pattern
    query := specifications.NewQueryBuilder("SELECT * FROM employees").
        Where("status", "=", criteria.Status).
        Where("department", "=", criteria.Department).
        Where("salary", ">=", criteria.MinSalary).
        OrderByDesc("salary").
        Paginate(1, 50).
        Build()
    
    handlerLogger.Debug("Query built", map[string]interface{}{
        "query": query.String(),
    })
    
    // Ejecutar en repositorio
    start := time.Now()
    employees, err := h.repo.FindByCriteria(ctx, query)
    duration := time.Since(start).Milliseconds()
    
    if err != nil {
        handlerLogger.ErrorWithCode("Search failed", 10001001, map[string]interface{}{
            "error": err.Error(),
            "duration_ms": duration,
        })
        return err
    }
    
    handlerLogger.Info("Search completed", map[string]interface{}{
        "results_count": len(employees),
        "duration_ms": duration,
    })
    
    return nil
}
```

---

## 📝 Testing con Specifications

```go
func TestEmployeeSpecifications(t *testing.T) {
    // Arrange
    spec := specifications.NewEqualSpecification("department", "IT").
        And(specifications.NewGreaterThanSpecification("salary", 50000))
    
    // Act
    sql, args := spec.ToSQL()
    
    // Assert
    assert.Contains(t, sql, "department = ?")
    assert.Contains(t, sql, "salary > ?")
    assert.Equal(t, []interface{}{"IT", 50000}, args)
}
```

---

## 🚀 Beneficios

1. **Queries Dinámicas**: Construye queries complejas sin concatenación de strings
2. **Type Safety**: Detecta errores en tiempo de compilación
3. **Reutilización**: Las especificaciones se pueden combinar y reutilizar
4. **Testing**: Fácil de probar sin base de datos
5. **Logging Completo**: Visibilidad total de queries, errores y contexto
6. **Debugging**: Stack traces y contexto por capa facilitan el debugging
7. **Monitoreo**: JSON output compatible con ELK, Splunk, etc.

---

## 📊 Comparación con SQL Directo

| Aspecto | SQL Directo | Specification Pattern |
|---------|-------------|----------------------|
| Type Safety | ❌ No | ✅ Sí |
| Testing | ❌ Difícil | ✅ Fácil |
| Reutilización | ❌ Limitada | ✅ Alta |
| Mantenibilidad | ❌ Compleja | ✅ Simple |
| Logging | ⚠️ Manual | ✅ Automático |
| Debugging | ❌ Difícil | ✅ Fácil |

---

## 🎓 Recursos Adicionales

- [Specification Pattern (Martin Fowler)](https://martinfowler.com/apsupp/spec.pdf)
- [Query Object Pattern](https://martinfowler.com/eaaCatalog/queryObject.html)
- [Domain-Driven Design Patterns](https://domainlanguage.com/ddd/)
