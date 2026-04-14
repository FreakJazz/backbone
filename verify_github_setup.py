"""
Script de verificación para el paquete Backbone antes de subir a GitHub
Verifica que la configuración es correcta para instalación desde GitHub
"""

import sys
import os
from pathlib import Path

def check_file_exists(filepath, description):
    """Verifica que un archivo existe"""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} NO ENCONTRADO: {filepath}")
        return False

def check_pyproject_toml():
    """Verifica configuración en pyproject.toml"""
    print("\n📋 Verificando pyproject.toml...")
    
    try:
        with open("pyproject.toml", "r", encoding="utf-8") as f:
            content = f.read()
            
        checks = {
            'name = "backbone"': "Nombre del paquete correcto",
            'version = "1.0.0"': "Versión especificada",
            'requires-python = ">=3.11"': "Versión de Python correcta",
            '"https://github.com/FreakJazz/backbone"': "URL de GitHub correcta",
            'dependencies = [': "Sección de dependencias presente",
            '"pydantic>=2.0.0"': "Dependencia pydantic",
            '"pydantic-settings>=2.0.0"': "Dependencia pydantic-settings",
        }
        
        all_ok = True
        for check, description in checks.items():
            if check in content:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description} - NO ENCONTRADO")
                all_ok = False
                
        return all_ok
        
    except Exception as e:
        print(f"❌ Error al leer pyproject.toml: {e}")
        return False

def check_setup_py():
    """Verifica configuración en setup.py"""
    print("\n📋 Verificando setup.py...")
    
    try:
        with open("setup.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        checks = {
            'name="backbone"': "Nombre del paquete correcto",
            'version="1.0.0"': "Versión especificada",
            'author="FreakJazz"': "Autor correcto",
            'url="https://github.com/FreakJazz/backbone"': "URL de GitHub correcta",
            'python_requires=">=3.11"': "Versión de Python correcta",
            '"pydantic>=2.0.0"': "Dependencia pydantic",
            '"pydantic-settings>=2.0.0"': "Dependencia pydantic-settings",
        }
        
        all_ok = True
        for check, description in checks.items():
            if check in content:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description} - NO ENCONTRADO")
                all_ok = False
                
        return all_ok
        
    except Exception as e:
        print(f"❌ Error al leer setup.py: {e}")
        return False

def check_package_structure():
    """Verifica la estructura del paquete"""
    print("\n📁 Verificando estructura del paquete...")
    
    required_files = [
        ("backbone/__init__.py", "Paquete principal backbone"),
        ("backbone/py.typed", "Marcador de tipos"),
        ("README.md", "README"),
        ("LICENSE", "Licencia"),
        ("MANIFEST.in", "Manifest"),
        ("CHANGELOG.md", "Changelog"),
    ]
    
    all_ok = True
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            all_ok = False
            
    return all_ok

def check_backbone_version():
    """Verifica que backbone/__init__.py tenga __version__"""
    print("\n🔍 Verificando versión en backbone/__init__.py...")
    
    try:
        # Leer el archivo __init__.py
        init_path = "backbone/__init__.py"
        if not Path(init_path).exists():
            print(f"❌ {init_path} no encontrado")
            return False
            
        with open(init_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        if '__version__' in content:
            print(f"  ✅ Variable __version__ encontrada")
            # Intentar extraer el valor
            for line in content.split('\n'):
                if '__version__' in line and '=' in line:
                    print(f"  ℹ️  {line.strip()}")
            return True
        else:
            print(f"  ⚠️  Variable __version__ no encontrada (opcional pero recomendada)")
            return True  # No es crítico
            
    except Exception as e:
        print(f"⚠️ Error al verificar versión: {e}")
        return True  # No es crítico

def check_gitignore():
    """Verifica que .gitignore existe y tiene contenido apropiado"""
    print("\n🚫 Verificando .gitignore...")
    
    if not Path(".gitignore").exists():
        print("  ⚠️  .gitignore no encontrado (se recomienda tenerlo)")
        return True  # No es crítico
        
    try:
        with open(".gitignore", "r", encoding="utf-8") as f:
            content = f.read()
            
        important_ignores = [
            '__pycache__',
            '*.egg-info',
            'dist/',
            'build/',
            '.venv',
            'venv',
        ]
        
        all_ok = True
        for pattern in important_ignores:
            if pattern in content:
                print(f"  ✅ Ignora: {pattern}")
            else:
                print(f"  ⚠️  No ignora: {pattern}")
                
        return True  # No es crítico para la instalación
        
    except Exception as e:
        print(f"⚠️ Error al leer .gitignore: {e}")
        return True

def main():
    """Ejecuta todas las verificaciones"""
    print("=" * 70)
    print("🔍 VERIFICACIÓN DE CONFIGURACIÓN PARA GITHUB")
    print("   Paquete: Backbone Framework")
    print("=" * 70)
    
    results = []
    
    # Verificaciones críticas
    results.append(("Estructura del paquete", check_package_structure()))
    results.append(("pyproject.toml", check_pyproject_toml()))
    results.append(("setup.py", check_setup_py()))
    
    # Verificaciones opcionales/informativas
    check_backbone_version()
    check_gitignore()
    
    # Resumen
    print("\n" + "=" * 70)
    print("📊 RESUMEN")
    print("=" * 70)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("""
🎉 ¡TODO ESTÁ CORRECTO!

Tu paquete está listo para subirse a GitHub y puede instalarse con:

    pip install git+https://github.com/FreakJazz/backbone.git

📋 PRÓXIMOS PASOS:

1. Subir a GitHub:
   git add .
   git commit -m "Initial commit: Backbone Framework v1.0.0"
   git remote add origin https://github.com/FreakJazz/backbone.git
   git push -u origin main

2. Crear release:
   git tag -a v1.0.0 -m "Backbone Framework v1.0.0"
   git push origin v1.0.0

3. Probar instalación:
   pip install git+https://github.com/FreakJazz/backbone.git

📖 Para más detalles, consulta: GITHUB_INSTALLATION.md
""")
        return 0
    else:
        print("""
⚠️  HAY PROBLEMAS QUE CORREGIR

Por favor revisa los errores arriba y corrígelos antes de continuar.
""")
        return 1

if __name__ == "__main__":
    sys.exit(main())
