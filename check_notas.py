import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()
from smapp.models import Calificacion, Inscripcion, Estudiante

count = Calificacion.objects.count()
print(f"Total calificaciones: {count}")

if count > 0:
    last = Calificacion.objects.last()
    print(f"Última calificación: {last.puntaje} - {last.nombre_evaluacion} para {last.inscripcion.estudiante.user.first_name}")
