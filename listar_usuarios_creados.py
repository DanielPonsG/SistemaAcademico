import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from django.contrib.auth.models import User
from smapp.models import Profesor, Estudiante, Apoderado

def listar_usuarios():
    print("="*60)
    print("LISTADO DE USUARIOS PARA ACCESO")
    print("="*60)
    
    print("\n--- ADMINISTRADORES ---")
    admins = User.objects.filter(is_superuser=True)
    for admin in admins:
        print(f"Usuario: {admin.username} | Contraseña: (la que configuraste, ej: admin123)")

    print("\n--- PROFESORES (Muestra 5) ---")
    profesores = Profesor.objects.all()[:5]
    for p in profesores:
        if p.user:
            print(f"Usuario: {p.user.username} | Contraseña: profesor123 | Nombre: {p.primer_nombre} {p.apellido_paterno}")

    print("\n--- ESTUDIANTES (Muestra 5) ---")
    estudiantes = Estudiante.objects.all()[:5]
    for e in estudiantes:
        if e.user:
            print(f"Usuario: {e.user.username} | Contraseña: estudiante123 | Nombre: {e.primer_nombre} {e.apellido_paterno}")

    print("\n--- APODERADOS (Muestra 5) ---")
    apoderados = Apoderado.objects.all()[:5]
    for a in apoderados:
        if a.user:
            print(f"Usuario: {a.user.username} | Contraseña: apoderado123 | Nombre: {a.primer_nombre} {a.apellido_paterno}")
            
    print("\n" + "="*60)
    print(f"TOTALES:")
    print(f"Profesores: {Profesor.objects.count()}")
    print(f"Estudiantes: {Estudiante.objects.count()}")
    print(f"Apoderados: {Apoderado.objects.count()}")
    print("="*60)

if __name__ == "__main__":
    listar_usuarios()
