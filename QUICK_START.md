# 🚀 Inicio Rápido: Usar Backbone en Industrial Prom

## ⚡ 3 Pasos para Empezar

### 1️⃣ Instalar Backbone

```powershell
cd C:\Users\Sistemas\Documents\programs\industrial_prom
.\venv\Scripts\Activate.ps1
pip install git+https://github.com/FreakJazz/backbone.git
```

### 2️⃣ Crear Estructura (Opcional - Automático)

```powershell
# Desde el directorio de Backbone
cd C:\Users\Sistemas\Documents\programs\backbone
python create_industrial_prom_structure.py
# Cuando pida la ruta, poner: C:\Users\Sistemas\Documents\programs\industrial_prom
```

### 3️⃣ Usar en tu Código

```python
# main.py
from fastapi import FastAPI
from backbone import (
    LoggerFactory,
    ProcessResponseBuilder,
    DomainException
)

logger = LoggerFactory.create_logger("industrial-prom")
app = FastAPI(title="Industrial Prom")

@app.get("/health")
def health():
    logger.info("Health check")
    return ProcessResponseBuilder.status(
        message="OK",
        data={"framework": "backbone"}
    )

@app.post("/machines/{code}/start")
def start_machine(code: str):
    try:
        logger.info(f"Starting machine: {code}")
        # Tu lógica aquí
        return ProcessResponseBuilder.success(
            message="Machine started",
            data={"code": code, "status": "running"}
        )
    except DomainException as e:
        return ErrorResponseBuilder.from_exception(e)
```

---

## 📚 Componentes Principales

```python
from backbone import (
    # Excepciones
    DomainException,        # Para errores de dominio/negocio
    ApplicationException,   # Para errores de aplicación
    
    # Logging
    LoggerFactory,          # Crear loggers consistentes
    
    # Response Builders (APIs)
    ProcessResponseBuilder, # Respuestas exitosas
    ErrorResponseBuilder,   # Respuestas de error
    
    # Repositorios
    IRepository,            # Interfaz para repositorios
    IUnitOfWork,           # Unit of Work pattern
    
    # Especificaciones (filtros/queries)
    FilterSpecification,    # Filtros dinámicos
    SortSpecification,      # Ordenamiento
    
    # Eventos
    DomainEvent,           # Eventos de dominio
    EventBus,              # Bus de eventos
)
```

---

## 🎯 Casos de Uso Comunes

### 1. Endpoint con manejo de errores

```python
from backbone import ProcessResponseBuilder, ErrorResponseBuilder, DomainException

@app.post("/machines/{machine_id}/start")
def start_machine(machine_id: int):
    try:
        # Validación
        if machine_id <= 0:
            raise DomainException(
                code=11001001,
                message="Invalid machine ID"
            )
        
        # Lógica
        # ...
        
        return ProcessResponseBuilder.success(
            message="Machine started",
            data={"id": machine_id}
        )
    except DomainException as e:
        return ErrorResponseBuilder.from_exception(e)
```

### 2. Repositorio

```python
from backbone import IRepository
from sqlalchemy.orm import Session

class MachineRepository(IRepository):
    def __init__(self, session: Session):
        self.session = session
    
    def add(self, machine):
        self.session.add(machine)
        return machine
    
    def get_by_id(self, id):
        return self.session.query(Machine).get(id)
```

### 3. Logging

```python
from backbone import LoggerFactory

logger = LoggerFactory.create_logger("machines")

def process_machine(machine_id):
    logger.info(f"Processing machine: {machine_id}")
    logger.debug(f"Details: {machine_id}")
    logger.error(f"Error processing: {machine_id}")
```

### 4. Eventos

```python
from backbone import DomainEvent, EventBus

# Crear evento
class MachineStarted(DomainEvent):
    def __init__(self, machine_id):
        super().__init__(
            event_type="machine.started",
            data={"machine_id": machine_id}
        )

# Handler
def on_machine_started(event):
    print(f"Machine {event.data['machine_id']} started")

# Configurar
event_bus = EventBus()
event_bus.subscribe("machine.started", on_machine_started)

# Disparar
event = MachineStarted(123)
event_bus.publish(event)
```

---

## 📖 Documentación Completa

- **[INDUSTRIAL_PROM_EXAMPLE.md](./INDUSTRIAL_PROM_EXAMPLE.md)** - Ejemplo completo paso a paso
- **[GITHUB_INSTALLATION.md](./GITHUB_INSTALLATION.md)** - Instalación desde GitHub
- **[PACKAGE_GUIDE.md](./PACKAGE_GUIDE.md)** - Guía completa del paquete

---

## ⚙️ Requirements.txt

```txt
# Framework
git+https://github.com/FreakJazz/backbone.git@v1.0.0

# API
fastapi>=0.104.0
uvicorn[standard]>=0.24.0

# Database
sqlalchemy>=2.0.0

# Utils
python-dotenv>=1.0.0
```

---

## 🏗️ Estructura Recomendada

```
industrial_prom/
├── main.py                 # FastAPI app
├── config.py               # Settings con BaseConfig
├── requirements.txt        # Incluye backbone
│
├── domain/                 # Lógica de negocio
│   ├── entities/          # Machine, Maintenance, etc.
│   └── repositories/      # Interfaces (IRepository)
│
├── application/            # Casos de uso
│   └── use_cases/         # StartMachine, etc.
│
├── infrastructure/         # Implementaciones
│   ├── database/          # SQLAlchemy models, session
│   └── repositories/      # Implementaciones concretas
│
└── interfaces/             # API HTTP
    └── http/
        └── routes/        # Endpoints (usa Response Builders)
```

---

## ✅ Checklist

- [ ] Instalar Backbone: `pip install git+https://github.com/FreakJazz/backbone.git`
- [ ] Agregar a `requirements.txt`
- [ ] Crear estructura de proyecto (o usar script)
- [ ] Importar componentes necesarios
- [ ] Implementar logging con `LoggerFactory`
- [ ] Usar `ProcessResponseBuilder` en APIs
- [ ] Implementar repositorios con `IRepository`
- [ ] Manejar excepciones con `DomainException`

---

## 🚀 Ejecutar

```powershell
python main.py
# O
uvicorn main:app --reload

# Ver docs en:
# http://localhost:8000/docs
```

---

**¡Listo para usar Backbone! 🎉**

¿Necesitas ayuda? Consulta los archivos de documentación completos.
