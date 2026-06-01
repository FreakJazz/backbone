# 🎯 Clean API Example - Go

API completa de gestión de productos con arquitectura limpia usando Backbone-Go.

## 📁 Estructura

```
clean-api-go/
├── domain/
│   ├── entities/
│   │   └── product.go           # Entidad Product
│   ├── repositories/
│   │   └── product_repository.go # Interface del repositorio
│   └── specifications/
│       └── product_specs.go      # Especificaciones de negocio
│
├── application/
│   └── usecases/
│       ├── create_product.go     # Caso de uso: Crear producto
│       ├── get_products.go       # Caso de uso: Listar productos
│       └── update_product.go     # Caso de uso: Actualizar producto
│
├── infrastructure/
│   └── repositories/
│       └── memory_product_repository.go # Repositorio en memoria
│
├── interfaces/
│   └── http/
│       ├── handlers/
│       │   └── product_handler.go # HTTP handlers
│       └── middleware/
│           └── logging_middleware.go # Middleware de logging
│
└── main.go                        # Punto de entrada
```

## 🚀 Ejecutar

```bash
# Ejecutar la API
go run examples/clean-api-go/main.go

# API disponible en: http://localhost:8080
```

## 📝 Endpoints

```
POST   /api/products           - Crear producto
GET    /api/products           - Listar productos (con filtros)
GET    /api/products/:id       - Obtener producto por ID
PUT    /api/products/:id       - Actualizar producto
DELETE /api/products/:id       - Eliminar producto
```

## 🔍 Ejemplo de Uso con Filtros

```bash
# Crear producto
curl -X POST http://localhost:8080/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop Dell XPS 15",
    "description": "High performance laptop",
    "price": 1500.00,
    "category": "Electronics",
    "stock": 50
  }'

# Listar con filtros (Specification Pattern)
curl "http://localhost:8080/api/products?category=Electronics&min_price=1000&max_price=2000&in_stock=true&page=1&page_size=10"
```

## 📊 Características Implementadas

### ✅ Por Capa

**Domain Layer:**
- Entidad `Product` con validaciones
- Especificaciones de negocio
- Interface del repositorio

**Application Layer:**
- Use cases con logging y validación
- Manejo de errores de aplicación (10xxxxxx)
- Context-aware operations

**Infrastructure Layer:**
- Repositorio en memoria con Specification Pattern
- Query logging completo
- Manejo de errores de infraestructura (12xxxxxx)

**Interface Layer:**
- HTTP handlers con validación de entrada
- Middleware de logging con request/response tracking
- Response builders estandarizados
- Manejo de errores HTTP (13xxxxxx)

### ✅ Logging por Capa

Cada capa genera logs con contexto completo:

```json
{
  "timestamp": "2026-06-01T10:30:45Z",
  "level": "INFO",
  "service": "product-api",
  "layer": "application",
  "handler": "CreateProductHandler",
  "method": "Execute",
  "message": "Creating product",
  "context": {
    "request_id": "req-123",
    "user_id": "user-abc"
  }
}
```

### ✅ Errores por Código

```go
// Domain (11xxxxxx)
11001001 - Invalid product name
11001002 - Invalid product price
11001003 - Invalid stock quantity

// Application (10xxxxxx)
10001001 - Product creation failed
10001002 - Product not found
10001003 - Invalid query parameters

// Infrastructure (12xxxxxx)
12001001 - Database query failed
12001002 - Repository error

// Interface (13xxxxxx)
13001001 - Invalid JSON payload
13001002 - Invalid request parameters
```

### ✅ Filtros Dinámicos

```go
// Construir query con Specification Pattern
query := specifications.NewQueryBuilder("SELECT * FROM products").
    Where("category", "=", category).
    WhereBetween("price", minPrice, maxPrice).
    Where("stock", ">", 0).
    OrderByDesc("created_at").
    Paginate(page, pageSize).
    Build()
```

## 🎓 Conceptos Demostrados

1. **Clean Architecture** - Separación clara de capas
2. **Specification Pattern** - Queries dinámicas tipo-seguras
3. **Enhanced Logging** - Logging con contexto de capa/método/handler
4. **Error Handling** - Sistema de códigos de 8 dígitos
5. **Dependency Injection** - Inversión de dependencias
6. **Repository Pattern** - Abstracción de persistencia
7. **Use Case Pattern** - Lógica de aplicación encapsulada
8. **Response Builders** - Respuestas estandarizadas
