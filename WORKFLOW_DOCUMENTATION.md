# 🚀 GitHub Actions Workflow - Documentación Completa

## 📋 Descripción General

Este workflow profesional automatiza la construcción, validación y publicación del paquete Backbone en GitHub Packages siguiendo las mejores prácticas de DevOps para proyectos Python empresariales.

## 🏗️ Estructura del Workflow

### Activadores (Triggers)
- **Principal**: Se ejecuta automáticamente cuando se crea un Release en GitHub
- **Manual**: Permite ejecución manual con opción de dry-run para testing

### Jobs Principales

1. **🏗️ build-and-validate**: Construcción y validación
2. **📦 publish-to-github**: Publicación en GitHub Packages  
3. **🎉 notify-success**: Notificación de éxito
4. **🚨 handle-failure**: Manejo de errores

## 🔧 Componentes del Workflow

### 1. Validaciones de Seguridad
```yaml
permissions:
  contents: read      # Leer código del repositorio
  packages: write     # Escribir en GitHub Packages
  id-token: write     # Para OIDC (Open ID Connect)
```

### 2. Validación de Versiones
- Extrae versión desde `pyproject.toml`
- Valida que coincida con el tag del Release
- Previene publicaciones accidentales

### 3. Testing Automático
- Busca y ejecuta `test_runner.py`, `pytest`, o `example.py`
- Valida que el código funciona antes de publicar

### 4. Construcción Robusta
- Genera wheel (`.whl`) y source distribution (`.tar.gz`)
- Valida integridad con `twine check`
- Sube artefactos para trazabilidad

### 5. Publicación Segura
- Usa `GITHUB_TOKEN` automático (no necesita configuración manual)
- Configura autenticación temporal
- Publica solo si todas las validaciones pasan

## 📝 Explicación Detallada por Sección

### Configuración de Entorno
```yaml
env:
  PYTHON_VERSION: "3.11"           # Versión de Python consistente
  PACKAGE_NAME: "backbone"         # Nombre del paquete
  REGISTRY_URL: "https://upload.pypi.pkg.github.com/FreakJazz/"
```

### Extracción de Versión
```python
# Script que extrae versión desde pyproject.toml
import tomli as toml
with open('pyproject.toml', 'rb') as f:
    data = tomli.load(f)
version = data['project']['version']
```

### Validación de Release
```bash
# Normaliza tags (v1.0.0 → 1.0.0) y compara
NORMALIZED_TAG="${RELEASE_TAG#v}"
if [ "$NORMALIZED_TAG" != "$PACKAGE_VERSION" ]; then
  exit 1  # Falla si no coinciden
fi
```

### Configuración de Twine
```bash
# Crea configuración temporal para autenticación
cat << EOF > ~/.pypirc
[github]
repository = https://upload.pypi.pkg.github.com/FreakJazz/
username = __token__
password = ${{ secrets.GITHUB_TOKEN }}
EOF
```

## 📦 Cómo Crear un Release

### Método 1: Interfaz Web de GitHub

1. Ve a tu repositorio en GitHub
2. Clic en "Releases" → "Create a new release"
3. **Tag version**: `v1.0.0` (debe coincidir con pyproject.toml)
4. **Release title**: `Backbone Framework v1.0.0`
5. **Description**:
```markdown
## 🎉 Backbone Framework v1.0.0

### ✨ Nuevas Características
- Clean Architecture implementation
- Event-driven microservices support
- 8-digit exception system
- Comprehensive testing framework

### 🔧 Improvements
- Structured logging with context
- Repository pattern with specifications
- Response builders for consistent APIs

### 📦 Installation
```bash
pip install --index-url https://pypi.pkg.github.com/FreakJazz/simple/ backbone==1.0.0
```

### 🔗 Documentation
- [README](./README.md)
- [Installation Guide](./INSTALLATION_GUIDE.md)
```

6. Marca "Set as the latest release"
7. Clic en "Publish release"

### Método 2: GitHub CLI

```bash
# Instalar GitHub CLI si no lo tienes
# https://cli.github.com/

# Crear release desde línea de comandos
gh release create v1.0.0 \
  --title "Backbone Framework v1.0.0" \
  --notes-file release-notes.md \
  --latest
```

