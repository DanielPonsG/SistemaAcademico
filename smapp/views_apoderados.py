from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Apoderado, RelacionApoderadoEstudiante, Estudiante
from .forms import ApoderadoForm

def verificar_permisos_admin_director(user):
    """Verifica si el usuario tiene permisos de administrador o director"""
    if user.is_superuser:
        return True
    
    try:
        if hasattr(user, 'perfil') and user.perfil:
            return user.perfil.tipo_usuario in ['administrador', 'director']
    except:
        pass
    
    return False

def detectar_y_redirigir_apoderado(request):
    """Función auxiliar para detectar y redirigir apoderados"""
    if not request.user.is_authenticated:
        return None
        
    # Verificar si el usuario es un apoderado
    try:
        apoderado = request.user.apoderado
        return redirect('dashboard_apoderado')
    except:
        pass
    
    # Verificar si es un profesor que también es apoderado
    try:
        if hasattr(request.user, 'profesor'):
            profesor = request.user.profesor
            if hasattr(profesor, 'apoderado_profile') and profesor.apoderado_profile:
                return redirect('dashboard_profesor_apoderado')
    except:
        pass
    
    return None

@login_required
def listar_apoderados(request):
    """Vista para listar todos los apoderados con filtros"""
    
    # Verificar permisos
    if not verificar_permisos_admin_director(request.user):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('inicio')
    
    # Obtener parámetros de filtro
    q_apoderado = request.GET.get('q_apoderado', '')
    parentesco = request.GET.get('parentesco', '')
    es_profesor_filter = request.GET.get('es_profesor', '')
    
    # Filtros base
    apoderados = Apoderado.objects.all()
    
    # Aplicar filtros
    if q_apoderado:
        apoderados = apoderados.filter(
            Q(primer_nombre__icontains=q_apoderado) |
            Q(segundo_nombre__icontains=q_apoderado) |
            Q(apellido_paterno__icontains=q_apoderado) |
            Q(apellido_materno__icontains=q_apoderado) |
            Q(numero_documento__icontains=q_apoderado) |
            Q(email__icontains=q_apoderado)
        )
    
    if parentesco:
        apoderados = apoderados.filter(parentesco_principal=parentesco)
    
    if es_profesor_filter:
        if es_profesor_filter == 'si':
            apoderados = apoderados.filter(profesor__isnull=False)
        elif es_profesor_filter == 'no':
            apoderados = apoderados.filter(profesor__isnull=True)
    
    # Agregar información adicional con anotaciones
    apoderados = apoderados.annotate(
        num_estudiantes=Count('estudiantes_a_cargo', distinct=True)
    ).prefetch_related(
        'estudiantes_a_cargo__estudiante',
        'estudiantes_a_cargo__estudiante__cursos'
    ).order_by('apellido_paterno', 'primer_nombre')
    
    # Paginación
    paginator = Paginator(apoderados, 15)  # 15 apoderados por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calcular estadísticas adicionales
    total_apoderados_count = apoderados.count()
    apoderados_profesores_count = apoderados.filter(profesor__isnull=False).count()
    apoderados_externos_count = total_apoderados_count - apoderados_profesores_count
    
    # Contexto para el template
    context = {
        'page_obj': page_obj,
        'apoderados': page_obj,
        'q_apoderado': q_apoderado,
        'parentesco': parentesco,
        'es_profesor': es_profesor_filter,
        'parentesco_choices': Apoderado.PARENTESCO_CHOICES,
        'total_apoderados': total_apoderados_count,
        'apoderados_profesores': apoderados_profesores_count,
        'apoderados_externos': apoderados_externos_count,
    }
    
    return render(request, 'listar_apoderados.html', context)

@login_required
def gestionar_apoderado(request, apoderado_id=None):
    """Vista para crear o editar un apoderado usando el template agregar.html unificado"""
    
    # Verificar permisos
    if not verificar_permisos_admin_director(request.user):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('inicio')
    
    apoderado = None
    es_edicion = bool(apoderado_id)
    mensaje = ""
    
    if apoderado_id:
        apoderado = get_object_or_404(Apoderado, id=apoderado_id)
    
    if request.method == 'POST':
        form = ApoderadoForm(request.POST, instance=apoderado)
        if form.is_valid():
            apoderado_obj = form.save()
            if apoderado_id:
                mensaje = f'Apoderado {apoderado_obj.get_nombre_completo()} actualizado correctamente.'
                messages.success(request, mensaje)
                return redirect('listar_apoderados')
            else:
                mensaje = f'Apoderado {apoderado_obj.get_nombre_completo()} creado correctamente.'
                form = ApoderadoForm()  # Limpiar formulario después de crear
    else:
        form = ApoderadoForm(instance=apoderado)
    
    # Contexto compatible con agregar.html
    context = {
        'form': form,
        'tipo': 'apoderado',  # Siempre apoderado para esta vista
        'mensaje': mensaje,
        'es_edicion': es_edicion,
        'apoderado': apoderado,
    }
    
    return render(request, 'agregar.html', context)

