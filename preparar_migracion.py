#!/usr/bin/env python
"""
Script para preparar la migración de SQLite a PostgreSQL en la nube
"""
import os
import sys
import django
import subprocess
from datetime import datetime

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

def crear_backup():
    """Crear backup de la base de datos actual"""
    print("🔄 Creando backup de la base de datos SQLite...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_data_{timestamp}.json"
    
    try:
        # Crear backup con dumpdata
        result = subprocess.run([
            sys.executable, 'manage.py', 'dumpdata',
            '--exclude', 'contenttypes',
            '--exclude', 'auth.permission',
            '--exclude', 'sessions.session',
            '--natural-foreign',
            '--natural-primary',
            '--output', backup_file
        ], capture_output=True, text=True, check=True)
        
        print(f"✅ Backup creado exitosamente: {backup_file}")
        return backup_file
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al crear backup: {e.stderr}")
        return None

def verificar_datos():
    """Verificar datos en la base de datos actual"""
    from smapp.models import Estudiante, Profesor, Apoderado, Curso
    
    print("\n📊 DATOS ACTUALES EN LA BASE DE DATOS:")
    print(f"  Estudiantes: {Estudiante.objects.count()}")
    print(f"  Profesores: {Profesor.objects.count()}")
    print(f"  Apoderados: {Apoderado.objects.count()}")
    print(f"  Cursos: {Curso.objects.count()}")

def crear_env_template():
    """Crear template del archivo .env"""
    env_content = """# Configuración de Base de Datos en la Nube
# Reemplaza estos valores con los de tu proveedor (Railway, Supabase, etc.)

DEBUG=False
DB_NAME=tu_nombre_bd
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_HOST=tu_host.com
DB_PORT=5432

# Ejemplo para Railway:
# DB_NAME=railway
# DB_USER=postgres
# DB_PASSWORD=ABC123xyz...
# DB_HOST=containers-us-west-1.railway.app
# DB_PORT=5432

# Ejemplo para Supabase:
# DB_NAME=postgres
# DB_USER=postgres
# DB_PASSWORD=tu_password
# DB_HOST=db.xxx.supabase.co
# DB_PORT=5432
"""
    
    with open('.env.template', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("📝 Archivo .env.template creado")
    print("   Copia este archivo a .env y completa con tus credenciales")

def instalar_dependencias():
    """Instalar dependencias necesarias"""
    print("\n📦 Instalando dependencias necesarias...")
    
    dependencias = [
        'psycopg2-binary',  # Driver PostgreSQL
        'python-decouple',  # Manejo de variables de entorno
    ]
    
    for dep in dependencias:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                         check=True, capture_output=True)
            print(f"✅ {dep} instalado correctamente")
        except subprocess.CalledProcessError:
            print(f"❌ Error instalando {dep}")

def actualizar_requirements():
    """Actualizar requirements.txt"""
    print("\n📋 Actualizando requirements.txt...")
    
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], 
                              capture_output=True, text=True, check=True)
        
        with open('requirements.txt', 'w') as f:
            f.write(result.stdout)
        
        print("✅ requirements.txt actualizado")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error actualizando requirements: {e}")

def main():
    print("🚀 PREPARANDO MIGRACIÓN A BASE DE DATOS EN LA NUBE")
    print("=" * 60)
    
    # 1. Verificar datos actuales
    verificar_datos()
    
    # 2. Crear backup
    backup_file = crear_backup()
    if not backup_file:
        print("❌ No se pudo crear el backup. Abortando.")
        return
    
    # 3. Instalar dependencias
    instalar_dependencias()
    
    # 4. Actualizar requirements
    actualizar_requirements()
    
    # 5. Crear template de .env
    crear_env_template()
    
    print("\n" + "=" * 60)
    print("✅ PREPARACIÓN COMPLETADA")
    print("\n📋 SIGUIENTES PASOS:")
    print("1. Crea una cuenta en Railway, Supabase o Neon")
    print("2. Crea una base de datos PostgreSQL")
    print("3. Copia las credenciales a un archivo .env")
    print("4. Ejecuta el script de migración")
    print(f"\n💾 Backup creado: {backup_file}")
    print("📄 Template de configuración: .env.template")

if __name__ == "__main__":
    main()
