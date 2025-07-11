#!/usr/bin/env python
"""
Script de diagnóstico y reparación para SAM
Ejecutar este script si los estilos no se cargan correctamente
"""

import os
import sys
import subprocess
from pathlib import Path

def print_separator():
    print("=" * 60)

def print_status(message, status="INFO"):
    status_symbols = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "WARNING": "⚠️",
        "ERROR": "❌"
    }
    print(f"{status_symbols.get(status, 'ℹ️')} {message}")

def check_python():
    print_status("Verificando versión de Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} - OK", "SUCCESS")
        return True
    else:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} - Versión muy antigua", "ERROR")
        return False

def check_virtual_env():
    print_status("Verificando entorno virtual...")
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_status("Entorno virtual activado", "SUCCESS")
        return True
    else:
        print_status("Entorno virtual NO activado", "WARNING")
        return False

def check_directories():
    print_status("Verificando estructura de directorios...")
    
    required_dirs = [
        Path("static"),
        Path("templates"),
        Path("sma"),
        Path("smapp"),
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if dir_path.exists():
            print_status(f"Directorio {dir_path} - OK", "SUCCESS")
        else:
            print_status(f"Directorio {dir_path} - FALTA", "ERROR")
            missing_dirs.append(dir_path)
    
    return len(missing_dirs) == 0

def check_static_files():
    print_status("Verificando archivos estáticos...")
    
    static_dir = Path("static")
    staticfiles_dir = Path("staticfiles")
    
    if not static_dir.exists():
        print_status("Directorio static/ no encontrado", "ERROR")
        return False
    
    if not staticfiles_dir.exists():
        print_status("Directorio staticfiles/ no encontrado - se creará", "WARNING")
        return False
    
    # Verificar archivos importantes
    important_files = [
        static_dir / "FrWork" / "admin_lte" / "build" / "css" / "custom.min.css",
        static_dir / "sma_moderno.css"
    ]
    
    found_files = 0
    for file_path in important_files:
        if file_path.exists():
            print_status(f"Archivo {file_path.name} - OK", "SUCCESS")
            found_files += 1
        else:
            print_status(f"Archivo {file_path} - FALTA", "WARNING")
    
    return found_files > 0

def run_collectstatic():
    print_status("Ejecutando collectstatic...")
    try:
        result = subprocess.run([
            sys.executable, "manage.py", "collectstatic", "--noinput", "--clear"
        ], capture_output=True, text=True, check=True)
        print_status("collectstatic ejecutado exitosamente", "SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print_status(f"Error al ejecutar collectstatic: {e}", "ERROR")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except FileNotFoundError:
        print_status("manage.py no encontrado", "ERROR")
        return False

def check_requirements():
    print_status("Verificando dependencias...")
    try:
        import django
        print_status(f"Django {django.get_version()} - OK", "SUCCESS")
    except ImportError:
        print_status("Django no instalado", "ERROR")
        return False
    
    try:
        import whitenoise
        print_status("WhiteNoise instalado - OK", "SUCCESS")
    except ImportError:
        print_status("WhiteNoise no instalado", "WARNING")
    
    return True

def main():
    print_separator()
    print("🔧 SAM - Diagnóstico y Reparación de Archivos Estáticos")
    print_separator()
    
    # Verificaciones
    all_good = True
    
    all_good &= check_python()
    print()
    
    check_virtual_env()  # No es crítico
    print()
    
    all_good &= check_directories()
    print()
    
    all_good &= check_requirements()
    print()
    
    static_files_ok = check_static_files()
    print()
    
    # Reparación automática
    if not static_files_ok:
        print_status("Intentando reparar archivos estáticos...", "INFO")
        if run_collectstatic():
            print_status("Reparación completada", "SUCCESS")
        else:
            print_status("No se pudo reparar automáticamente", "ERROR")
            all_good = False
    
    print_separator()
    
    if all_good and static_files_ok:
        print_status("✨ Todo está en orden. El proyecto debería funcionar correctamente.", "SUCCESS")
    else:
        print_status("⚠️ Se encontraron problemas. Sigue estos pasos:", "WARNING")
        print()
        print("1. Asegúrate de estar en el directorio correcto del proyecto")
        print("2. Activa el entorno virtual:")
        print("   Windows: .venv\\Scripts\\activate")
        print("   Linux/Mac: source .venv/bin/activate")
        print("3. Instala las dependencias: pip install -r requirements.txt")
        print("4. Ejecuta: python manage.py collectstatic --noinput")
        print("5. Ejecuta: python manage.py runserver")
    
    print_separator()

if __name__ == "__main__":
    main()