@login_required
def eliminar_apoderado(request, apoderado_id):
    """Vista para eliminar un apoderado"""
    
    # Verificar permisos
    if not verificar_permisos_admin_director(request.user):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('inicio')
    
    apoderado = get_object_or_404(Apoderado, id=apoderado_id)
    
    if request.method == 'POST':
        nombre_completo = apoderado.get_nombre_completo()
        
        # Verificar si tiene estudiantes asociados
        relaciones = RelacionApoderadoEstudiante.objects.filter(apoderado=apoderado)
        if relaciones.exists():
            messages.error(request, f'No se puede eliminar al apoderado {nombre_completo} porque tiene estudiantes asociados.')
        else:
            apoderado.delete()
            messages.success(request, f'Apoderado {nombre_completo} eliminado correctamente.')
        
        return redirect('listar_apoderados')
    
    # Obtener estudiantes asociados para mostrar en la confirmación
    estudiantes_asociados = RelacionApoderadoEstudiante.objects.filter(
        apoderado=apoderado
    ).select_related('estudiante')
    
    context = {
        'apoderado': apoderado,
        'estudiantes_asociados': estudiantes_asociados,
    }
    
    return render(request, 'confirmar_eliminar_apoderado.html', context)

@login_required
def detalle_apoderado(request, apoderado_id):
    """Vista para ver el detalle completo de un apoderado"""
    
    # Verificar permisos
    if not verificar_permisos_admin_director(request.user):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('inicio')
    
    apoderado = get_object_or_404(Apoderado, id=apoderado_id)
    
    # Obtener estudiantes asociados
    relaciones = RelacionApoderadoEstudiante.objects.filter(
        apoderado=apoderado
    ).select_related('estudiante').prefetch_related('estudiante__cursos')
    
    context = {
        'apoderado': apoderado,
        'relaciones': relaciones,
        'total_estudiantes': relaciones.count(),
    }
    
    return render(request, 'detalle_apoderado.html', context)

@login_required
def dashboard_apoderado(request):
    """Vista de dashboard para apoderados normales - redirige a inicio.html"""
    
    # Verificar que el usuario sea un apoderado
    try:
        apoderado = request.user.apoderado
        return _preparar_contexto_apoderado(request, apoderado, es_profesor_apoderado=False)
    except AttributeError:
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        # Redirigir al login en lugar de inicio para evitar bucles
        return redirect('login')

@login_required
def dashboard_profesor_apoderado(request):
    """Vista especial para profesores que también son apoderados - redirige a inicio.html"""
    
    # Verificar que el usuario sea un profesor
    try:
        profesor = request.user.profesor
    except AttributeError:
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        # Redirigir al login en lugar de inicio para evitar bucles
        return redirect('login')
    
    # Verificar que también sea apoderado
    try:
        apoderado = profesor.apoderado_profile
        return _preparar_contexto_profesor_apoderado(request, profesor, apoderado)
    except AttributeError:
        # Si no es apoderado, redirigir al dashboard normal de profesor
        messages.info(request, "No tienes estudiantes a cargo como apoderado.")
        # Crear un contexto básico para mostrar un mensaje
        context = {
            'user': request.user,
            'es_profesor_apoderado': True,
            'tiene_estudiantes': False,
            'mensaje': 'No tienes estudiantes a cargo como apoderado.'
        }
        return render(request, 'inicio.html', context)

@login_required
def inicio_apoderado(request):
    """Vista para manejar el inicio de apoderados usando inicio.html"""
    
    # Verificar si es un apoderado directo
    try:
        apoderado = request.user.apoderado
        return _preparar_contexto_apoderado(request, apoderado, es_profesor_apoderado=False)
    except AttributeError:
        pass
    
    # Verificar si es un profesor-apoderado
    try:
        if hasattr(request.user, 'profesor'):
            profesor = request.user.profesor
            if hasattr(profesor, 'apoderado_profile') and profesor.apoderado_profile:
                return _preparar_contexto_profesor_apoderado(request, profesor, profesor.apoderado_profile)
    except AttributeError:
        pass
    
    # Si no es apoderado, mostrar mensaje y redirigir al login
    messages.error(request, "No tienes permisos de apoderado.")
    return redirect('login')

