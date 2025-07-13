#!/usr/bin/env python
"""
Script para listar usuarios con permisos administrativos
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from smapp.models import Perfil

def listar_admins():
    print("=== Usuarios con Permisos Administrativos ===")
    
    print("\n1. Superusuarios:")
    superusers = User.objects.filter(is_superuser=True)
    for user in superusers:
        print(f"   - {user.username} ({user.get_full_name()})")
        print(f"     Email: {user.email}")
        try:
            perfil = user.perfil
            print(f"     Perfil: {perfil.tipo_usuario} - {perfil.cargo}")
        except:
            print(f"     Sin perfil asignado")
        print()
    
    print("2. Usuarios con perfil de director:")
    directores = Perfil.objects.filter(tipo_usuario='director')
    for perfil in directores:
        user = perfil.user
        print(f"   - {user.username} ({user.get_full_name()})")
        print(f"     Email: {user.email}")
        print(f"     Cargo: {perfil.cargo}")
        print(f"     Superusuario: {'Sí' if user.is_superuser else 'No'}")
        print()
    
    print("3. Staff users:")
    staff = User.objects.filter(is_staff=True)
    for user in staff:
        print(f"   - {user.username} ({user.get_full_name()})")
        print(f"     Email: {user.email}")
        print()

if __name__ == "__main__":
    listar_admins()
