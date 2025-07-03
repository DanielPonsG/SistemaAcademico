#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

def simular_flujo_usuario():
    print("=== SIMULACIÓN DEL FLUJO DE USUARIO PASO A PASO ===")
    
    try:
        client = Client()
        
        print("👤 PASO 1: Usuario intenta hacer login")
        print("  Credenciales: username='asd', password='123'")
        
        login_response = client.post('/login/', {
            'username': 'asd',
            'password': '123'
        })
        
        if login_response.status_code == 302:
            print("✅ Login exitoso, redirigido")
            
            print("\n📊 PASO 2: Usuario accede a 'Ver Notas'")
            response_inicial = client.get('/notas/ver/')
            
            if response_inicial.status_code == 200:
                content_inicial = response_inicial.content.decode('utf-8')
                
                # Buscar la tabla de resumen
                if "Mis Notas por Asignatura" in content_inicial:
                    print("✅ Vista de resumen cargada correctamente")
                    
                    # Buscar enlaces de "Ver detalles"
                    if "Ver detalles" in content_inicial:
                        count_detalles = content_inicial.count("Ver detalles")
                        print(f"📋 Enlaces 'Ver detalles' encontrados: {count_detalles}")
                        
                        # Buscar específicamente el enlace para Matemáticas
                        if "asignatura_id=2" in content_inicial:
                            print("🔗 Enlace para Matemáticas (ID=2) encontrado")
                        else:
                            print("❌ Enlace para Matemáticas NO encontrado")
                            
                        # Mostrar promedios por asignatura
                        lines = content_inicial.split('\n')
                        for i, line in enumerate(lines):
                            if "Matemáticas" in line:
                                print(f"📌 Línea con Matemáticas: {line.strip()}")
                                # Buscar las siguientes 5 líneas para ver el promedio
                                for j in range(1, 6):
                                    if i+j < len(lines):
                                        next_line = lines[i+j].strip()
                                        if next_line and ("badge" in next_line or "Ver detalles" in next_line):
                                            print(f"     {next_line}")
                    else:
                        print("❌ No se encontraron enlaces 'Ver detalles'")
                else:
                    print("❌ Vista de resumen no cargada correctamente")
                
                print("\n🔍 PASO 3: Usuario hace clic en 'Ver detalles' de Matemáticas")
                response_detalles = client.get('/notas/ver/?asignatura_id=2')
                
                if response_detalles.status_code == 200:
                    content_detalles = response_detalles.content.decode('utf-8')
                    
                    print("✅ Vista de detalles cargada correctamente")
                    
                    # Verificar el título de la vista
                    if "Mis Notas - Matemáticas" in content_detalles:
                        print("✅ Título correcto: 'Mis Notas - Matemáticas'")
                    
                    # Contar evaluaciones en el encabezado
                    count_th = content_detalles.count('<th class="text-center">')
                    print(f"📊 Columnas en encabezado: {count_th}")
                    
                    # Contar evaluaciones por nombre
                    count_eval = content_detalles.count('Evaluación de Ejemplo')
                    print(f"📝 'Evaluación de Ejemplo' aparece: {count_eval} veces")
                    
                    # Verificar notas específicas
                    if "4,60" in content_detalles or "4.60" in content_detalles:
                        print("✅ Nota 4.60 visible")
                    else:
                        print("❌ Nota 4.60 NO visible")
                        
                    if "5,90" in content_detalles or "5.90" in content_detalles:
                        print("✅ Nota 5.90 visible")
                    else:
                        print("❌ Nota 5.90 NO visible")
                    
                    # Verificar estructura de la tabla
                    if content_detalles.count('<td class="text-center nota-celda">') >= 2:
                        print("✅ Al menos 2 celdas de notas encontradas")
                    else:
                        print("❌ Menos de 2 celdas de notas encontradas")
                    
                    # Guardar para inspección manual
                    with open('flujo_usuario_detalles.html', 'w', encoding='utf-8') as f:
                        f.write(content_detalles)
                    print("💾 HTML de detalles guardado en flujo_usuario_detalles.html")
                    
                else:
                    print(f"❌ Error al cargar detalles: {response_detalles.status_code}")
            else:
                print(f"❌ Error al cargar vista inicial: {response_inicial.status_code}")
        else:
            print(f"❌ Login falló: {login_response.status_code}")
            
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()

print("=" * 60)
print("GUÍA PARA EL USUARIO:")
print("1. Abrir http://localhost:8000")
print("2. Hacer login con:")
print("   - Usuario: asd")
print("   - Password: 123")
print("3. Ir a 'Ver Notas'")
print("4. Hacer clic en 'Ver detalles' de Matemáticas")
print("5. Deberías ver 2 evaluaciones: 4,60 y 5,90")
print("=" * 60)

if __name__ == "__main__":
    simular_flujo_usuario()
