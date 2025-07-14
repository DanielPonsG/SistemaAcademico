#!/usr/bin/env python
"""
Script para agregar datos académicos de prueba a los estudiantes del apoderado 'zxc'
"""
import os
import django
import sys

# Agregar el directorio del proyecto al path
project_path = r'c:\Users\Danie\Desktop\Estudios\SAM-main'
sys.path.append(project_path)
os.chdir(project_path)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from django.contrib.auth.models import User
from smapp.models import (
    Apoderado, RelacionApoderadoEstudiante, Estudiante, 
    Calificacion, AsistenciaAlumno, Anotacion, Inscripcion,
    Asignatura, Grupo, Profesor, Curso
)
from django.utils import timezone
from datetime import datetime, timedelta
import random

def agregar_datos_academicos():
    print("=== AGREGANDO DATOS ACADÉMICOS DE PRUEBA ===")
    
    # Buscar apoderado zxc y sus estudiantes
    try:
        apoderado = Apoderado.objects.get(primer_nombre__icontains='zxc')
        relaciones = RelacionApoderadoEstudiante.objects.filter(apoderado=apoderado)
        
        print(f"✅ Procesando {relaciones.count()} estudiantes del apoderado {apoderado.primer_nombre}")
        
        # Obtener o crear algunas asignaturas básicas
        asignaturas_base = [
            'Matemática', 'Lenguaje y Comunicación', 'Historia', 'Ciencias Naturales',
            'Inglés', 'Educación Física', 'Artes Visuales', 'Música'
        ]
        
        asignaturas = []
        for nombre in asignaturas_base:
            asignatura, created = Asignatura.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'codigo_asignatura': nombre.upper()[:3] + '001',
                    'descripcion': f'Asignatura de {nombre}'
                }
            )
            asignaturas.append(asignatura)
            if created:
                print(f"📚 Creada asignatura: {nombre}")
        
        # Obtener o crear algunos profesores
        profesores = []
        nombres_profesores = [
            ('Ana', 'García'), ('Carlos', 'López'), ('María', 'Rodríguez'),
            ('Pedro', 'Martínez'), ('Laura', 'González')
        ]
        
        for nombre, apellido in nombres_profesores:
            try:
                profesor = Profesor.objects.get(primer_nombre=nombre, apellido_paterno=apellido)
                profesores.append(profesor)
            except Profesor.DoesNotExist:
                print(f"⚠️ Profesor {nombre} {apellido} no encontrado, usando profesores existentes")
        
        # Si no hay profesores, usar los existentes
        if not profesores:
            profesores = list(Profesor.objects.all()[:5])
            print(f"📋 Usando {len(profesores)} profesores existentes")
        
        # Procesar cada estudiante
        for relacion in relaciones:
            estudiante = relacion.estudiante
            print(f"\n👨‍🎓 Procesando: {estudiante.get_nombre_completo()}")
            
            # 1. Asignar profesor jefe al curso (si no tiene)
            curso = estudiante.get_curso_actual()
            if curso and not curso.profesor_jefe and profesores:
                curso.profesor_jefe = profesores[0]
                curso.save()
                print(f"   ✅ Asignado profesor jefe: {curso.profesor_jefe}")
            
            # 2. Crear inscripciones en asignaturas
            inscripciones_existentes = Inscripcion.objects.filter(estudiante=estudiante).count()
            if inscripciones_existentes == 0:
                print("   📝 Creando inscripciones en asignaturas...")
                
                # Obtener o crear periodo académico actual
                from smapp.models import PeriodoAcademico
                periodo_actual, created = PeriodoAcademico.objects.get_or_create(
                    nombre="2025",
                    defaults={
                        'fecha_inicio': datetime(2025, 3, 1).date(),
                        'fecha_fin': datetime(2025, 12, 15).date(),
                        'activo': True
                    }
                )
                
                for i, asignatura in enumerate(asignaturas[:6]):  # Inscribir en 6 asignaturas
                    profesor = profesores[i % len(profesores)] if profesores else None
                    
                    # Buscar o crear grupo para esta asignatura
                    grupo, created = Grupo.objects.get_or_create(
                        asignatura=asignatura,
                        profesor=profesor,
                        periodo_academico=periodo_actual,
                        defaults={
                            'capacidad_maxima': 30
                        }
                    )
                    
                    # Crear inscripción
                    inscripcion, created = Inscripcion.objects.get_or_create(
                        estudiante=estudiante,
                        grupo=grupo,
                        defaults={
                            'fecha_inscripcion': timezone.now().date()
                        }
                    )
                    
                    if created:
                        print(f"     • {asignatura.nombre} (Prof: {profesor})")
            
            # 3. Crear calificaciones de prueba
            inscripciones = Inscripcion.objects.filter(estudiante=estudiante)
            calificaciones_existentes = Calificacion.objects.filter(inscripcion__estudiante=estudiante).count()
            
            if calificaciones_existentes == 0 and inscripciones.exists():
                print("   📊 Creando calificaciones de prueba...")
                
                for inscripcion in inscripciones:
                    # Crear 3-5 calificaciones por asignatura
                    num_notas = random.randint(3, 5)
                    for j in range(num_notas):
                        fecha_eval = timezone.now().date() - timedelta(days=random.randint(1, 60))
                        puntaje = round(random.uniform(4.0, 7.0), 1)
                        
                        Calificacion.objects.create(
                            inscripcion=inscripcion,
                            nombre_evaluacion=f"Evaluación {j+1}",
                            puntaje=puntaje,
                            fecha_evaluacion=fecha_eval,
                            descripcion=f"Evaluación {j+1} de {inscripcion.grupo.asignatura.nombre}"
                        )
                    
                    print(f"     • {inscripcion.grupo.asignatura.nombre}: {num_notas} calificaciones")
            
            # 4. Crear registros de asistencia
            asistencias_existentes = AsistenciaAlumno.objects.filter(estudiante=estudiante).count()
            if asistencias_existentes == 0:
                print("   📅 Creando registros de asistencia...")
                
                # Crear asistencia para los últimos 30 días
                for i in range(30):
                    fecha = timezone.now().date() - timedelta(days=i)
                    # Saltear fines de semana
                    if fecha.weekday() < 5:  # 0-4 son lunes a viernes
                        presente = random.choice([True, True, True, True, False])  # 80% presente
                        
                        # Usar la primera asignatura del estudiante para la asistencia
                        inscripciones = Inscripcion.objects.filter(estudiante=estudiante)
                        if inscripciones.exists() and curso:
                            asignatura = inscripciones.first().grupo.asignatura
                            
                            AsistenciaAlumno.objects.create(
                                estudiante=estudiante,
                                curso=curso,
                                asignatura=asignatura,
                                fecha=fecha,
                                presente=presente,
                                justificacion="Enfermedad" if not presente else "",
                                observacion=f"Asistencia del {fecha}"
                            )
                
                print(f"     • Creados registros para últimos 30 días")
            
            # 5. Crear algunas anotaciones
            anotaciones_existentes = Anotacion.objects.filter(estudiante=estudiante).count()
            if anotaciones_existentes == 0 and profesores:
                print("   📝 Creando anotaciones de prueba...")
                
                tipos_anotacion = ['positiva', 'negativa', 'neutra']
                descripciones = {
                    'positiva': [
                        'Excelente participación en clase',
                        'Ayuda a sus compañeros',
                        'Entrega trabajos a tiempo'
                    ],
                    'negativa': [
                        'Llegó tarde a clases',
                        'No trajo materiales',
                        'Conversó durante la explicación'
                    ],
                    'neutra': [
                        'Padre solicita reunión',
                        'Estudiante se siente mareado',
                        'Cambio de horario médico'
                    ]
                }
                
                for i in range(3):  # 3 anotaciones por estudiante
                    tipo = random.choice(tipos_anotacion)
                    descripcion = random.choice(descripciones[tipo])
                    fecha = timezone.now() - timedelta(days=random.randint(1, 30))
                    
                    if curso:  # Solo crear si tiene curso
                        Anotacion.objects.create(
                            estudiante=estudiante,
                            curso=curso,
                            profesor_autor=profesores[i % len(profesores)],
                            tipo=tipo,
                            categoria='comportamiento',
                            titulo=f"Anotación {tipo}",
                            descripcion=descripcion,
                            fecha_creacion=fecha,
                            es_grave=random.choice([True, False]) if tipo == 'negativa' else False
                        )
                
                print(f"     • Creadas 3 anotaciones")
        
        print("\n🎉 ¡Datos académicos de prueba agregados exitosamente!")
        print("El panel de apoderados ahora debería mostrar información completa.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    agregar_datos_academicos()
