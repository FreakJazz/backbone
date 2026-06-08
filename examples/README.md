# 🎯 Clean API Examples - Go vs Python

Ejemplos completos de APIs con **arquitectura limpia** usando los frameworks Backbone en **Go** y **Python**.

## 📋 Descripción

Ambos ejemplos implementan la **misma API de gestión de productos** demostrando:

✅ **Arquitectura limpia** por capas (Domain, Application, Infrastructure, Interfaces)  
✅ **Specification Pattern** para queries dinámicas  
✅ **Logging estructurado** con contexto de capa, método, handler y queries  
✅ **Manejo de errores** con códigos de 8 dígitos  
✅ **Filtros dinámicos** por categoría, precio, stock, nombre  
✅ **Paginación** y ordenamiento  
✅ **Validaciones** en capa de dominio  
✅ **Response builders** estandarizados  

---

## 🆚 Comparación

| Característica | Go | Python |
|----------------|-----|---------|
| **Framework Web** | net/http (stdlib) | Flask |
| **Puerto** | 8080 | 5000 |
| **Logger** | EnhancedLogger | LoggerFactory |
| **Specification** | query_object.go | filter_specification.py |
| **Type Safety** | Fuerte | Dinámico + type hints |
| **Concurrencia** | Goroutines nativas | Threading |
| **Performance** | Alta (compilado) | Media (interpretado) |

---

## 🚀 Go Example

### Estructura

```
clean-api-go/
├── domain/
│   ├── entities/product.go
│   ├── repositories/product_repository.go
│   └── specifications/product_specs.go
├── application/
│   └── usecases/
│       ├── create_product.go
│       └── get_products.go
├── infrastructure/
│   └── repositories/memory_product_repository.go
├── interfaces/
│   └── http/
│       ├── handlers/product_handler.go
│       └── middleware/logging_middleware.go
└── main.go
```

### Ejecutar

```bash
cd examples/clean-api-go
go run main.go
```

### Endpoints

```
http://localhost:8080/api/products       # POST, GET
http://localhost:8080/health             # GET
```

### Ejemplo de Request

```bash
# Crear producto
curl -X POST http://localhost:8080/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gaming Laptop",
    "description": "High-end gaming laptop",
    "price": 2500.00,
    "category": "Electronics",
    "stock": 25
  }'

# Listar con filtros
curl "http://localhost:8080/api/products?category=Electronics&min_price=1000&max_price=2000&in_stock=true&page=1&page_size=10"
```

### Características Go

**✅ Type Safety Fuerte**
```go
query := specifications.NewQueryBuilder("SELECT * FROM products").
    Where("category", "=", category).
    WhereBetween("price", minPrice, maxPrice).
    OrderByDesc("created_at").
    Paginate(page, pageSize).
    Build()
```

**✅ Enhanced Logger**
```go
logger := logging.NewEnhancedLogger("product-api").
    WithLayer("application").
    WithHandler("CreateProductHandler").
    WithMethod("Execute")

logger.LogQuery(sql, args, durationMs, err)
```

**✅ Goroutines para Concurrencia**
```go
go func() {
    server.ListenAndServe()
}()
```

---

## 🐍 Python Example

### Estructura

```
clean_api_python/
├── domain/
│   ├── entities/product.py
│   ├── repositories/product_repository.py
│   └── specifications/product_specs.py
├── application/
│   └── use_cases/
│       ├── create_product.py
│       └── get_products.py
├── infrastructure/
│   └── repositories/memory_product_repository.py
├── interfaces/
│   └── http/
│       ├── handlers/product_handler.py
│       └── middleware/logging_middleware.py
├── requirements.txt
└── main.py
```

### Ejecutar

```bash
cd examples/clean_api_python
pip install -r requirements.txt
python main.py
```

### Endpoints

```
http://localhost:5000/api/products       # POST, GET
http://localhost:5000/health             # GET
```

### Ejemplo de Request

```bash
# Crear producto
curl -X POST http://localhost:5000/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gaming Laptop",
    "description": "High-end gaming laptop",
    "price": 2500.00,
    "category": "Electronics",
    "stock": 25
  }'

# Listar con filtros
curl "http://localhost:5000/api/products?category=Electronics&min_price=1000&max_price=2000&in_stock=true&page=1&page_size=10"
```

### Características Python

**✅ Specification Pattern**
```python
from backbone.domain.specifications import FilterSpecification

spec = FilterSpecification("category", "=", category)
spec = spec & FilterSpecification("price", ">=", min_price)
spec = spec & FilterSpecification("stock", ">", 0)
```

**✅ Logger con Capas**
```python
logger = LoggerFactory.create_layer_logger(
    "product-api",
    "application",
    "CreateProductUseCase"
)

logger.log(LogLevel.INFO, "Creating product", extra_data={...}, context={...})
```

**✅ Flask Decorators**
```python
@app.route("/api/products", methods=["POST"])
@logging_middleware
def create_product():
    return product_handler.create_product()
```

---

## 📊 Logging por Capa

### Go Output

```json
{
  "timestamp": "2026-06-01T10:30:45Z",
  "level": "INFO",
  "service": "product-api",
  "layer": "infrastructure",
  "component": "MemoryProductRepository",
  "method": "FindByCriteria",
  "message": "Query executed",
  "query": {
    "sql": "SELECT * FROM products WHERE category = ? AND price BETWEEN ? AND ?",
    "args": ["Electronics", 1000, 2000],
    "duration_ms": 15
  }
}
```