### Método 3: API de GitHub

```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/FreakJazz/backbone/releases \
  -d '{
    "tag_name": "v1.0.0",
    "target_commitish": "main",
    "name": "Backbone Framework v1.0.0",
    "body": "## Release Notes\n\n- Feature 1\n- Feature 2",
    "draft": false,
    "prerelease": false
  }'
```

## 🔄 Flujo Completo de Release

### 1. Preparación
```bash
# 1. Actualizar versión en pyproject.toml
vim pyproject.toml  # Cambiar version = "1.0.0"

# 2. Commit cambios
git add pyproject.toml
git commit -m "chore: bump version to 1.0.0"

# 3. Push to main
git push origin main
```

### 2. Crear Release
```bash
# Crear tag localmente (opcional)
git tag v1.0.0
git push origin v1.0.0

# O crear release directamente en GitHub
gh release create v1.0.0 --generate-notes
```

### 3. Monitorear Workflow
- Ve a GitHub → Actions → "🚀 Publish to GitHub Packages"
- Observa el progreso en tiempo real
- Verifica que todos los jobs pasen

### 4. Verificar Publicación
- Ve a GitHub → Packages
- Confirma que el paquete está disponible
- Prueba la instalación en otro proyecto

## 🔍 Monitoreo y Troubleshooting

### Ver Logs del Workflow
```bash
# Usando GitHub CLI
gh run list --workflow="publish.yml"
gh run view RUN_ID --log
```

### Errores Comunes y Soluciones

1. **Version Mismatch**
```
❌ Error: Version mismatch! Release tag: 1.0.0, pyproject.toml version: 1.0.1

✅ Solución: Asegurar que el tag del release coincida exactamente con pyproject.toml
```

2. **Authentication Failed**
```
❌ Error: 401 Unauthorized

✅ Solución: El GITHUB_TOKEN se genera automáticamente, verificar permisos del repositorio
```

3. **Package Already Exists**
```
❌ Error: File already exists

✅ Solución: Incrementar versión en pyproject.toml antes del release
```

4. **Build Failed**
```
❌ Error: No module named 'backbone'

✅ Solución: Verificar estructura de directorios y __init__.py
```

## 📊 Métricas y Monitoreo

### GitHub Actions Insights
- Ve a GitHub → Insights → Actions
- Monitorea:
  - Tiempo de ejecución promedio
  - Tasa de éxito/fallo
  - Uso de runners

### Package Analytics
- Ve a GitHub → Packages → backbone
- Monitorea:
  - Descargas por versión
  - Dependientes del paquete
  - Estadísticas de uso

## 🔐 Configuración de Seguridad Avanzada

### Branch Protection Rules
```yaml
# Configurar en GitHub → Settings → Branches
protection_rules:
  - pattern: "main"
    required_status_checks:
      - "build-and-validate"
    enforce_admins: true
    required_pull_request_reviews:
      required_approving_review_count: 1
```

### Environment Protection
```yaml
# Configurar en GitHub → Settings → Environments
environment:
  name: "github-packages"
  protection_rules:
    - required_reviewers: ["FreakJazz"]
    - wait_timer: 0
```

### Secrets Management
- Nunca hardcodear tokens
- Usar `GITHUB_TOKEN` automático cuando sea posible
- Para tokens adicionales, usar GitHub Secrets

## 🚀 Mejores Prácticas

### 1. Versionado Semántico
- **Major** (1.0.0): Cambios incompatibles
- **Minor** (1.1.0): Nuevas características compatibles
- **Patch** (1.1.1): Bug fixes compatibles

### 2. Release Notes
- Usar formato estándar (Added, Changed, Fixed, Removed)
- Incluir breaking changes
- Mencionar contributors

### 3. Testing
- Siempre ejecutar tests antes de release
- Incluir integration tests
- Verificar en múltiples entornos

### 4. Documentación
- Actualizar README.md
- Mantener CHANGELOG.md
- Documentar API changes

## 📚 Recursos Adicionales

- [GitHub Packages Documentation](https://docs.github.com/en/packages)
- [Python Packaging Guide](https://packaging.python.org/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)