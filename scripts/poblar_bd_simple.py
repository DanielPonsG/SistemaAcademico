import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from django.contrib.auth.models import User
from smapp.models import Curso, Asignatura, Profesor

def asignar_asignaturas_a_cursos():
    """
    Script simple para asignar todas las asignaturas a todos los cursos existentes
    """
    print("Iniciando asignación de asignaturas a cursos...")
    
    # Obtener todos los cursos
    cursos = Curso.objects.all()
    print(f"Cursos encontrados: {cursos.count()}")
    
    # Obtener todas las asignaturas
    asignaturas = Asignatura.objects.all()
    print(f"Asignaturas encontradas: {asignaturas.count()}")
    
    if not cursos.exists():
        print("ADVERTENCIA: No hay cursos en la base de datos. Primero crea algunos cursos.")
        return
    
    if not asignaturas.exists():
        print("ADVERTENCIA: No hay asignaturas en la base de datos. Creando asignaturas básicas...")
        crear_asignaturas_basicas()
        asignaturas = Asignatura.objects.all()
    
    # Asignar todas las asignaturas a todos los cursos
    for curso in cursos:
        print(f"\nProcesando curso: {curso}")
        asignaturas_actuales = curso.asignaturas.count()
        print(f"  Asignaturas actuales: {asignaturas_actuales}")
        
        # Agregar todas las asignaturas al curso
        for asignatura in asignaturas:
            if asignatura not in curso.asignaturas.all():
                curso.asignaturas.add(asignatura)
                print(f"  + Asignada: {asignatura.nombre}")
        
        print(f"  Total asignaturas ahora: {curso.asignaturas.count()}")
    
    print("\n[OK] Proceso completado exitosamente!")
    print("\nResumen:")
    for curso in cursos:
        print(f"  {curso}: {curso.asignaturas.count()} asignaturas")

def crear_asignaturas_basicas():
    """Crea asignaturas básicas si no existen"""
    print("\nCreando asignaturas básicas...")
    
    # Obtener o crear profesores para asignar
    profesores = Profesor.objects.all()
    if not profesores.exists():
        print("ADVERTENCIA: No hay profesores. Las asignaturas se crearan sin profesor responsable.")
        profesor_default = None
    else:
        profesor_default = profesores.first()
    
    asignaturas_data = [
        {'nombre': 'Matemáticas', 'codigo': 'MAT', 'descripcion': 'Matemáticas generales'},
        {'nombre': 'Lenguaje y Comunicación', 'codigo': 'LEN', 'descripcion': 'Lenguaje y Literatura'},
        {'nombre': 'Historia y Geografía', 'codigo': 'HIS', 'descripcion': 'Historia, Geografía y Ciencias Sociales'},
        {'nombre': 'Ciencias Naturales', 'codigo': 'CIE', 'descripcion': 'Biología, Química y Física'},
        {'nombre': 'Inglés', 'codigo': 'ING', 'descripcion': 'Idioma Inglés'},
        {'nombre': 'Educación Física', 'codigo': 'EFI', 'descripcion': 'Educación Física y Salud'},
        {'nombre': 'Artes Visuales', 'codigo': 'ART', 'descripcion': 'Artes Visuales'},
        {'nombre': 'Música', 'codigo': 'MUS', 'descripcion': 'Educación Musical'},
        {'nombre': 'Tecnología', 'codigo': 'TEC', 'descripcion': 'Educación Tecnológica'},
    ]
    
    for data in asignaturas_data:
        asignatura, created = Asignatura.objects.get_or_create(
            codigo_asignatura=data['codigo'],
            defaults={
                'nombre': data['nombre'],
                'descripcion': data['descripcion'],
                'profesor_responsable': profesor_default
            }
        )
        if created:
            print(f"  + Creada: {asignatura.nombre}")
        else:
            print(f"  - Ya existe: {asignatura.nombre}")

if __name__ == '__main__':
    asignar_asignaturas_a_cursos()
