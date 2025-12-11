import os
import sys
import random
import django
from datetime import date, datetime, timedelta, time

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from django.contrib.auth.models import User
from smapp.models import (
    Asignatura, Curso, Profesor, Estudiante, Apoderado, 
    RelacionApoderadoEstudiante, EventoCalendario, PeriodoAcademico,
    Perfil, Grupo, Inscripcion, Calificacion, Anotacion, Salon,
    AsistenciaAlumno
)
from django.utils import timezone

def poblar_datos():
    print("Iniciando poblado de datos completo...")

    # --- 1. Limpieza Selectiva (Para evitar duplicados) ---
    print("Limpiando datos de prueba antiguos...")
    
    # Lista de usuarios a limpiar
    usernames_to_clean = ['director']
    usernames_to_clean += [f'profesor{i}' for i in range(1, 4)]
    usernames_to_clean += [f'estudiante{i}' for i in range(1, 21)]
    usernames_to_clean += [f'apoderado{i}' for i in range(1, 6)]
    
    # Eliminar usuarios (esto elimina perfiles y datos relacionados por CASCADE)
    User.objects.filter(username__in=usernames_to_clean).delete()
    
    # Eliminar por códigos si quedaron huérfanos (por seguridad)
    Estudiante.objects.filter(codigo_estudiante__in=[f'EST{i:03d}' for i in range(1, 21)]).delete()
    Profesor.objects.filter(codigo_profesor__in=[f'PROF{i}' for i in range(1, 4)]).delete()
    Apoderado.objects.filter(codigo_apoderado__in=[f'APO{i}' for i in range(1, 6)]).delete()

    # --- 2. Periodo Académico ---
    print("Creando/Obteniendo Periodo Académico...")
    periodo, _ = PeriodoAcademico.objects.get_or_create(
        nombre='Año Académico 2025',
        defaults={
            'fecha_inicio': date(2025, 3, 1),
            'fecha_fin': date(2025, 12, 15),
            'activo': True
        }
    )

    # --- 3. Salones ---
    print("Creando Salones...")
    salones = []
    for i in range(1, 11):
        salon, _ = Salon.objects.get_or_create(
            numero_salon=f"S-{100+i}",
            defaults={'capacidad': 35, 'ubicacion': 'Pabellón A'}
        )
        salones.append(salon)

    # --- 4. Asignaturas ---
    print("Creando Asignaturas...")
    asignaturas_data = [
        {'nombre': 'Matemáticas', 'codigo': 'MAT'},
        {'nombre': 'Lenguaje', 'codigo': 'LEN'},
        {'nombre': 'Historia', 'codigo': 'HIS'},
        {'nombre': 'Ciencias', 'codigo': 'CIE'},
        {'nombre': 'Inglés', 'codigo': 'ING'},
        {'nombre': 'Educación Física', 'codigo': 'EFI'},
    ]
    asignaturas = []
    for data in asignaturas_data:
        asig, _ = Asignatura.objects.get_or_create(
            codigo_asignatura=data['codigo'],
            defaults={'nombre': data['nombre']}
        )
        asignaturas.append(asig)

    # --- 5. Usuarios y Perfiles ---
    print("Creando Usuarios...")

    # Director
    user_dir, created = User.objects.get_or_create(username='director', defaults={'email': 'director@escuela.cl', 'first_name': 'Director', 'last_name': 'Principal'})
    if created: user_dir.set_password('director123'); user_dir.save()
    Perfil.objects.get_or_create(user=user_dir, defaults={'tipo_usuario': 'director', 'cargo': 'Director General'})

    # Profesores (3)
    profesores = []
    for i in range(1, 4):
        username = f'profesor{i}'
        user, created = User.objects.get_or_create(username=username, defaults={'email': f'{username}@escuela.cl', 'first_name': f'Profesor', 'last_name': f'{i}'})
        if created: user.set_password('profesor123'); user.save()
        
        perfil, _ = Perfil.objects.get_or_create(user=user, defaults={'tipo_usuario': 'profesor', 'tipo_documento': 'CC', 'numero_documento': f'1000000{i}'})
        
        prof, _ = Profesor.objects.get_or_create(
            user=user,
            defaults={
                'primer_nombre': f'Profesor', 'apellido_paterno': f'{i}',
                'codigo_profesor': f'PROF{i}', 'especialidad': 'General',
                'email': user.email, 'numero_documento': perfil.numero_documento,
                'fecha_nacimiento': date(1980, 1, 1), 'genero': 'M'
            }
        )
        profesores.append(prof)

    # Asignar asignaturas a profesores (simple round-robin)
    for idx, asig in enumerate(asignaturas):
        prof = profesores[idx % len(profesores)]
        asig.profesor_responsable = prof
        asig.save()
        prof.asignaturas.add(asig)

    # Cursos (Solo unos pocos para demo)
    print("Creando Cursos...")
    cursos_demo = ['1M', '2M'] # 1° Medio, 2° Medio
    cursos_objs = []
    for nivel in cursos_demo:
        curso, _ = Curso.objects.get_or_create(
            nivel=nivel, paralelo='A', anio=2025,
            defaults={'profesor_jefe': profesores[0]}
        )
        cursos_objs.append(curso)

    # Estudiantes (20)
    print("Creando Estudiantes...")
    estudiantes = []
    for i in range(1, 21):
        username = f'estudiante{i}'
        user, created = User.objects.get_or_create(username=username, defaults={'email': f'{username}@escuela.cl', 'first_name': 'Estudiante', 'last_name': f'{i}'})
        if created: user.set_password('estudiante123'); user.save()

        perfil, _ = Perfil.objects.get_or_create(user=user, defaults={'tipo_usuario': 'alumno', 'numero_documento': f'200000{i:02d}'})
        
        est, _ = Estudiante.objects.get_or_create(
            user=user,
            defaults={
                'primer_nombre': 'Estudiante', 'apellido_paterno': f'{i}',
                'codigo_estudiante': f'EST{i:03d}',
                'numero_documento': perfil.numero_documento,
                'fecha_nacimiento': date(2010, 1, 1), 'genero': random.choice(['M', 'F']),
                'email': user.email
            }
        )
        estudiantes.append(est)
        
        # Matricular en curso (mitad en 1M, mitad en 2M)
        curso_destino = cursos_objs[0] if i <= 10 else cursos_objs[1]
        if est not in curso_destino.estudiantes.all():
            curso_destino.estudiantes.add(est)

    # Apoderados (5)
    print("Creando Apoderados...")
    for i in range(1, 6):
        username = f'apoderado{i}'
        user, created = User.objects.get_or_create(username=username, defaults={'email': f'{username}@escuela.cl', 'first_name': 'Apoderado', 'last_name': f'{i}'})
        if created: user.set_password('apoderado123'); user.save()

        perfil, _ = Perfil.objects.get_or_create(user=user, defaults={'tipo_usuario': 'apoderado', 'numero_documento': f'300000{i}'})
        
        apo, _ = Apoderado.objects.get_or_create(
            user=user,
            defaults={
                'primer_nombre': 'Apoderado', 'apellido_paterno': f'{i}',
                'codigo_apoderado': f'APO{i}',
                'numero_documento': perfil.numero_documento,
                'fecha_nacimiento': date(1975, 1, 1), 'genero': random.choice(['M', 'F']),
                'email': user.email
            }
        )
        
        # Asignar pupilos (4 estudiantes por apoderado para cubrir los 20)
        start_idx = (i - 1) * 4
        end_idx = start_idx + 4
        pupilos = estudiantes[start_idx:end_idx]
        for pupilo in pupilos:
            RelacionApoderadoEstudiante.objects.get_or_create(
                apoderado=apo, estudiante=pupilo,
                defaults={'parentesco': 'padre', 'es_apoderado_principal': True}
            )

    # --- 6. Grupos e Inscripciones (Lógica Académica) ---
    print("Creando Grupos e Inscripciones...")
    grupos = []
    for curso in cursos_objs:
        for asig in asignaturas:
            # Crear Grupo
            grupo, _ = Grupo.objects.get_or_create(
                asignatura=asig,
                periodo_academico=periodo,
                profesor=asig.profesor_responsable, # Asignar el profe responsable de la asignatura
                defaults={'salon': salones[0], 'capacidad_maxima': 40}
            )
            grupos.append(grupo)
            
            # Inscribir estudiantes del curso en el grupo
            for est in curso.estudiantes.all():
                inscripcion, _ = Inscripcion.objects.get_or_create(
                    estudiante=est,
                    grupo=grupo
                )
                
                # --- 7. Calificaciones ---
                # Crear 3 notas parciales aleatorias
                if Calificacion.objects.filter(inscripcion=inscripcion).count() == 0:
                    for n in range(1, 4):
                        nota = random.uniform(2.0, 7.0)
                        Calificacion.objects.create(
                            inscripcion=inscripcion,
                            nombre_evaluacion=f'Evaluación {n}',
                            puntaje=round(nota, 1),
                            porcentaje=33.3,
                            fecha_evaluacion=date(2025, 3 + n, 15)
                        )

    # --- 8. Anotaciones ---
    print("Creando Anotaciones...")
    tipos = ['positiva', 'negativa', 'neutra']
    for est in estudiantes:
        if random.random() > 0.5: # 50% de tener anotación
            tipo = random.choice(tipos)
            curso_est = est.cursos.last() # Asumimos el último curso
            prof_autor = profesores[0]
            Anotacion.objects.create(
                estudiante=est,
                curso=curso_est,
                profesor_autor=prof_autor,
                tipo=tipo,
                titulo=f"Anotación de comportamiento {tipo}",
                descripcion="Comportamiento observado en clase durante la semana.",
                fecha_creacion=timezone.now()
            )

    # --- 9. Eventos Calendario ---
    print("Creando Eventos...")
    eventos = [
        {'titulo': 'Prueba de Matemáticas', 'fecha': date(2025, 4, 10), 'tipo': 'evaluacion'},
        {'titulo': 'Reunión de Apoderados', 'fecha': date(2025, 4, 20), 'tipo': 'reunion'},
        {'titulo': 'Día del Alumno', 'fecha': date(2025, 5, 11), 'tipo': 'actividad'},
    ]
    for ev in eventos:
        EventoCalendario.objects.get_or_create(
            titulo=ev['titulo'],
            fecha=ev['fecha'],
            defaults={
                'tipo_evento': ev['tipo'],
                'para_todos_los_cursos': True,
                'descripcion': 'Evento generado automáticamente'
            }
        )

    print("\nProceso finalizado exitosamente.")
    print("Credenciales:")
    print("Director: director / director123")
    print("Profesor: profesor1 / profesor123")
    print("Estudiante: estudiante1 / estudiante123")
    print("Apoderado: apoderado1 / apoderado123")

if __name__ == '__main__':
    poblar_datos()
