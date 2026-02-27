# Documentación: Configuración para instalar desde GitHub Packages

## 📦 Instalación de Backbone desde GitHub Packages

### Método 1: Configuración Global de pip

Crea el archivo `~/.pip/pip.conf` (Linux/macOS) o `%APPDATA%\pip\pip.ini` (Windows):

```ini
[global]
extra-index-url = https://pypi.pkg.github.com/FreakJazz/simple/

[install]
trusted-host = pypi.pkg.github.com
```

### Método 2: Configuración con Token de Acceso

1. **Crear Personal Access Token en GitHub:**
   - Ve a GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Crea un token con permisos: `read:packages`
   - Guarda el token de forma segura

2. **Configurar pip con token:**

**Linux/macOS:**
```bash
# Crear archivo de configuración
mkdir -p ~/.pip
cat << EOF > ~/.pip/pip.conf
[global]
extra-index-url = https://YOUR_TOKEN@pypi.pkg.github.com/FreakJazz/simple/

[install]
trusted-host = pypi.pkg.github.com
EOF
```

**Windows:**
```cmd
# Crear directorio si no existe
mkdir %APPDATA%\pip

# Crear archivo pip.ini
echo [global] > %APPDATA%\pip\pip.ini
echo extra-index-url = https://YOUR_TOKEN@pypi.pkg.github.com/FreakJazz/simple/ >> %APPDATA%\pip\pip.ini
echo. >> %APPDATA%\pip\pip.ini
echo [install] >> %APPDATA%\pip\pip.ini
echo trusted-host = pypi.pkg.github.com >> %APPDATA%\pip\pip.ini
```

### Método 3: Variable de Entorno

```bash
# Exportar token como variable de entorno
export GITHUB_TOKEN="your_personal_access_token"

# Instalar usando el token
pip install --index-url https://${GITHUB_TOKEN}@pypi.pkg.github.com/FreakJazz/simple/ backbone
```

### Método 4: Instalación Directa (Recomendado para proyectos)

```bash
# Instalar versión específica
pip install --index-url https://pypi.pkg.github.com/FreakJazz/simple/ backbone==1.0.0

# O instalar la última versión
pip install --index-url https://pypi.pkg.github.com/FreakJazz/simple/ backbone
```

## 🏭 Uso en Proyecto Industrial (industrial_prom)

### 1. Archivo requirements.txt

```txt
# requirements.txt para industrial_prom

# Dependencias principales
backbone>=1.0.0

# Otras dependencias de tu proyecto
fastapi>=0.104.0
uvicorn>=0.24.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
redis>=5.0.0
```

### 2. Instalación en el proyecto

```bash
cd industrial_prom

# Opción A: Instalar con configuración temporal
pip install --index-url https://pypi.pkg.github.com/FreakJazz/simple/ -r requirements.txt

# Opción B: Con token de entorno
GITHUB_TOKEN=your_token pip install --index-url https://${GITHUB_TOKEN}@pypi.pkg.github.com/FreakJazz/simple/ -r requirements.txt
```

### 3. Docker Configuration (para contenedores)

```dockerfile
# Dockerfile para industrial_prom
FROM python:3.11-slim

WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias con acceso a GitHub Packages
ARG GITHUB_TOKEN
RUN pip install --index-url https://${GITHUB_TOKEN}@pypi.pkg.github.com/FreakJazz/simple/ -r requirements.txt

# Resto de tu aplicación
COPY . .
CMD ["python", "main.py"]
```

Construir la imagen:
```bash
docker build --build-arg GITHUB_TOKEN=your_token -t industrial_prom .
```

### 4. GitHub Actions para industrial_prom

```yaml
# .github/workflows/deploy.yml en industrial_prom
name: Deploy Industrial Prom

on:
  push:
    branches: [main]

jobs:
  deploy:
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
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## 🔧 Configuraciones Avanzadas

### pip.conf completo para entornos corporativos

```ini
[global]
# Índices de paquetes
index-url = https://pypi.org/simple/
extra-index-url = 
    https://pypi.pkg.github.com/FreakJazz/simple/
    https://pypi.org/simple/

# Configuración de confianza
trusted-host = 
    pypi.org
    pypi.pkg.github.com
    files.pythonhosted.org

# Cache y timeout
cache-dir = ~/.cache/pip
timeout = 60
retries = 3

# Configuración de compilación
no-build-isolation = false
```

### Verificación de instalación

```python
# verificar_backbone.py
try:
    import backbone
    print(f"✅ Backbone instalado correctamente")
    print(f"📦 Versión: {backbone.__version__}")
    print(f"📍 Ubicación: {backbone.__file__}")
    
    # Verificar componentes principales
    from backbone import (
        DomainException,
        ApplicationException,
        LoggerFactory,
        ProcessResponseBuilder
    )
    print("✅ Componentes principales disponibles")
    
except ImportError as e:
    print(f"❌ Error al importar backbone: {e}")
    print("💡 Verifica la configuración de pip y el token de acceso")
```

## 🚨 Troubleshooting

### Errores comunes y soluciones

1. **Error 401 Unauthorized**
   ```
   Solución: Verificar que el token tiene permisos read:packages
   ```

2. **Error 404 Not Found**
   ```
   Solución: Verificar que el paquete existe y la URL es correcta
   ```

3. **SSL Certificate errors**
   ```bash
   pip install --trusted-host pypi.pkg.github.com --index-url https://pypi.pkg.github.com/FreakJazz/simple/ backbone
   ```

4. **Cache issues**
   ```bash
   pip cache purge
   pip install --no-cache-dir --index-url https://pypi.pkg.github.com/FreakJazz/simple/ backbone
   ```