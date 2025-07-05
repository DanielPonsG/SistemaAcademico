#!/usr/bin/env python
"""
Script para agregar más estudiantes y calificaciones para una mejor demostración del ranking
"""
import os
import sys
import django
from decimal import Decimal
import random

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from smapp.models import (
    Estudiante, Curso, Asignatura, Grupo, Calificacion, 
    Inscripcion, PeriodoAcademico, Profesor
)
from django.contrib.auth.models import User
from datetime import date

def agregar_mas_estudiantes():
    print("🚀 Agregando más estudiantes para el ranking...")
    
    # Obtener el curso creado anteriormente
    curso = Curso.objects.filter(nivel='1M', paralelo='A', anio=2025).first()
    if not curso:
        print("❌ No se encontró el curso 1° Medio A 2025")
        return
    
    print(f"✅ Curso encontrado: {curso}")
    
    # Obtener los grupos
    periodo = PeriodoAcademico.objects.filter(nombre="Año Escolar 2025").first()
    grupos = Grupo.objects.filter(periodo_academico=periodo)
    
    if not grupos.exists():
        print("❌ No se encontraron grupos")
        return
    
    print(f"✅ Grupos encontrados: {grupos.count()}")
    
    # Crear estudiantes adicionales con códigos únicos
    estudiantes_adicionales = [
        {'nombre': 'Javiera', 'apellido': 'Pérez', 'numero_documento': '20111222-3', 'codigo': 'EST011'},
        {'nombre': 'Francisco', 'apellido': 'Sánchez', 'numero_documento': '20111333-4', 'codigo': 'EST012'},
        {'nombre': 'Isidora', 'apellido': 'Rivera', 'numero_documento': '20111444-5', 'codigo': 'EST013'},
        {'nombre': 'Benjamín', 'apellido': 'Flores', 'numero_documento': '20111555-6', 'codigo': 'EST014'},
        {'nombre': 'Constanza', 'apellido': 'Muñoz', 'numero_documento': '20111666-7', 'codigo': 'EST015'},
        {'nombre': 'Gabriel', 'apellido': 'Cortés', 'numero_documento': '20111777-8', 'codigo': 'EST016'},
        {'nombre': 'Antonia', 'apellido': 'Vega', 'numero_documento': '20111888-9', 'codigo': 'EST017'},
        {'nombre': 'Vicente', 'apellido': 'Fuentes', 'numero_documento': '20111999-0', 'codigo': 'EST018'},
    ]
    
    nuevos_estudiantes = []
    
    for i, est_data in enumerate(estudiantes_adicionales):
        try:
            # Crear usuario estudiante
            username = f"estudiante_nuevo_{i+1}"
            user_est, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'password': 'pbkdf2_sha256$390000$dummy$dummy/',
                    'email': f'{username}@test.com'
                }
            )
            
            # Crear estudiante
            estudiante, created = Estudiante.objects.get_or_create(
                numero_documento=est_data['numero_documento'],
                defaults={
                    'user': user_est,
                    'primer_nombre': est_data['nombre'],
                    'apellido_paterno': est_data['apellido'],
                    'fecha_nacimiento': date(2008, 6, 15),
                    'telefono': f"9876543{i+10:02d}",
                    'direccion': f"Nueva Dirección {i+1}",
                    'tipo_documento': 'RUT',
                    'codigo_estudiante': est_data['codigo']
                }
            )
            
            if created:
                nuevos_estudiantes.append(estudiante)
                
                # Asociar estudiante al curso
                curso.estudiantes.add(estudiante)
                
                print(f"✅ Estudiante creado: {estudiante}")
            else:
                print(f"⚠️ Estudiante ya existía: {estudiante}")
                nuevos_estudiantes.append(estudiante)
                curso.estudiantes.add(estudiante)
                
        except Exception as e:
            print(f"❌ Error creando estudiante {est_data['nombre']}: {e}")
            continue
    
    # Crear inscripciones para los nuevos estudiantes
    print("\n📝 Creando inscripciones...")
    for estudiante in nuevos_estudiantes:
        for grupo in grupos:
            inscripcion, created = Inscripcion.objects.get_or_create(
                estudiante=estudiante,
                grupo=grupo,
                defaults={
                    'fecha_inscripcion': date.today()
                }
            )
            if created:
                print(f"✅ Inscripción: {estudiante.primer_nombre} en {grupo.asignatura.nombre}")
    
    # Crear calificaciones variadas para los nuevos estudiantes
    print("\n📊 Creando calificaciones para nuevos estudiantes...")
    
    evaluaciones = [
        'Prueba 1', 'Prueba 2', 'Prueba 3', 
        'Trabajo en Clase', 'Proyecto Final'
    ]
    
    # Definir diferentes niveles de rendimiento
    rendimientos = {
        'Javiera': {'base': 6.8, 'variacion': 0.3},  # Excelente
        'Francisco': {'base': 6.4, 'variacion': 0.4},  # Muy bueno
        'Isidora': {'base': 6.1, 'variacion': 0.5},  # Bueno
        'Benjamín': {'base': 5.8, 'variacion': 0.6},  # Bueno
        'Constanza': {'base': 5.2, 'variacion': 0.7},  # Regular
        'Gabriel': {'base': 4.9, 'variacion': 0.8},  # Regular
        'Antonia': {'base': 4.5, 'variacion': 0.9},  # Regular-bajo
        'Vicente': {'base': 4.1, 'variacion': 1.0},  # Bajo
    }
    
    calificaciones_creadas = 0
    
    for estudiante in nuevos_estudiantes:
        nombre = estudiante.primer_nombre
        rendimiento = rendimientos.get(nombre, {'base': 5.0, 'variacion': 1.0})
        
        for grupo in grupos:
            inscripcion = Inscripcion.objects.filter(
                estudiante=estudiante,
                grupo=grupo
            ).first()
            
            if inscripcion:
                # Crear 3-4 evaluaciones por asignatura
                num_evaluaciones = random.randint(3, 4)
                evaluaciones_seleccionadas = random.sample(evaluaciones, num_evaluaciones)
                
                for eval_nombre in evaluaciones_seleccionadas:
                    # Generar nota basada en el rendimiento del estudiante
                    base = rendimiento['base']
                    variacion = rendimiento['variacion']
                    nota = base + random.uniform(-variacion, variacion)
                    
                    # Mantener nota en rango válido (1.0 - 7.0)
                    nota = max(1.0, min(7.0, nota))
                    nota = round(nota, 1)
                    
                    calificacion, created = Calificacion.objects.get_or_create(
                        inscripcion=inscripcion,
                        nombre_evaluacion=eval_nombre,
                        defaults={
                            'puntaje': Decimal(str(nota)),
                            'fecha_evaluacion': date.today()
                        }
                    )
                    
                    if created:
                        calificaciones_creadas += 1
    
    print(f"✅ Nuevas calificaciones creadas: {calificaciones_creadas}")
    
    # Mostrar resumen final
    print("\n📈 RESUMEN FINAL:")
    print(f"   👥 Total estudiantes en {curso}: {curso.estudiantes.count()}")
    print(f"   📖 Asignaturas en {curso}: {curso.asignaturas.count()}")
    print(f"   📝 Total inscripciones: {Inscripcion.objects.filter(grupo__in=grupos).count()}")
    print(f"   ⭐ Total calificaciones: {Calificacion.objects.filter(inscripcion__grupo__in=grupos).count()}")
    
    print(f"\n🎯 Ranking listo para ver en:")
    print(f"   URL: http://127.0.0.1:8000/ver_notas_curso/?curso_id={curso.id}")
    
    # Simular el ranking para mostrar un preview
    print(f"\n🏆 PREVIEW DEL RANKING para {curso}:")
    estudiantes_curso = curso.estudiantes.all()
    asignaturas_curso = curso.asignaturas.all()
    
    ranking_data = []
    for estudiante in estudiantes_curso:
        suma_promedios = 0
        asignaturas_con_notas = 0
        
        for asignatura in asignaturas_curso:
            inscripciones_asignatura = Inscripcion.objects.filter(
                estudiante=estudiante,
                grupo__asignatura=asignatura
            )
            notas_asignatura = Calificacion.objects.filter(
                inscripcion__in=inscripciones_asignatura
            )
            
            if notas_asignatura.exists():
                puntajes = [nota.puntaje for nota in notas_asignatura]
                promedio_asignatura = sum(puntajes) / len(puntajes)
                suma_promedios += promedio_asignatura
                asignaturas_con_notas += 1
        
        if asignaturas_con_notas > 0:
            promedio_general = suma_promedios / asignaturas_con_notas
            ranking_data.append({
                'estudiante': estudiante,
                'promedio': round(promedio_general, 2),
                'asignaturas': asignaturas_con_notas
            })
    
    # Ordenar por promedio descendente
    ranking_data.sort(key=lambda x: x['promedio'], reverse=True)
    
    # Mostrar top 10
    print("   🥇 Top 10 Estudiantes:")
    for i, data in enumerate(ranking_data[:10], 1):
        estudiante = data['estudiante']
        promedio = data['promedio']
        asignaturas = data['asignaturas']
        
        # Emojis para los primeros 3 puestos
        if i == 1:
            emoji = "🥇"
        elif i == 2:
            emoji = "🥈"
        elif i == 3:
            emoji = "🥉"
        else:
            emoji = f"{i:2d}."
        
        print(f"   {emoji} {estudiante.get_nombre_completo()}: {promedio} ({asignaturas} asignaturas)")

if __name__ == '__main__':
    agregar_mas_estudiantes()
