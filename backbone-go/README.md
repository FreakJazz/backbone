# 🎯 Backbone Framework - Go

![Go Version](https://img.shields.io/badge/go-1.21%2B-blue)
![License](https://img.shields.io/badge/license-MIT-blue)
![Status](https://img.shields.io/badge/status-production--ready-green)

> **Clean Architecture Framework with Event-Driven Microservices for Go**

Port completo del framework Backbone de Python a Go, manteniendo todos los principios de arquitectura limpia y funcionalidades event-driven.

## 📦 Instalación

```bash
go get github.com/freakjazz/backbone-go
```

## 🚀 Quick Start

```go
package main

import (
    "github.com/freakjazz/backbone-go/domain/exceptions"
    "github.com/freakjazz/backbone-go/infrastructure/logging"
    "github.com/freakjazz/backbone-go/interfaces/responses"
)

func main() {
    // Crear logger
    logger := logging.NewLogger("my-service")
    
    // Usar response builders
    response := responses.ProcessResponseBuilder.Success(
        "Operation completed",
        map[string]interface{}{"id": "123"},
        201,
    )
    
    logger.Info("Response created", map[string]interface{}{
        "response": response,
    })
}
```

## 🏛️ Arquitectura

```
backbone-go/
├── domain/              # Capa de Dominio (Lógica de negocio)
│   ├── exceptions/     # Excepciones de dominio (11xxxxxx)
│   ├── ports/         # Contratos/Interfaces
│   ├── repositories/  # Interfaces de repositorios
│   └── specifications/ # Patrón Specification
│
├── application/        # Capa de Aplicación (Casos de uso)
│   ├── exceptions/    # Excepciones de aplicación (10xxxxxx)
│   └── handlers/      # Event handlers
│
├── infrastructure/     # Capa de Infraestructura (Detalles técnicos)
│   ├── config/        # Configuración
│   ├── logging/       # Sistema de logging estructurado
│   ├── messaging/     # Adaptadores de eventos (Kafka, RabbitMQ, Redis)
│   ├── persistence/   # Repositorios concretos
│   └── events/        # Event store
│
└── interfaces/         # Capa de Interfaces (Presentación)
    ├── exceptions/    # Excepciones de interfaces (13xxxxxx)
    └── responses/     # Response builders
```

## ✨ Características Principales

### 🔢 Sistema de Excepciones de 8 Dígitos

```go
import "github.com/freakjazz/backbone-go/domain/exceptions"

// Excepción de dominio (11xxxxxx)
err := exceptions.NewDomainException(
    11001001,
    "User age must be between 18 and 120",
    map[string]interface{}{"age": 15},
)

// Excepción de aplicación (10xxxxxx)
err := exceptions.NewApplicationException(
    10001001,
    "Failed to create user",
    nil,
)
```

### 🔄 Event-Driven Architecture

```go
import (
    "github.com/freakjazz/backbone-go/domain/ports"
    "github.com/freakjazz/backbone-go/infrastructure/messaging"
)

// Crear evento
event := ports.NewBaseEvent(
    "UserCreated",
    "industrial-prom",
    map[string]interface{}{"user_id": 123},
    "users-service",
    "create-user",
)

// Publicar con Kafka
kafkaBus := messaging.NewKafkaEventBus("localhost:9092", logger)
err := kafkaBus.Publish(context.Background(), event)

// Suscribirse
err = kafkaBus.Subscribe(context.Background(), "UserCreated", func(event *ports.BaseEvent) error {
    log.Printf("User created: %v", event.Data["user_id"])
    return nil
})
```

### 📊 Logging Estructurado

```go
import "github.com/freakjazz/backbone-go/infrastructure/logging"

logger := logging.NewLogger("my-service")

logger.Info("User created", map[string]interface{}{
    "user_id": 123,
    "email": "user@example.com",
})

logger.Error("Failed to create user", map[string]interface{}{
    "error": err.Error(),
    "user_id": 123,
})
```

### 🔧 Response Builders

```go
import "github.com/freakjazz/backbone-go/interfaces/responses"

// Respuesta exitosa
response := responses.ProcessResponseBuilder.Success(
    "User created successfully",
    map[string]interface{}{"id": "uuid-123"},
    201,
)

// Respuesta de error
response := responses.ErrorResponseBuilder.FromException(err)

// Query response
response := responses.QueryResponseBuilder.Success(
    "Users retrieved",
    users,
    page,
    pageSize,
    totalRecords,
)
```

### 📋 Repository Pattern

```go
import "github.com/freakjazz/backbone-go/domain/repositories"

type UserRepository interface {
    repositories.IRepository
    FindByEmail(ctx context.Context, email string) (*User, error)
}

// Implementación
type userRepositoryImpl struct {
    db *sql.DB
}

func (r *userRepositoryImpl) Add(ctx context.Context, entity interface{}) error {
    user := entity.(*User)
    // Implementación...
    return nil
}
```

## 📖 Documentación

- [Installation Guide](./docs/INSTALLATION.md)
- [Architecture Guide](./docs/ARCHITECTURE.md)
- [Event System Guide](./docs/EVENTS.md)
- **[🔍 Query Patterns & Enhanced Logging](./docs/QUERY_PATTERNS.md)** ⭐ NUEVO
- [API Reference](./docs/API.md)
- [Examples](./examples/)

## 🧪 Testing

```bash
# Ejecutar todos los tests
go test ./...

# Con cobertura
go test -cover ./...

# Tests específicos
go test ./domain/exceptions/...
```

## 📦 Uso en Proyectos

```go
import (
    backbone "github.com/freakjazz/backbone-go"
    "github.com/freakjazz/backbone-go/domain/exceptions"
    "github.com/freakjazz/backbone-go/infrastructure/logging"
)

func main() {
    // Configurar logger
    logger := logging.NewLogger("industrial-prom")
    
    // Tu aplicación...
}
```

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para más detalles

## 🔗 Enlaces

- **Versión Python**: [backbone (Python)](../README.md)
- **GitHub**: https://github.com/freakjazz/backbone-go
- **Documentación**: https://backbone-go.readthedocs.io/
