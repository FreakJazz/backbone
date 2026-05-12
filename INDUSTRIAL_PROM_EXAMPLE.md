# 🏭 Ejemplo Completo: Industrial Prom con Backbone

Guía paso a paso para integrar Backbone Framework en tu proyecto **industrial_prom**.

---

## 📋 Paso 1: Instalación

```powershell
# Ir al proyecto
cd C:\Users\Sistemas\Documents\programs\industrial_prom

# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Instalar Backbone
pip install git+https://github.com/FreakJazz/backbone.git
```

### Crear/Actualizar `requirements.txt`

```txt
# Framework
git+https://github.com/FreakJazz/backbone.git@v1.0.0

# API
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6

# Database
sqlalchemy>=2.0.0
alembic>=1.12.0
psycopg2-binary>=2.9.0  # PostgreSQL
# o pymysql>=1.1.0  # MySQL

# Utils
python-dotenv>=1.0.0
pydantic>=2.0.0
```

Instalar:
```powershell
pip install -r requirements.txt
```

---

## 📁 Paso 2: Estructura del Proyecto

```
industrial_prom/
├── venv/
├── .env
├── requirements.txt
├── main.py                      # Punto de entrada FastAPI
├── config.py                    # Configuración
│
├── domain/                      # ← Lógica de negocio (usa Backbone)
│   ├── __init__.py
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── machine.py          # Entidad Máquina
│   │   ├── maintenance.py      # Entidad Mantenimiento
│   │   └── work_order.py       # Entidad Orden de Trabajo
│   │
│   └── repositories/            # ← Interfaces (IRepository de Backbone)
│       ├── __init__.py
│       ├── machine_repository.py
│       └── maintenance_repository.py
│
├── application/                 # ← Casos de uso (usa excepciones de Backbone)
│   ├── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── machine_service.py
│   │   └── maintenance_service.py
│   │
│   └── use_cases/
│       ├── __init__.py
│       ├── start_machine.py
│       └── schedule_maintenance.py
│
├── infrastructure/              # ← Implementaciones (usa Backbone)
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py           # SQLAlchemy models
│   │   └── session.py          # Database session
│   │
│   ├── repositories/            # ← Implementación de repositorios
│   │   ├── __init__.py
│   │   ├── sqlalchemy_machine_repository.py
│   │   └── sqlalchemy_maintenance_repository.py
│   │
│   └── events/                  # ← Event handlers
│       ├── __init__.py
│       └── machine_events.py
│
└── interfaces/                  # ← API HTTP (usa Response Builders)
    ├── __init__.py
    └── http/
        ├── __init__.py
        ├── routes/
        │   ├── __init__.py
        │   ├── machines.py
        │   ├── maintenance.py
        │   └── health.py
        │
        └── dependencies.py      # FastAPI dependencies
```

---

## 🔧 Paso 3: Archivos de Configuración

### `.env`

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/industrial_prom
# o para MySQL: mysql+pymysql://user:password@localhost:3306/industrial_prom

# App
APP_NAME=Industrial Prom
APP_VERSION=1.0.0
DEBUG=True

# Logging
LOG_LEVEL=INFO
```

### `config.py`

```python
"""
Configuración de la aplicación usando Backbone
"""
from backbone.infrastructure.configuration import BaseConfig
from pydantic import Field

