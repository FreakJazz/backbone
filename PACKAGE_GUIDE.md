# 📦 Guía Completa: Backbone como Paquete Pip

## 🎯 Objetivo
Convertir Backbone en un paquete pip instalable que puedas usar en cualquier proyecto Python.

---

## 🏗️ Estructura del Paquete

Tu proyecto ya tiene la estructura correcta:

```
backbone/
├── backbone/              # Paquete principal
│   ├── __init__.py       # Exporta componentes públicos
│   ├── py.typed          # Soporte para type hints
│   ├── domain/           # Capa de dominio
│   ├── application/      # Capa de aplicación
│   ├── infrastructure/   # Capa de infraestructura
│   └── interfaces/       # Capa de interfaces
├── pyproject.toml        # Configuración moderna del paquete
├── setup.py              # Configuración legacy (compatibilidad)
├── MANIFEST.in           # Archivos adicionales a incluir
├── README.md             # Documentación principal
├── LICENSE               # Licencia MIT
├── CHANGELOG.md          # Historial de cambios
└── requirements.txt      # Dependencias (si las hay)
```

---

## 📝 Archivos Clave Creados

### ✅ `pyproject.toml`
Configuración moderna del paquete con:
- Metadata del proyecto
- Dependencias
- Build system
- Herramientas de desarrollo

### ✅ `MANIFEST.in`
Define qué archivos incluir en la distribución

### ✅ `backbone/py.typed`
Marca el paquete como compatible con type hints

### ✅ `CHANGELOG.md`
Historial de versiones y cambios

---

## 🔨 Paso 1: Construir el Paquete

### Instalar herramientas de construcción

```powershell
# Actualizar pip
python -m pip install --upgrade pip

# Instalar herramientas de build
pip install build twine wheel setuptools
```

### Construir el paquete

```powershell
# Limpiar builds anteriores (si existen)
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue

# Construir el paquete
python -m build

# Esto genera:
# dist/backbone-1.0.0-py3-none-any.whl  (wheel - rápido)
# dist/backbone-1.0.0.tar.gz             (source - compatible)
```

### Verificar que se construyó correctamente

```powershell
# Verificar integridad del paquete
twine check dist/*

# Listar contenido del paquete
python -m zipfile -l dist/backbone-1.0.0-py3-none-any.whl
```

---

## 📦 Paso 2: Instalar Localmente (Testing)

### Método 1: Instalación en modo desarrollo (Recomendado para desarrollo)

```powershell
# Desde el directorio backbone/
pip install -e .

# Ventajas:
# - Cambios en el código se reflejan inmediatamente
# - No necesitas reinstalar después de cada cambio
# - Perfecto para desarrollo y testing
```

### Método 2: Instalación desde el archivo .whl

```powershell
# Instalar desde el wheel construido
pip install dist/backbone-1.0.0-py3-none-any.whl

# O desde el source distribution
pip install dist/backbone-1.0.0.tar.gz
```

### Método 3: Instalación directa desde el directorio

```powershell
# Instalar desde el directorio actual
pip install .
```

### Verificar la instalación

```powershell
# Verificar que se instaló
pip show backbone

# Probar la importación
python -c "import backbone; print(backbone.__version__)"
```

---

## 🚀 Paso 3: Usar en Otros Proyectos

### Ejemplo: Proyecto `industrial_prom`

```powershell
# 1. Ir al proyecto donde quieres usar backbone
cd C:\Users\Sistemas\Documents\programs\industrial_prom

# 2. Activar entorno virtual del proyecto
.\venv\Scripts\Activate.ps1

# 3. Instalar backbone

# Opción A: Desde archivo local
pip install C:\Users\Sistemas\Documents\programs\backbone\dist\backbone-1.0.0-py3-none-any.whl

# Opción B: Desde directorio (modo desarrollo)
pip install -e C:\Users\Sistemas\Documents\programs\backbone

# Opción C: Desde GitHub (Recomendado)
pip install git+https://github.com/FreakJazz/backbone.git

# Opción D: Desde GitHub Packages (si está publicado)
pip install --index-url https://pypi.pkg.github.com/FreakJazz/simple/ backbone
```

