import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()
from smapp.models import AsistenciaAlumno
print(f"Total asistencias: {AsistenciaAlumno.objects.count()}")
