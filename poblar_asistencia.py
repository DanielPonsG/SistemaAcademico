#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para poblar asistencia (AsistenciaAlumno) basado en los horarios existentes.
Genera asistencia para las últimas 2 semanas.
"""

import os
import sys
import random
import django
from datetime import date, timedelta, datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from smapp.models import (
    Curso, Asignatura, Profesor, Estudiante, 
    HorarioCurso, AsistenciaAlumno, PeriodoAcademico
)

def poblar_asistencia():
    print("🚀 Iniciando poblado de Asistencia...")
    
    # Definir rango de fechas (últimas 2 semanas)
    hoy = date.today()
    fecha_inicio = hoy - timedelta(days=14)
    
    dias_map = {
        0: 'LU', 1: 'MA', 2: 'MI', 3: 'JU', 4: 'VI', 5: 'SA', 6: 'DO'
    }
    
    total_registros = 0
    
    # Iterar por cada día en el rango
    delta = timedelta(days=1)
    fecha_actual = fecha_inicio
    
    while fecha_actual <= hoy:
        dia_semana = fecha_actual.weekday()
        dia_codigo = dias_map.get(dia_semana)
        
        print(f"📅 Procesando fecha: {fecha_actual} ({dia_codigo})")
        
        # Obtener horarios para este día
        horarios = HorarioCurso.objects.filter(dia=dia_codigo)
        
        if not horarios.exists():
            print(f"   ⚠️ No hay horarios para el día {dia_codigo}. Saltando...")
            fecha_actual += delta
            continue
            
        for horario in horarios:
            curso = horario.curso
            asignatura = horario.asignatura
            profesor = horario.profesor
            
            if not asignatura:
                continue
                
            estudiantes = curso.estudiantes.all()
            
            if not estudiantes.exists():
                continue
                
            # print(f"   🏫 Curso: {curso.nombre} | Asignatura: {asignatura.nombre}")
            
            for estudiante in estudiantes:
                # Determinar asistencia (90% probabilidad de asistir)
                presente = random.random() < 0.90
                observacion = ""
                justificacion = ""
                
                if not presente:
                    if random.random() < 0.3:
                        justificacion = "Licencia médica"
                    else:
                        observacion = "Ausencia sin aviso"
                
                # Crear registro
                asistencia, created = AsistenciaAlumno.objects.get_or_create(
                    estudiante=estudiante,
                    curso=curso,
                    asignatura=asignatura,
                    fecha=fecha_actual,
                    defaults={
                        'presente': presente,
                        'observacion': observacion,
                        'justificacion': justificacion,
                        'profesor_registro': profesor,
                        'hora_registro': datetime.now().time()
                    }
                )
                
                if created:
                    total_registros += 1
        
        fecha_actual += delta

    print(f"\n✅ ¡Proceso completado! Se han creado {total_registros} registros de asistencia.")

if __name__ == "__main__":
    poblar_asistencia()
