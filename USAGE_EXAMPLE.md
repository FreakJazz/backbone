# Ejemplo de uso de Backbone en proyecto industrial_prom

## Estructura del proyecto industrial_prom

```
industrial_prom/
├── requirements.txt
├── pyproject.toml
├── main.py
├── config/
│   └── settings.py
├── src/
│   ├── __init__.py
│   ├── domain/
│   │   ├── entities/
│   │   └── services/
│   ├── application/
│   │   └── use_cases/
│   └── infrastructure/
│       └── repositories/
└── tests/
```

## requirements.txt

```txt
# GitHub Packages - Backbone Framework
backbone>=1.0.0

# API Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0

# Database
sqlalchemy>=2.0.0
alembic>=1.12.0
psycopg2-binary>=2.9.0

# Validation
pydantic>=2.0.0
pydantic-settings>=2.0.0

# Monitoring
prometheus-client>=0.17.0
```

## main.py

```python
"""
Aplicación Industrial usando Backbone Framework
"""
import asyncio
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

# Importar componentes de Backbone
from backbone import (
    LoggerFactory,
    ProcessResponseBuilder,
    ErrorResponseBuilder,
    DomainException,
    ApplicationException
)
from backbone.infrastructure.messaging import EventBusAdapterFactory

# Configurar logging estructurado
logger = LoggerFactory.create_logger("industrial-prom")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle de la aplicación"""
    logger.info("🚀 Starting Industrial Prom Application")
    
    # Inicializar event bus
    event_bus = EventBusAdapterFactory.create_in_memory_bus(logger)
    app.state.event_bus = event_bus
    
    yield
    
    logger.info("🛑 Shutting down Industrial Prom Application")

# Crear aplicación FastAPI
app = FastAPI(
    title="Industrial Prom",
    description="Sistema Industrial con Arquitectura Limpia usando Backbone",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return ProcessResponseBuilder.status(
            message="Industrial Prom is running",
            data={
                "service": "industrial-prom",
                "status": "healthy",
                "backbone_version": "1.0.0"
            }
        )
    except Exception as e:
        logger.error("Health check failed", extra_data={"error": str(e)})
        return ErrorResponseBuilder.internal_server_error(
            message="Health check failed"
        )

@app.get("/api/v1/machines")
async def list_machines():
    """Listar máquinas industriales"""
    try:
        # Simular datos de máquinas
        machines = [
            {
                "id": 1,
                "name": "Prensa Hidráulica 001",
                "status": "active",
                "temperature": 75.5,
                "pressure": 120.0
            },
            {
                "id": 2,
                "name": "Torno CNC 002",
                "status": "maintenance",
                "temperature": 45.2,
                "pressure": 0.0
            }
        ]
        
        logger.info("Machines listed successfully", extra_data={"count": len(machines)})
        
        return ProcessResponseBuilder.found(
            message=f"Found {len(machines)} machines",
            data={"machines": machines}
        )
        
    except Exception as e:
        logger.error("Failed to list machines", extra_data={"error": str(e)})
        return ErrorResponseBuilder.internal_server_error()

@app.post("/api/v1/machines/{machine_id}/start")
async def start_machine(machine_id: int):
    """Iniciar una máquina"""
    try:
        # Simular validación de dominio
        if machine_id <= 0:
            raise DomainException(
                code=11002001,
                message="Invalid machine ID",
                details={"machine_id": machine_id}
            )
        
        # Simular lógica de negocio
        if machine_id > 100:
            raise ApplicationException(
                code=10002001,
                message="Machine not found",
                details={"machine_id": machine_id}
            )
        
        # Simular inicio de máquina
        result = {
            "machine_id": machine_id,
            "status": "starting",
            "timestamp": "2026-02-24T00:00:00Z"
        }
        
        logger.info(
            "Machine started successfully", 
            extra_data={"machine_id": machine_id}
        )
        
        return ProcessResponseBuilder.success(
            message="Machine started successfully",
            data=result
        )
        
    except DomainException as e:
        logger.error(f"Domain error starting machine {machine_id}", extra_data={"error": str(e)})
        return ErrorResponseBuilder.from_exception(e)
    
    except ApplicationException as e:
        logger.error(f"Application error starting machine {machine_id}", extra_data={"error": str(e)})
        return ErrorResponseBuilder.from_exception(e)
    
    except Exception as e:
        logger.error(f"Unexpected error starting machine {machine_id}", extra_data={"error": str(e)})
        return ErrorResponseBuilder.internal_server_error()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None  # Usar logging de Backbone
    )
```