@login_required
def estudiantes_a_cargo_profesor_apoderado(request):
    """Vista específica para que profesores-apoderados vean sus estudiantes a cargo"""
    
    # Verificar que el usuario sea un profesor
    try:
        profesor = request.user.profesor
    except AttributeError:
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('inicio')
    
    # Verificar que también sea apoderado
    try:
        apoderado = profesor.apoderado_profile
        if not apoderado:
            messages.error(request, "No tienes estudiantes a cargo como apoderado.")
            return redirect('inicio')
    except AttributeError:
        messages.error(request, "No tienes estudiantes a cargo como apoderado.")
        return redirect('inicio')
    
    # Obtener estudiantes a cargo del apoderado
    estudiantes_a_cargo = RelacionApoderadoEstudiante.objects.filter(
        apoderado=apoderado,
        activa=True
    ).select_related(
        'estudiante'
    ).prefetch_related(
        'estudiante__cursos',
        'estudiante__cursos__profesor_jefe'
    ).order_by('estudiante__apellido_paterno', 'estudiante__primer_nombre')
    
    # Preparar información detallada de cada estudiante
    estudiantes_info = []
    for relacion in estudiantes_a_cargo:
        estudiante = relacion.estudiante
        curso_actual = estudiante.get_curso_actual()
        
        # Obtener información académica básica
        from .models import Calificacion, AsistenciaAlumno, Anotacion, Inscripcion
        from django.utils import timezone
        from django.db.models import Avg
        
        # Promedio general del estudiante
        promedio_obj = Calificacion.objects.filter(
            inscripcion__estudiante=estudiante
        ).aggregate(promedio=Avg('puntaje'))
        promedio_general = round(promedio_obj['promedio'], 1) if promedio_obj['promedio'] else None
        
        # Asistencia del mes actual
        hoy = timezone.now().date()
        inicio_mes = hoy.replace(day=1)
        asistencias_mes = AsistenciaAlumno.objects.filter(
            estudiante=estudiante,
            fecha__gte=inicio_mes,
            fecha__lte=hoy
        )
        total_asistencias = asistencias_mes.count()
        asistencias_presentes = asistencias_mes.filter(presente=True).count()
        porcentaje_asistencia = round((asistencias_presentes / total_asistencias * 100), 1) if total_asistencias > 0 else 0
        
        # Anotaciones recientes (últimas 3)
        anotaciones_recientes = Anotacion.objects.filter(
            estudiante=estudiante
        ).select_related('profesor_autor').order_by('-fecha_creacion')[:3]
        
        # Total de asignaturas del estudiante
        total_asignaturas = Inscripcion.objects.filter(estudiante=estudiante).count()
        
        estudiante_data = {
            'estudiante': estudiante,
            'relacion': relacion,
            'curso_actual': curso_actual,
            'profesor_jefe': curso_actual.profesor_jefe if curso_actual else None,
            'promedio_general': promedio_general,
            'total_asistencias': total_asistencias,
            'asistencias_presentes': asistencias_presentes,
            'ausencias': total_asistencias - asistencias_presentes,
            'porcentaje_asistencia': porcentaje_asistencia,
            'anotaciones_recientes': anotaciones_recientes,
            'total_asignaturas': total_asignaturas,
            'total_anotaciones': anotaciones_recientes.count() if anotaciones_recientes else 0,
        }
        estudiantes_info.append(estudiante_data)
    
    # Calcular estadísticas generales
    total_estudiantes = len(estudiantes_info)
    estudiantes_con_promedio = [e for e in estudiantes_info if e['promedio_general']]
    promedio_general_conjunto = None
    if estudiantes_con_promedio:
        suma_promedios = sum(e['promedio_general'] for e in estudiantes_con_promedio)
        promedio_general_conjunto = round(suma_promedios / len(estudiantes_con_promedio), 1)
    
    estudiantes_con_asistencia = [e for e in estudiantes_info if e['total_asistencias'] > 0]
    promedio_asistencia_conjunto = None
    if estudiantes_con_asistencia:
        suma_asistencia = sum(e['porcentaje_asistencia'] for e in estudiantes_con_asistencia)
        promedio_asistencia_conjunto = round(suma_asistencia / len(estudiantes_con_asistencia), 1)
    
    context = {
        'profesor': profesor,
        'apoderado': apoderado,
        'estudiantes_a_cargo': estudiantes_a_cargo,
        'estudiantes_info': estudiantes_info,
        'total_estudiantes': total_estudiantes,
        'promedio_general_conjunto': promedio_general_conjunto,
        'promedio_asistencia_conjunto': promedio_asistencia_conjunto,
        'es_profesor_apoderado': True,
    }
    
    return render(request, 'estudiantes_a_cargo_profesor_apoderado.html', context)

