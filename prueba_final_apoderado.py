#!/usr/bin/env python
import os
import django
import sys

# Añadir el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from smapp.models import Apoderado, ApoderadoEstudiante
from smapp.forms import ApoderadoForm

def test_completo_apoderado():
    print("=== PRUEBA COMPLETA DE FUNCIONALIDAD APODERADO ===")
    
    # 0. Crear un usuario admin y hacer login
    admin_user, created = User.objects.get_or_create(
        username='admin_test',
        defaults={
            'email': 'admin@test.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print("✓ Usuario admin creado")
    else:
        print("✓ Usuario admin ya existe")
    
    # 1. Verificar que el formulario se renderiza correctamente
    client = Client()
    
    # Hacer login
    login_success = client.login(username='admin_test', password='admin123')
    print(f"Login exitoso: {login_success}")
    
    response = client.get('/agregar?tipo=apoderado')
    print(f"GET /agregar?tipo=apoderado: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ La página se carga correctamente")
        # Verificar que contiene los elementos esperados
        content = response.content.decode('utf-8')
        if 'name="rut"' in content:
            print("✓ Campo RUT presente en el formulario")
        if 'name="nombre"' in content:
            print("✓ Campo nombre presente en el formulario")
        if 'name="apellido"' in content:
            print("✓ Campo apellido presente en el formulario")
        if 'name="tipo"' in content and 'value="apoderado"' in content:
            print("✓ Campo tipo oculto presente con valor correcto")
    else:
        print(f"✗ Error al cargar la página: {response.status_code}")
        return False
    
    # 2. Contar apoderados antes de la prueba
    apoderados_antes = Apoderado.objects.count()
    usuarios_antes = User.objects.count()
    print(f"\nApoderados antes de la prueba: {apoderados_antes}")
    print(f"Usuarios antes de la prueba: {usuarios_antes}")
    
    # 3. Realizar POST con datos válidos (sin usuario)
    datos_sin_usuario = {
        'tipo': 'apoderado',
        # Campos de Persona (obligatorios)
        'primer_nombre': 'Juan Carlos',
        'apellido_paterno': 'González',
        'apellido_materno': 'Pérez',
        'tipo_documento': 'CC',
        'numero_documento': '11111111-1',  # RUT válido
        'fecha_nacimiento': '1980-05-15',
        'genero': 'M',
        'email': 'juan.gonzalez@email.com',
        # Campos opcionales de Persona
        'telefono': '+56912345678',
        'direccion': 'Av. Principal 123',
        # Campos de Apoderado (obligatorios)
        'tipo_apoderado': 'padre',
        'estado_civil': 'casado',
    }
    
    print("\n--- Prueba 1: Apoderado sin usuario ---")
    response = client.post('/agregar', datos_sin_usuario)
    print(f"POST /agregar (sin usuario): {response.status_code}")
    
    apoderados_despues = Apoderado.objects.count()
    usuarios_despues = User.objects.count()
    
    if apoderados_despues == apoderados_antes + 1:
        print("✓ Apoderado creado exitosamente")
        apoderado = Apoderado.objects.filter(numero_documento='11111111-1').first()
        if apoderado:
            print(f"✓ Apoderado encontrado: {apoderado.primer_nombre} {apoderado.apellido_paterno}")
            print(f"  - RUT: {apoderado.numero_documento}")
            print(f"  - Email: {apoderado.email}")
            print(f"  - Teléfono: {apoderado.telefono}")
            print(f"  - Usuario asociado: {apoderado.user}")
    else:
        print(f"✗ Error: Esperado {apoderados_antes + 1}, actual {apoderados_despues}")
    
    if usuarios_despues == usuarios_antes:
        print("✓ No se creó usuario adicional (correcto)")
    else:
        print(f"✗ Se creó usuario inesperadamente: {usuarios_despues} vs {usuarios_antes}")
    
    # 4. Realizar POST con datos válidos (con usuario)
    datos_con_usuario = {
        'tipo': 'apoderado',
        # Campos de Persona (obligatorios)
        'primer_nombre': 'María Elena',
        'apellido_paterno': 'Rodríguez',
        'apellido_materno': 'Silva',
        'tipo_documento': 'CC',
        'numero_documento': '22222222-2',  # RUT válido
        'fecha_nacimiento': '1975-12-20',
        'genero': 'F',
        'email': 'maria.rodriguez@email.com',
        # Campos opcionales de Persona
        'telefono': '+56987654321',
        'direccion': 'Calle Secundaria 456',
        # Campos de Apoderado (obligatorios)
        'tipo_apoderado': 'madre',
        'estado_civil': 'soltero',
        # Campos de usuario
        'crear_usuario': 'on',
        'username': 'mrodriguez',
        'password': 'password123',
        'password_confirm': 'password123',
    }
    
    print("\n--- Prueba 2: Apoderado con usuario ---")
    response = client.post('/agregar', datos_con_usuario)
    print(f"POST /agregar (con usuario): {response.status_code}")
    
    apoderados_final = Apoderado.objects.count()
    usuarios_final = User.objects.count()
    
    if apoderados_final == apoderados_despues + 1:
        print("✓ Segundo apoderado creado exitosamente")
        apoderado = Apoderado.objects.filter(numero_documento='22222222-2').first()
        if apoderado:
            print(f"✓ Apoderado encontrado: {apoderado.primer_nombre} {apoderado.apellido_paterno}")
            print(f"  - RUT: {apoderado.numero_documento}")
            print(f"  - Email: {apoderado.email}")
            print(f"  - Usuario asociado: {apoderado.user}")
            if apoderado.user:
                print(f"  - Username: {apoderado.user.username}")
    else:
        print(f"✗ Error: Esperado {apoderados_despues + 1}, actual {apoderados_final}")
    
    if usuarios_final == usuarios_despues + 1:
        print("✓ Usuario creado correctamente")
        usuario = User.objects.filter(username='mrodriguez').first()
        if usuario:
            print(f"✓ Usuario encontrado: {usuario.username}")
    else:
        print(f"✗ Error en creación de usuario: {usuarios_final} vs {usuarios_despues + 1}")
    
    # 5. Verificar formulario directamente
    print("\n--- Prueba 3: Validación directa del formulario ---")
    form = ApoderadoForm(datos_sin_usuario)
    if form.is_valid():
        print("✓ Formulario válido para datos sin usuario")
    else:
        print(f"✗ Formulario inválido: {form.errors}")
    
    form_con_usuario = ApoderadoForm(datos_con_usuario)
    if form_con_usuario.is_valid():
        print("✓ Formulario válido para datos con usuario")
    else:
        print(f"✗ Formulario inválido: {form_con_usuario.errors}")
    
    print(f"\n=== RESUMEN ===")
    print(f"Total apoderados: {Apoderado.objects.count()}")
    print(f"Total usuarios: {User.objects.count()}")
    print("Prueba completa finalizada")
    
    return True

if __name__ == "__main__":
    test_completo_apoderado()
