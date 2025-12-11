#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para poblar notas (calificaciones) para los estudiantes existentes.
Crea las estructuras necesarias (Grupos, Inscripciones) si no existen.
"""

import os
import sys
import random
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from smapp.models import (
    Curso, Asignatura, Profesor, Estudiante, 
    Grupo, Inscripcion, Calificacion, PeriodoAcademico, Salon
)

def poblar_notas():
    print("🚀 Iniciando poblado de Notas...")
    
    # Verificar datos base
    periodo = PeriodoAcademico.objects.first()
    if not periodo:
        print("❌ No se encontró Periodo Académico. Ejecuta poblar_bd_ligero.py primero.")
        return

    cursos = Curso.objects.all()
    profesores = list(Profesor.objects.all())
    todas_asignaturas = list(Asignatura.objects.all())
    
    if not cursos.exists():
        print("❌ No hay cursos. Ejecuta poblar_bd_ligero.py primero.")
        return

    # Crear salón dummy si es necesario
    salon, _ = Salon.objects.get_or_create(
        numero_salon="VIRTUAL",
        defaults={'capacidad': 99, 'ubicacion': 'Virtual'}
    )

    print(f"ℹ️ Procesando {cursos.count()} cursos...")
    
    total_notas = 0
    
    for curso in cursos:
        print(f"  🏫 Procesando curso: {curso.nombre}")
        
        estudiantes = curso.estudiantes.all()
        asignaturas = curso.asignaturas.all()
        
        if not estudiantes.exists():
            print("     ⚠️ Curso sin estudiantes.")
            continue
            
        # FIX: Si el curso no tiene asignaturas, asignarle todas
        if not asignaturas.exists():
            print("     ⚠️ Curso sin asignaturas asignadas. Asignando todas las disponibles...")
            for asig in todas_asignaturas:
                curso.asignaturas.add(asig)
            asignaturas = curso.asignaturas.all()

        # Para cada asignatura del curso
        for asignatura in asignaturas:
            # Determinar profesor (usar el jefe de curso o uno aleatorio)
            profesor = curso.profesor_jefe
            if not profesor and profesores:
                profesor = random.choice(profesores)
            
            # 1. Crear o recuperar Grupo
            grupo, created = Grupo.objects.get_or_create(
                asignatura=asignatura,
                periodo_academico=periodo,
                defaults={
                    'profesor': profesor,
                    'salon': salon,
                    'capacidad_maxima': 45
                }
            )
            
            # 2. Inscribir estudiantes y poner notas
            for estudiante in estudiantes:
                inscripcion, created = Inscripcion.objects.get_or_create(
                    estudiante=estudiante,
                    grupo=grupo
                )
                
                # Si ya tiene notas, saltar (o borrar y recrear si prefieres)
                if Calificacion.objects.filter(inscripcion=inscripcion).exists():
                    continue
                
                # Crear 3 a 5 notas aleatorias
                num_notas = random.randint(3, 5)
                for i in range(1, num_notas + 1):
                    nota = random.uniform(3.0, 7.0)
                    # Ajustar para que haya algunos rojos
                    if random.random() < 0.15:
                        nota = random.uniform(2.0, 3.9)
                        
                    Calificacion.objects.create(
                        inscripcion=inscripcion,
                        nombre_evaluacion=f"Evaluación {i}",
                        puntaje=round(nota, 1),
                        porcentaje=100/num_notas,
                        detalle=f"Nota generada automáticamente para {asignatura.nombre}",
                        descripcion="Evaluación sumativa"
                    )
                    total_notas += 1
    
    print(f"\n✅ ¡Proceso completado! Se han creado {total_notas} calificaciones nuevas.")

if __name__ == "__main__":
    poblar_notas()
