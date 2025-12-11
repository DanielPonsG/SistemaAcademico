#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script LIGERO para poblar la base de datos con datos esenciales.
Diseñado para ser rápido y demostrar funcionalidad completa sin sobrecarga.
"""

import os
import sys
import random
from datetime import date, time

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')

import django
django.setup()

from django.contrib.auth.models import User
from smapp.models import (
    Asignatura, Curso, Profesor, Estudiante, Apoderado, 
    RelacionApoderadoEstudiante, PeriodoAcademico,
    Perfil, HorarioCurso
)

def poblar_ligero():
    print("🚀 Iniciando poblado LIGERO de la base de datos...")
    
    # 0. Limpieza preventiva
    print("🧹 0. Limpiando datos antiguos para evitar conflictos...")
    HorarioCurso.objects.all().delete()
    RelacionApoderadoEstudiante.objects.all().delete()
    Estudiante.objects.all().delete()
    Apoderado.objects.all().delete()
    Profesor.objects.all().delete()
    Curso.objects.all().delete()
    Asignatura.objects.all().delete()
    Perfil.objects.all().delete()
    # Eliminar usuarios de prueba anteriores si existen
    User.objects.filter(username__startswith='profe_demo').delete()
    User.objects.filter(username__startswith='alumno_demo').delete()
    User.objects.filter(username__startswith='apoderado_demo').delete()
    User.objects.filter(username__in=['director_demo', 'utp_demo']).delete()
    
    # 1. Crear período académico
    print("📅 1. Período Académico...")
    periodo, created = PeriodoAcademico.objects.get_or_create(
        nombre='Año 2025',
        defaults={
            'fecha_inicio': date(2025, 3, 1),
            'fecha_fin': date(2025, 12, 15),
            'activo': True
        }
    )
    
    # 2. Crear asignaturas (Solo las principales)
    print("📚 2. Asignaturas principales...")
    asignaturas_data = [
        {'nombre': 'Lenguaje', 'codigo_asignatura': 'LEN'},
        {'nombre': 'Matemática', 'codigo_asignatura': 'MAT'},
        {'nombre': 'Historia', 'codigo_asignatura': 'HIS'},
        {'nombre': 'Ciencias', 'codigo_asignatura': 'CIE'},
        {'nombre': 'Inglés', 'codigo_asignatura': 'ING'},
        {'nombre': 'Educación Física', 'codigo_asignatura': 'EFI'},
        {'nombre': 'Artes', 'codigo_asignatura': 'ART'},
    ]
    
    asignaturas = []
    for asig_data in asignaturas_data:
        asignatura, created = Asignatura.objects.get_or_create(
            codigo_asignatura=asig_data['codigo_asignatura'],
            defaults=asig_data
        )
        asignaturas.append(asignatura)
    
    # 3. Crear cursos (Todos los niveles)
    print("🏫 3. Cursos (1° Básico a 4° Medio)...")
    cursos_data = [
        {'nivel': '1B', 'paralelo': 'A'},
        {'nivel': '2B', 'paralelo': 'A'},
        {'nivel': '3B', 'paralelo': 'A'},
        {'nivel': '4B', 'paralelo': 'A'},
        {'nivel': '5B', 'paralelo': 'A'},
        {'nivel': '6B', 'paralelo': 'A'},
        {'nivel': '7B', 'paralelo': 'A'},
        {'nivel': '8B', 'paralelo': 'A'},
        {'nivel': '1M', 'paralelo': 'A'},
        {'nivel': '2M', 'paralelo': 'A'},
        {'nivel': '3M', 'paralelo': 'A'},
        {'nivel': '4M', 'paralelo': 'A'},
    ]
    
    cursos = []
    for curso_data in cursos_data:
        curso, created = Curso.objects.get_or_create(
            nivel=curso_data['nivel'],
            paralelo=curso_data['paralelo'],
            anio=2025,
            defaults=curso_data
        )
        cursos.append(curso)

    # 4. Crear Directivos
    print("👔 4. Directivos...")
    directores_data = [
        {'username': 'director_demo', 'nombre': 'Director', 'apellido': 'Demo', 'email': 'director.demo@colegio.cl'},
        {'username': 'utp_demo', 'nombre': 'Jefe', 'apellido': 'UTP', 'email': 'utp.demo@colegio.cl'},
    ]

    for dir_data in directores_data:
        user, created = User.objects.get_or_create(
            username=dir_data['username'],
            defaults={
                'first_name': dir_data['nombre'],
                'last_name': dir_data['apellido'],
                'email': dir_data['email'],
                'is_staff': True,
                'is_superuser': True if 'director' in dir_data['username'] else False
            }
        )
        if created:
            user.set_password('123456') # Contraseña simple
            user.save()
        
        Perfil.objects.get_or_create(
            user=user,
            defaults={
                'tipo_usuario': 'director',
                'tipo_documento': 'rut',
                'numero_documento': f"{random.randint(10000000, 20000000)}-K",
                'cargo': 'Director'
            }
        )

    # 5. Crear Profesores (5 profesores para cubrir cursos)
    print("👨‍🏫 5. Profesores...")
    profesores_data = [
        {'nombre': 'Juan', 'apellido': 'Pérez', 'email': 'juan.perez@colegio.cl', 'especialidad': 'Matemática'},
        {'nombre': 'Ana', 'apellido': 'Silva', 'email': 'ana.silva@colegio.cl', 'especialidad': 'Lenguaje'},
        {'nombre': 'Pedro', 'apellido': 'Rojas', 'email': 'pedro.rojas@colegio.cl', 'especialidad': 'Ciencias'},
        {'nombre': 'Maria', 'apellido': 'Gonzalez', 'email': 'maria.gonzalez@colegio.cl', 'especialidad': 'Historia'},
        {'nombre': 'Luis', 'apellido': 'Soto', 'email': 'luis.soto@colegio.cl', 'especialidad': 'Inglés'},
    ]
    
    profesores = []
    for i, prof_data in enumerate(profesores_data):
        username = f"profe_demo_{i+1}"
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': prof_data['nombre'],
                'last_name': prof_data['apellido'],
                'email': prof_data['email'],
                'is_staff': True
            }
        )
        if created:
            user.set_password('123456')
            user.save()
        
        perfil, _ = Perfil.objects.get_or_create(
            user=user,
            defaults={
                'tipo_usuario': 'profesor',
                'tipo_documento': 'rut',
                'numero_documento': f"{random.randint(10000000, 20000000)}-{i}",
            }
        )
        
        profesor, _ = Profesor.objects.get_or_create(
            user=user,
            defaults={
                'primer_nombre': prof_data['nombre'],
                'apellido_paterno': prof_data['apellido'],
                'tipo_documento': 'CC',
                'numero_documento': perfil.numero_documento,
                'fecha_nacimiento': date(1985, 1, 1),
                'genero': 'M' if i % 2 == 0 else 'F',
                'email': prof_data['email'],
                'codigo_profesor': f"PROF{i+1:03d}",
                'especialidad': prof_data['especialidad']
            }
        )
        profesores.append(profesor)
    
    # Asignar jefaturas (rotativas) y Asignaturas a Cursos
    print("🔗 Asignando jefaturas y asignaturas a cursos...")
    for i, curso in enumerate(cursos):
        curso.profesor_jefe = profesores[i % len(profesores)]
        # Asignar todas las asignaturas al curso para que aparezcan en el horario
        for asignatura in asignaturas:
            curso.asignaturas.add(asignatura)
        curso.save()

    # 6. Crear Estudiantes (1 por curso)
    print("👦 6. Estudiantes...")
    estudiantes = []
    
    for i, curso in enumerate(cursos):
        for j in range(1): # Solo 1 estudiante por curso
            num = (i * 1) + j + 1
            username = f"alumno_demo_{num}"
            rut = f"{20000000 + num}-K"
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': 'Alumno',
                    'last_name': f'Demo {num}',
                    'email': f"alumno{num}@demo.cl"
                }
            )
            if created:
                user.set_password('123456')
                user.save()
            
            Perfil.objects.get_or_create(
                user=user,
                defaults={
                    'tipo_usuario': 'alumno',
                    'tipo_documento': 'rut',
                    'numero_documento': rut,
                }
            )
            
            estudiante, _ = Estudiante.objects.get_or_create(
                user=user,
                defaults={
                    'primer_nombre': 'Alumno',
                    'apellido_paterno': f'Demo {num}',
                    'tipo_documento': 'CC',
                    'numero_documento': rut,
                    'fecha_nacimiento': date(2012, 1, 1),
                    'genero': 'M',
                    'email': f"alumno{num}@demo.cl",
                    'codigo_estudiante': f"EST{num:03d}"
                }
            )
            
            curso.estudiantes.add(estudiante)
            estudiantes.append(estudiante)

    # 7. Crear Apoderados (1 por estudiante)
    print("👨‍👩‍👧 7. Apoderados...")
    for i, est in enumerate(estudiantes):
        username = f"apoderado_demo_{i+1}"
        rut = f"{10000000 + i}-K"
        
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': 'Apoderado',
                'last_name': f'De {est.apellido_paterno}',
                'email': f"apoderado{i+1}@demo.cl"
            }
        )
        if created:
            user.set_password('123456')
            user.save()
            
        Perfil.objects.get_or_create(
            user=user,
            defaults={
                'tipo_usuario': 'apoderado',
                'tipo_documento': 'rut',
                'numero_documento': rut
            }
        )
        
        apoderado, _ = Apoderado.objects.get_or_create(
            user=user,
            defaults={
                'primer_nombre': 'Apoderado',
                'apellido_paterno': f'De {est.apellido_paterno}',
                'tipo_documento': 'CC',
                'numero_documento': rut,
                'fecha_nacimiento': date(1980, 1, 1),
                'genero': 'F',
                'email': f"apoderado{i+1}@demo.cl",
                'codigo_apoderado': f"APO{i+1:03d}",
                'parentesco_principal': 'madre'
            }
        )
        
        RelacionApoderadoEstudiante.objects.get_or_create(
            apoderado=apoderado,
            estudiante=est,
            defaults={
                'parentesco': 'madre',
                'es_apoderado_principal': True
            }
        )

    # 8. Crear Horarios (Simple: Lunes a Viernes, 2 bloques)
    print("🕒 8. Horarios...")
    bloques = [
        (time(8, 0), time(9, 30)),
        (time(10, 0), time(11, 30))
    ]
    dias = ['LU', 'MA', 'MI', 'JU', 'VI']
    
    for curso in cursos:
        idx_asig = 0
        for dia in dias:
            for bloque in bloques:
                # Rotar asignaturas y profesores
                asignatura = asignaturas[idx_asig % len(asignaturas)]
                profesor = profesores[idx_asig % len(profesores)]
                
                HorarioCurso.objects.get_or_create(
                    curso=curso,
                    dia=dia,
                    hora_inicio=bloque[0],
                    defaults={
                        'hora_fin': bloque[1],
                        'asignatura': asignatura,
                        'profesor': profesor
                    }
                )
                idx_asig += 1

    print("\n✅ ¡Poblado LIGERO completado con éxito!")
    print("==================================================")
    print("🔑 CREDENCIALES DE PRUEBA (Contraseña para todos: 123456)")
    print("==================================================")
    print("• Director:   director_demo")
    print("• UTP:        utp_demo")
    print("• Profesor:   profe_demo_1")
    print("• Alumno:     alumno_demo_1")
    print("• Apoderado:  apoderado_demo_1")
    print("==================================================")

if __name__ == "__main__":
    poblar_ligero()
