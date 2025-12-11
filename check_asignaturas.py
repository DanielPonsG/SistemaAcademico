import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()
from smapp.models import Asignatura
print([a.nombre for a in Asignatura.objects.all()])