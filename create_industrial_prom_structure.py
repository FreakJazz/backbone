"""
Script para generar estructura inicial de Industrial Prom con Backbone
Ejecutar: python create_industrial_prom_structure.py
"""
import os
from pathlib import Path

# Estructura del proyecto
PROJECT_STRUCTURE = {
    "domain": {
        "__init__.py": "",
        "entities": {
            "__init__.py": "",
            "machine.py": "# Entidades de máquinas",
            "maintenance.py": "# Entidades de mantenimiento",
        },
        "repositories": {
            "__init__.py": "",
            "machine_repository.py": "# Interfaz IMachineRepository",
            "maintenance_repository.py": "# Interfaz IMaintenanceRepository",
        }
    },
    "application": {
        "__init__.py": "",
        "services": {
            "__init__.py": "",
            "machine_service.py": "# Servicios de máquinas",
        },
        "use_cases": {
            "__init__.py": "",
            "start_machine.py": "# Caso de uso: iniciar máquina",
            "schedule_maintenance.py": "# Caso de uso: programar mantenimiento",
        }
    },
    "infrastructure": {
        "__init__.py": "",
        "database": {
            "__init__.py": "",
            "models.py": "# Modelos SQLAlchemy",
            "session.py": "# Configuración de sesión DB",
        },
        "repositories": {
            "__init__.py": "",
            "sqlalchemy_machine_repository.py": "# Implementación del repositorio",
        },
        "events": {
            "__init__.py": "",
            "machine_events.py": "# Eventos de dominio",
        }
    },
    "interfaces": {
        "__init__.py": "",
        "http": {
            "__init__.py": "",
            "routes": {
                "__init__.py": "",
                "machines.py": "# Rutas de máquinas",
                "maintenance.py": "# Rutas de mantenimiento",
                "health.py": "# Health check",
            },
            "dependencies.py": "# Dependencias de FastAPI",
        }
    }
}

# Contenido de archivos principales
FILES_CONTENT = {
    "main.py": '''"""
Industrial Prom - FastAPI Application
Usando Backbone Framework
"""
from fastapi import FastAPI
from backbone import LoggerFactory
from config import settings

logger = LoggerFactory.create_logger("industrial-prom")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Sistema de Mantenimiento Industrial"
)

@app.get("/")
def root():
    return {"message": "Industrial Prom API", "version": settings.app_version}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
''',
    
    "config.py": '''"""
Configuración de la aplicación
"""
from backbone.infrastructure.configuration import BaseConfig
from pydantic import Field

class Settings(BaseConfig):
    """Configuración de Industrial Prom"""
    
    app_name: str = Field(default="Industrial Prom", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=True, env="DEBUG")
    database_url: str = Field(default="sqlite:///./industrial_prom.db", env="DATABASE_URL")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
''',
    
    ".env": '''# Database
DATABASE_URL=sqlite:///./industrial_prom.db

# App
APP_NAME=Industrial Prom
APP_VERSION=1.0.0
DEBUG=True

# Logging
LOG_LEVEL=INFO
''',
    
    "requirements.txt": '''# Backbone Framework
git+https://github.com/FreakJazz/backbone.git@v1.0.0

# API
fastapi>=0.104.0
uvicorn[standard]>=0.24.0

# Database
sqlalchemy>=2.0.0

# Utils
python-dotenv>=1.0.0
pydantic>=2.0.0
''',
    
    ".gitignore": '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/
env/
ENV/

# Database
*.db
*.sqlite
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo

# Env
.env
.env.local

# Distribution
dist/
build/
*.egg-info/
''',
    
    "README.md": '''# 🏭 Industrial Prom

Sistema de Mantenimiento Industrial usando Backbone Framework.

## 🚀 Instalación

```powershell
# Crear entorno virtual
python -m venv venv
.\\venv\\Scripts\\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
```

## 🏃 Ejecutar

```powershell
python main.py
```

Abrir en: http://localhost:8000

## 📚 Documentación

- API Docs: http://localhost:8000/docs
- Ver `INDUSTRIAL_PROM_EXAMPLE.md` en el repo de Backbone para ejemplos completos

## 🏗️ Estructura

```
industrial_prom/
├── domain/           # Lógica de negocio
├── application/      # Casos de uso
├── infrastructure/   # Implementaciones
└── interfaces/       # API HTTP
```
'''
}

def create_directory_structure(base_path: Path, structure: dict):
    """Crea la estructura de directorios y archivos"""
    for name, content in structure.items():
        path = base_path / name
        
        if isinstance(content, dict):
            # Es un directorio
            path.mkdir(exist_ok=True)
            print(f"📁 Creado: {path}")
            create_directory_structure(path, content)
        else:
            # Es un archivo
            if not path.exists():
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"📄 Creado: {path}")
            else:
                print(f"⏭️  Existe: {path}")

def create_main_files(base_path: Path, files: dict):
    """Crea archivos principales en la raíz"""
    for filename, content in files.items():
        path = base_path / filename
        if not path.exists():
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"📄 Creado: {path}")
        else:
            print(f"⏭️  Existe: {path}")

def main():
    """Función principal"""
    print("=" * 70)
    print("🏭 CREANDO ESTRUCTURA DE INDUSTRIAL PROM")
    print("=" * 70)
    print()
    
    # Obtener ruta del proyecto
    project_path = input("Ruta del proyecto (Enter para actual): ").strip()
    
    if not project_path:
        project_path = Path.cwd()
    else:
        project_path = Path(project_path)
    
    if not project_path.exists():
        print(f"❌ Ruta no existe: {project_path}")
        return
    
    print(f"\n📍 Proyecto en: {project_path}\n")
    
    # Confirmar
    confirm = input("¿Continuar? (s/n): ").strip().lower()
    if confirm != 's':
        print("❌ Cancelado")
        return
    
    print("\n🚀 Creando estructura...\n")
    
    # Crear archivos raíz
    print("📋 Creando archivos principales...")
    create_main_files(project_path, FILES_CONTENT)
    
    print("\n📂 Creando estructura de directorios...")
    create_directory_structure(project_path, PROJECT_STRUCTURE)
    
    print("\n" + "=" * 70)
    print("✅ ¡ESTRUCTURA CREADA EXITOSAMENTE!")
    print("=" * 70)
    print(f"""
📋 PRÓXIMOS PASOS:

1. Activar entorno virtual:
   .\\venv\\Scripts\\Activate.ps1

2. Instalar Backbone y dependencias:
   pip install -r requirements.txt

3. Ver el archivo completo de ejemplo:
   - Consulta: INDUSTRIAL_PROM_EXAMPLE.md en el repo de Backbone
   - Tiene código completo listo para copiar

4. Ejecutar aplicación:
   python main.py

5. Abrir en navegador:
   http://localhost:8000/docs

📖 DOCUMENTACIÓN:
   - Ejemplo completo: backbone/INDUSTRIAL_PROM_EXAMPLE.md
   - GitHub install: backbone/GITHUB_INSTALLATION.md
   - Package guide: backbone/PACKAGE_GUIDE.md

🎉 ¡Tu proyecto está listo para usar Backbone!
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelado por usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
