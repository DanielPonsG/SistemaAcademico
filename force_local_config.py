#!/usr/bin/env python
import os
import sys

# Forzar configuración local sin decouple
print("=== CONFIGURACIÓN MANUAL SIN CACHE ===")

# Configurar variables de entorno manualmente
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_NAME'] = 'sam'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'inacap2024'
os.environ['DB_PORT'] = '5432'
os.environ['DB_SSL_MODE'] = 'disable'

print("Variables de entorno configuradas:")
print(f"DB_HOST: {os.environ.get('DB_HOST')}")
print(f"DB_NAME: {os.environ.get('DB_NAME')}")
print(f"DB_USER: {os.environ.get('DB_USER')}")
print(f"DB_PASSWORD: {os.environ.get('DB_PASSWORD')}")
print(f"DB_PORT: {os.environ.get('DB_PORT')}")
print(f"DB_SSL_MODE: {os.environ.get('DB_SSL_MODE')}")

# Ahora probar Django
print("\n=== PROBANDO CONFIGURACIÓN DJANGO ===")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')

import django
django.setup()

from django.conf import settings
print(f"DATABASES Django: {settings.DATABASES}")

# Probar conexión
try:
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    print("✅ Django puede conectarse a PostgreSQL local!")
    
except Exception as e:
    print(f"❌ Error Django: {e}")
