import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SAM.settings')
django.setup()

from smapp.models import Profesor
from smapp.forms import AnotacionForm

# Obtener primer profesor con asignaturas
profesor = Profesor.objects.filter(asignaturas__isnull=False).first()

if profesor:
    print(f"Profesor: {profesor.get_nombre_completo()}")
    print(f"Cursos asignados: {profesor.get_cursos_asignados().count()}")
    
    form = AnotacionForm(profesor=profesor)
    print(f"Cursos en formulario: {form.fields['curso'].queryset.count()}")
    print(f"Estudiantes en formulario: {form.fields['estudiante'].queryset.count()}")
    print(f"Estudiante requerido: {form.fields['estudiante'].required}")
    print("Prueba exitosa!")
else:
    print("No hay profesores con asignaturas")