def _preparar_contexto_apoderado(request, apoderado, es_profesor_apoderado=False):
    """Función auxiliar para preparar el contexto de un apoderado"""
    
    # Obtener estudiantes a cargo
    estudiantes_a_cargo = RelacionApoderadoEstudiante.objects.filter(
        apoderado=apoderado
    ).select_related(
        'estudiante'
    ).prefetch_related(
        'estudiante__cursos',
        'estudiante__cursos__profesor_jefe'
    )
    
    # Estadísticas básicas
    total_estudiantes = estudiantes_a_cargo.count()
    
    # Información para cada estudiante
    estudiantes_info = []
    for relacion in estudiantes_a_cargo:
        estudiante = relacion.estudiante
        
        # Obtener curso actual del estudiante
        curso_actual = estudiante.get_curso_actual()
        
        # Obtener calificaciones recientes (últimas 5)
        # Usando el modelo Calificacion a través de inscripcion
        from .models import Calificacion, Inscripcion
        notas_recientes = Calificacion.objects.filter(
            inscripcion__estudiante=estudiante
        ).select_related('inscripcion__grupo__asignatura').order_by('-fecha_evaluacion')[:5]
        
        # Obtener asistencia del mes actual
        from django.utils import timezone
        hoy = timezone.now().date()
        inicio_mes = hoy.replace(day=1)
        
        from .models import AsistenciaAlumno
        asistencias_mes = AsistenciaAlumno.objects.filter(
            estudiante=estudiante,
            fecha__gte=inicio_mes,
            fecha__lte=hoy
        )
        
        total_asistencias = asistencias_mes.count()
        asistencias_presentes = asistencias_mes.filter(presente=True).count()
        ausencias = total_asistencias - asistencias_presentes
        porcentaje_asistencia = round((asistencias_presentes / total_asistencias * 100), 1) if total_asistencias > 0 else 0
        
        # Obtener anotaciones recientes (últimas 3)
        from .models import Anotacion
        anotaciones_recientes = Anotacion.objects.filter(
            estudiante=estudiante
        ).select_related('profesor_autor').order_by('-fecha_creacion')[:3]
        
        # Calcular promedio general
        promedio_general = None
        if notas_recientes.exists():
            from django.db.models import Avg
            promedio_obj = Calificacion.objects.filter(
                inscripcion__estudiante=estudiante
            ).aggregate(promedio=Avg('puntaje'))
            promedio_general = round(promedio_obj['promedio'], 1) if promedio_obj['promedio'] else None
        
        # Obtener información básica del estudiante
        
        # Obtener asignaturas con notas del estudiante
        from .models import Grupo
        asignaturas_con_notas = []
        inscripciones = Inscripcion.objects.filter(estudiante=estudiante).select_related(
            'grupo__asignatura',
            'grupo__profesor'
        )
        
        for inscripcion in inscripciones:
            calificaciones = Calificacion.objects.filter(inscripcion=inscripcion).order_by('fecha_evaluacion')
            promedio_asignatura = None
            if calificaciones.exists():
                from django.db.models import Avg
                promedio_obj = calificaciones.aggregate(promedio=Avg('puntaje'))
                promedio_asignatura = round(promedio_obj['promedio'], 1) if promedio_obj['promedio'] else None
            
            asignaturas_con_notas.append({
                'asignatura': inscripcion.grupo.asignatura,
                'profesor': inscripcion.grupo.profesor,
                'promedio': promedio_asignatura,
                'total_notas': calificaciones.count(),
                'calificaciones_detalle': calificaciones,
            })
        
        # Obtener horarios de la semana
        from .models import HorarioCurso
        horarios_semana = {}
        if curso_actual:
            horarios = HorarioCurso.objects.filter(
                curso=curso_actual
            ).select_related('asignatura').order_by('hora_inicio', 'dia')
            
            # Organizar horarios por bloque de tiempo
            for horario in horarios:
                hora_key = f"{horario.hora_inicio.strftime('%H:%M')} - {horario.hora_fin.strftime('%H:%M')}"
                if hora_key not in horarios_semana:
                    horarios_semana[hora_key] = []
                horarios_semana[hora_key].append(horario)

        # Obtener compañeros de curso
        companeros = []
        if curso_actual:
            companeros = Estudiante.objects.filter(
                cursos=curso_actual
            ).exclude(id=estudiante.id).order_by('apellido_paterno', 'apellido_materno', 'primer_nombre')

        # Obtener asistencia anual para detalles
        inicio_ano = hoy.replace(month=1, day=1)
        asistencia_anual = AsistenciaAlumno.objects.filter(
            estudiante=estudiante,
            fecha__gte=inicio_ano,
            fecha__lte=hoy
        ).order_by('-fecha')
        
        # Obtener asistencia reciente (últimos 7 días)
        from datetime import timedelta
        fecha_limite = hoy - timedelta(days=7)
        asistencia_reciente = AsistenciaAlumno.objects.filter(
            estudiante=estudiante,
            fecha__gte=fecha_limite,
            fecha__lte=hoy
        ).order_by('-fecha')[:7]
        
        estudiante_data = {
            'estudiante': estudiante,
            'parentesco': relacion.parentesco,
            'curso': curso_actual,
            'profesor_jefe': curso_actual.profesor_jefe if curso_actual else None,
            'notas_recientes': notas_recientes,
            'promedio_general': promedio_general,
            'total_asistencias': total_asistencias,
            'asistencias_presentes': asistencias_presentes,
            'ausencias': ausencias,
            'porcentaje_asistencia': porcentaje_asistencia,
            'anotaciones_recientes': anotaciones_recientes,
            'asignaturas_con_notas': asignaturas_con_notas,
            'total_asignaturas': len(asignaturas_con_notas),
            'total_anotaciones': anotaciones_recientes.count() if hasattr(anotaciones_recientes, 'count') else len(anotaciones_recientes),
            'horarios_semana': horarios_semana,
            'asistencia_reciente': asistencia_reciente,
            'companeros': companeros,
            'asistencia_anual': asistencia_anual,
        }
        
        estudiantes_info.append(estudiante_data)
    
    # Calcular estadísticas de resumen para todos los estudiantes
    total_promedio = 0
    count_con_notas = 0
    total_asistencia = 0
    count_con_asistencia = 0
    
    for info in estudiantes_info:
        if info.get('promedio_general'):
            total_promedio += info['promedio_general']
            count_con_notas += 1
        if info.get('porcentaje_asistencia') is not None:
            total_asistencia += info['porcentaje_asistencia']
            count_con_asistencia += 1
    
    promedio_general_conjunto = round(total_promedio / count_con_notas, 1) if count_con_notas > 0 else None
    promedio_asistencia_conjunto = round(total_asistencia / count_con_asistencia, 1) if count_con_asistencia > 0 else None

    context = {
        'apoderado': apoderado,
        'estudiantes_a_cargo': estudiantes_a_cargo,
        'estudiantes_info': estudiantes_info,
        'total_estudiantes': total_estudiantes,
        'promedio_general_conjunto': promedio_general_conjunto,
        'promedio_asistencia_conjunto': promedio_asistencia_conjunto,
        'tipo_usuario': 'apoderado',
        'es_profesor_apoderado': es_profesor_apoderado,
        'fecha_actual': timezone.now().date(),
    }
    
    return render(request, 'dashboard_apoderado.html', context)

