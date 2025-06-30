#!/usr/bin/env python
"""
Script para simular exactamente lo que hace la vista web
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from django.test import Client, RequestFactory
from django.contrib.auth.models import User
from smapp.models import Perfil, Profesor
from smapp.views import crear_anotacion

def simular_creacion_anotacion():
    """Simular la creación de una anotación desde la vista web"""
    print("=== SIMULANDO CREACIÓN DE ANOTACIÓN VÍA WEB ===")
    
    # Obtener usuario profesor
    user = User.objects.get(username='prof_matematicas')
    print(f"Usuario: {user.username}")
    
    # Crear cliente
    client = Client()
    client.force_login(user)
    
    # 1. Probar GET (cargar formulario)
    print("\n1. Probando carga del formulario...")
    response = client.get('/anotaciones/crear/')
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ Formulario cargado correctamente")
    else:
        print(f"❌ Error al cargar formulario: {response.status_code}")
        print(response.content.decode()[:500])
        return
    
    # 2. Probar AJAX para obtener estudiantes
    print("\n2. Probando carga AJAX de estudiantes...")
    response = client.get('/ajax/obtener-estudiantes-curso/?curso_id=1')
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        import json
        data = json.loads(response.content)
        print(f"✓ AJAX funcionando: {len(data.get('estudiantes', []))} estudiantes encontrados")
        for est in data.get('estudiantes', []):
            print(f"  - {est['nombre']} (ID: {est['id']})")
    else:
        print(f"❌ Error en AJAX: {response.status_code}")
        print(response.content.decode())
        return
    
    # 3. Probar POST (enviar formulario)
    print("\n3. Probando envío del formulario...")
    
    datos_post = {
        'curso': '1',
        'estudiante': '1',
        'tipo': 'positiva',
        'categoria': 'comportamiento',
        'titulo': 'Prueba desde script',
        'descripcion': 'Esta es una prueba de anotación desde el script de simulación.',
        'puntos': '5',
        'es_grave': False,
        'requiere_atencion_apoderado': False,
    }
    
    response = client.post('/anotaciones/crear/', datos_post)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 302:
        print("✓ Anotación creada exitosamente (redirección)")
        print(f"Redirigiendo a: {response.url}")
    elif response.status_code == 200:
        print("❌ Formulario devuelto con errores")
        # Buscar errores en el contenido HTML
        content = response.content.decode()
        if 'Errores en el formulario:' in content:
            print("Se encontraron errores específicos en el formulario")
        if 'Por favor corrige los errores' in content:
            print("Mensaje de error general encontrado")
    else:
        print(f"❌ Error inesperado: {response.status_code}")
        print(response.content.decode()[:500])
    
    print("\n=== FIN DE SIMULACIÓN ===")

if __name__ == '__main__':
    simular_creacion_anotacion()
