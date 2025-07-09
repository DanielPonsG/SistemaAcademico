#!/usr/bin/env python
"""
Script para migrar datos desde SQLite a PostgreSQL en la nube
"""
import os
import sys
import django
import subprocess
from pathlib import Path

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')

def verificar_env():
    """Verificar que existe el archivo .env"""
    if not os.path.exists('.env'):
        print("❌ No se encontró el archivo .env")
        print("   Crea el archivo .env con tus credenciales de base de datos")
        print("   Puedes usar .env.template como referencia")
        return False
    return True

def verificar_conexion_postgresql():
    """Verificar conexión a PostgreSQL"""
    print("🔄 Verificando conexión a PostgreSQL...")
    
    try:
        django.setup()
        from django.db import connection
        
        # Intentar conectar
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        print("✅ Conexión a PostgreSQL exitosa")
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a PostgreSQL: {e}")
        print("   Verifica las credenciales en el archivo .env")
        return False

def ejecutar_migraciones():
    """Ejecutar migraciones en la nueva base de datos"""
    print("\n🔄 Ejecutando migraciones...")
    
    try:
        # makemigrations
        result = subprocess.run([
            sys.executable, 'manage.py', 'makemigrations'
        ], capture_output=True, text=True, check=True)
        
        print("✅ Migraciones creadas")
        
        # migrate
        result = subprocess.run([
            sys.executable, 'manage.py', 'migrate'
        ], capture_output=True, text=True, check=True)
        
        print("✅ Migraciones aplicadas")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en migraciones: {e.stderr}")
        return False

def cargar_backup():
    """Cargar datos del backup más reciente"""
    print("\n🔄 Buscando archivo de backup...")
    
    # Buscar archivos de backup
    backup_files = list(Path('.').glob('backup_data_*.json'))
    
    if not backup_files:
        print("❌ No se encontraron archivos de backup")
        return False
    
    # Usar el más reciente
    backup_file = max(backup_files, key=os.path.getctime)
    print(f"📁 Usando backup: {backup_file}")
    
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'loaddata', str(backup_file)
        ], capture_output=True, text=True, check=True)
        
        print("✅ Datos cargados exitosamente")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error cargando datos: {e.stderr}")
        return False

def crear_superuser():
    """Crear superuser en la nueva base de datos"""
    print("\n👤 Creando superuser...")
    
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'createsuperuser'
        ], input='admin\nadmin@example.com\nadmin123\nadmin123\n', 
        text=True, capture_output=True)
        
        print("✅ Superuser creado (usuario: admin, contraseña: admin123)")
        print("⚠️  Cambia la contraseña después del primer login")
        
    except Exception as e:
        print(f"ℹ️  Crea manualmente el superuser con: python manage.py createsuperuser")

def verificar_datos_migrados():
    """Verificar que los datos se migraron correctamente"""
    print("\n📊 Verificando datos migrados...")
    
    try:
        django.setup()
        from smapp.models import Estudiante, Profesor, Apoderado, Curso
        
        print(f"  Estudiantes: {Estudiante.objects.count()}")
        print(f"  Profesores: {Profesor.objects.count()}")
        print(f"  Apoderados: {Apoderado.objects.count()}")
        print(f"  Cursos: {Curso.objects.count()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando datos: {e}")
        return False

def main():
    print("🚀 MIGRACIÓN A BASE DE DATOS POSTGRESQL")
    print("=" * 50)
    
    # 1. Verificar archivo .env
    if not verificar_env():
        return
    
    # 2. Verificar conexión
    if not verificar_conexion_postgresql():
        return
    
    # 3. Ejecutar migraciones
    if not ejecutar_migraciones():
        return
    
    # 4. Cargar backup
    if not cargar_backup():
        return
    
    # 5. Crear superuser
    crear_superuser()
    
    # 6. Verificar datos
    verificar_datos_migrados()
    
    print("\n" + "=" * 50)
    print("🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
    print("\n📋 VERIFICACIONES FINALES:")
    print("1. Inicia el servidor: python manage.py runserver")
    print("2. Ve al admin: http://localhost:8000/admin")
    print("3. Verifica que todos los datos estén presentes")
    print("4. Actualiza las credenciales de producción")

if __name__ == "__main__":
    main()
