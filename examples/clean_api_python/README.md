# 🎯 Clean API Example - Python

API completa de gestión de productos con arquitectura limpia usando Backbone-Python.

## 📁 Estructura

```
examples/clean_api_python/
├── domain/
│   ├── entities/
│   │   └── product.py           # Entidad Product
│   ├── repositories/
│   │   └── product_repository.py # Interface del repositorio
│   └── specifications/
│       └── product_specs.py      # Especificaciones de negocio
│
├── application/
│   └── use_cases/
│       ├── create_product.py     # Caso de uso: Crear producto
│       └── get_products.py       # Caso de uso: Listar productos
│
├── infrastructure/
│   └── repositories/
│       └── memory_product_repository.py # Repositorio en memoria
│
├── interfaces/
│   └── http/
│       ├── handlers/
│       │   └── product_handler.py # HTTP handlers
│       └── middleware/
│           └── logging_middleware.py # Middleware de logging
│
├── requirements.txt               # Dependencias
└── main.py                        # Punto de entrada (Flask API)
```

## 🚀 Ejecutar

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la API
python examples/clean_api_python/main.py

# API disponible en: http://localhost:5000
```

## 📝 Endpoints

```
POST   /api/products           - Crear producto
GET    /api/products           - Listar productos (con filtros)
GET    /api/products/<id>      - Obtener producto por ID
PUT    /api/products/<id>      - Actualizar producto
DELETE /api/products/<id>      - Eliminar producto
```

## 🔍 Ejemplo de Uso con Filtros

```bash
# Crear producto
curl -X POST http://localhost:5000/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop Dell XPS 15",
    "description": "High performance laptop",
    "price": 1500.00,
    "category": "Electronics",
    "stock": 50
  }'

# Listar con filtros (Specification Pattern)
curl "http://localhost:5000/api/products?category=Electronics&min_price=1000&max_price=2000&in_stock=true&page=1&page_size=10"
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
- Flask handlers con validación de entrada
- Middleware de logging con request/response tracking
- Response builders estandarizados
- Manejo de errores HTTP (13xxxxxx)

### ✅ Logging por Capa

Cada capa genera logs con contexto completo usando el framework Backbone Python.

### ✅ Errores por Código

```python
# Domain (11xxxxxx)
11001001 - Invalid product name
11001002 - Invalid product price
11001003 - Invalid stock quantity

# Application (10xxxxxx)
10001001 - Product creation failed
10001002 - Product not found
10001003 - Invalid query parameters

# Infrastructure (12xxxxxx)
12001001 - Database query failed
12001002 - Repository error

# Interface (13xxxxxx)
13001001 - Invalid JSON payload
13001002 - Invalid request parameters
```

### ✅ Filtros Dinámicos

```python
# Construir query con Specification Pattern
from backbone.domain.specifications import FilterSpecification

spec = FilterSpecification("category", "=", category)
spec = spec & FilterSpecification("price", ">=", min_price)
spec = spec & FilterSpecification("stock", ">", 0)
```

## 🎓 Conceptos Demostrados

1. **Clean Architecture** - Separación clara de capas
2. **Specification Pattern** - Queries dinámicas tipo-seguras
3. **Logging Estructurado** - Logging con contexto de capa/método/handler
4. **Error Handling** - Sistema de códigos de 8 dígitos
5. **Dependency Injection** - Inversión de dependencias
6. **Repository Pattern** - Abstracción de persistencia
7. **Use Case Pattern** - Lógica de aplicación encapsulada
8. **Response Builders** - Respuestas estandarizadas
