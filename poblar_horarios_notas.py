import os
import django
import random
from datetime import date, time, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from smapp.models import (
    Curso, Asignatura, Profesor, Estudiante, 
    HorarioCurso, Grupo, Inscripcion, Calificacion,
    PeriodoAcademico, Salon
)

def poblar_horarios_y_notas():
    print("🚀 Iniciando poblado de Horarios y Notas...")

    # 1. Obtener datos existentes
    cursos = Curso.objects.all()
    asignaturas = list(Asignatura.objects.all())
    profesores = list(Profesor.objects.all())
    periodo = PeriodoAcademico.objects.first()
    
    if not periodo:
        print("❌ No se encontró Periodo Académico. Ejecuta poblar_bd_nuevo.py primero.")
        return

    # Crear un salón genérico si no existe
    salon, _ = Salon.objects.get_or_create(
        numero_salon="101",
        defaults={'capacidad': 40, 'ubicacion': 'Pabellón A'}
    )

    print(f"ℹ️ Procesando {cursos.count()} cursos...")

    # Bloques horarios
    bloques = [
        (time(8, 0), time(9, 30)),
        (time(9, 45), time(11, 15)),
        (time(11, 30), time(13, 0)),
        (time(14, 0), time(15, 30)),
        (time(15, 45), time(17, 15))
    ]
    dias = ['LU', 'MA', 'MI', 'JU', 'VI']

    for curso in cursos:
        print(f"  🏫 Curso: {curso.nombre}")
        
        # Asignar asignaturas al curso (si no las tiene)
        if curso.asignaturas.count() == 0:
            # Asignar todas las asignaturas básicas
            curso.asignaturas.set(asignaturas)
        
        asignaturas_curso = list(curso.asignaturas.all())
        estudiantes_curso = curso.estudiantes.all()

        # --- CREAR GRUPOS E INSCRIPCIONES ---
        grupos_curso = {} # Map asignatura -> grupo
        
        for asignatura in asignaturas_curso:
            # Asignar un profesor aleatorio a la asignatura si no tiene
            profesor = asignatura.profesor_responsable
            if not profesor and profesores:
                profesor = random.choice(profesores)
            
            # Crear Grupo
            grupo, created = Grupo.objects.get_or_create(
                asignatura=asignatura,
                periodo_academico=periodo,
                defaults={
                    'profesor': profesor,
                    'salon': salon,
                    'capacidad_maxima': 45
                }
            )
            grupos_curso[asignatura.id] = grupo

            # Inscribir estudiantes
            for estudiante in estudiantes_curso:
                inscripcion, created = Inscripcion.objects.get_or_create(
                    estudiante=estudiante,
                    grupo=grupo
                )
                
                # --- CREAR CALIFICACIONES ---
                if created or Calificacion.objects.filter(inscripcion=inscripcion).count() == 0:
                    # Crear 3 notas parciales
                    for i in range(1, 4):
                        nota = random.uniform(2.0, 7.0)
                        Calificacion.objects.create(
                            inscripcion=inscripcion,
                            nombre_evaluacion=f"Evaluación {i}",
                            puntaje=round(nota, 1),
                            porcentaje=33.3,
                            detalle="Evaluación generada automáticamente",
                            descripcion="Contenido de la unidad..."
                        )

        # --- CREAR HORARIO ---
        # Limpiar horarios existentes para evitar duplicados
        HorarioCurso.objects.filter(curso=curso).delete()
        
        for dia in dias:
            # Mezclar asignaturas para el día
            random.shuffle(asignaturas_curso)
            asignaturas_dia = asignaturas_curso[:len(bloques)] # Tomar tantas como bloques
            
            for i, bloque in enumerate(bloques):
                if i < len(asignaturas_dia):
                    asignatura = asignaturas_dia[i]
                    profesor = grupos_curso[asignatura.id].profesor
                    
                    HorarioCurso.objects.create(
                        curso=curso,
                        asignatura=asignatura,
                        profesor=profesor,
                        dia=dia,
                        hora_inicio=bloque[0],
                        hora_fin=bloque[1]
                    )

    print("\n✅ ¡Poblado de Horarios y Notas completado!")
    print(f"   • {HorarioCurso.objects.count()} bloques de horario creados")
    print(f"   • {Grupo.objects.count()} grupos creados")
    print(f"   • {Inscripcion.objects.count()} inscripciones creadas")
    print(f"   • {Calificacion.objects.count()} calificaciones creadas")

if __name__ == "__main__":
    poblar_horarios_y_notas()
