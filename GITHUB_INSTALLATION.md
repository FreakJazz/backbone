# 🚀 Instalación desde GitHub

## ✅ Estado: TODO LISTO

Tu paquete **Backbone** ya está completamente configurado para instalarse directamente desde GitHub usando pip.

---

## 📋 Requisitos Previos

1. **Python 3.11 o superior** instalado
2. **Git** instalado (para el método directo desde GitHub)
3. El repositorio **debe estar en GitHub** en: `https://github.com/FreakJazz/backbone`

---

## 🎯 Método 1: Instalación Directa desde GitHub (Recomendado)

### Instalación básica

```powershell
pip install git+https://github.com/FreakJazz/backbone.git
```

### Instalación de una versión específica (tag)

```powershell
# Instalar una versión específica (ejemplo: v1.0.0)
pip install git+https://github.com/FreakJazz/backbone.git@v1.0.0

# Instalar desde una rama específica
pip install git+https://github.com/FreakJazz/backbone.git@main

# Instalar desde un commit específico
pip install git+https://github.com/FreakJazz/backbone.git@abc123def
```

### Instalación en modo desarrollo

```powershell
# Clonar el repositorio
git clone https://github.com/FreakJazz/backbone.git
cd backbone

# Instalar en modo editable
pip install -e .
```

---

## 🔧 Método 2: Instalación en un Proyecto

### Agregarlo a `requirements.txt`

```txt
# Desde GitHub (última versión)
git+https://github.com/FreakJazz/backbone.git

# Desde GitHub (versión específica)
git+https://github.com/FreakJazz/backbone.git@v1.0.0

# Desde GitHub (rama específica)
git+https://github.com/FreakJazz/backbone.git@main
```

Luego instalar:

```powershell
pip install -r requirements.txt
```

### Agregarlo a `pyproject.toml`

```toml
[project]
dependencies = [
    "backbone @ git+https://github.com/FreakJazz/backbone.git@v1.0.0"
]
```

---

## 📦 Pasos para Subir a GitHub (Si aún no está)

### 1. Verificar que todos los archivos estén listos

```powershell
# Verificar que estamos en el directorio correcto
cd C:\Users\Sistemas\Documents\programs\backbone

# Ver el estado de Git
git status
```

### 2. Crear el repositorio en GitHub

