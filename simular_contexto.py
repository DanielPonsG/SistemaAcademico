#!/usr/bin/env python
"""
Script para simular exactamente el contexto de la vista listar_asignaturas
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from django.contrib.auth.models import User
from smapp.models import Profesor, Asignatura

def simular_contexto_profesor(username):
    print(f"=== SIMULANDO CONTEXTO PARA: {username} ===\n")
    
    try:
        # Obtener usuario y profesor
        user = User.objects.get(username=username)
        profesor = user.profesor
        user_type = 'profesor'
        
        print(f"Usuario: {user.username}")
        print(f"Profesor: {profesor.get_nombre_completo()}")
        
        # Simular la lógica exacta del backend
        asignaturas = Asignatura.objects.filter(
            profesor_responsable=profesor
        ).select_related('profesor_responsable').prefetch_related(
            'cursos__estudiantes'
        ).order_by('nombre')
        
        # Estadísticas específicas para el profesor
        total_asignaturas = asignaturas.count()
        asignaturas_como_responsable = total_asignaturas  # Todas las que ve son de su responsabilidad
        
        # Calcular total de cursos y estudiantes para este profesor
        total_cursos_profesor = 0
        total_estudiantes_profesor = 0
        cursos_unicos = set()
        
        print(f"\n=== CÁLCULO DE ESTADÍSTICAS ===")
        print(f"Total asignaturas: {total_asignaturas}")
        
        for asignatura in asignaturas:
            print(f"\nAsignatura: {asignatura.nombre}")
            cursos_asignatura = asignatura.cursos.all()
            print(f"  Cursos asignados: {cursos_asignatura.count()}")
            
            for curso in cursos_asignatura:
                estudiantes_count = curso.estudiantes.count()
                print(f"    - {curso}: {estudiantes_count} estudiantes")
                
                if curso.id not in cursos_unicos:
                    cursos_unicos.add(curso.id)
                    # Solo contar estudiantes una vez por curso
                    total_estudiantes_profesor += estudiantes_count
                    print(f"      -> Sumando {estudiantes_count} estudiantes (nuevo curso)")
                else:
                    print(f"      -> Curso ya contado, no sumando estudiantes")
        
        total_cursos_profesor = len(cursos_unicos)
        
        # Variables para el contexto del profesor
        asignaturas_con_profesor = total_asignaturas  # Todas las suyas tienen profesor (él mismo)
        asignaturas_sin_profesor_count = 0
        
        print(f"\n=== ESTADÍSTICAS FINALES ===")
        print(f"total_asignaturas: {total_asignaturas}")
        print(f"total_cursos_profesor: {total_cursos_profesor}")
        print(f"total_estudiantes_profesor: {total_estudiantes_profesor}")
        print(f"asignaturas_como_responsable: {asignaturas_como_responsable}")
        print(f"asignaturas_con_profesor: {asignaturas_con_profesor}")
        print(f"asignaturas_sin_profesor_count: {asignaturas_sin_profesor_count}")
        
        # Simular context como en la vista
        context = {
            'asignaturas': asignaturas,
            'tipo_usuario': user_type,
            'total_asignaturas': total_asignaturas,
            'asignaturas_con_profesor': asignaturas_con_profesor,
            'asignaturas_sin_profesor_count': asignaturas_sin_profesor_count,
            'total_cursos_profesor': total_cursos_profesor,
            'total_estudiantes_profesor': total_estudiantes_profesor,
            'asignaturas_como_responsable': asignaturas_como_responsable,
            'puede_editar': False,
        }
        
        print(f"\n=== CONTEXTO COMPLETO ===")
        for key, value in context.items():
            if key != 'asignaturas':  # No imprimir las asignaturas completas
                print(f"{key}: {value}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    simular_contexto_profesor('qwe')
