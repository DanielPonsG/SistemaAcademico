#!/usr/bin/env python3
"""
Script simple para verificar usuario zxc
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from django.contrib.auth.models import User
from smapp.models import Apoderado

try:
    user = User.objects.get(username='zxc')
    print(f"✅ Usuario encontrado: {user.get_full_name()}")
    print(f"📧 Email: {user.email}")
    
    # Verificar perfil
    if hasattr(user, 'perfil'):
        print(f"✅ Tiene perfil: {user.perfil.tipo_usuario}")
    else:
        print("❌ No tiene perfil")
        
    # Verificar apoderado
    if hasattr(user, 'apoderado'):
        print(f"✅ Tiene apoderado: {user.apoderado.codigo_apoderado}")
    else:
        print("❌ No tiene apoderado")
        
    # Buscar si existe un apoderado sin usuario asignado que podría ser de este usuario
    apoderados_sin_usuario = Apoderado.objects.filter(user__isnull=True)
    print(f"\n📋 Apoderados disponibles sin usuario:")
    for apoderado in apoderados_sin_usuario:
        print(f"   • {apoderado.codigo_apoderado} - {apoderado.get_nombre_completo()}")
        
except User.DoesNotExist:
    print("❌ Usuario zxc no encontrado")
