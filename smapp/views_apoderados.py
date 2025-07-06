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
    }
    
    return render(request, 'inicio.html', context)

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
    }
    
    return render(request, 'inicio.html', context)
