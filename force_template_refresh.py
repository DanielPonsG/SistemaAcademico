#!/usr/bin/env python
"""
Script para forzar la actualización del template inicio.html
"""
import os
import sys
import django
from django.conf import settings
from django.template.loader import get_template
from django.template import Context

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

def force_template_refresh():
    """Forzar la recarga del template"""
    print("=== FORZANDO ACTUALIZACIÓN DEL TEMPLATE ===")
    
    # 1. Verificar la ruta del template
    print(f"DIRS de templates: {settings.TEMPLATES[0]['DIRS']}")
    
    # 2. Verificar que el archivo existe
    template_path = os.path.join(settings.BASE_DIR, 'templates', 'inicio.html')
    print(f"Ruta del template: {template_path}")
    print(f"¿Existe el archivo?: {os.path.exists(template_path)}")
    
    # 3. Verificar el contenido del comentario de verificación
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if "VERIFICACION CACHE 2024" in content:
            print("✓ El template contiene el comentario de verificación")
        else:
            print("✗ El template NO contiene el comentario de verificación")
    
    # 4. Forzar la recarga del template
    try:
        # Limpiar el cache de templates si existe
        if hasattr(django.template.loader, '_template_cache'):
            django.template.loader._template_cache.clear()
            print("✓ Cache de templates limpiado")
        
        # Cargar el template
        template = get_template('inicio.html')
        print("✓ Template 'inicio.html' cargado exitosamente")
        
        # Verificar que el template cargado contiene nuestros cambios
        template_source = template.source
        if "VERIFICACION CACHE 2024" in template_source:
            print("✓ El template cargado contiene el comentario de verificación")
        else:
            print("✗ El template cargado NO contiene el comentario de verificación")
            
        if "function cambiarEstudiante" in template_source:
            print("✓ El template contiene la función JavaScript actualizada")
        else:
            print("✗ El template NO contiene la función JavaScript actualizada")
            
    except Exception as e:
        print(f"✗ Error al cargar el template: {e}")
    
    print("\n=== INFORMACIÓN ADICIONAL ===")
    print(f"DEBUG setting: {settings.DEBUG}")
    
    # 5. Verificar el entorno virtual
    print(f"Python executable: {sys.executable}")
    print(f"Django version: {django.__version__}")
    
    print("\n=== RECOMENDACIONES ===")
    print("1. Asegúrate de que el servidor Django esté ejecutándose en modo DEBUG=True")
    print("2. Recarga completamente la página en el navegador (Ctrl+F5)")
    print("3. Limpia la caché del navegador")
    print("4. Si usas un proxy o CDN, límpialo también")

if __name__ == "__main__":
    force_template_refresh()