def _preparar_contexto_profesor_apoderado(request, profesor, apoderado):
    """Función auxiliar para preparar el contexto de un profesor-apoderado"""
    
    # Obtener estudiantes a cargo como apoderado
    estudiantes_a_cargo = RelacionApoderadoEstudiante.objects.filter(
        apoderado=apoderado
    ).select_related(
        'estudiante'
    ).prefetch_related(
        'estudiante__cursos',
        'estudiante__cursos__profesor_jefe'
    )
    
    # Información para estudiantes a cargo
    estudiantes_info = []
    for relacion in estudiantes_a_cargo:
        estudiante = relacion.estudiante
        
        # Obtener curso actual del estudiante
        curso_actual = estudiante.get_curso_actual()
        
        # Obtener información académica básica
        from .models import Calificacion, AsistenciaAlumno, Anotacion, Inscripcion
        from django.utils import timezone
        from django.db.models import Avg
        
        # Notas recientes
        notas_recientes = Calificacion.objects.filter(
            inscripcion__estudiante=estudiante
        ).select_related('inscripcion__grupo__asignatura').order_by('-fecha_evaluacion')[:3]
        
        # Promedio general
        promedio_obj = Calificacion.objects.filter(
            inscripcion__estudiante=estudiante
        ).aggregate(promedio=Avg('puntaje'))
        promedio_general = round(promedio_obj['promedio'], 1) if promedio_obj['promedio'] else None
        
        # Asistencia del mes
        hoy = timezone.now().date()
        inicio_mes = hoy.replace(day=1)
        asistencias_mes = AsistenciaAlumno.objects.filter(
            estudiante=estudiante,
            fecha__gte=inicio_mes,
            fecha__lte=hoy
        )
        total_asistencias = asistencias_mes.count()
        asistencias_presentes = asistencias_mes.filter(presente=True).count()
        ausencias = total_asistencias - asistencias_presentes
        porcentaje_asistencia = round((asistencias_presentes / total_asistencias * 100), 1) if total_asistencias > 0 else 0
        
        # Obtener anotaciones recientes (últimas 3)
        from .models import Anotacion
        anotaciones_recientes = Anotacion.objects.filter(
            estudiante=estudiante
        ).select_related('profesor_autor').order_by('-fecha_creacion')[:3]
        
        # Obtener asignaturas con notas del estudiante
        from .models import Grupo
        asignaturas_con_notas = []
        inscripciones = Inscripcion.objects.filter(estudiante=estudiante).select_related(
            'grupo__asignatura',
            'grupo__profesor'
        )
        
        for inscripcion in inscripciones:
            calificaciones = Calificacion.objects.filter(inscripcion=inscripcion).order_by('fecha_evaluacion')
            promedio_asignatura = None
            if calificaciones.exists():
                from django.db.models import Avg
                promedio_obj = calificaciones.aggregate(promedio=Avg('puntaje'))
                promedio_asignatura = round(promedio_obj['promedio'], 1) if promedio_obj['promedio'] else None
            
            asignaturas_con_notas.append({
                'asignatura': inscripcion.grupo.asignatura,
                'profesor': inscripcion.grupo.profesor,
                'promedio': promedio_asignatura,
                'total_notas': calificaciones.count(),
                'calificaciones_detalle': calificaciones,
            })
        
        # Obtener horarios de la semana
        from .models import HorarioCurso
        horarios_semana = {}
        if curso_actual:
            horarios = HorarioCurso.objects.filter(
                curso=curso_actual
            ).select_related('asignatura').order_by('hora_inicio', 'dia')
            
            # Organizar horarios por bloque de tiempo
            for horario in horarios:
                hora_key = f"{horario.hora_inicio.strftime('%H:%M')} - {horario.hora_fin.strftime('%H:%M')}"
                if hora_key not in horarios_semana:
                    horarios_semana[hora_key] = []
                horarios_semana[hora_key].append(horario)
    
        # Obtener compañeros de curso
        companeros = Estudiante.objects.filter(
            cursos=curso_actual
        ).exclude(id=estudiante.id).order_by('apellido_paterno', 'apellido_materno', 'primer_nombre')

        # Obtener asistencia anual para detalles
        inicio_ano = hoy.replace(month=1, day=1)
        asistencia_anual = AsistenciaAlumno.objects.filter(
            estudiante=estudiante,
            fecha__gte=inicio_ano,
            fecha__lte=hoy
        ).order_by('-fecha')
        
        # Obtener asistencia reciente (últimos 7 días)
        from datetime import timedelta
        fecha_limite = hoy - timedelta(days=7)
        asistencia_reciente = AsistenciaAlumno.objects.filter(
            estudiante=estudiante,
            fecha__gte=fecha_limite,
            fecha__lte=hoy
        ).order_by('-fecha')[:7]
        
        estudiante_data = {
            'estudiante': estudiante,
            'parentesco': relacion.parentesco,
            'curso': curso_actual,
            'profesor_jefe': curso_actual.profesor_jefe if curso_actual else None,
            'notas_recientes': notas_recientes,
            'promedio_general': promedio_general,
            'total_asistencias': total_asistencias,
            'asistencias_presentes': asistencias_presentes,
            'ausencias': ausencias,
            'porcentaje_asistencia': porcentaje_asistencia,
            'anotaciones_recientes': anotaciones_recientes,
            'asignaturas_con_notas': asignaturas_con_notas,
            'total_asignaturas': len(asignaturas_con_notas),
            'total_anotaciones': anotaciones_recientes.count() if hasattr(anotaciones_recientes, 'count') else len(anotaciones_recientes),
            'horarios_semana': horarios_semana,
            'asistencia_reciente': asistencia_reciente,
            'companeros': companeros,
            'asistencia_anual': asistencia_anual,
        }
        estudiantes_info.append(estudiante_data)
    
    # Calcular estadísticas de resumen para todos los estudiantes
    total_promedio = 0
    count_con_notas = 0
    total_asistencia = 0
    count_con_asistencia = 0
    
    for info in estudiantes_info:
        if info.get('promedio_general'):
            total_promedio += info['promedio_general']
            count_con_notas += 1
        if info.get('porcentaje_asistencia') is not None:
            total_asistencia += info['porcentaje_asistencia']
            count_con_asistencia += 1
    
    promedio_general_conjunto = round(total_promedio / count_con_notas, 1) if count_con_notas > 0 else None
    promedio_asistencia_conjunto = round(total_asistencia / count_con_asistencia, 1) if count_con_asistencia > 0 else None
    
    # Obtener estadísticas del profesor (usando la misma lógica que listar_cursos)
    from .models import Grupo, Anotacion, Curso, PeriodoAcademico, Asignatura
    from django.utils import timezone
    
    # Usar la misma lógica que la vista de cursos para profesores
    try:
        # Obtener asignaturas del profesor (como en listar_cursos)
        asignaturas_profesor_queryset = Asignatura.objects.filter(
            profesor_responsable=profesor
        )
        total_asignaturas_profesor = asignaturas_profesor_queryset.count()
        
        # Obtener cursos donde tiene asignaturas asignadas (como en listar_cursos)
        cursos_queryset = Curso.objects.filter(
            anio=timezone.now().year,
            asignaturas__in=asignaturas_profesor_queryset
        ).distinct().prefetch_related('estudiantes', 'asignaturas')
        
        # Filtrar solo las asignaturas del profesor para cada curso
        cursos_con_asignaturas_profesor = []
        for curso in cursos_queryset:
            # Solo asignaturas del profesor en este curso
            asignaturas_curso_profesor = curso.asignaturas.filter(
                profesor_responsable=profesor
            )
            # Agregar las asignaturas filtradas al curso
            curso.asignaturas_profesor = asignaturas_curso_profesor
            cursos_con_asignaturas_profesor.append(curso)
        
        todos_los_cursos = sorted(cursos_con_asignaturas_profesor, key=lambda c: (c.orden_nivel, c.paralelo))
        total_cursos_profesor = len(todos_los_cursos)
        
        # Debug detallado usando la misma lógica
        print(f"DEBUG - Profesor: {profesor}")
        print(f"DEBUG - Asignaturas como responsable:")
        for asignatura in asignaturas_profesor_queryset:
            print(f"  - Asignatura: {asignatura.nombre} (ID: {asignatura.id})")
        print(f"DEBUG - Total asignaturas como responsable: {total_asignaturas_profesor}")
        
        print(f"DEBUG - Cursos donde enseña (año {timezone.now().year}):")
        for curso in todos_los_cursos:
            print(f"  - Curso: {curso.nombre} (ID: {curso.id})")
        print(f"DEBUG - Total cursos: {total_cursos_profesor}")
        
        # Para el template, usar un QuerySet compatible
        asignaturas_profesor = asignaturas_profesor_queryset
        
    except Exception as e:
        print(f"DEBUG - Error al obtener estadísticas del profesor: {e}")
        asignaturas_profesor = Asignatura.objects.none()
        todos_los_cursos = []
        total_asignaturas_profesor = 0
        total_cursos_profesor = 0
    
    # Anotaciones creadas por el profesor (objeto con total para template)
    anotaciones_profesor = Anotacion.objects.filter(profesor_autor=profesor)
    total_anotaciones_profesor = anotaciones_profesor.count()
    stats_anotaciones = {'total': total_anotaciones_profesor}
    
    print(f"DEBUG - Total anotaciones: {total_anotaciones_profesor}")
    
    context = {
        'profesor': profesor,
        'apoderado': apoderado,
        'estudiantes_a_cargo': estudiantes_a_cargo,
        'estudiantes_info': estudiantes_info,
        'total_estudiantes': estudiantes_a_cargo.count(),
        'promedio_general_conjunto': promedio_general_conjunto,
        'promedio_asistencia_conjunto': promedio_asistencia_conjunto,
        'tipo_usuario': 'profesor',
        'es_profesor_apoderado': True,
        'mostrar_seccion_apoderado': True,
        # Variables que espera el template (usando la misma lógica que listar_cursos)
        'asignaturas_profesor': asignaturas_profesor,
        'cursos_con_asignaturas': todos_los_cursos, 
        'stats_anotaciones': stats_anotaciones,
        # También mantener las variables originales por compatibilidad
        'total_asignaturas': total_asignaturas_profesor,
        'total_cursos': total_cursos_profesor,
        'total_anotaciones': total_anotaciones_profesor,
    }
    
    return render(request, 'inicio.html', context)

