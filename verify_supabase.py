import os
import sys
import django

print("Starting verification...")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from django.contrib.auth.models import User
from smapp.models import Estudiante, Profesor, Curso

from django.conf import settings
print(f"DB Engine: {settings.DATABASES['default']['ENGINE']}")
print(f"DB Name: {settings.DATABASES['default']['NAME']}")

print("--- VERIFICACIÓN DE DATOS EN SUPABASE ---")
print(f"Usuarios: {User.objects.count()}")
print(f"Estudiantes: {Estudiante.objects.count()}")
print(f"Profesores: {Profesor.objects.count()}")
print(f"Cursos: {Curso.objects.count()}")
print("-----------------------------------------")
