#!/usr/bin/env python
"""
Script para recolectar archivos estáticos.
Ejecutar este script después de clonar el repositorio.
"""
import os
import sys
import django
from pathlib import Path

def setup_django():
    """Configurar Django"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
    try:
        django.setup()
        return True
    except Exception as e:
        print(f"❌ Error al configurar Django: {e}")
        return False

def collect_static():
    """Recolectar archivos estáticos"""
    from django.core.management import execute_from_command_line
    
    print("🔄 Recolectando archivos estáticos...")
    
    # Verificar que el directorio static existe
    static_dir = Path("static")
    if not static_dir.exists():
        print("❌ Directorio 'static' no encontrado.")
        print("   Asegúrate de estar en el directorio raíz del proyecto.")
        return False
    
    try:
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput', '--clear'])
        print("✅ Archivos estáticos recolectados exitosamente!")
        
        # Verificar que se creó el directorio staticfiles
        staticfiles_dir = Path("staticfiles")
        if staticfiles_dir.exists():
            file_count = len(list(staticfiles_dir.rglob("*")))
            print(f"� Se recolectaron {file_count} archivos en 'staticfiles/'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al recolectar archivos estáticos: {e}")
        print("\n🔧 Intentando método alternativo...")
        try:
            execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
            print("✅ Archivos estáticos recolectados con método alternativo!")
            return True
        except Exception as e2:
            print(f"❌ También falló el método alternativo: {e2}")
            return False

def main():
    print("=" * 50)
    print("📚 SAM - Recolección de Archivos Estáticos")
    print("=" * 50)
    
    if not setup_django():
        sys.exit(1)
    
    if not collect_static():
        print("\n❌ No se pudieron recolectar los archivos estáticos.")
        print("   Ejecuta: python manage.py collectstatic --noinput")
        sys.exit(1)
    
    print("\n🎉 ¡Proceso completado!")
    print("   Ahora puedes ejecutar: python manage.py runserver")

if __name__ == '__main__':
    main()