class Settings(BaseConfig):
    """Configuración de Industrial Prom"""
    
    # App
    app_name: str = Field(default="Industrial Prom", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Instancia global
settings = Settings()
```

---

## 🎯 Paso 4: Dominio (Entities)

### `domain/entities/machine.py`

```python
"""
Entidad de dominio: Máquina
"""
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

@dataclass
class Machine:
    """Representa una máquina en la planta"""
    
    id: Optional[int] = None
    name: str = ""
    code: str = ""  # Código único
    status: str = "stopped"  # stopped, running, maintenance, error
    capacity: int = 0
    location: str = ""
    last_maintenance: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def start(self) -> None:
        """Iniciar máquina - Lógica de dominio"""
        if self.status == "maintenance":
            from backbone import DomainException
            raise DomainException(
                code=11001001,
                message="No se puede iniciar máquina en mantenimiento",
                details={"machine_code": self.code, "status": self.status}
            )
        
        if self.status == "error":
            from backbone import DomainException
            raise DomainException(
                code=11001002,
                message="Máquina tiene errores, requiere revisión",
                details={"machine_code": self.code}
            )
        
        self.status = "running"
    
    def stop(self) -> None:
        """Detener máquina"""
        self.status = "stopped"
    
    def requires_maintenance(self) -> bool:
        """Verifica si requiere mantenimiento"""
        if not self.last_maintenance:
            return True
        
        # Mantenimiento cada 30 días
        days_since = (datetime.now() - self.last_maintenance).days
        return days_since > 30
    
    def to_dict(self) -> dict:
        """Convertir a diccionario"""
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "status": self.status,
            "capacity": self.capacity,
            "location": self.location,
            "last_maintenance": self.last_maintenance.isoformat() if self.last_maintenance else None,
            "requires_maintenance": self.requires_maintenance(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
```

### `domain/entities/maintenance.py`

```python
"""
Entidad de dominio: Mantenimiento
"""
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

@dataclass
class Maintenance:
    """Registro de mantenimiento"""
    
    id: Optional[int] = None
    machine_id: int = 0
    maintenance_type: str = "preventive"  # preventive, corrective, emergency
    description: str = ""
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    status: str = "scheduled"  # scheduled, in_progress, completed, cancelled
    technician: str = ""
    notes: str = ""
    cost: float = 0.0
    created_at: Optional[datetime] = None
    
    def complete(self, notes: str = "") -> None:
        """Completar mantenimiento"""
        if self.status == "completed":
            from backbone import DomainException
            raise DomainException(
                code=11002001,
                message="Mantenimiento ya completado",
                details={"maintenance_id": self.id}
            )
        
        self.status = "completed"
        self.completed_date = datetime.now()
        if notes:
            self.notes = notes
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "machine_id": self.machine_id,
            "maintenance_type": self.maintenance_type,
            "description": self.description,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "completed_date": self.completed_date.isoformat() if self.completed_date else None,
            "status": self.status,
            "technician": self.technician,
            "notes": self.notes,
            "cost": self.cost,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
```

---

## 💾 Paso 5: Repositorios

### `domain/repositories/machine_repository.py` (Interfaz)

```python
"""
Interfaz del repositorio de máquinas
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from backbone.domain.repositories import IRepository
from domain.entities.machine import Machine

class IMachineRepository(IRepository, ABC):
    """Interfaz para el repositorio de máquinas"""
    
    @abstractmethod
    def get_by_code(self, code: str) -> Optional[Machine]:
        """Obtener máquina por código"""
        pass
    
    @abstractmethod
    def get_by_status(self, status: str) -> List[Machine]:
        """Obtener máquinas por estado"""
        pass
    
    @abstractmethod
    def get_requiring_maintenance(self) -> List[Machine]:
        """Obtener máquinas que requieren mantenimiento"""
        pass
```

### `infrastructure/repositories/sqlalchemy_machine_repository.py` (Implementación)

```python
"""
Implementación SQLAlchemy del repositorio de máquinas
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from backbone import LoggerFactory
from domain.repositories.machine_repository import IMachineRepository
from domain.entities.machine import Machine
from infrastructure.database.models import MachineModel

logger = LoggerFactory.create_logger("machine-repository")

class SQLAlchemyMachineRepository(IMachineRepository):
    """Repositorio de máquinas usando SQLAlchemy"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def add(self, machine: Machine) -> Machine:
        """Agregar nueva máquina"""
        logger.info(f"Agregando máquina: {machine.code}")
        
        model = MachineModel(
            name=machine.name,
            code=machine.code,
            status=machine.status,
            capacity=machine.capacity,
            location=machine.location,
            last_maintenance=machine.last_maintenance
        )
        
        self.session.add(model)
        self.session.flush()  # Para obtener el ID
        
        machine.id = model.id
        machine.created_at = model.created_at
        machine.updated_at = model.updated_at
        
        logger.info(f"Máquina agregada con ID: {machine.id}")
        return machine
    
    def get_by_id(self, machine_id: int) -> Optional[Machine]:
        """Obtener máquina por ID"""
        logger.debug(f"Buscando máquina ID: {machine_id}")
        
        model = self.session.query(MachineModel).filter(
            MachineModel.id == machine_id
        ).first()
        
        if not model:
            logger.warning(f"Máquina no encontrada: {machine_id}")
            return None
        
        return self._to_entity(model)
    
    def get_by_code(self, code: str) -> Optional[Machine]:
        """Obtener máquina por código"""
        logger.debug(f"Buscando máquina código: {code}")
        
        model = self.session.query(MachineModel).filter(
            MachineModel.code == code
        ).first()
        
        return self._to_entity(model) if model else None
    
    def get_by_status(self, status: str) -> List[Machine]:
        """Obtener máquinas por estado"""
        logger.debug(f"Buscando máquinas con estado: {status}")
        
        models = self.session.query(MachineModel).filter(
            MachineModel.status == status
        ).all()
        
        return [self._to_entity(model) for model in models]
    
    def get_all(self) -> List[Machine]:
        """Obtener todas las máquinas"""
        logger.debug("Obteniendo todas las máquinas")
        
        models = self.session.query(MachineModel).all()
        return [self._to_entity(model) for model in models]
    
    def update(self, machine: Machine) -> Machine:
        """Actualizar máquina"""
        logger.info(f"Actualizando máquina ID: {machine.id}")
        
        model = self.session.query(MachineModel).filter(
            MachineModel.id == machine.id
        ).first()
        
        if not model:
            from backbone import DomainException
            raise DomainException(
                code=11001003,
                message="Máquina no encontrada para actualizar",
                details={"machine_id": machine.id}
            )
        
        model.name = machine.name
        model.status = machine.status
        model.capacity = machine.capacity
        model.location = machine.location
        model.last_maintenance = machine.last_maintenance
        
        self.session.flush()
        
        machine.updated_at = model.updated_at
        logger.info(f"Máquina actualizada: {machine.id}")
        
        return machine
    
    def delete(self, machine_id: int) -> bool:
        """Eliminar máquina"""
        logger.warning(f"Eliminando máquina ID: {machine_id}")
        
        result = self.session.query(MachineModel).filter(
            MachineModel.id == machine_id
        ).delete()
        
        return result > 0
    
    def get_requiring_maintenance(self) -> List[Machine]:
        """Obtener máquinas que requieren mantenimiento"""
        logger.debug("Buscando máquinas que requieren mantenimiento")
        
        machines = self.get_all()
        return [m for m in machines if m.requires_maintenance()]
    
    def _to_entity(self, model: MachineModel) -> Machine:
        """Convertir modelo SQLAlchemy a entidad"""
        return Machine(
            id=model.id,
            name=model.name,
            code=model.code,
            status=model.status,
            capacity=model.capacity,
            location=model.location,
            last_maintenance=model.last_maintenance,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
```

---

## 🎬 Paso 6: Casos de Uso

### `application/use_cases/start_machine.py`

```python
"""
Caso de uso: Iniciar Máquina
"""
from backbone import (
    LoggerFactory,
    DomainException,
    ApplicationException
)
from domain.repositories.machine_repository import IMachineRepository
from domain.entities.machine import Machine
from infrastructure.events.machine_events import MachineStartedEvent, event_bus

logger = LoggerFactory.create_logger("start-machine-usecase")

class StartMachineUseCase:
    """Caso de uso para iniciar una máquina"""
    
    def __init__(self, machine_repository: IMachineRepository):
        self.machine_repository = machine_repository
    
    def execute(self, machine_code: str, user_id: int) -> Machine:
        """
        Ejecutar caso de uso
        
        Args:
            machine_code: Código de la máquina
            user_id: ID del usuario que inicia
            
        Returns:
            Máquina actualizada
            
        Raises:
            DomainException: Si hay validaciones de dominio
            ApplicationException: Si hay errores de aplicación
        """
        logger.info(f"Iniciando máquina: {machine_code} por usuario: {user_id}")
        
        # 1. Buscar máquina
        machine = self.machine_repository.get_by_code(machine_code)
        
        if not machine:
            logger.error(f"Máquina no encontrada: {machine_code}")
            raise ApplicationException(
                code=12001001,
                message="Máquina no encontrada",
                details={"machine_code": machine_code}
            )
        
        # 2. Validar si requiere mantenimiento (warning, no error)
        if machine.requires_maintenance():
            logger.warning(f"Máquina {machine_code} requiere mantenimiento")
        
        # 3. Iniciar máquina (lógica de dominio)
        try:
            machine.start()
        except DomainException as e:
            logger.error(f"Error de dominio al iniciar máquina: {e}")
            raise
        
        # 4. Persistir cambios
        updated_machine = self.machine_repository.update(machine)
        
        # 5. Publicar evento
        event = MachineStartedEvent(
            machine_id=updated_machine.id,
            machine_code=updated_machine.code,
            user_id=user_id
        )
        event_bus.publish(event)
        
        logger.info(f"Máquina iniciada exitosamente: {machine_code}")
        
        return updated_machine
```

---

## 🌐 Paso 7: API HTTP (FastAPI)

### `interfaces/http/routes/machines.py`

```python
"""
Rutas HTTP para máquinas
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session

from backbone import (
    ProcessResponseBuilder,
    ErrorResponseBuilder,
    DomainException,
    ApplicationException,
    LoggerFactory,
    FilterSpecification
)

from interfaces.http.dependencies import get_db_session
from infrastructure.repositories.sqlalchemy_machine_repository import SQLAlchemyMachineRepository
from application.use_cases.start_machine import StartMachineUseCase
from domain.entities.machine import Machine

router = APIRouter(prefix="/api/machines", tags=["Machines"])
logger = LoggerFactory.create_logger("machines-api")

@router.get("/")
def list_machines(
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    location: Optional[str] = Query(None, description="Filtrar por ubicación"),
    requires_maintenance: Optional[bool] = Query(None, description="Solo máquinas que requieren mantenimiento"),
    db: Session = Depends(get_db_session)
):
    """Listar máquinas con filtros"""
    try:
        logger.info(f"Listando máquinas - status: {status}, location: {location}")
        
        repository = SQLAlchemyMachineRepository(db)
        
        # Aplicar filtros
        if requires_maintenance:
            machines = repository.get_requiring_maintenance()
        elif status:
            machines = repository.get_by_status(status)
        else:
            machines = repository.get_all()
        
        # Filtro adicional por ubicación
        if location:
            machines = [m for m in machines if m.location == location]
        
        # Convertir a dict
        machines_data = [m.to_dict() for m in machines]
        
        return ProcessResponseBuilder.success(
            message="Máquinas obtenidas exitosamente",
            data=machines_data,
            pagination={
                "total": len(machines_data),
                "page": 1,
                "per_page": len(machines_data)
            }
        )
        
    except Exception as e:
        logger.error(f"Error al listar máquinas: {e}")
        return ErrorResponseBuilder.error(
            message="Error al obtener máquinas",
            error=str(e)
        )

@router.get("/{machine_id}")
def get_machine(
    machine_id: int,
    db: Session = Depends(get_db_session)
):
    """Obtener detalles de una máquina"""
    try:
        logger.info(f"Obteniendo máquina ID: {machine_id}")
        
        repository = SQLAlchemyMachineRepository(db)
        machine = repository.get_by_id(machine_id)
        
        if not machine:
            return ErrorResponseBuilder.not_found(
                message="Máquina no encontrada",
                details={"machine_id": machine_id}
            )
        
        return ProcessResponseBuilder.success(
            message="Máquina encontrada",
            data=machine.to_dict()
        )
        
    except Exception as e:
        logger.error(f"Error al obtener máquina: {e}")
        return ErrorResponseBuilder.error(
            message="Error al obtener máquina",
            error=str(e)
        )

@router.post("/{machine_code}/start")
def start_machine(
    machine_code: str,
    user_id: int = Query(..., description="ID del usuario"),
    db: Session = Depends(get_db_session)
):
    """Iniciar una máquina"""
    try:
        logger.info(f"Iniciando máquina: {machine_code}")
        
        # Crear repositorio
        repository = SQLAlchemyMachineRepository(db)
        
        # Ejecutar caso de uso
        use_case = StartMachineUseCase(repository)
        machine = use_case.execute(machine_code, user_id)
        
        # Commit de la transacción
        db.commit()
        
        return ProcessResponseBuilder.success(
            message="Máquina iniciada exitosamente",
            data=machine.to_dict()
        )
        
    except DomainException as e:
        logger.error(f"Error de dominio: {e}")
        db.rollback()
        return ErrorResponseBuilder.from_exception(e)
    
    except ApplicationException as e:
        logger.error(f"Error de aplicación: {e}")
        db.rollback()
        return ErrorResponseBuilder.from_exception(e)
    
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        db.rollback()
        return ErrorResponseBuilder.error(
            message="Error al iniciar máquina",
            error=str(e)
        )

@router.post("/{machine_code}/stop")
def stop_machine(
    machine_code: str,
    db: Session = Depends(get_db_session)
):
    """Detener una máquina"""
    try:
        logger.info(f"Deteniendo máquina: {machine_code}")
        
        repository = SQLAlchemyMachineRepository(db)
        machine = repository.get_by_code(machine_code)
        
        if not machine:
            return ErrorResponseBuilder.not_found(
                message="Máquina no encontrada",
                details={"machine_code": machine_code}
            )
        
        machine.stop()
        repository.update(machine)
        db.commit()
        
        return ProcessResponseBuilder.success(
            message="Máquina detenida exitosamente",
            data=machine.to_dict()
        )
        
    except Exception as e:
        logger.error(f"Error al detener máquina: {e}")
        db.rollback()
        return ErrorResponseBuilder.error(
            message="Error al detener máquina",
            error=str(e)
        )

@router.post("/")
def create_machine(
    machine_data: dict,
    db: Session = Depends(get_db_session)
):
    """Crear nueva máquina"""
    try:
        logger.info(f"Creando máquina: {machine_data.get('code')}")
        
        # Crear entidad
        machine = Machine(
            name=machine_data.get("name"),
            code=machine_data.get("code"),
            capacity=machine_data.get("capacity", 0),
            location=machine_data.get("location", ""),
            status="stopped"
        )
        
        # Guardar
        repository = SQLAlchemyMachineRepository(db)
        created_machine = repository.add(machine)
        db.commit()
        
        return ProcessResponseBuilder.created(
            message="Máquina creada exitosamente",
            data=created_machine.to_dict()
        )
        
    except Exception as e:
        logger.error(f"Error al crear máquina: {e}")
        db.rollback()
        return ErrorResponseBuilder.error(
            message="Error al crear máquina",
            error=str(e)
        )
```

### `interfaces/http/routes/health.py`

```python
"""
Health check endpoint
"""
from fastapi import APIRouter
from backbone import ProcessResponseBuilder, LoggerFactory
from config import settings

router = APIRouter(tags=["Health"])
logger = LoggerFactory.create_logger("health")

@router.get("/health")
def health_check():
    """Health check endpoint"""
    logger.info("Health check solicitado")
    
    return ProcessResponseBuilder.status(
        message="Servicio funcionando correctamente",
        data={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "framework": "backbone",
            "status": "healthy"
        }
    )
```

---

## 🚀 Paso 8: Main Application

### `main.py`

```python
"""
Industrial Prom - FastAPI Application
Usando Backbone Framework
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backbone import LoggerFactory
from config import settings
from interfaces.http.routes import machines, health
from infrastructure.database.session import init_db

# Crear logger
logger = LoggerFactory.create_logger("industrial-prom")

# Crear aplicación
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Sistema de Mantenimiento Industrial con Backbone Framework"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(health.router)
app.include_router(machines.router)

@app.on_event("startup")
async def startup_event():
    """Evento de inicio"""
    logger.info(f"Iniciando {settings.app_name} v{settings.app_version}")
    logger.info("Inicializando base de datos...")
    init_db()
    logger.info("✅ Aplicación iniciada correctamente")

@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre"""
    logger.info("Cerrando aplicación...")

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Iniciando servidor...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
```

---

## 🗄️ Paso 9: Database Setup

### `infrastructure/database/session.py`

```python
"""
Configuración de sesión de base de datos
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True
)

# Session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base para modelos
Base = declarative_base()

def init_db():
    """Inicializar base de datos (crear tablas)"""
    from infrastructure.database.models import MachineModel, MaintenanceModel
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency para obtener sesión de BD"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### `infrastructure/database/models.py`

```python
"""
Modelos SQLAlchemy
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from infrastructure.database.session import Base

class MachineModel(Base):
    """Modelo de máquina"""
    __tablename__ = "machines"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(50), default="stopped", index=True)
    capacity = Column(Integer, default=0)
    location = Column(String(200))
    last_maintenance = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class MaintenanceModel(Base):
    """Modelo de mantenimiento"""
    __tablename__ = "maintenances"
    
    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False, index=True)
    maintenance_type = Column(String(50), default="preventive")
    description = Column(String(500))
    scheduled_date = Column(DateTime)
    completed_date = Column(DateTime, nullable=True)
    status = Column(String(50), default="scheduled", index=True)
    technician = Column(String(200))
    notes = Column(String(1000))
    cost = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default=func.now())