### 📖 Ejemplo Completo para Industrial Prom

Para ver un ejemplo completo de cómo usar Backbone en el proyecto `industrial_prom`, consulta:

- **[INDUSTRIAL_PROM_EXAMPLE.md](./INDUSTRIAL_PROM_EXAMPLE.md)** - Guía completa con código listo para usar
- **[create_industrial_prom_structure.py](./create_industrial_prom_structure.py)** - Script para generar estructura automáticamente

```powershell
# Generar estructura del proyecto automáticamente
python create_industrial_prom_structure.py
```

---

## 💻 Paso 4: Usar Backbone en Tu Código

### Ejemplo básico en `industrial_prom/main.py`

```python
"""
Aplicación usando Backbone Framework
"""
from fastapi import FastAPI

# Importar componentes de Backbone
from backbone import (
    # Exceptions
    DomainException,
    ApplicationException,
    
    # Logging
    LoggerFactory,
    
    # Response builders
    ProcessResponseBuilder,
    ErrorResponseBuilder,
    
    # Repository pattern
    IRepository,
    
    # Specifications
    FilterSpecification,
    
    # Events
    DomainEvent,
    EventBus
)

# Crear logger
logger = LoggerFactory.create_logger("industrial-prom")

# Crear app
app = FastAPI(title="Industrial Prom")

@app.get("/health")
def health_check():
    logger.info("Health check called")
    
    return ProcessResponseBuilder.status(
        message="Service is healthy",
        data={"backbone_version": "1.0.0"}
    )

@app.post("/api/machines/{machine_id}/start")
def start_machine(machine_id: int):
    try:
        # Validación de dominio
        if machine_id <= 0:
            raise DomainException(
                code=11001001,
                message="Invalid machine ID"
            )
        
        # Lógica de negocio
        logger.info(f"Starting machine {machine_id}")
        
        return ProcessResponseBuilder.success(
            message="Machine started",
            data={"machine_id": machine_id, "status": "running"}
        )
        
    except DomainException as e:
        return ErrorResponseBuilder.from_exception(e)
```

---

## 📋 Paso 5: Agregar a `requirements.txt`

### En tu proyecto `industrial_prom/requirements.txt`

```txt
# Framework base
backbone>=1.0.0

# O especificar la ruta local durante desarrollo
# -e file:///C:/Users/Sistemas/Documents/programs/backbone

# Otras dependencias
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
```

### Instalar todas las dependencias

```powershell
pip install -r requirements.txt
```

---

## 🔄 Paso 6: Actualizar el Paquete (Workflow)

### Cuando hagas cambios en Backbone:

```powershell
# 1. Hacer cambios en el código de backbone
cd C:\Users\Sistemas\Documents\programs\backbone

# 2. Actualizar versión en pyproject.toml
# version = "1.0.1"

# 3. Actualizar CHANGELOG.md con los cambios

# 4. Reconstruir el paquete
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
python -m build

# 5. Actualizar en proyecto que lo usa
cd C:\Users\Sistemas\Documents\programs\industrial_prom
pip install --upgrade C:\Users\Sistemas\Documents\programs\backbone\dist\backbone-1.0.1-py3-none-any.whl

# O si instalaste en modo desarrollo (-e), los cambios ya están disponibles
```

---

## 🌐 Paso 7: Publicar el Paquete (Opcional)

### Opción A: PyPI Público (Python Package Index)

```powershell
# 1. Crear cuenta en https://pypi.org/
# 2. Crear API token en Account Settings

# 3. Configurar credenciales
# En Windows, crear: %USERPROFILE%\.pypirc
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc... (tu token)

# 4. Subir a PyPI
twine upload dist/*

# 5. Instalar desde cualquier lugar
pip install backbone
```

### Opción B: GitHub Packages (Ya configurado)

```powershell
# 1. Crear Release en GitHub
gh release create v1.0.0

# 2. El workflow automático publicará en GitHub Packages

# 3. Instalar desde GitHub Packages
pip install --index-url https://pypi.pkg.github.com/FreakJazz/simple/ backbone
```