### Python Output

```json
{
  "timestamp": "2026-06-01T10:30:45.123456",
  "level": "INFO",
  "service": "product-api",
  "layer": "infrastructure",
  "component": "MemoryProductRepository",
  "source_file": "memory_product_repository.py",
  "message": "Query executed",
  "extra_data": {
    "sql": "SELECT * FROM products WHERE category = ? AND price >= ? AND price <= ?",
    "args": ["Electronics", 1000, 2000],
    "duration_ms": 15
  }
}
```

---

## 🎯 Errores por Código

Ambos ejemplos usan el sistema de **códigos de error de 8 dígitos**:

| Código | Capa | Descripción |
|--------|------|-------------|
| **11001001** | Domain | Invalid product name |
| **11001002** | Domain | Invalid product price |
| **11001003** | Domain | Invalid stock quantity |
| **10001001** | Application | Product creation failed |
| **10001002** | Application | Product not found |
| **10002001** | Application | Failed to count products |
| **10002002** | Application | Failed to get products |
| **12001001** | Infrastructure | Product already exists |
| **12001002** | Infrastructure | Product not found for update |
| **12001003** | Infrastructure | Product not found for deletion |
| **13001001** | Interface | Invalid JSON payload |
| **13001002** | Interface | Use case failed |
| **13001003** | Interface | Query failed |

---

## 🔍 Filtros Dinámicos

### Go

```go
// Specification Pattern
query := specifications.NewQueryBuilder("SELECT * FROM products").
    Where("category", "=", "Electronics").
    WhereBetween("price", 1000.0, 2000.0).
    Where("stock", ">", 0).
    OrderByDesc("created_at").
    Paginate(1, 10).
    Build()

sql, args := query.GetSQL()
```

### Python

```python
# Specification Pattern
from backbone.domain.specifications import FilterSpecification

filters = [
    FilterSpecification("category", "=", "Electronics"),
    FilterSpecification("price", ">=", 1000),
    FilterSpecification("price", "<=", 2000),
    FilterSpecification("stock", ">", 0)
]

products = repository.find_by_criteria(filters=filters, page=1, page_size=10)
```

---

## 📝 Casos de Uso Implementados

### 1. Crear Producto

**Input:**
```json
{
  "name": "Laptop Dell XPS 15",
  "description": "High performance laptop",
  "price": 1500.00,
  "category": "Electronics",
  "stock": 50
}
```

**Output:**
```json
{
  "success": true,
  "message": "Product created successfully",
  "data": {
    "product": {
      "id": "uuid",
      "name": "Laptop Dell XPS 15",
      "price": 1500.00,
      ...
    }
  },
  "status": 201
}
```

### 2. Listar Productos con Filtros

**Query Parameters:**
- `category` - Filtrar por categoría
- `min_price` - Precio mínimo
- `max_price` - Precio máximo
- `in_stock` - Solo productos en stock
- `name` - Buscar por nombre (pattern)
- `page` - Número de página
- `page_size` - Tamaño de página
- `sort_by` - Campo para ordenar
- `sort_order` - Orden (asc/desc)

**Output:**
```json
{
  "success": true,
  "message": "Products retrieved successfully",
  "data": [
    {
      "id": "1",
      "name": "Laptop Dell XPS 15",
      "price": 1500.00,
      ...
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_records": 50,
    "total_pages": 5
  },
  "status": 200
}
```

---

## 🎓 Conceptos Demostrados

### Ambos Ejemplos

1. ✅ **Clean Architecture** - 4 capas bien definidas
2. ✅ **Specification Pattern** - Queries dinámicas
3. ✅ **Repository Pattern** - Abstracción de persistencia
4. ✅ **Use Case Pattern** - Lógica de aplicación
5. ✅ **Dependency Injection** - Inversión de dependencias
6. ✅ **Logging Estructurado** - Con contexto completo
7. ✅ **Error Handling** - Códigos de 8 dígitos
8. ✅ **Response Builders** - Respuestas estandarizadas
9. ✅ **Validation** - En capa de dominio
10. ✅ **Middleware** - Logging de requests/responses

---

## 🚦 Testing

### Go

```bash
# Unit tests (cuando se implementen)
go test ./... -v

# Integration tests
curl http://localhost:8080/health
```

### Python

```bash
# Unit tests (cuando se implementen)
pytest

# Integration tests
curl http://localhost:5000/health
```

---

## 📚 Referencias

- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Specification Pattern](https://martinfowler.com/apsupp/spec.pdf)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Domain-Driven Design](https://domainlanguage.com/ddd/)

---

## 💡 Conclusión

Ambos ejemplos demuestran cómo implementar una **API completa con arquitectura limpia** usando los frameworks Backbone:

- **Go**: Mayor performance, type safety fuerte, concurrencia nativa
- **Python**: Más expresivo, desarrollo rápido, comunidad grande

Elige según tus necesidades:
- **Go** para sistemas de alto rendimiento y baja latencia
- **Python** para desarrollo rápido y ecosistema rico

Ambos implementan los **mismos patrones y principios** de arquitectura limpia! 🎯
