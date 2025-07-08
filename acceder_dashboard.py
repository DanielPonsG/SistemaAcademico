#!/usr/bin/env python
"""
Script para hacer login automático y acceder al dashboard
"""
import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from django.test import Client
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User

def crear_sesion_automatica():
    """Crea una sesión automática para acceder al dashboard"""
    
    print("🔐 CREANDO SESIÓN AUTOMÁTICA PARA DASHBOARD")
    print("="*50)
    
    try:
        # Verificar que el usuario zxc existe
        user = User.objects.get(username='zxc')
        print(f"✅ Usuario encontrado: {user.username}")
        
        # Crear cliente y hacer login
        client = Client()
        login_success = client.login(username='zxc', password='zxc')
        
        if login_success:
            print("✅ Login exitoso")
            
            # Obtener la sesión
            session_key = client.session.session_key
            print(f"✅ Sesión creada: {session_key}")
            
            # URLs de acceso
            urls = {
                "🏠 Dashboard Principal": "http://127.0.0.1:8000/dashboard-apoderado/",
                "🔑 Login": "http://127.0.0.1:8000/login/",
                "📊 Inicio": "http://127.0.0.1:8000/inicio/",
            }
            
            print("\n📍 URLs DE ACCESO:")
            for nombre, url in urls.items():
                print(f"   {nombre}: {url}")
            
            print("\n🎯 CREDENCIALES:")
            print("   Usuario: zxc")
            print("   Contraseña: zxc")
            
            print("\n✨ CARACTERÍSTICAS DEL DASHBOARD:")
            print("   🎨 Menú lateral con diseño moderno")
            print("   🔄 Selector de estudiantes ultra visible")
            print("   📱 Diseño responsive y adaptativo")
            print("   ⚡ Cambio dinámico de contenido")
            print("   🎭 Animaciones y efectos visuales")
            
            return True
        else:
            print("❌ Error en el login")
            return False
            
    except User.DoesNotExist:
        print("❌ Usuario zxc no encontrado")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    crear_sesion_automatica()