@login_required
def ver_notas_estudiante_apoderado(request, estudiante_id):
    """Vista para que un profesor-apoderado vea las notas de un estudiante a su cargo"""
    
    # Verificar que el usuario sea un profesor
    try:
        profesor = request.user.profesor
    except AttributeError:
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('inicio')
    
    # Verificar que también sea apoderado
    try:
        apoderado = profesor.apoderado_profile
        if not apoderado:
            messages.error(request, "No tienes permisos de apoderado.")
            return redirect('inicio')
    except AttributeError:
        messages.error(request, "No tienes permisos de apoderado.")
        return redirect('inicio')
    
    # Verificar que el estudiante esté a cargo del apoderado
    from .models import RelacionApoderadoEstudiante, Estudiante
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    
    relacion = RelacionApoderadoEstudiante.objects.filter(
        apoderado=apoderado,
        estudiante=estudiante,
        activa=True
    ).first()
    
    if not relacion:
        messages.error(request, "No tienes permisos para ver las notas de este estudiante.")
        return redirect('estudiantes_a_cargo_profesor_apoderado')
    
    # Obtener las notas del estudiante
    from .models import Calificacion, Inscripcion, Grupo
    from django.db.models import Avg
    
    # Obtener inscripciones del estudiante
    inscripciones = Inscripcion.objects.filter(
        estudiante=estudiante
    ).select_related(
        'grupo__asignatura',
        'grupo__profesor'
    ).prefetch_related(
        'calificacion_set'
    )
    
    # Preparar información de notas por asignatura
    asignaturas_con_notas = []
    promedio_general_total = 0
    asignaturas_con_promedio = 0
    
    for inscripcion in inscripciones:
        calificaciones = inscripcion.calificacion_set.all().order_by('fecha_evaluacion')
        
        if calificaciones.exists():
            promedio_asignatura = calificaciones.aggregate(promedio=Avg('puntaje'))['promedio']
            promedio_asignatura = round(promedio_asignatura, 1) if promedio_asignatura else None
            
            if promedio_asignatura:
                promedio_general_total += promedio_asignatura
                asignaturas_con_promedio += 1
        else:
            promedio_asignatura = None
        
        asignaturas_con_notas.append({
            'asignatura': inscripcion.grupo.asignatura,
            'profesor': inscripcion.grupo.profesor,
            'calificaciones': calificaciones,
            'promedio': promedio_asignatura,
            'total_notas': calificaciones.count(),
        })
    
    # Calcular promedio general
    promedio_general = round(promedio_general_total / asignaturas_con_promedio, 1) if asignaturas_con_promedio > 0 else None
    
    context = {
        'estudiante': estudiante,
        'relacion': relacion,
        'asignaturas_con_notas': asignaturas_con_notas,
        'promedio_general': promedio_general,
        'curso_actual': estudiante.get_curso_actual(),
        'es_profesor_apoderado': True,
    }
    
    return render(request, 'ver_notas_estudiante_apoderado.html', context)

