#!/usr/bin/env python
"""
Script para verificar el estado del apoderado 'zxc'
"""
import os
import django
import sys

# Agregar el directorio del proyecto al path
project_path = r'c:\Users\Danie\Desktop\Estudios\SAM-main'
sys.path.append(project_path)
os.chdir(project_path)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from smapp.models import Apoderado, Perfil

def check_apoderado_zxc():
    print("=== VERIFICACIÓN DEL APODERADO 'ZXC' ===")
    
    # Buscar apoderado por nombre
    apoderados_zxc = Apoderado.objects.filter(primer_nombre__icontains='zxc')
    
    if not apoderados_zxc.exists():
        print("❌ No se encontró ningún apoderado con nombre 'zxc'")
        
        # Buscar por código
        apoderados_por_codigo = Apoderado.objects.filter(codigo_apoderado__icontains='zxc')
        if apoderados_por_codigo.exists():
            print("✅ Encontrado apoderado por código:")
            for apoderado in apoderados_por_codigo:
                print(f"   - {apoderado.primer_nombre} {apoderado.apellido_paterno} (Código: {apoderado.codigo_apoderado})")
        else:
            print("❌ No se encontró ningún apoderado con código 'zxc'")
        
        return
    
    for apoderado in apoderados_zxc:
        print(f"📋 Apoderado encontrado:")
        print(f"   - Nombre: {apoderado.primer_nombre} {apoderado.apellido_paterno}")
        print(f"   - RUT: {apoderado.numero_documento}")
        print(f"   - Código: {apoderado.codigo_apoderado}")
        print(f"   - Email: {apoderado.email}")
        
        # Verificar si tiene usuario asociado
        if apoderado.user:
            user = apoderado.user
            print(f"✅ Tiene usuario asociado:")
            print(f"   - Username: {user.username}")
            print(f"   - Email: {user.email}")
            print(f"   - Activo: {user.is_active}")
            print(f"   - Staff: {user.is_staff}")
            
            # Verificar perfil
            try:
                perfil = user.perfil
                print(f"   - Tipo de usuario: {perfil.tipo_usuario}")
            except:
                print("   - ❌ No tiene perfil asociado")
            
            # Probar autenticación
            print(f"\n🔐 Probando autenticación...")
            passwords_to_try = ['temp123', 'zxc', '123456', 'admin', user.username]
            
            for password in passwords_to_try:
                auth_user = authenticate(username=user.username, password=password)
                if auth_user:
                    print(f"✅ Autenticación exitosa con contraseña: {password}")
                    break
                else:
                    print(f"❌ Falló con contraseña: {password}")
            else:
                print("❌ No se pudo autenticar con ninguna contraseña común")
                print("🔧 Estableciendo contraseña temporal 'temp123'...")
                user.set_password('temp123')
                user.save()
                
                # Probar de nuevo
                auth_user = authenticate(username=user.username, password='temp123')
                if auth_user:
                    print("✅ Contraseña temporal establecida correctamente")
                else:
                    print("❌ Error: aún no se puede autenticar")
        else:
            print("❌ No tiene usuario asociado")
            print("🔧 Creando usuario para este apoderado...")
            
            # Crear usuario
            username = f"apoderado_{apoderado.codigo_apoderado}"
            try:
                user = User.objects.create_user(
                    username=username,
                    email=apoderado.email or '',
                    password='temp123',
                    first_name=apoderado.primer_nombre,
                    last_name=apoderado.apellido_paterno
                )
                
                # Asociar usuario al apoderado
                apoderado.user = user
                apoderado.save()
                
                # Crear perfil
                Perfil.objects.create(user=user, tipo_usuario='apoderado')
                
                print(f"✅ Usuario creado exitosamente:")
                print(f"   - Username: {username}")
                print(f"   - Contraseña: temp123")
                
                # Probar autenticación
                auth_user = authenticate(username=username, password='temp123')
                if auth_user:
                    print("✅ Autenticación exitosa con nuevo usuario")
                else:
                    print("❌ Error: no se puede autenticar con nuevo usuario")
                    
            except Exception as e:
                print(f"❌ Error creando usuario: {e}")

if __name__ == "__main__":
    check_apoderado_zxc()
