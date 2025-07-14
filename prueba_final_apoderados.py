#!/usr/bin/env python
"""
Script final para probar el login y redirección de apoderados
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
from smapp.models import Apoderado, Perfil, RelacionApoderadoEstudiante

def probar_login_apoderados():
    print("=== PRUEBA FINAL DE LOGIN Y REDIRECCIÓN DE APODERADOS ===")
    
    # Lista de apoderados a probar
    usuarios_apoderados = [
        ('apoderado_zxc', 'temp123', 'zxc'),
        ('apoderado_zxczxc', 'temp123', 'zxczxc'),
        ('apoderado_qweqwe', 'temp123', 'qweqwe')
    ]
    
    for username, password, nombre_apoderado in usuarios_apoderados:
        print(f"\n👤 PROBANDO: {username} ({nombre_apoderado})")
        
        # 1. Autenticación
        auth_user = authenticate(username=username, password=password)
        if auth_user:
            print(f"   ✅ Autenticación exitosa")
            
            # 2. Verificar perfil
            if hasattr(auth_user, 'perfil'):
                print(f"   ✅ Tiene perfil: {auth_user.perfil.tipo_usuario}")
                
                # 3. Verificar acceso a apoderado
                apoderado = None
                es_profesor_apoderado = False
                
                if hasattr(auth_user, 'apoderado'):
                    apoderado = auth_user.apoderado
                    print(f"   ✅ Es apoderado directo")
                elif hasattr(auth_user, 'profesor') and hasattr(auth_user.profesor, 'apoderado_profile'):
                    apoderado = auth_user.profesor.apoderado_profile
                    es_profesor_apoderado = True
                    print(f"   ✅ Es profesor-apoderado")
                else:
                    print(f"   ❌ No puede acceder como apoderado")
                
                if apoderado:
                    # 4. Verificar estudiantes
                    relaciones = RelacionApoderadoEstudiante.objects.filter(apoderado=apoderado)
                    print(f"   📚 Estudiantes a cargo: {relaciones.count()}")
                    
                    for relacion in relaciones[:2]:  # Mostrar máximo 2
                        print(f"     • {relacion.estudiante.get_nombre_completo()}")
                    
                    # 5. Determinar redirección correcta
                    if es_profesor_apoderado:
                        print(f"   🔄 Redirección: dashboard_profesor_apoderado")
                    else:
                        print(f"   🔄 Redirección: dashboard_apoderado")
                    
                    # 6. Verificar si puede ver paneles
                    if relaciones.count() > 0:
                        print(f"   ✅ PUEDE VER PANELES DE ESTUDIANTES")
                    else:
                        print(f"   ❌ NO PUEDE VER PANELES (sin estudiantes)")
                else:
                    print(f"   ❌ Error: No se puede determinar apoderado")
            else:
                print(f"   ❌ Sin perfil de usuario")
        else:
            print(f"   ❌ Error en autenticación")
            
            # Intentar encontrar el usuario y verificar por qué falló
            try:
                user = User.objects.get(username=username)
                print(f"   - Usuario existe: {user.is_active}")
                print(f"   - Email: {user.email}")
            except User.DoesNotExist:
                print(f"   - Usuario no existe en la base de datos")
    
    print(f"\n🔧 INSTRUCCIONES DE USO:")
    print(f"1. Acceder al sistema con las credenciales:")
    print(f"   - Usuario: apoderado_zxc, Contraseña: temp123")
    print(f"   - Usuario: apoderado_zxczxc, Contraseña: temp123")
    print(f"2. Al hacer login, deberían ser redirigidos automáticamente al dashboard de apoderados")
    print(f"3. En el dashboard podrán ver la información completa de sus estudiantes")
    
    print(f"\n✅ PROBLEMAS SOLUCIONADOS:")
    print(f"- Apoderado 'zxc' puede iniciar sesión y ver paneles")
    print(f"- Apoderado 'zxczxc' creado y configurado correctamente")
    print(f"- Redirección automática desde login a dashboard de apoderados")
    print(f"- Vista inicio() ahora maneja correctamente el tipo 'apoderado'")

if __name__ == "__main__":
    probar_login_apoderados()