### Opción C: Servidor Privado (Corporativo)

```powershell
# Usando devpi, Artifactory, Nexus, etc.
twine upload --repository-url https://tu-servidor.com/pypi/ dist/*
```

---

## 🧪 Paso 8: Testing del Paquete

### Script de verificación

```python
# test_backbone_installation.py
"""
Verifica que Backbone está correctamente instalado
"""

def test_installation():
    """Test básico de instalación"""
    print("Testing Backbone installation...")
    
    try:
        # Test 1: Import básico
        import backbone
        print(f"✅ Backbone imported successfully")
        print(f"   Version: {backbone.__version__}")
        
        # Test 2: Componentes core
        from backbone import (
            DomainException,
            ApplicationException,
            LoggerFactory,
            ProcessResponseBuilder,
            FilterSpecification
        )
        print(f"✅ Core components available")
        
        # Test 3: Logger funcional
        logger = LoggerFactory.create_logger("test")
        logger.info("Test log")
        print(f"✅ Logger working")
        
        # Test 4: Response builders
        response = ProcessResponseBuilder.success(
            "Test", {"test": True}
        )
        assert response["status"] == "success"
        print(f"✅ Response builders working")
        
        # Test 5: Exceptions
        try:
            raise DomainException(
                code=11001001,
                message="Test exception"
            )
        except DomainException as e:
            assert e.code == 11001001
            print(f"✅ Exception system working")
        
        print(f"\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_installation()
```

### Ejecutar tests

```powershell
python test_backbone_installation.py
```

---

## 📚 Comandos Rápidos de Referencia

```powershell
# === CONSTRUCCIÓN ===
python -m build                          # Construir paquete

# === INSTALACIÓN LOCAL ===
pip install -e .                         # Modo desarrollo
pip install .                            # Instalación normal
pip install dist/*.whl                   # Desde wheel

# === VERIFICACIÓN ===
pip show backbone                        # Info del paquete
pip list | Select-String backbone        # Verificar instalación
python -c "import backbone; print(backbone.__version__)"

# === ACTUALIZACIÓN ===
pip install --upgrade .                  # Actualizar versión

# === DESINSTALACIÓN ===
pip uninstall backbone                   # Desinstalar

# === PUBLICACIÓN ===
twine check dist/*                       # Verificar antes de publicar
twine upload dist/*                      # Subir a PyPI
gh release create v1.0.0                 # Publicar en GitHub
```

---

## 🎯 Resumen: Tu Flujo de Trabajo

### Durante Desarrollo

1. **Editar código** en `C:\Users\Sistemas\Documents\programs\backbone`
2. **Instalar en modo desarrollo**: `pip install -e .`
3. **Cambios disponibles inmediatamente** en otros proyectos
4. **Probar** en `industrial_prom` o cualquier otro proyecto

### Para Producción

1. **Actualizar versión** en `pyproject.toml`
2. **Actualizar** `CHANGELOG.md`
3. **Construir**: `python -m build`
4. **Verificar**: `twine check dist/*`
5. **Publicar**: Crear Release en GitHub o subir a PyPI

### En Otros Proyectos

1. **Agregar a requirements.txt**: `backbone>=1.0.0`
2. **Instalar**: `pip install -r requirements.txt`
3. **Importar y usar**: `from backbone import ...`
4. **¡Listo!**

---

## 🎉 ¡Tu paquete está listo!

Backbone ya es un paquete pip completo y profesional que puedes:
- ✅ Instalar en cualquier proyecto Python
- ✅ Compartir con tu equipo
- ✅ Publicar en PyPI o GitHub Packages
- ✅ Versionarlo y actualizarlo fácilmente
- ✅ Usar como dependencia estándar

**Para empezar ahora mismo**:
```powershell
cd C:\Users\Sistemas\Documents\programs\backbone
python -m build
pip install -e .
```

**¡Ya puedes usar backbone en cualquier proyecto!**