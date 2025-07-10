#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from smapp.models import EventoCalendario, Curso
from django.contrib.auth.models import User
import json

print("📋 REPORTE COMPLETO DEL CALENDARIO")
print("=" * 60)

# 1. Verificar eventos
eventos = EventoCalendario.objects.all()
print(f"📊 EVENTOS:")
print(f"   Total: {eventos.count()}")

if eventos.exists():
    print("   📅 Lista completa:")
    for evento in eventos:
        print(f"     • ID: {evento.id}")
        print(f"       Título: {evento.titulo}")
        print(f"       Fecha: {evento.fecha}")
        print(f"       Tipo: {evento.tipo_evento}")
        print(f"       Color: {getattr(evento, 'color_por_tipo', 'N/A')}")
        print(f"       Para todos: {evento.para_todos_los_cursos}")
        print()

# 2. Verificar usuarios
print(f"👥 USUARIOS:")
usuarios = User.objects.all()
print(f"   Total: {usuarios.count()}")
superusers = User.objects.filter(is_superuser=True)
print(f"   Superusuarios: {superusers.count()}")

# 3. Verificar cursos
print(f"🎓 CURSOS:")
cursos = Curso.objects.all()
print(f"   Total: {cursos.count()}")

# 4. Generar JSON para FullCalendar
print(f"🎯 JSON PARA FULLCALENDAR:")
eventos_json = []
for evento in eventos:
    evento_dict = {
        'id': evento.id,
        'title': evento.titulo,
        'start': evento.fecha.isoformat(),
        'description': evento.descripcion or '',
        'backgroundColor': getattr(evento, 'color_por_tipo', '#007bff'),
        'borderColor': getattr(evento, 'color_por_tipo', '#007bff'),
        'textColor': '#fff',
        'extendedProps': {
            'description': evento.descripcion or '',
            'responsable': evento.creado_por.first_name if evento.creado_por and evento.creado_por.first_name else (evento.creado_por.username if evento.creado_por else 'Sistema'),
            'tipo': evento.get_tipo_evento_display(),
            'prioridad': evento.get_prioridad_display()
        }
    }
    eventos_json.append(evento_dict)

print(f"   Eventos en JSON: {len(eventos_json)}")

# Verificar que el JSON es válido
try:
    json_string = json.dumps(eventos_json, ensure_ascii=False, indent=2)
    json.loads(json_string)  # Verificar que se puede parsear de vuelta
    print("   ✅ JSON válido")
    
    # Mostrar primer evento como ejemplo
    if eventos_json:
        print("   📝 Ejemplo del primer evento:")
        print(json.dumps(eventos_json[0], ensure_ascii=False, indent=4))
        
except Exception as e:
    print(f"   ❌ Error en JSON: {e}")

# 5. Verificar el método color_por_tipo
print(f"\n🎨 VERIFICAR COLORES:")
if eventos.exists():
    for evento in eventos[:3]:  # Solo los primeros 3
        try:
            color = evento.color_por_tipo
            print(f"   {evento.titulo}: {color}")
        except Exception as e:
            print(f"   {evento.titulo}: Error - {e}")

print(f"\n✅ Reporte completado")
print("=" * 60)
