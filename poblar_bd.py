#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para poblar la base de datos con datos de ejemplo
Ejecutar con: python manage.py shell < poblar_bd.py
"""

import os
import sys
import django
from datetime import date, datetime, timedelta
from django.utils import timezone
import random

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from django.contrib.auth.models import User, Group
from smapp.models import (
    Estudiante, Profesor, Apoderado, RelacionApoderadoEstudiante, 
    Curso, Asignatura, PeriodoAcademico, HorarioCurso, Perfil,
    EventoCalendario, Calificacion, AsistenciaAlumno, Anotacion
)

def crear_datos_ejemplo():
    print("🚀 Iniciando poblado de la base de datos...")
    
    # 1. Crear período académico
    print("📅 Creando período académico...")
    periodo, created = PeriodoAcademico.objects.get_or_create(
        nombre="2025",
        defaults={
            'fecha_inicio': date(2025, 3, 1),
            'fecha_fin': date(2025, 12, 15),
            'activo': True
        }
    )
    
    # 2. Crear asignaturas
    print("📚 Creando asignaturas...")
    asignaturas_data = [
        {'nombre': 'Matemáticas', 'codigo_asignatura': 'MAT', 'descripcion': 'Matemáticas básicas y avanzadas'},
        {'nombre': 'Lenguaje y Comunicación', 'codigo_asignatura': 'LEN', 'descripcion': 'Comprensión lectora y expresión escrita'},
        {'nombre': 'Historia y Geografía', 'codigo_asignatura': 'HIS', 'descripcion': 'Historia universal y geografía'},
        {'nombre': 'Ciencias Naturales', 'codigo_asignatura': 'CIE', 'descripcion': 'Biología, Química y Física'},
        {'nombre': 'Inglés', 'codigo_asignatura': 'ING', 'descripcion': 'Idioma inglés básico e intermedio'},
        {'nombre': 'Educación Física', 'codigo_asignatura': 'EDF', 'descripcion': 'Actividad física y deportes'},
        {'nombre': 'Artes Visuales', 'codigo_asignatura': 'ART', 'descripcion': 'Expresión artística y creatividad'},
        {'nombre': 'Música', 'codigo_asignatura': 'MUS', 'descripcion': 'Educación musical'},
        {'nombre': 'Tecnología', 'codigo_asignatura': 'TEC', 'descripcion': 'Tecnología e informática'},
        {'nombre': 'Religión', 'codigo_asignatura': 'REL', 'descripcion': 'Educación religiosa'},
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
        {
            'nombres': ['María', 'Elena'], 'apellidos': ['González', 'Rodríguez'],
            'email': 'maria.gonzalez@colegio.cl', 'especialidad': 'Educación Básica',
            'codigo': 'PROF001', 'telefono': '+56912345678'
        },
        {
            'nombres': ['Carlos', 'Alberto'], 'apellidos': ['Muñoz', 'Silva'],
            'email': 'carlos.munoz@colegio.cl', 'especialidad': 'Matemáticas',
            'codigo': 'PROF002', 'telefono': '+56912345679'
        },
        {
            'nombres': ['Ana', 'Sofía'], 'apellidos': ['López', 'Torres'],
            'email': 'ana.lopez@colegio.cl', 'especialidad': 'Lenguaje',
            'codigo': 'PROF003', 'telefono': '+56912345680'
        },
        {
            'nombres': ['Roberto', 'José'], 'apellidos': ['Fernández', 'Morales'],
            'email': 'roberto.fernandez@colegio.cl', 'especialidad': 'Historia',
            'codigo': 'PROF004', 'telefono': '+56912345681'
        },
        {
            'nombres': ['Patricia', 'Isabel'], 'apellidos': ['Herrera', 'Campos'],
            'email': 'patricia.herrera@colegio.cl', 'especialidad': 'Ciencias',
            'codigo': 'PROF005', 'telefono': '+56912345682'
        },
        {
            'nombres': ['Luis', 'Fernando'], 'apellidos': ['Vargas', 'Soto'],
            'email': 'luis.vargas@colegio.cl', 'especialidad': 'Inglés',
            'codigo': 'PROF006', 'telefono': '+56912345683'
        },
        {
            'nombres': ['Carmen', 'Rosa'], 'apellidos': ['Jiménez', 'Ramos'],
            'email': 'carmen.jimenez@colegio.cl', 'especialidad': 'Educación Física',
            'codigo': 'PROF007', 'telefono': '+56912345684'
        },
        {
            'nombres': ['Miguel', 'Ángel'], 'apellidos': ['Castro', 'Peña'],
            'email': 'miguel.castro@colegio.cl', 'especialidad': 'Artes',
            'codigo': 'PROF008', 'telefono': '+56912345685'
        },
    ]
    
    profesores = []
    for i, prof_data in enumerate(profesores_data):
        # Crear usuario
        username = f"profesor{i+1}"
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': ' '.join(prof_data['nombres']),
                'last_name': ' '.join(prof_data['apellidos']),
                'email': prof_data['email'],
                'password': 'pbkdf2_sha256$600000$test$test'  # password: test
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
        # Crear entre 25-30 estudiantes por curso
        num_estudiantes = random.randint(25, 30)
        
        for j in range(num_estudiantes):
            genero = random.choice(['M', 'F'])
            nombres = random.sample(nombres_masculinos if genero == 'M' else nombres_femeninos, 2)
            apellido_paterno = random.choice(apellidos)
            apellido_materno = random.choice(apellidos)
            
            # Calcular edad aproximada según el nivel
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
            fecha_nacimiento = date(2025 - edad_base, random.randint(1, 12), random.randint(1, 28))
            
            # Crear usuario
            username = f"estudiante{estudiante_counter}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': ' '.join(nombres),
                    'last_name': f"{apellido_paterno} {apellido_materno}",
                    'email': f"estudiante{estudiante_counter}@ejemplo.cl",
                    'password': 'pbkdf2_sha256$600000$test$test'
                }
            )
            
            if created:
                user.set_password('estudiante123')
                user.save()
            
            # Crear perfil
            rut = f"{random.randint(20000000, 25999999)}-{random.randint(0, 9)}"
            perfil, created = Perfil.objects.get_or_create(
                user=user,
                defaults={
                    'tipo_usuario': 'alumno',
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
                    'apellido_paterno': apellido_paterno,
                    'apellido_materno': apellido_materno,
                    'tipo_documento': 'CC',
                    'numero_documento': rut,
                    'fecha_nacimiento': fecha_nacimiento,
                    'genero': genero,
                    'email': f"estudiante{estudiante_counter}@ejemplo.cl",
                    'codigo_estudiante': f"EST{estudiante_counter:04d}"
                }
            )
            
            # Asignar al curso
            estudiante.cursos.add(curso)
            estudiantes.append(estudiante)
            estudiante_counter += 1
    
    # 7. Crear apoderados
    print("👨‍👩‍👧‍👦 Creando apoderados...")
    nombres_apoderados_m = ['Pedro', 'Juan', 'Luis', 'Carlos', 'José', 'Manuel', 'Francisco', 'Antonio', 'Álvaro', 'Fernando']
    nombres_apoderados_f = ['María', 'Carmen', 'Ana', 'Isabel', 'Patricia', 'Rosa', 'Elena', 'Gloria', 'Mónica', 'Claudia']
    
    apoderados = []
    apoderado_counter = 1
    
    # Crear apoderados para grupos de hermanos y estudiantes individuales
    estudiantes_sin_apoderado = list(estudiantes)
    
    while estudiantes_sin_apoderado:
        # Decidir si es un grupo de hermanos (20% probabilidad) o estudiante individual
        es_grupo_hermanos = random.random() < 0.2 and len(estudiantes_sin_apoderado) > 1
        
        if es_grupo_hermanos:
            # Seleccionar 2-3 estudiantes como hermanos
            num_hermanos = min(random.randint(2, 3), len(estudiantes_sin_apoderado))
            estudiantes_hijos = random.sample(estudiantes_sin_apoderado, num_hermanos)
            # Usar el apellido del primer estudiante para los padres
            apellido_familia = estudiantes_hijos[0].apellido_paterno
        else:
            # Un solo estudiante
            estudiantes_hijos = [estudiantes_sin_apoderado[0]]
            apellido_familia = estudiantes_hijos[0].apellido_paterno
        
        # Remover estudiantes de la lista
        for estudiante in estudiantes_hijos:
            estudiantes_sin_apoderado.remove(estudiante)
        
        # Crear 1-2 apoderados por familia
        num_apoderados = random.randint(1, 2)
        
        for k in range(num_apoderados):
            genero = random.choice(['M', 'F'])
            nombres = random.sample(nombres_apoderados_m if genero == 'M' else nombres_apoderados_f, 2)
            
            # El segundo apoderado (si existe) tendrá apellido diferente en algunos casos
            if k == 1 and random.random() < 0.3:  # 30% de madres con apellido diferente
                apellido_paterno = random.choice(apellidos)
                apellido_materno = random.choice(apellidos)
            else:
                apellido_paterno = apellido_familia
                apellido_materno = random.choice(apellidos)
            
            # Crear usuario
            username = f"apoderado{apoderado_counter}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': ' '.join(nombres),
                    'last_name': f"{apellido_paterno} {apellido_materno}",
                    'email': f"apoderado{apoderado_counter}@ejemplo.cl",
                    'password': 'pbkdf2_sha256$600000$test$test'
                }
            )
            
            if created:
                user.set_password('apoderado123')
                user.save()
            
            # Crear perfil
            rut = f"{random.randint(10000000, 19999999)}-{random.randint(0, 9)}"
            perfil, created = Perfil.objects.get_or_create(
                user=user,
                defaults={
                    'tipo_usuario': 'apoderado',
                    'tipo_documento': 'CC',
                    'numero_documento': rut,
                    'fecha_nacimiento': date(random.randint(1975, 1995), random.randint(1, 12), random.randint(1, 28)),
                    'genero': genero,
                    'telefono': f"+5691234{random.randint(1000, 9999)}"
                }
            )
            
            # Crear apoderado
            parentesco = 'padre' if genero == 'M' else 'madre'
            if k == 1:  # Segundo apoderado puede ser otro pariente
                parentesco = random.choice(['padre', 'madre', 'abuelo', 'abuela', 'tío', 'tía'])
            
            apoderado, created = Apoderado.objects.get_or_create(
                user=user,
                defaults={
                    'primer_nombre': nombres[0],
                    'segundo_nombre': nombres[1] if len(nombres) > 1 else '',
                    'apellido_paterno': apellido_paterno,
                    'apellido_materno': apellido_materno,
                    'tipo_documento': 'CC',
                    'numero_documento': rut,
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
                        'es_apoderado_principal': k == 0,  # El primer apoderado es principal
                        'puede_retirar': True
                    }
                )
            
            apoderados.append(apoderado)
            apoderado_counter += 1
    
    # 8. Asignar asignaturas a profesores
    print("📋 Asignando asignaturas a profesores...")
    especialidades_asignaturas = {
        'Educación Básica': ['Matemáticas', 'Lenguaje y Comunicación'],
        'Matemáticas': ['Matemáticas'],
        'Lenguaje': ['Lenguaje y Comunicación'],
        'Historia': ['Historia y Geografía'],
        'Ciencias': ['Ciencias Naturales'],
        'Inglés': ['Inglés'],
        'Educación Física': ['Educación Física'],
        'Artes': ['Artes Visuales', 'Música'],
    }
    
    for profesor in profesores:
        asignaturas_profesor = especialidades_asignaturas.get(profesor.especialidad, ['Religión', 'Tecnología'])
        for nombre_asig in asignaturas_profesor:
            try:
                asignatura = Asignatura.objects.get(nombre=nombre_asig)
                profesor.asignaturas.add(asignatura)
            except Asignatura.DoesNotExist:
                pass
    
    # 9. Crear algunos eventos de calendario
    print("📅 Creando eventos de calendario...")
    eventos_data = [
        {
            'titulo': 'Inicio de clases',
            'descripcion': 'Primer día del año escolar 2025',
            'fecha': date(2025, 3, 1),
            'tipo': 'academico'
        },
        {
            'titulo': 'Reunión de apoderados 1° básico',
            'descripcion': 'Primera reunión del año para padres de 1° básico',
            'fecha': date(2025, 3, 15),
            'tipo': 'reunion'
        },
        {
            'titulo': 'Día del alumno',
            'descripcion': 'Celebración del día del estudiante',
            'fecha': date(2025, 5, 11),
            'tipo': 'celebracion'
        },
        {
            'titulo': 'Vacaciones de invierno',
            'descripcion': 'Período de vacaciones de invierno',
            'fecha': date(2025, 7, 15),
            'tipo': 'vacaciones'
        },
        {
            'titulo': 'Fiestas Patrias',
            'descripcion': 'Celebración de Fiestas Patrias',
            'fecha': date(2025, 9, 18),
            'tipo': 'celebracion'
        }
    ]
    
    for evento_data in eventos_data:
        EventoCalendario.objects.get_or_create(
            titulo=evento_data['titulo'],
            defaults={
                'descripcion': evento_data['descripcion'],
                'fecha': evento_data['fecha'],
                'tipo_evento': evento_data['tipo'],
                'creado_por': User.objects.filter(is_superuser=True).first()
            }
        )
    
    print("✅ ¡Base de datos poblada exitosamente!")
    print(f"📊 Resumen:")
    print(f"   • {Curso.objects.count()} cursos creados")
    print(f"   • {Asignatura.objects.count()} asignaturas creadas")
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