```

### `interfaces/http/dependencies.py`

```python
"""
Dependencias de FastAPI
"""
from infrastructure.database.session import get_db

# Re-export
get_db_session = get_db
```

---

## 📡 Paso 10: Eventos (Opcional pero recomendado)

### `infrastructure/events/machine_events.py`

```python
"""
Eventos de dominio para máquinas
"""
from datetime import datetime
from backbone import DomainEvent, EventBus, LoggerFactory

logger = LoggerFactory.create_logger("machine-events")

# Event Bus global
event_bus = EventBus()

class MachineStartedEvent(DomainEvent):
    """Evento cuando una máquina se inicia"""
    
    def __init__(self, machine_id: int, machine_code: str, user_id: int):
        super().__init__(
            event_type="machine.started",
            data={
                "machine_id": machine_id,
                "machine_code": machine_code,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
        )

# Handlers
def on_machine_started(event: MachineStartedEvent):
    """Handler cuando una máquina se inicia"""
    logger.info(f"🚀 Máquina iniciada: {event.data['machine_code']} por usuario {event.data['user_id']}")
    # Aquí puedes:
    # - Enviar notificaciones
    # - Actualizar dashboard en tiempo real
    # - Registrar en auditoría
    # - Activar otros procesos

# Suscribir handlers
event_bus.subscribe("machine.started", on_machine_started)
```

---

## 🏃 Paso 11: Ejecutar la Aplicación

```powershell
# Activar entorno
.\venv\Scripts\Activate.ps1

# Ejecutar
python main.py

# O con uvicorn directamente
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Abrir: http://localhost:8000/docs

---

## 🧪 Paso 12: Probar los Endpoints

### Health Check

```powershell
curl http://localhost:8000/health
```

### Crear Máquina

```powershell
curl -X POST http://localhost:8000/api/machines/ `
  -H "Content-Type: application/json" `
  -d '{
    "name": "Torno CNC 1",
    "code": "CNC-001",
    "capacity": 1000,
    "location": "Planta A - Sector 1"
  }'
```

### Listar Máquinas

```powershell
curl http://localhost:8000/api/machines/
```

### Iniciar Máquina

```powershell
curl -X POST "http://localhost:8000/api/machines/CNC-001/start?user_id=1"
```

### Obtener Máquina

```powershell
curl http://localhost:8000/api/machines/1
```

---

## 📊 Resumen de Integración con Backbone

| Componente | Uso de Backbone |
|------------|-----------------|
| **Entities** | Lógica de dominio pura, usa `DomainException` |
| **Repositories** | Implementa `IRepository` de Backbone |
| **Use Cases** | Usa `LoggerFactory`, excepciones, eventos |
| **API Routes** | Usa `ProcessResponseBuilder`, `ErrorResponseBuilder` |
| **Events** | Usa `DomainEvent`, `EventBus` |
| **Config** | Extiende `BaseConfig` de Backbone |

---

## ✅ Ventajas que obtienes con Backbone:

1. ✅ **Logging consistente** en toda la aplicación
2. ✅ **Manejo de errores estandarizado** con códigos
3. ✅ **Respuestas HTTP uniformes** con Response Builders
4. ✅ **Arquitectura limpia** con separación de capas
5. ✅ **Event-driven**: desacopla lógica con eventos
6. ✅ **Type hints completos**: mejor IDE support
7. ✅ **Testing más fácil**: interfaces claramente definidas

---

¿Necesitas ayuda con alguna parte específica? 🚀
