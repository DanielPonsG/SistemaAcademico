import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()
from smapp.models import HorarioCurso
print(f"Horarios count: {HorarioCurso.objects.count()}")