## Comandos de instalación

```bash
# 1. Clonar o crear el proyecto industrial_prom
mkdir industrial_prom
cd industrial_prom

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
# o
venv\Scripts\activate     # Windows

# 3. Instalar dependencias desde GitHub Packages
pip install --index-url https://pypi.pkg.github.com/FreakJazz/simple/ -r requirements.txt

# 4. Ejecutar la aplicación
python main.py
```

## Dockerfile para producción

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias Python con acceso a GitHub Packages
ARG GITHUB_TOKEN
ENV GITHUB_TOKEN=${GITHUB_TOKEN}

RUN pip install --no-cache-dir \
    --index-url https://${GITHUB_TOKEN}@pypi.pkg.github.com/FreakJazz/simple/ \
    -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Exponer puerto
EXPOSE 8000

# Comando de inicio
CMD ["python", "main.py"]
```

## docker-compose.yml

```yaml
version: '3.8'

services:
  industrial-prom:
    build:
      context: .
      args:
        GITHUB_TOKEN: ${GITHUB_TOKEN}
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=info
    volumes:
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: industrial_prom
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

## GitHub Actions para industrial_prom

```yaml
# .github/workflows/ci.yml
name: CI/CD Industrial Prom

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install --index-url https://${{ secrets.GITHUB_TOKEN }}@pypi.pkg.github.com/FreakJazz/simple/ -r requirements.txt
          pip install pytest pytest-asyncio
        
      - name: Run tests
        run: pytest tests/ -v
      
      - name: Build Docker image
        run: |
          docker build --build-arg GITHUB_TOKEN=${{ secrets.GITHUB_TOKEN }} -t industrial-prom .

  deploy:
    if: github.ref == 'refs/heads/main'
    needs: test
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to production
        run: |
          echo "Deploying to production environment"
          # Aquí irían los comandos de deployment
```

## Tests de ejemplo

```python
# tests/test_main.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert "backbone_version" in data["data"]

def test_list_machines():
    """Test machines listing"""
    response = client.get("/api/v1/machines")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert "machines" in data["data"]
    assert len(data["data"]["machines"]) == 2

def test_start_machine():
    """Test machine start"""
    response = client.post("/api/v1/machines/1/start")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["machine_id"] == 1

def test_start_invalid_machine():
    """Test invalid machine ID"""
    response = client.post("/api/v1/machines/-1/start")
    assert response.status_code == 400  # Bad Request from DomainException
    
    data = response.json()
    assert data["status"] == "error"
    assert data["error_details"]["error_code"] == 11002001

def test_start_nonexistent_machine():
    """Test nonexistent machine"""
    response = client.post("/api/v1/machines/999/start")
    assert response.status_code == 404  # Not Found from ApplicationException
    
    data = response.json()
    assert data["status"] == "error"
    assert data["error_details"]["error_code"] == 10002001
```

## Variables de entorno

```bash
# .env
ENVIRONMENT=development
LOG_LEVEL=debug
DATABASE_URL=postgresql://app_user:secure_password@localhost:5432/industrial_prom
REDIS_URL=redis://localhost:6379/0
GITHUB_TOKEN=your_github_token_here
```

## Verificación de instalación

```python
# verify_installation.py
"""
Script para verificar que Backbone está correctamente instalado
"""

def verify_backbone_installation():
    try:
        import backbone
        print("✅ Backbone imported successfully")
        
        # Test core components
        from backbone import (
            DomainException,
            ApplicationException,
            LoggerFactory,
            ProcessResponseBuilder,
            ErrorResponseBuilder
        )
        print("✅ Core components available")
        
        # Test logger
        logger = LoggerFactory.create_logger("test-service")
        logger.info("Test log message")
        print("✅ Logger working")
        
        # Test response builders
        response = ProcessResponseBuilder.success("Test successful", {"test": True})
        assert response["status"] == "success"
        print("✅ Response builders working")
        
        # Test exceptions
        try:
            raise DomainException(code=11001001, message="Test domain exception")
        except DomainException as e:
            assert e.code == 11001001
            print("✅ Exception system working")
        
        print("\n🎉 All Backbone components verified successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure to install from GitHub Packages:")
        print("   pip install --index-url https://pypi.pkg.github.com/FreakJazz/simple/ backbone")
        return False
    
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    verify_backbone_installation()
```