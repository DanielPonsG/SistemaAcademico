#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para poblar la base de datos con datos de ejemplo
para probar el sistema SAM.
"""

import os
import sys
import random
from datetime import date, datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')

import django
django.setup()

from django.contrib.auth.models import User
from smapp.models import (
    Asignatura, Curso, Profesor, Estudiante, Apoderado, 
    RelacionApoderadoEstudiante, EventoCalendario, PeriodoAcademico,
    Perfil
)

def crear_datos_ejemplo():
    print("🚀 Iniciando poblado de la base de datos...")
    
    # 1. Crear período académico
    print("📅 Creando período académico...")
    periodo, created = PeriodoAcademico.objects.get_or_create(
        nombre='Año Académico 2025',
        defaults={
            'fecha_inicio': date(2025, 3, 1),
            'fecha_fin': date(2025, 12, 15),
            'activo': True
        }
    )
    
    # 2. Crear asignaturas
    print("📚 Creando asignaturas...")
    asignaturas_data = [
        {'nombre': 'Lenguaje y Comunicación', 'codigo_asignatura': 'LEN'},
        {'nombre': 'Matemática', 'codigo_asignatura': 'MAT'},
        {'nombre': 'Historia, Geografía y Ciencias Sociales', 'codigo_asignatura': 'HIS'},
        {'nombre': 'Ciencias Naturales', 'codigo_asignatura': 'CIE'},
        {'nombre': 'Inglés', 'codigo_asignatura': 'ING'},
        {'nombre': 'Educación Física y Salud', 'codigo_asignatura': 'EFI'},
        {'nombre': 'Artes Visuales', 'codigo_asignatura': 'ART'},
        {'nombre': 'Música', 'codigo_asignatura': 'MUS'},
        {'nombre': 'Tecnología', 'codigo_asignatura': 'TEC'},
        {'nombre': 'Religión', 'codigo_asignatura': 'REL'},
    ]
    
    asignaturas = []
    for asig_data in asignaturas_data:
        asignatura, created = Asignatura.objects.get_or_create(
            codigo_asignatura=asig_data['codigo_asignatura'],
            defaults=asig_data
        )
        asignaturas.append(asignatura)
    
    # 3. Crear cursos
    print("🏫 Creando cursos...")
    cursos_data = [
        {'nivel': '1B', 'paralelo': 'A'},
        {'nivel': '1B', 'paralelo': 'B'},
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
    
    # 4. Crear profesores
    print("👨‍🏫 Creando profesores...")
    profesores_data = [
        {'nombres': ['María', 'José'], 'apellidos': ['González', 'Silva'], 'email': 'maria.gonzalez@colegio.cl', 'telefono': '+56912345678', 'codigo': 'PROF001', 'especialidad': 'Lenguaje y Comunicación'},
        {'nombres': ['Carlos', 'Eduardo'], 'apellidos': ['Rodríguez', 'López'], 'email': 'carlos.rodriguez@colegio.cl', 'telefono': '+56912345679', 'codigo': 'PROF002', 'especialidad': 'Matemática'},
        {'nombres': ['Ana', 'Cristina'], 'apellidos': ['Morales', 'Díaz'], 'email': 'ana.morales@colegio.cl', 'telefono': '+56912345680', 'codigo': 'PROF003', 'especialidad': 'Historia y Ciencias Sociales'},
        {'nombres': ['Roberto', 'Fernando'], 'apellidos': ['Soto', 'Contreras'], 'email': 'roberto.soto@colegio.cl', 'telefono': '+56912345681', 'codigo': 'PROF004', 'especialidad': 'Ciencias Naturales'},
        {'nombres': ['Patricia', 'Andrea'], 'apellidos': ['Martínez', 'Sepúlveda'], 'email': 'patricia.martinez@colegio.cl', 'telefono': '+56912345682', 'codigo': 'PROF005', 'especialidad': 'Inglés'},
        {'nombres': ['Felipe', 'Andrés'], 'apellidos': ['Fuentes', 'Hernández'], 'email': 'felipe.fuentes@colegio.cl', 'telefono': '+56912345683', 'codigo': 'PROF006', 'especialidad': 'Educación Física'},
        {'nombres': ['Carmen', 'Gloria'], 'apellidos': ['Torres', 'Araya'], 'email': 'carmen.torres@colegio.cl', 'telefono': '+56912345684', 'codigo': 'PROF007', 'especialidad': 'Artes'},
        {'nombres': ['Rodrigo', 'Patricio'], 'apellidos': ['Flores', 'Espinoza'], 'email': 'rodrigo.flores@colegio.cl', 'telefono': '+56912345685', 'codigo': 'PROF008', 'especialidad': 'Música'},
    ]
    
    profesores = []
    for i, prof_data in enumerate(profesores_data):
        # Crear usuario
        username = f"profesor{i+1}"
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': prof_data['nombres'][0],
                'last_name': prof_data['apellidos'][0],
                'email': prof_data['email'],
                'is_staff': True
            }
        )
        if created:
            user.set_password('profesor123')
            user.save()
        
        # Crear perfil
        perfil, created = Perfil.objects.get_or_create(
            user=user,
            defaults={
                'tipo_usuario': 'profesor',
                'tipo_documento': 'CC',
                'numero_documento': f"{random.randint(12000000, 19999999)}-{random.randint(0, 9)}",
                'fecha_nacimiento': date(random.randint(1970, 1990), random.randint(1, 12), random.randint(1, 28)),
                'genero': random.choice(['M', 'F']),
                'telefono': prof_data['telefono']
            }
        )
        
        # Crear profesor
        profesor, created = Profesor.objects.get_or_create(
            user=user,
            defaults={
                'primer_nombre': prof_data['nombres'][0],
                'segundo_nombre': prof_data['nombres'][1] if len(prof_data['nombres']) > 1 else '',
                'apellido_paterno': prof_data['apellidos'][0],
                'apellido_materno': prof_data['apellidos'][1] if len(prof_data['apellidos']) > 1 else '',
                'tipo_documento': 'CC',
                'numero_documento': perfil.numero_documento,
                'fecha_nacimiento': perfil.fecha_nacimiento,
                'genero': 'M' if perfil.genero == 'M' else 'F',
                'email': prof_data['email'],
                'telefono': prof_data['telefono'],
                'codigo_profesor': prof_data['codigo'],
                'especialidad': prof_data['especialidad']
            }
        )
        profesores.append(profesor)
    
    # 5. Asignar profesores jefe a cursos
    print("👩‍🏫 Asignando profesores jefe...")
    for i, curso in enumerate(cursos[:len(profesores)]):
        if i < len(profesores):
            curso.profesor_jefe = profesores[i]
            curso.save()
    
    # 6. Crear estudiantes
    print("👦👧 Creando estudiantes...")
    nombres_masculinos = ['Sebastián', 'Mateo', 'Santiago', 'Benjamín', 'Vicente', 'Tomás', 'Agustín', 'Lucas', 'Diego', 'Gabriel', 'Joaquín', 'Martín', 'Felipe', 'Nicolás', 'Maximiliano']
    nombres_femeninos = ['Sofía', 'Emma', 'Valentina', 'Isabella', 'Camila', 'Antonia', 'Constanza', 'Francisca', 'Magdalena', 'Amanda', 'Catalina', 'Javiera', 'Fernanda', 'Trinidad', 'Esperanza']
    apellidos = ['González', 'Muñoz', 'Rojas', 'Díaz', 'Pérez', 'Soto', 'Contreras', 'Silva', 'Martínez', 'Sepúlveda', 'Morales', 'Rodríguez', 'López', 'Fuentes', 'Hernández', 'Torres', 'Araya', 'Flores', 'Espinoza', 'Tapia']
    
    estudiantes = []
    estudiante_counter = 1
    
    for curso in cursos:
        # Crear entre 20-30 estudiantes por curso
        num_estudiantes = random.randint(20, 30)
        estudiantes_curso = []
        
        for _ in range(num_estudiantes):
            # Calcular edad aproximada basada en el nivel
            if curso.nivel.startswith('1'):
                edad_base = 6
            elif curso.nivel.startswith('2'):
                edad_base = 7
            elif curso.nivel.startswith('3'):
                edad_base = 8
            elif curso.nivel.startswith('4'):
                edad_base = 9
            elif curso.nivel.startswith('5'):
                edad_base = 10
            elif curso.nivel.startswith('6'):
                edad_base = 11
            elif curso.nivel.startswith('7'):
                edad_base = 12
            elif curso.nivel.startswith('8'):
                edad_base = 13
            elif curso.nivel == '1M':
                edad_base = 14
            elif curso.nivel == '2M':
                edad_base = 15
            elif curso.nivel == '3M':
                edad_base = 16
            elif curso.nivel == '4M':
                edad_base = 17
            else:
                edad_base = 10
            
            genero = random.choice(['M', 'F'])
            nombres = random.sample(nombres_masculinos if genero == 'M' else nombres_femeninos, 2)
            apellidos_estudiante = random.sample(apellidos, 2)
            
            # Calcular fecha de nacimiento
            edad = edad_base + random.randint(-1, 1)
            fecha_nacimiento = date(2025 - edad, random.randint(1, 12), random.randint(1, 28))
            
            # Generar RUT
            rut = f"{random.randint(20000000, 25999999)}-{random.randint(0, 9)}"
            
            # Crear usuario
            username = f"estudiante{estudiante_counter}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': nombres[0],
                    'last_name': apellidos_estudiante[0],
                    'email': f"estudiante{estudiante_counter}@ejemplo.cl"
                }
            )
            if created:
                user.set_password('estudiante123')
                user.save()
            
            # Crear perfil
            perfil, created = Perfil.objects.get_or_create(
                user=user,
                defaults={
                    'tipo_usuario': 'estudiante',
                    'tipo_documento': 'CC',
                    'numero_documento': rut,
                    'fecha_nacimiento': fecha_nacimiento,
                    'genero': 'M' if genero == 'M' else 'F'
                }
            )
            
            # Crear estudiante
            estudiante, created = Estudiante.objects.get_or_create(
                user=user,
                defaults={
                    'primer_nombre': nombres[0],
                    'segundo_nombre': nombres[1] if len(nombres) > 1 else '',
                    'apellido_paterno': apellidos_estudiante[0],
                    'apellido_materno': apellidos_estudiante[1] if len(apellidos_estudiante) > 1 else '',
                    'tipo_documento': 'CC',
                    'numero_documento': rut,
                    'fecha_nacimiento': fecha_nacimiento,
                    'genero': genero,
                    'email': f"estudiante{estudiante_counter}@ejemplo.cl",
                    'codigo_estudiante': f"EST{estudiante_counter:04d}"
                }
            )
            
            # Asignar al curso
            if estudiante not in curso.estudiantes.all():
                curso.estudiantes.add(estudiante)
            
            estudiantes.append(estudiante)
            estudiantes_curso.append(estudiante)
            estudiante_counter += 1
    
    # 7. Crear apoderados
    print("👨‍👩‍👧‍👦 Creando apoderados...")
    nombres_apoderados_m = ['José', 'Carlos', 'Luis', 'Manuel', 'Roberto', 'Fernando', 'Andrés', 'Ricardo', 'Francisco', 'Jorge', 'Pedro', 'Miguel', 'Alejandro', 'Eduardo', 'Patricio']
    nombres_apoderados_f = ['María', 'Carmen', 'Ana', 'Patricia', 'Gloria', 'Teresa', 'Mónica', 'Sandra', 'Claudia', 'Soledad', 'Rosa', 'Luz', 'Marcela', 'Paulina', 'Verónica']
    
    apoderados = []
    apoderado_counter = 1
    
    # Crear apoderados agrupando estudiantes por apellidos (familias)
    estudiantes_por_apellido = {}
    for estudiante in estudiantes:
        apellido = estudiante.apellido_paterno
        if apellido not in estudiantes_por_apellido:
            estudiantes_por_apellido[apellido] = []
        estudiantes_por_apellido[apellido].append(estudiante)
    
    for apellido, estudiantes_familia in estudiantes_por_apellido.items():
        # Crear uno o dos apoderados por familia
        for i in range(random.randint(1, 2)):
            genero = random.choice(['M', 'F'])
            nombres = random.sample(nombres_apoderados_m if genero == 'M' else nombres_apoderados_f, 2)
            
            # Tomar algunos estudiantes de la familia (máximo 3)
            estudiantes_hijos = random.sample(estudiantes_familia, min(len(estudiantes_familia), 3))
            
            # Crear usuario para el apoderado
            username = f"apoderado{apoderado_counter}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': nombres[0],
                    'last_name': apellido,
                    'email': f"apoderado{apoderado_counter}@ejemplo.cl"
                }
            )
            if created:
                user.set_password('apoderado123')
                user.save()
            
            # Crear perfil
            perfil, created = Perfil.objects.get_or_create(
                user=user,
                defaults={
                    'tipo_usuario': 'apoderado',
                    'tipo_documento': 'CC',
                    'numero_documento': f"{random.randint(8000000, 18999999)}-{random.randint(0, 9)}",
                    'fecha_nacimiento': date(random.randint(1970, 1990), random.randint(1, 12), random.randint(1, 28)),
                    'genero': genero,
                    'telefono': f"+569{random.randint(10000000, 99999999)}"
                }
            )
            
            parentesco = 'padre' if genero == 'M' else 'madre'
            
            # Crear apoderado
            apoderado, created = Apoderado.objects.get_or_create(
                user=user,
                defaults={
                    'primer_nombre': nombres[0],
                    'segundo_nombre': nombres[1] if len(nombres) > 1 else '',
                    'apellido_paterno': apellido,
                    'apellido_materno': random.choice(apellidos),
                    'tipo_documento': 'CC',
                    'numero_documento': perfil.numero_documento,
                    'fecha_nacimiento': perfil.fecha_nacimiento,
                    'genero': 'M' if genero == 'M' else 'F',
                    'email': f"apoderado{apoderado_counter}@ejemplo.cl",
                    'telefono': perfil.telefono,
                    'codigo_apoderado': f"APO{apoderado_counter:04d}",
                    'parentesco_principal': parentesco,
                    'ocupacion': random.choice(['Ingeniero', 'Profesora', 'Contador', 'Médico', 'Comerciante', 'Funcionario Público', 'Trabajador Independiente'])
                }
            )
            
            # Crear relaciones con los estudiantes
            for estudiante in estudiantes_hijos:
                RelacionApoderadoEstudiante.objects.get_or_create(
                    apoderado=apoderado,
                    estudiante=estudiante,
                    defaults={
                        'parentesco': parentesco,
                        'es_apoderado_principal': True,
                        'puede_retirar': True
                    }
                )
            
            apoderados.append(apoderado)
            apoderado_counter += 1
    
    # 8. Crear algunos eventos de calendario
    print("📅 Creando eventos de calendario...")
    eventos_data = [
        {'titulo': 'Reunión de Apoderados 1° Básico', 'fecha': date(2025, 4, 15), 'tipo': 'reunion'},
        {'titulo': 'Día del Estudiante', 'fecha': date(2025, 5, 11), 'tipo': 'celebracion'},
        {'titulo': 'Feria Científica', 'fecha': date(2025, 6, 20), 'tipo': 'academico'},
        {'titulo': 'Festival de Talentos', 'fecha': date(2025, 7, 25), 'tipo': 'cultural'},
        {'titulo': 'Evaluación Nacional SIMCE', 'fecha': date(2025, 9, 10), 'tipo': 'evaluacion'},
        {'titulo': 'Ceremonia de Graduación', 'fecha': date(2025, 12, 10), 'tipo': 'ceremonia'},
    ]
    
    for evento_data in eventos_data:
        EventoCalendario.objects.get_or_create(
            titulo=evento_data['titulo'],
            fecha=evento_data['fecha'],
            defaults={
                'descripcion': f"Evento importante: {evento_data['titulo']}",
                'tipo_evento': evento_data.get('tipo', 'general'),
                'para_todos_los_cursos': True
            }
        )
    
    # Mostrar resumen
    print("\n✅ ¡Poblado de base de datos completado!")
    print(f"   • {Asignatura.objects.count()} asignaturas creadas")
    print(f"   • {Curso.objects.count()} cursos creados")
    print(f"   • {Profesor.objects.count()} profesores creados")
    print(f"   • {Estudiante.objects.count()} estudiantes creados")
    print(f"   • {Apoderado.objects.count()} apoderados creados")
    print(f"   • {RelacionApoderadoEstudiante.objects.count()} relaciones apoderado-estudiante")
    print(f"   • {EventoCalendario.objects.count()} eventos de calendario")
    
    print("\n🔑 Credenciales de acceso:")
    print("   • Administrador: admin / admin")
    print("   • Profesores: profesor1, profesor2, etc. / profesor123")
    print("   • Estudiantes: estudiante1, estudiante2, etc. / estudiante123")
    print("   • Apoderados: apoderado1, apoderado2, etc. / apoderado123")

if __name__ == "__main__":
    crear_datos_ejemplo()