@login_required
def ver_anotaciones_estudiante_apoderado(request, estudiante_id):
    """Vista para que un profesor-apoderado vea las anotaciones de un estudiante a su cargo"""
    
    # Verificar que el usuario sea un profesor
    try:
        profesor = request.user.profesor
    except AttributeError:
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('inicio')
    
    # Verificar que también sea apoderado
    try:
        apoderado = profesor.apoderado_profile
        if not apoderado:
            messages.error(request, "No tienes permisos de apoderado.")
            return redirect('inicio')
    except AttributeError:
        messages.error(request, "No tienes permisos de apoderado.")
        return redirect('inicio')
    
    # Verificar que el estudiante esté a cargo del apoderado
    from .models import RelacionApoderadoEstudiante, Estudiante
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    
    relacion = RelacionApoderadoEstudiante.objects.filter(
        apoderado=apoderado,
        estudiante=estudiante,
        activa=True
    ).first()
    
    if not relacion:
        messages.error(request, "No tienes permisos para ver las anotaciones de este estudiante.")
        return redirect('estudiantes_a_cargo_profesor_apoderado')
    
    # Obtener anotaciones del estudiante
    from .models import Anotacion
    anotaciones = Anotacion.objects.filter(
        estudiante=estudiante
    ).select_related(
        'profesor_autor',
        'curso'
    ).order_by('-fecha_creacion')
    
    # Estadísticas de anotaciones
    total_anotaciones = anotaciones.count()
    anotaciones_positivas = anotaciones.filter(tipo='positiva').count()
    anotaciones_negativas = anotaciones.filter(tipo='negativa').count()
    anotaciones_neutras = anotaciones.filter(tipo='neutra').count()
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(anotaciones, 10)  # 10 anotaciones por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'estudiante': estudiante,
        'relacion': relacion,
        'anotaciones': page_obj,
        'page_obj': page_obj,
        'total_anotaciones': total_anotaciones,
        'anotaciones_positivas': anotaciones_positivas,
        'anotaciones_negativas': anotaciones_negativas,
        'anotaciones_neutras': anotaciones_neutras,
        'curso_actual': estudiante.get_curso_actual(),
        'es_profesor_apoderado': True,
    }
    
    return render(request, 'ver_anotaciones_estudiante_apoderado.html', context)

