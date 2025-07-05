#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from smapp.models import Apoderado

# Listar todos los apoderados
apoderados = Apoderado.objects.all()
print(f"Total de apoderados: {apoderados.count()}")

for apoderado in apoderados:
    print(f"- {apoderado.primer_nombre} {apoderado.apellido_paterno} (RUT: {apoderado.numero_documento})")