1. Ve a [GitHub](https://github.com)
2. Click en **"New repository"**
3. Nombre: `backbone`
4. Descripción: `Clean Architecture Framework with Event-Driven Microservices for Python`
5. **Public** (para que pip pueda instalarlo sin autenticación)
6. **NO** inicializar con README, .gitignore o LICENSE (ya los tienes)
7. Click en **"Create repository"**

### 3. Conectar tu repositorio local con GitHub

```powershell
# Si es un nuevo repositorio de Git
git init
git add .
git commit -m "Initial commit: Backbone Framework v1.0.0"

# Agregar el remote de GitHub (reemplaza FreakJazz con tu usuario)
git remote add origin https://github.com/FreakJazz/backbone.git

# Subir a GitHub
git push -u origin main
```

### 4. Crear un Release/Tag (Recomendado)

```powershell
# Crear tag para la versión 1.0.0
git tag -a v1.0.0 -m "Backbone Framework v1.0.0 - Initial Release"

# Subir el tag a GitHub
git push origin v1.0.0
```

O desde la interfaz de GitHub:
1. Ve a tu repositorio en GitHub
2. Click en **"Releases"** → **"Create a new release"**
3. Tag version: `v1.0.0`
4. Release title: `Backbone Framework v1.0.0`
5. Descripción: Copia el contenido relevante de `CHANGELOG.md`
6. Click en **"Publish release"**

---

## ✅ Verificar la Instalación

### Test en un entorno virtual nuevo

```powershell
# Crear un nuevo entorno de prueba
cd C:\Users\Sistemas\Documents\programs
mkdir test_backbone_install
cd test_backbone_install

# Crear entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# Instalar desde GitHub
pip install git+https://github.com/FreakJazz/backbone.git

# Verificar la instalación
pip show backbone

# Probar que funciona
python -c "import backbone; print('✅ Backbone version:', backbone.__version__)"
```

### Test de importaciones

```powershell
python -c "
from backbone import (
    DomainException,
    ApplicationException,
    LoggerFactory,
    ProcessResponseBuilder,
    FilterSpecification
)
print('✅ All imports successful!')
"
```

---

## 🔄 Actualizar a Nueva Versión

### Para usuarios del paquete

```powershell
# Actualizar a la última versión
pip install --upgrade git+https://github.com/FreakJazz/backbone.git

# Forzar reinstalación
pip install --force-reinstall git+https://github.com/FreakJazz/backbone.git
```

### Para publicar una nueva versión (como desarrollador)

```powershell
# 1. Actualizar versión en pyproject.toml y setup.py
# version = "1.0.1"

# 2. Actualizar CHANGELOG.md

# 3. Commit y push
git add .
git commit -m "Release v1.0.1"
git push

# 4. Crear nuevo tag
git tag -a v1.0.1 -m "Backbone Framework v1.0.1"
git push origin v1.0.1
```

---

## 🌐 Instalación desde Repositorio Privado

Si tu repositorio es privado, necesitas autenticación:

### Método 1: Token de GitHub

```powershell
# Crear un Personal Access Token en GitHub:
# Settings → Developer settings → Personal access tokens → Tokens (classic)
# Dar permiso: repo (Full control of private repositories)

# Instalar usando el token
pip install git+https://<TOKEN>@github.com/FreakJazz/backbone.git
```

### Método 2: SSH

```powershell
# Configurar SSH key en GitHub primero
# Luego instalar usando SSH
pip install git+ssh://git@github.com/FreakJazz/backbone.git
```

---

## 🐛 Solución de Problemas

### Error: "Repository not found"

- ✅ Verifica que el repositorio existe: `https://github.com/FreakJazz/backbone`
- ✅ Verifica que el repositorio es público o tienes acceso
- ✅ Verifica que la URL es correcta

### Error: "Could not find setup.py or pyproject.toml"

- ✅ Verifica que subiste todos los archivos a GitHub (especialmente `pyproject.toml` y `setup.py`)
- ✅ Asegúrate de hacer commit y push de todos los archivos

### Error: "No matching distribution found"

- ✅ Verifica tu versión de Python (`python --version`) - requiere Python 3.11+
- ✅ Actualiza pip: `python -m pip install --upgrade pip`

### Error: Dependencias no se instalan

- ✅ Verifica que `pyproject.toml` tenga las dependencias correctas
- ✅ Instala manualmente: `pip install pydantic pydantic-settings typing-extensions`

---

## 📚 Ejemplo de Uso en Otro Proyecto

### Proyecto: `industrial_prom`

```powershell
# 1. Ir al proyecto
cd C:\Users\Sistemas\Documents\programs\industrial_prom

# 2. Activar entorno virtual
.\venv\Scripts\Activate.ps1

# 3. Crear o actualizar requirements.txt
echo "git+https://github.com/FreakJazz/backbone.git@v1.0.0" >> requirements.txt

# 4. Instalar todas las dependencias
pip install -r requirements.txt

# 5. Usar en tu código
# main.py
```

```python
from backbone import (
    DomainException,
    LoggerFactory,
    ProcessResponseBuilder
)

logger = LoggerFactory.create_logger("industrial-prom")

def main():
    logger.info("Application started with Backbone Framework")
    # Tu código aquí...
```

---

## 🎉 ¡Listo!

Tu paquete ahora puede instalarse con un simple comando:

```powershell
pip install git+https://github.com/FreakJazz/backbone.git
```

**Ventajas:**
- ✅ No necesitas publicar en PyPI
- ✅ Control total sobre el código
- ✅ Versionado con Git tags
- ✅ Instalación directa con un comando
- ✅ Fácil de actualizar
- ✅ Compatible con `requirements.txt` y `pyproject.toml`

---

## 📞 Soporte

Si tienes problemas:
1. Revisa los [Issues en GitHub](https://github.com/FreakJazz/backbone/issues)
2. Lee la [documentación completa](README.md)
3. Verifica el [CHANGELOG](CHANGELOG.md) para cambios recientes
