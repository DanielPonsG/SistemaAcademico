#!/usr/bin/env python
"""
Script para verificar usuarios apoderados disponibles
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from smapp.models import Apoderado, Profesor

def check_apoderados():
    print("=== VERIFICANDO USUARIOS APODERADOS ===")
    
    apoderados = Apoderado.objects.all()[:10]
    print(f"Total de apoderados: {Apoderado.objects.count()}")
    
    for apo in apoderados:
        username = apo.user.username if apo.user else "Sin usuario"
        documento = apo.numero_documento if apo.numero_documento else "Sin documento"
        print(f"- {username} (Doc: {documento}) - {apo.get_nombre_completo()}")
    
    print("\n=== VERIFICANDO PROFESORES-APODERADOS ===")
    
    profesores = Profesor.objects.all()[:10]
    print(f"Total de profesores: {Profesor.objects.count()}")
    
    for prof in profesores:
        username = prof.user.username if prof.user else "Sin usuario"
        es_apoderado = hasattr(prof, 'apoderado_profile') and prof.apoderado_profile
        print(f"- {username} (Es apoderado: {es_apoderado})")

if __name__ == '__main__':
    check_apoderados()
