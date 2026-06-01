# Backbone-Go Framework

Implementación completa del framework Backbone en Go (Golang).

## 🚀 Instalación

```bash
go get github.com/freakjazz/backbone-go
```

## 📚 Documentación

Ver [README.md](./README.md) para documentación completa.

## 🧪 Ejecutar Tests

```bash
# Todos los tests
go test ./...

# Con cobertura
go test -cover ./...

# Tests específicos
go test ./domain/exceptions/...
go test ./infrastructure/messaging/...

# Verbose
go test -v ./...
```

## 🎯 Ejecutar Ejemplo

```bash
cd examples/basic
go run main.go
```

## 📦 Estructura

```
backbone-go/
├── domain/              # Capa de dominio
│   ├── exceptions/     # Excepciones (11xxxxxx)
│   ├── ports/         # Contratos
│   └── repositories/  # Interfaces de repositorios
│
├── application/        # Capa de aplicación
│   └── exceptions/    # Excepciones (10xxxxxx)
│
├── infrastructure/     # Capa de infraestructura
│   ├── config/        # Configuración
│   ├── events/        # Event store
│   ├── logging/       # Logging estructurado
│   └── messaging/     # Event bus adapters
│
├── interfaces/         # Capa de interfaces
│   └── responses/     # Response builders
│
└── examples/          # Ejemplos de uso
```

## 🔧 Configuración

Copia `config.example.yaml` a `config.yaml` y ajusta los valores:

```bash
cp config.example.yaml config.yaml
```

## 📝 Licencia

MIT License
