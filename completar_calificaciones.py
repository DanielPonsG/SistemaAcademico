#!/usr/bin/env python
"""
Script para agregar calificaciones a estudiantes existentes
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
from datetime import date

def agregar_calificaciones_existentes():
    print("🚀 Agregando calificaciones a estudiantes existentes...")
    
    # Obtener el curso con datos
    curso = Curso.objects.filter(nivel='1M', paralelo='A', anio=2025).first()
    if not curso:
        print("❌ No se encontró el curso 1° Medio A 2025")
        return
    
    # Obtener todos los estudiantes del curso
    estudiantes = curso.estudiantes.all()
    print(f"✅ Estudiantes en {curso}: {estudiantes.count()}")
    for est in estudiantes:
        print(f"   - {est.get_nombre_completo()}")
    
    # Obtener grupos del curso
    periodo = PeriodoAcademico.objects.filter(nombre="Año Escolar 2025").first()
    asignaturas_curso = curso.asignaturas.all()
    grupos = Grupo.objects.filter(
        periodo_academico=periodo,
        asignatura__in=asignaturas_curso
    )
    
    print(f"✅ Grupos encontrados: {grupos.count()}")
    
    evaluaciones = [
        'Prueba 1', 'Prueba 2', 'Prueba 3', 
        'Trabajo en Clase', 'Proyecto Final'
    ]
    
    # Rendimientos diferentes para cada estudiante
    rendimientos_por_estudiante = [
        {'base': 6.5, 'variacion': 0.4},  # Primer estudiante (muy bueno)
        {'base': 5.8, 'variacion': 0.6},  # Segundo estudiante (bueno)
        {'base': 5.2, 'variacion': 0.8},  # Tercer estudiante (regular)
        {'base': 4.8, 'variacion': 0.7},  # Cuarto estudiante (regular-bajo)
        {'base': 4.3, 'variacion': 0.9},  # Quinto estudiante (bajo)
    ]
    
    calificaciones_creadas = 0
    
    for i, estudiante in enumerate(estudiantes):
        print(f"\n📊 Creando calificaciones para {estudiante.get_nombre_completo()}...")
        
        # Usar rendimiento según el índice del estudiante
        if i < len(rendimientos_por_estudiante):
            rendimiento = rendimientos_por_estudiante[i]
        else:
            rendimiento = {'base': 5.0, 'variacion': 1.0}
        
        for grupo in grupos:
            # Verificar si ya existe inscripción
            inscripcion = Inscripcion.objects.filter(
                estudiante=estudiante,
                grupo=grupo
            ).first()
            
            if not inscripcion:
                # Crear inscripción si no existe
                inscripcion = Inscripcion.objects.create(
                    estudiante=estudiante,
                    grupo=grupo,
                    fecha_inscripcion=date.today()
                )
                print(f"   ✅ Inscripción creada: {estudiante.primer_nombre} en {grupo.asignatura.nombre}")
            
            # Crear calificaciones para esta asignatura
            # Verificar cuántas evaluaciones ya tiene
            calificaciones_existentes = Calificacion.objects.filter(inscripcion=inscripcion)
            evaluaciones_existentes = set(calificaciones_existentes.values_list('nombre_evaluacion', flat=True))
            
            # Crear evaluaciones que no existen
            evaluaciones_faltantes = [ev for ev in evaluaciones if ev not in evaluaciones_existentes]
            
            if evaluaciones_faltantes:
                # Crear 2-3 evaluaciones más
                num_evaluaciones = min(3, len(evaluaciones_faltantes))
                evaluaciones_crear = random.sample(evaluaciones_faltantes, num_evaluaciones)
                
                for eval_nombre in evaluaciones_crear:
                    # Generar nota basada en el rendimiento del estudiante
                    base = rendimiento['base']
                    variacion = rendimiento['variacion']
                    nota = base + random.uniform(-variacion, variacion)
                    
                    # Mantener nota en rango válido (1.0 - 7.0)
                    nota = max(1.0, min(7.0, nota))
                    nota = round(nota, 1)
                    
                    calificacion = Calificacion.objects.create(
                        inscripcion=inscripcion,
                        nombre_evaluacion=eval_nombre,
                        puntaje=Decimal(str(nota)),
                        fecha_evaluacion=date.today()
                    )
                    
                    calificaciones_creadas += 1
                    print(f"   ✅ Calificación: {eval_nombre} = {nota} en {grupo.asignatura.nombre}")
    
    print(f"\n✅ Total calificaciones creadas: {calificaciones_creadas}")
    
    # Mostrar ranking actualizado
    print(f"\n🏆 RANKING ACTUALIZADO para {curso}:")
    estudiantes_curso = curso.estudiantes.all()
    asignaturas_curso = curso.asignaturas.all()
    
    ranking_data = []
    estadisticas = {'aprobados': 0, 'reprobados': 0}
    
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
                puntajes = [float(nota.puntaje) for nota in notas_asignatura]
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
            
            # Contar aprobados/reprobados
            if promedio_general >= 4.0:
                estadisticas['aprobados'] += 1
            else:
                estadisticas['reprobados'] += 1
    
    # Ordenar por promedio descendente
    ranking_data.sort(key=lambda x: x['promedio'], reverse=True)
    
    # Mostrar top estudiantes
    for i, data in enumerate(ranking_data, 1):
        estudiante = data['estudiante']
        promedio = data['promedio']
        asignaturas = data['asignaturas']
        
        if i == 1:
            emoji = "🥇"
        elif i == 2:
            emoji = "🥈"
        elif i == 3:
            emoji = "🥉"
        else:
            emoji = f"{i:2d}."
        
        estado = "✅ Aprobado" if promedio >= 4.0 else "❌ Reprobado"
        print(f"   {emoji} {estudiante.get_nombre_completo()}: {promedio} ({asignaturas} asignaturas) {estado}")
    
    # Mostrar estadísticas
    promedio_curso = sum(data['promedio'] for data in ranking_data) / len(ranking_data) if ranking_data else 0
    print(f"\n📊 ESTADÍSTICAS DEL CURSO:")
    print(f"   ✅ Aprobados: {estadisticas['aprobados']}")
    print(f"   ❌ Reprobados: {estadisticas['reprobados']}")
    print(f"   📈 Promedio del curso: {round(promedio_curso, 2)}")
    print(f"   👥 Total estudiantes: {len(ranking_data)}")
    
    print(f"\n🎯 Ver ranking completo en:")
    print(f"   http://127.0.0.1:8000/ver_notas_curso/?curso_id={curso.id}")

if __name__ == '__main__':
    agregar_calificaciones_existentes()