@login_required
def ver_horario_estudiante_apoderado(request, estudiante_id):
    """Vista para que un profesor-apoderado vea el horario de un estudiante a su cargo"""
    
    # Verificar que el usuario sea un profesor
    try:
        profesor = request.user.profesor
    except AttributeError:
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('inicio')
    
    # Verificar que también sea apoderado
    try:
        apoderado = profesor.apoderado_profile
        if not apoderado:
            messages.error(request, "No tienes permisos de apoderado.")
            return redirect('inicio')
    except AttributeError:
        messages.error(request, "No tienes permisos de apoderado.")
        return redirect('inicio')
    
    # Verificar que el estudiante esté a cargo del apoderado
    from .models import RelacionApoderadoEstudiante, Estudiante
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    
    relacion = RelacionApoderadoEstudiante.objects.filter(
        apoderado=apoderado,
        estudiante=estudiante,
        activa=True
    ).first()
    
    if not relacion:
        messages.error(request, "No tienes permisos para ver el horario de este estudiante.")
        return redirect('estudiantes_a_cargo_profesor_apoderado')
    
    # Obtener curso del estudiante
    curso_actual = estudiante.get_curso_actual()
    
    if not curso_actual:
        messages.warning(request, "El estudiante no tiene un curso asignado actualmente.")
        return redirect('estudiantes_a_cargo_profesor_apoderado')
    
    # Obtener horarios del curso
    from .models import HorarioCurso
    horarios = HorarioCurso.objects.filter(
        curso=curso_actual
    ).select_related(
        'asignatura',
        'profesor'
    ).order_by('dia', 'hora_inicio')
    
    # Organizar horarios por día y hora
    dias_semana = [
        ('1', 'Lunes'),
        ('2', 'Martes'),
        ('3', 'Miércoles'),
        ('4', 'Jueves'),
        ('5', 'Viernes'),
        ('6', 'Sábado'),
    ]
    
    # Obtener todas las horas únicas
    horas_unicas = sorted(set(
        (h.hora_inicio, h.hora_fin) for h in horarios
    ))
    
    # Crear estructura simplificada para el template
    horarios_matriz = {}
    for horario in horarios:
        key = f"{horario.dia}-{horario.hora_inicio}-{horario.hora_fin}"
        horarios_matriz[key] = horario
    
    context = {
        'estudiante': estudiante,
        'relacion': relacion,
        'curso_actual': curso_actual,
        'horarios': horarios,
        'horarios_matriz': horarios_matriz,
        'horas_unicas': horas_unicas,
        'dias_semana': dias_semana,
        'es_profesor_apoderado': True,
    }
    
    return render(request, 'ver_horario_estudiante_apoderado.html', context)

@login_required
def editar_relacion_apoderado(request, relacion_id):
    """Vista para editar permisos de una relación apoderado-estudiante"""
    # Verificar permisos
    if not verificar_permisos_admin_director(request.user):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('inicio')
        
    relacion = get_object_or_404(RelacionApoderadoEstudiante, id=relacion_id)
    
    if request.method == 'POST':
        # Actualizar permisos
        relacion.es_apoderado_principal = request.POST.get('es_apoderado_principal') == 'on'
        relacion.puede_retirar = request.POST.get('puede_retirar') == 'on'
        relacion.puede_autorizar = request.POST.get('puede_autorizar') == 'on'
        relacion.parentesco = request.POST.get('parentesco')
        relacion.save()
        
        messages.success(request, 'Permisos actualizados correctamente.')
        return redirect('detalle_apoderado', apoderado_id=relacion.apoderado.id)
        
    return render(request, 'editar_relacion_apoderado.html', {'relacion': relacion})

@login_required
def eliminar_relacion_apoderado(request, relacion_id):
    """Vista para eliminar una relación apoderado-estudiante"""
    # Verificar permisos
    if not verificar_permisos_admin_director(request.user):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('inicio')
        
    relacion = get_object_or_404(RelacionApoderadoEstudiante, id=relacion_id)
    apoderado_id = relacion.apoderado.id
    
    if request.method == 'POST':
        relacion.delete()
        messages.success(request, 'Estudiante desvinculado correctamente.')
        return redirect('detalle_apoderado', apoderado_id=apoderado_id)
        
    return render(request, 'confirmar_eliminar_relacion.html', {'relacion': relacion})
