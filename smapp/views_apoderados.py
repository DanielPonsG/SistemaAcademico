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
    ).select_related('estudiante', 'estudiante__curso')
    
    context = {
        'apoderado': apoderado,
        'relaciones': relaciones,
        'total_estudiantes': relaciones.count(),
    }
    
    return render(request, 'detalle_apoderado.html', context)

@login_required
def dashboard_apoderado(request):
    """Vista de dashboard para apoderados normales"""
    
    # Verificar que el usuario sea un apoderado
    try:
        apoderado = request.user.apoderado
    except:
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('inicio')
    
    # Obtener estudiantes a cargo
    estudiantes_a_cargo = RelacionApoderadoEstudiante.objects.filter(
        apoderado=apoderado
    ).select_related(
        'estudiante',
        'estudiante__curso',
        'estudiante__curso__profesor_jefe'
    ).prefetch_related(
        'estudiante__notas_set',
        'estudiante__asistencias_set'
    )
    
    # Estadísticas básicas
    total_estudiantes = estudiantes_a_cargo.count()
    
    # Información para cada estudiante
    estudiantes_info = []
    for relacion in estudiantes_a_cargo:
        estudiante = relacion.estudiante
        
        # Obtener información básica del estudiante
        estudiante_data = {
            'estudiante': estudiante,
            'parentesco': relacion.parentesco,
            'curso': estudiante.curso if hasattr(estudiante, 'curso') else None,
            'profesor_jefe': estudiante.curso.profesor_jefe if hasattr(estudiante, 'curso') and estudiante.curso else None,
        }
        
        estudiantes_info.append(estudiante_data)
    
    context = {
        'apoderado': apoderado,
        'estudiantes_a_cargo': estudiantes_a_cargo,
        'estudiantes_info': estudiantes_info,
        'total_estudiantes': total_estudiantes,
        'tipo_usuario': 'apoderado',
        'es_profesor_apoderado': bool(apoderado.profesor),
    }
    
    return render(request, 'inicio.html', context)

@login_required
def dashboard_profesor_apoderado(request):
    """Vista especial para profesores que también son apoderados"""
    
    # Verificar que el usuario sea un profesor
    try:
        profesor = request.user.profesor
    except:
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('inicio')
    
    # Verificar que también sea apoderado
    try:
        apoderado = profesor.apoderado_profile
    except:
        # Si no es apoderado, redirigir al dashboard normal de profesor
        return redirect('inicio')
    
    # Obtener estudiantes a cargo como apoderado
    estudiantes_a_cargo = RelacionApoderadoEstudiante.objects.filter(
        apoderado=apoderado
    ).select_related(
        'estudiante',
        'estudiante__curso',
        'estudiante__curso__profesor_jefe'
    )
    
    # Obtener información básica del profesor
    from .models import HorarioCurso, Asignatura
    
    # Obtener cursos donde el profesor enseña
    cursos_con_asignaturas = profesor.get_cursos_asignados() if hasattr(profesor, 'get_cursos_asignados') else []
    
    # Horarios del profesor
    horarios_profesor = HorarioCurso.objects.filter(
        asignatura__in=profesor.asignaturas.all()
    ).select_related('asignatura', 'curso').order_by('dia', 'hora_inicio')
    
    # Asignaturas que enseña
    asignaturas_profesor = profesor.asignaturas.all()
    
    # Información para estudiantes a cargo
    estudiantes_info = []
    for relacion in estudiantes_a_cargo:
        estudiante = relacion.estudiante
        estudiante_data = {
            'estudiante': estudiante,
            'parentesco': relacion.parentesco,
            'curso': estudiante.curso if hasattr(estudiante, 'curso') else None,
            'profesor_jefe': estudiante.curso.profesor_jefe if hasattr(estudiante, 'curso') and estudiante.curso else None,
        }
        estudiantes_info.append(estudiante_data)
    
    context = {
        'profesor': profesor,
        'apoderado': apoderado,
        'estudiantes_a_cargo': estudiantes_a_cargo,
        'estudiantes_info': estudiantes_info,
        'total_estudiantes': estudiantes_a_cargo.count(),
        'horarios_profesor': horarios_profesor,
        'asignaturas_profesor': asignaturas_profesor,
        'tipo_usuario': 'profesor',
        'es_profesor_apoderado': True,
        'mostrar_seccion_apoderado': True,
    }
    
    return render(request, 'inicio.html', context)
