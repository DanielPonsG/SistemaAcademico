from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import Estudiante, Profesor, EventoCalendario, Curso, HorarioCurso, Asignatura, PeriodoAcademico, Anotacion
from .forms import EstudianteForm, ProfesorForm, EventoCalendarioForm, CursoForm, HorarioCursoForm, AsignaturaForm, AsignaturaCompletaForm, SeleccionCursoAlumnoForm, CalificacionForm, AsistenciaAlumnoForm, AsistenciaProfesorForm, RegistroMasivoAsistenciaForm, AnotacionForm, FiltroAnotacionesForm
from django.db import models
from django.db.models import Q, Avg
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Perfil
from django.http import HttpResponseForbidden, JsonResponse
from django.forms import formset_factory
from .models import Inscripcion, Grupo, Calificacion, AsistenciaAlumno, AsistenciaProfesor
from datetime import date, datetime, timedelta
from .decorators import admin_required, profesor_admin_required, all_users_required, profesor_con_asignaturas_required
from django.contrib import messages
from django.utils import timezone
import json

# Create your views here.
# Vista de la página de inicio del maestro
def index_master(request):
    """
    Redirección.
    """
    return render(request, 'index_master.html')

# Vista de la página de inicio del alumno
def index(request):
    """
    Redirección a la página de inicio.
    """
    return render(request, 'index.html')

# Vistas para el CRUD de Administrador
@admin_required
def agregar(request):
    tipo = request.GET.get('tipo', 'estudiante')
    mensaje = ""
    if tipo == 'profesor':
        form = ProfesorForm(request.POST or None)
        if request.method == 'POST' and form.is_valid():
            # Crear usuario
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            email = form.cleaned_data['email']
            user = User.objects.create_user(username=username, password=password, email=email)
            # Crear perfil
            Perfil.objects.create(user=user, tipo_usuario='profesor')
            # Crear profesor
            profesor = form.save(commit=False)
            profesor.user = user
            profesor.save()
            # Si tienes campos ManyToMany (como asignaturas), asígnalos después de save()
            if 'asignaturas' in form.cleaned_data:
                profesor.asignaturas.set(form.cleaned_data['asignaturas'])
            mensaje = "Profesor agregado correctamente."
            form = ProfesorForm()  # Limpiar formulario
    else:
        form = EstudianteForm(request.POST or None)
        if request.method == 'POST' and form.is_valid():
            # Crear usuario
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            email = form.cleaned_data['email']
            user = User.objects.create_user(username=username, password=password, email=email)
            # Crear perfil
            Perfil.objects.create(user=user, tipo_usuario='alumno')
            # Crear estudiante
            estudiante = form.save(commit=False)
            estudiante.user = user
            estudiante.save()
            # Si tienes campos ManyToMany (como cursos), asígnalos después de save()
            if 'cursos' in form.cleaned_data:
                estudiante.cursos.set(form.cleaned_data['cursos'])
            mensaje = "Estudiante agregado correctamente."
            form = EstudianteForm()  # Limpiar formulario
    return render(request, 'agregar.html', {'form': form, 'tipo': tipo, 'mensaje': mensaje})

@admin_required
def modificar(request):
    tipo = request.GET.get('tipo', 'estudiante')
    query = request.GET.get('q', '')
    seleccionado_id = request.GET.get('id')
    mensaje = ""
    form = None
    resultados = []

    if tipo == 'profesor':
        if query:
            resultados = Profesor.objects.filter(
                Q(primer_nombre__icontains=query) |
                Q(apellido_paterno__icontains=query) |
                Q(codigo_profesor__icontains=query) |
                Q(id__iexact=query)  # Permite buscar por ID exacto
            )
        else:
            resultados = Profesor.objects.none()
        if seleccionado_id:
            seleccionado = Profesor.objects.get(id=seleccionado_id)
            if request.method == 'POST':
                form = ProfesorForm(request.POST, instance=seleccionado)
                if form.is_valid():
                    form.save()
                    mensaje = "Profesor modificado correctamente."
            else:
                form = ProfesorForm(instance=seleccionado)
    else:
        if query:
            resultados = Estudiante.objects.filter(
                Q(primer_nombre__icontains=query) |
                Q(apellido_paterno__icontains=query) |
                Q(codigo_estudiante__icontains=query) |
                Q(id__iexact=query)  # Permite buscar por ID exacto
            )
        else:
            resultados = Estudiante.objects.none()
        if seleccionado_id:
            seleccionado = Estudiante.objects.get(id=seleccionado_id)
            if request.method == 'POST':
                form = EstudianteForm(request.POST, instance=seleccionado)
                if form.is_valid():
                    form.save()
                    mensaje = "Estudiante modificado correctamente."
            else:
                form = EstudianteForm(instance=seleccionado)

    return render(request, 'modificar.html', {
        'tipo': tipo,
        'query': query,
        'resultados': resultados,
        'form': form,
        'seleccionado_id': seleccionado_id,
        'mensaje': mensaje
    })

@admin_required
def eliminar(request):
    tipo = request.GET.get('tipo', 'estudiante')
    query = request.GET.get('q', '')
    seleccionado_id = request.GET.get('id')
    mensaje = ""
    resultados = []
    objeto = None

    # Eliminar por ID directo
    if request.method == 'POST' and request.POST.get('eliminar_por_id'):
        id_a_eliminar = request.POST.get('id_a_eliminar')
        if tipo == 'profesor':
            try:
                obj = Profesor.objects.get(id=id_a_eliminar)
                obj.delete()
                mensaje = f"Profesor con ID {id_a_eliminar} eliminado correctamente."
            except Profesor.DoesNotExist:
                mensaje = f"No existe un profesor con ID {id_a_eliminar}."
        else:
            try:
                obj = Estudiante.objects.get(id=id_a_eliminar)
                obj.delete()
                mensaje = f"Estudiante con ID {id_a_eliminar} eliminado correctamente."
            except Estudiante.DoesNotExist:
                mensaje = f"No existe un estudiante con ID {id_a_eliminar}."

    # Buscar y mostrar resultados
    if tipo == 'profesor':
        if query:
            resultados = Profesor.objects.filter(
                models.Q(primer_nombre__icontains=query) |
                models.Q(apellido_paterno__icontains=query) |
                models.Q(codigo_profesor__icontains=query)
            )
        else:
            resultados = Profesor.objects.none()
        if seleccionado_id:
            objeto = Profesor.objects.get(id=seleccionado_id)
            if request.method == 'POST':
                objeto.delete()
                mensaje = "Profesor eliminado correctamente."
                objeto = None
    else:
        if query:
            resultados = Estudiante.objects.filter(
                models.Q(primer_nombre__icontains=query) |
                models.Q(apellido_paterno__icontains=query) |
                models.Q(codigo_estudiante__icontains=query)
            )
        else:
            resultados = Estudiante.objects.none()
        if seleccionado_id:
            objeto = Estudiante.objects.get(id=seleccionado_id)
            if request.method == 'POST':
                objeto.delete()
                mensaje = "Estudiante eliminado correctamente."
                objeto = None

    return render(request, 'eliminar.html', {
        'tipo': tipo,
        'query': query,
        'resultados': resultados,
        'objeto': objeto,
        'seleccionado_id': seleccionado_id,
        'mensaje': mensaje
    })

@profesor_admin_required
def listar_estudiantes(request):
    # Filtros para estudiantes
    q_estudiante = request.GET.get('q_estudiante', '')
    genero_estudiante = request.GET.get('genero_estudiante', '')
    tipo_doc_estudiante = request.GET.get('tipo_doc_estudiante', '')
    fecha_ingreso = request.GET.get('fecha_ingreso', '')
    
    # Filtros para profesores
    q_profesor = request.GET.get('q_profesor', '')
    genero_profesor = request.GET.get('genero_profesor', '')
    especialidad_profesor = request.GET.get('especialidad_profesor', '')

    # Obtener todos los estudiantes y profesores
    estudiantes = Estudiante.objects.select_related('user').all()
    profesores = Profesor.objects.select_related('user').all()

    # Aplicar filtros para estudiantes
    if q_estudiante:
        estudiantes = estudiantes.filter(
            models.Q(primer_nombre__icontains=q_estudiante) |
            models.Q(segundo_nombre__icontains=q_estudiante) |
            models.Q(apellido_paterno__icontains=q_estudiante) |
            models.Q(apellido_materno__icontains=q_estudiante) |
            models.Q(codigo_estudiante__icontains=q_estudiante) |
            models.Q(numero_documento__icontains=q_estudiante) |
            models.Q(email__icontains=q_estudiante)
        )
    
    if genero_estudiante:
        estudiantes = estudiantes.filter(genero=genero_estudiante)
    
    if tipo_doc_estudiante:
        estudiantes = estudiantes.filter(tipo_documento=tipo_doc_estudiante)
    
    if fecha_ingreso:
        estudiantes = estudiantes.filter(fecha_ingreso=fecha_ingreso)

    # Aplicar filtros para profesores
    if q_profesor:
        profesores = profesores.filter(
            models.Q(primer_nombre__icontains=q_profesor) |
            models.Q(segundo_nombre__icontains=q_profesor) |
            models.Q(apellido_paterno__icontains=q_profesor) |
            models.Q(apellido_materno__icontains=q_profesor) |
            models.Q(codigo_profesor__icontains=q_profesor) |
            models.Q(numero_documento__icontains=q_profesor) |
            models.Q(email__icontains=q_profesor)
        )
    
    if genero_profesor:
        profesores = profesores.filter(genero=genero_profesor)
    
    if especialidad_profesor:
        profesores = profesores.filter(especialidad__icontains=especialidad_profesor)

    # Ordenar resultados
    estudiantes = estudiantes.order_by('primer_nombre', 'apellido_paterno')
    profesores = profesores.order_by('primer_nombre', 'apellido_paterno')

    # Estadísticas
    total_estudiantes = estudiantes.count()
    total_profesores = profesores.count()
    
    # Obtener especialidades únicas para el filtro
    especialidades = Profesor.objects.values_list('especialidad', flat=True).distinct().exclude(especialidad__isnull=True).exclude(especialidad__exact='')
    
    return render(request, 'listar_estudiantes.html', {
        'estudiantes': estudiantes,
        'profesores': profesores,
        'estudiantes_filtrados': estudiantes,  # Para compatibilidad con template
        'profesores_filtrados': profesores,    # Para compatibilidad con template
        'total_estudiantes': total_estudiantes,
        'total_profesores': total_profesores,
        'especialidades': especialidades,
    })

@admin_required
def listar_profesores(request):
    """Vista para que el administrador gestione profesores"""
    filtro_profesor = request.GET.get('filtro_profesor', '')
    
    # Obtener todos los profesores
    profesores = Profesor.objects.select_related('user').all()
    
    # Aplicar filtros si existen
    if filtro_profesor:
        profesores = profesores.filter(
            models.Q(primer_nombre__icontains=filtro_profesor) |
            models.Q(apellido_paterno__icontains=filtro_profesor) |
            models.Q(apellido_materno__icontains=filtro_profesor) |
            models.Q(codigo_profesor__icontains=filtro_profesor) |
            models.Q(email__icontains=filtro_profesor) |
            models.Q(id__iexact=filtro_profesor)
        )
    
    # Estadísticas
    total_profesores = profesores.count()
    profesores_activos = profesores.filter(user__is_active=True).count()
    profesores_con_asignaturas = profesores.filter(asignaturas__isnull=False).distinct().count()
    
    return render(request, 'listar_profesores.html', {
        'profesores': profesores,
        'filtro_profesor': filtro_profesor,
        'total_profesores': total_profesores,
        'profesores_activos': profesores_activos,
        'profesores_con_asignaturas': profesores_con_asignaturas,
    })

@admin_required
def gestionar_profesor(request, profesor_id=None):
    """Vista para agregar/editar profesores"""
    from django.contrib.auth.models import User
    from .models import Perfil
    
    profesor = None
    if profesor_id:
        try:
            profesor = Profesor.objects.get(id=profesor_id)
        except Profesor.DoesNotExist:
            messages.error(request, 'El profesor no existe.')
            return redirect('listar_profesores')
    
    if request.method == 'POST':
        try:
            # Datos del formulario
            primer_nombre = request.POST.get('primer_nombre')
            apellido_paterno = request.POST.get('apellido_paterno')
            apellido_materno = request.POST.get('apellido_materno', '')
            email = request.POST.get('email')
            telefono = request.POST.get('telefono', '')
            direccion = request.POST.get('direccion', '')
            codigo_profesor = request.POST.get('codigo_profesor')
            asignaturas_ids = request.POST.getlist('asignaturas')
            
            # Validaciones básicas
            if not all([primer_nombre, apellido_paterno, email, codigo_profesor]):
                messages.error(request, 'Todos los campos obligatorios deben ser completados.')
                return render(request, 'gestionar_profesor.html', {
                    'profesor': profesor,
                    'asignaturas': Asignatura.objects.all(),
                    'action': 'Editar' if profesor else 'Agregar',
                })
            
            if profesor:
                # Editar profesor existente
                profesor.primer_nombre = primer_nombre
                profesor.apellido_paterno = apellido_paterno
                profesor.apellido_materno = apellido_materno
                profesor.email = email
                profesor.telefono = telefono
                profesor.direccion = direccion
                profesor.codigo_profesor = codigo_profesor
                profesor.save()
                
                # Actualizar asignaturas
                profesor.asignaturas.set(asignaturas_ids)
                
                # Actualizar usuario asociado si existe
                if profesor.user:
                    profesor.user.first_name = primer_nombre
                    profesor.user.last_name = f"{apellido_paterno} {apellido_materno}".strip()
                    profesor.user.email = email
                    profesor.user.save()
                
                messages.success(request, f'Profesor {primer_nombre} {apellido_paterno} actualizado correctamente.')
                
            else:
                # Crear nuevo profesor
                username = f"prof_{codigo_profesor.lower()}"
                password = f"temp_{codigo_profesor}123"  # Contraseña temporal
                
                # Verificar si el username ya existe
                if User.objects.filter(username=username).exists():
                    counter = 1
                    original_username = username
                    while User.objects.filter(username=f"{original_username}_{counter}").exists():
                        counter += 1
                    username = f"{original_username}_{counter}"
                
                # Crear usuario
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=primer_nombre,
                    last_name=f"{apellido_paterno} {apellido_materno}".strip()
                )
                
                # Crear perfil
                perfil = Perfil.objects.create(
                    user=user,
                    tipo_usuario='profesor'
                )
                
                # Crear profesor
                profesor = Profesor.objects.create(
                    user=user,
                    primer_nombre=primer_nombre,
                    apellido_paterno=apellido_paterno,
                    apellido_materno=apellido_materno,
                    email=email,
                    telefono=telefono,
                    direccion=direccion,
                    codigo_profesor=codigo_profesor
                )
                
                # Asignar asignaturas
                profesor.asignaturas.set(asignaturas_ids)
                
                messages.success(request, f'Profesor {primer_nombre} {apellido_paterno} creado correctamente.')
                messages.info(request, f'Usuario: {username}, Contraseña temporal: {password}')
            
            return redirect('listar_profesores')
            
        except Exception as e:
            messages.error(request, f'Error al guardar profesor: {str(e)}')
    
    context = {
        'profesor': profesor,
        'asignaturas': Asignatura.objects.all(),
        'action': 'Editar' if profesor else 'Agregar',
    }
    
    return render(request, 'gestionar_profesor.html', context)

@all_users_required
def calendario(request):
    """Vista del calendario con funcionalidad completa"""
    from django.utils import timezone
    from django.db.models import Q
    from django.http import JsonResponse
    import json
    
    # Determinar tipo de usuario y permisos
    user_type = 'otro'
    puede_crear_eventos = False
    
    # Lógica mejorada para detectar tipo de usuario
    if request.user.is_superuser:
        user_type = 'administrador'
        puede_crear_eventos = True
    else:
        try:
            if hasattr(request.user, 'perfil') and request.user.perfil:
                user_type = request.user.perfil.tipo_usuario
                puede_crear_eventos = user_type in ['administrador', 'director', 'profesor']
            elif hasattr(request.user, 'profesor'):
                user_type = 'profesor'
                puede_crear_eventos = True
            elif hasattr(request.user, 'estudiante'):
                user_type = 'estudiante'
        except Exception as e:
            # Fallback para superusuarios sin perfil
            if request.user.is_superuser or request.user.is_staff:
                user_type = 'administrador'
                puede_crear_eventos = True
    
    print(f"DEBUG: Usuario {request.user.username}, tipo: {user_type}, puede crear: {puede_crear_eventos}")  # Debug
    
    # Obtener filtros
    fecha_filtro = request.GET.get('fecha_filtro', '')
    curso_filtro = request.GET.get('curso_filtro', '')
    
    # Base de eventos según tipo de usuario
    eventos_base = EventoCalendario.objects.all()
    
    # Filtrar eventos por permisos de usuario
    if user_type == 'estudiante':
        # Estudiantes ven eventos de sus cursos o eventos generales (NO los de solo profesores)
        try:
            estudiante = request.user.estudiante
            cursos_estudiante = estudiante.cursos.all()
            eventos_base = eventos_base.filter(
                Q(para_todos_los_cursos=True) | Q(cursos__in=cursos_estudiante)
            ).filter(solo_profesores=False).distinct()
        except:
            eventos_base = eventos_base.filter(
                para_todos_los_cursos=True,
                solo_profesores=False
            )
    elif user_type == 'profesor':
        # Profesores ven eventos de sus cursos asignados, eventos generales y eventos solo para profesores
        try:
            profesor = request.user.profesor
            cursos_profesor = Curso.objects.filter(
                Q(profesor_jefe=profesor) | Q(asignaturas__profesores=profesor)
            ).distinct()
            eventos_base = eventos_base.filter(
                Q(para_todos_los_cursos=True) | Q(cursos__in=cursos_profesor) | Q(solo_profesores=True)
            ).distinct()
        except:
            eventos_base = eventos_base.filter(
                Q(para_todos_los_cursos=True) | Q(solo_profesores=True)
            )
    # Administradores y directores ven todos los eventos (sin filtro adicional)
    
    # Aplicar filtros de búsqueda
    eventos = eventos_base
    if fecha_filtro:
        try:
            from datetime import datetime
            fecha_obj = datetime.strptime(fecha_filtro, '%Y-%m-%d').date()
            eventos = eventos.filter(fecha=fecha_obj)
        except ValueError:
            pass
    
    if curso_filtro and user_type in ['administrador', 'director']:
        eventos = eventos.filter(cursos__id=curso_filtro)
    
    # Manejar creación de evento (AJAX POST)
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if not puede_crear_eventos:
            return JsonResponse({'success': False, 'error': 'Sin permisos para crear eventos'})
        
        try:
            # Validaciones de servidor
            titulo = request.POST.get('titulo', '').strip()
            fecha = request.POST.get('fecha')
            hora_inicio = request.POST.get('hora_inicio') or None
            hora_fin = request.POST.get('hora_fin') or None
            
            # Validar campos obligatorios
            if not titulo:
                return JsonResponse({'success': False, 'error': 'El título es obligatorio'})
            if not fecha:
                return JsonResponse({'success': False, 'error': 'La fecha es obligatoria'})
            
            # Validar horas
            if hora_inicio and hora_fin:
                from datetime import datetime
                inicio = datetime.strptime(hora_inicio, '%H:%M').time()
                fin = datetime.strptime(hora_fin, '%H:%M').time()
                if inicio >= fin:
                    return JsonResponse({'success': False, 'error': 'La hora de inicio debe ser menor que la hora de fin'})
            
            # Crear evento
            dirigido_a = request.POST.get('dirigido_a', 'todos')
            evento = EventoCalendario.objects.create(
                titulo=titulo,
                descripcion=request.POST.get('descripcion', ''),
                fecha=fecha,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                tipo_evento=request.POST.get('tipo_evento', 'general'),
                prioridad=request.POST.get('prioridad', 'media'),
                para_todos_los_cursos=dirigido_a == 'todos',
                solo_profesores=dirigido_a == 'solo_profesores',
                creado_por=request.user
            )
            
            # Asignar cursos específicos si es necesario
            if dirigido_a == 'cursos_especificos':
                cursos_ids = request.POST.getlist('cursos_especificos')
                if not cursos_ids:
                    return JsonResponse({'success': False, 'error': 'Debes seleccionar al menos un curso específico'})
                
                # Validar que el usuario tenga permisos sobre los cursos seleccionados
                if user_type == 'profesor':
                    profesor = request.user.profesor
                    cursos_permitidos = Curso.objects.filter(
                        Q(profesor_jefe=profesor) | Q(asignaturas__profesores=profesor)
                    ).values_list('id', flat=True)
                    
                    cursos_no_permitidos = [cid for cid in cursos_ids if int(cid) not in cursos_permitidos]
                    if cursos_no_permitidos:
                        return JsonResponse({'success': False, 'error': 'No tienes permisos para crear eventos en algunos de los cursos seleccionados'})
                
                evento.cursos.set(cursos_ids)
            
            return JsonResponse({
                'success': True, 
                'evento_id': evento.id,
                'message': 'Evento creado exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al crear el evento: {str(e)}'})
    
    # Preparar datos para FullCalendar
    eventos_json = []
    for evento in eventos:
        eventos_json.append({
            'id': evento.id,
            'title': evento.titulo,
            'start': evento.fecha.isoformat(),
            'description': evento.descripcion or '',
            'backgroundColor': evento.color_por_tipo,
            'borderColor': evento.color_por_tipo,
            'textColor': '#fff',
            'extendedProps': {
                'description': evento.descripcion or '',
                'responsable': evento.creado_por.first_name if evento.creado_por and evento.creado_por.first_name else (evento.creado_por.username if evento.creado_por else 'Sistema'),
                'tipo': evento.get_tipo_evento_display(),
                'prioridad': evento.get_prioridad_display()
            }
        })
    
    print(f"DEBUG: Preparando {len(eventos_json)} eventos para FullCalendar")  # Debug
    
    # Calcular estadísticas para las tarjetas
    from datetime import datetime, timedelta
    hoy = datetime.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)
    
    eventos_hoy = eventos_base.filter(fecha=hoy).count()
    eventos_semana = eventos_base.filter(fecha__range=[inicio_semana, fin_semana]).count()
    
    eventos_count = {
        'hoy': eventos_hoy,
        'semana': eventos_semana
    }
    
    # Obtener cursos disponibles para filtros y modal
    cursos = []
    if user_type in ['administrador', 'director']:
        cursos = Curso.objects.filter(anio=timezone.now().year).order_by('nivel', 'paralelo')
    elif user_type == 'profesor':
        try:
            profesor = request.user.profesor
            cursos = Curso.objects.filter(
                Q(profesor_jefe=profesor) | Q(asignaturas__profesores=profesor),
                anio=timezone.now().year
            ).distinct().order_by('nivel', 'paralelo')
        except:
            cursos = []
    
    context = {
        'eventos': eventos.order_by('fecha')[:10],  # Próximos 10 eventos para la tabla
        'eventos_json': json.dumps(eventos_json),
        'eventos_count': eventos_count,
        'cursos': cursos,
        'fecha_filtro': fecha_filtro,
        'curso_filtro': curso_filtro,
        'puede_crear_eventos': puede_crear_eventos,
        'user_type': user_type,
        'tipos_evento': EventoCalendario.TIPO_EVENTO_CHOICES,
        'prioridades': EventoCalendario.PRIORIDAD_CHOICES,
    }
    
    return render(request, 'calendario.html', context)

@login_required
def inicio(request):
    """Vista del panel de inicio personalizado por tipo de usuario"""
    context = {
        'user': request.user,
    }
    return render(request, 'inicio.html', context)

def login_view(request):
    """Vista de login personalizada"""
    mensaje = ""
    
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index_master')
            else:
                mensaje = "Credenciales inválidas"
        else:
            mensaje = "Por favor ingresa usuario y contraseña"
    
    return render(request, 'login.html', {'mensaje': mensaje})

def logout_view(request):
    """Vista de logout personalizada"""
    logout(request)
    return redirect('login')

@login_required
def agregar_evento(request):
    """Vista para agregar un nuevo evento al calendario"""
    from django.utils import timezone
    from django.db.models import Q
    
    # Determinar tipo de usuario y permisos
    user_type = 'otro'
    puede_crear_eventos = False
    
    # Lógica mejorada para detectar tipo de usuario
    if request.user.is_superuser:
        user_type = 'administrador'
        puede_crear_eventos = True
    else:
        try:
            if hasattr(request.user, 'perfil') and request.user.perfil:
                user_type = request.user.perfil.tipo_usuario
                puede_crear_eventos = user_type in ['administrador', 'director', 'profesor']
            elif hasattr(request.user, 'profesor'):
                user_type = 'profesor'
                puede_crear_eventos = True
        except Exception as e:
            if request.user.is_superuser or request.user.is_staff:
                user_type = 'administrador'
                puede_crear_eventos = True
    
    if not puede_crear_eventos:
        context = {
            'user_type': user_type,
            'required_types': ['administrador', 'director', 'profesor'],
            'error_message': 'No tienes permisos para crear eventos.'
        }
        return render(request, 'error_permisos.html', context, status=403)
    
    # Obtener cursos disponibles según el tipo de usuario
    cursos = []
    if user_type in ['administrador', 'director']:
        cursos = Curso.objects.all().order_by('nivel', 'paralelo', 'anio')
    elif user_type == 'profesor':
        try:
            profesor = request.user.profesor
            cursos = Curso.objects.filter(
                Q(profesor_jefe=profesor) | Q(asignaturas__profesores=profesor)
            ).distinct().order_by('nivel', 'paralelo', 'anio')
        except:
            cursos = []
    
    if request.method == 'POST':
        try:
            # Validaciones de servidor
            titulo = request.POST.get('titulo', '').strip()
            fecha = request.POST.get('fecha')
            descripcion = request.POST.get('descripcion', '').strip()
            hora_inicio = request.POST.get('hora_inicio') or None
            hora_fin = request.POST.get('hora_fin') or None
            tipo_evento = request.POST.get('tipo_evento', 'general')
            prioridad = request.POST.get('prioridad', 'media')
            dirigido_a = request.POST.get('dirigido_a', 'todos')
            
            # Validar campos obligatorios
            if not titulo:
                messages.error(request, 'El título es obligatorio')
                return render(request, 'agregar_evento.html', {'cursos': cursos})
            if not fecha:
                messages.error(request, 'La fecha es obligatoria')
                return render(request, 'agregar_evento.html', {'cursos': cursos})
            
            # Validar horas
            if hora_inicio and hora_fin:
                from datetime import datetime
                try:
                    inicio = datetime.strptime(hora_inicio, '%H:%M').time()
                    fin = datetime.strptime(hora_fin, '%H:%M').time()
                    if inicio >= fin:
                        messages.error(request, 'La hora de inicio debe ser menor que la hora de fin')
                        return render(request, 'agregar_evento.html', {'cursos': cursos})
                except ValueError:
                    messages.error(request, 'Formato de hora inválido')
                    return render(request, 'agregar_evento.html', {'cursos': cursos})
            
            # Crear evento
            evento = EventoCalendario.objects.create(
                titulo=titulo,
                descripcion=descripcion,
                fecha=fecha,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                tipo_evento=tipo_evento,
                prioridad=prioridad,
                para_todos_los_cursos=dirigido_a == 'todos',
                solo_profesores=dirigido_a == 'solo_profesores',
                creado_por=request.user
            )
            
            # Asignar cursos específicos si es necesario
            if dirigido_a == 'cursos_especificos':
                cursos_ids = request.POST.getlist('cursos_especificos')
                if not cursos_ids:
                    messages.error(request, 'Debes seleccionar al menos un curso específico')
                    evento.delete()
                    return render(request, 'agregar_evento.html', {'cursos': cursos})
                
                # Validar que el usuario tenga permisos sobre los cursos seleccionados
                if user_type == 'profesor':
                    profesor = request.user.profesor
                    cursos_permitidos = Curso.objects.filter(
                        Q(profesor_jefe=profesor) | Q(asignaturas__profesores=profesor)
                    ).values_list('id', flat=True)
                    
                    cursos_no_permitidos = [cid for cid in cursos_ids if int(cid) not in cursos_permitidos]
                    if cursos_no_permitidos:
                        messages.error(request, 'No tienes permisos para crear eventos en algunos de los cursos seleccionados')
                        evento.delete()
                        return render(request, 'agregar_evento.html', {'cursos': cursos})
                
                evento.cursos.set(cursos_ids)
            
            messages.success(request, f'Evento "{titulo}" creado exitosamente')
            return redirect('calendario')
            
        except Exception as e:
            messages.error(request, f'Error al crear el evento: {str(e)}')
            return render(request, 'agregar_evento.html', {'cursos': cursos})
    
    context = {
        'cursos': cursos,
        'user_type': user_type,
        'puede_crear_eventos': puede_crear_eventos
    }
    return render(request, 'agregar_evento.html', context)

# Funciones adicionales requeridas por urls.py
@login_required
def mis_horarios(request):
    """Vista para mostrar horarios del usuario"""
    context = {'user': request.user}
    return render(request, 'mis_horarios.html', context)

@login_required  
def mi_curso(request):
    """Vista para mostrar información del curso"""
    context = {'user': request.user}
    return render(request, 'mi_curso.html', context)

@login_required
def listar_cursos(request):
    """Vista para listar cursos y gestionar estudiantes pendientes"""
    from .forms import AsignarEstudianteForm
    from django.contrib import messages
    from django.utils import timezone
    
    # Manejar la asignación de estudiantes pendientes
    if request.method == 'POST' and 'asignar_estudiante' in request.POST:
        # Verificar permisos
        if not (hasattr(request.user, 'perfil') and 
                request.user.perfil.tipo_usuario in ['director', 'administrador', 'profesor_jefe']):
            messages.error(request, 'No tienes permisos para asignar estudiantes a cursos.')
        else:
            form_asignar = AsignarEstudianteForm(request.POST)
            if form_asignar.is_valid():
                estudiante = form_asignar.cleaned_data['estudiante']
                curso = form_asignar.cleaned_data['curso']
                
                # Asignar el estudiante al curso
                curso.estudiantes.add(estudiante)
                messages.success(
                    request, 
                    f'Estudiante {estudiante.primer_nombre} {estudiante.apellido_paterno} '
                    f'asignado exitosamente al curso {curso.get_nivel_display()}{curso.paralelo}.'
                )
            else:
                for error in form_asignar.errors.values():
                    messages.error(request, error[0])
    
    # Obtener datos de cursos
    cursos_queryset = Curso.objects.filter(anio=timezone.now().year)
    total_cursos = cursos_queryset.count()
    
    # Ordenar correctamente: básica antes que media
    cursos = sorted(cursos_queryset, key=lambda c: (c.orden_nivel, c.paralelo))
    
    # Calcular estadísticas
    total_estudiantes = Estudiante.objects.count()  # Total de estudiantes en el sistema
    total_estudiantes_asignados = sum(curso.estudiantes.count() for curso in cursos)
    profesores_jefe_asignados = len([curso for curso in cursos if curso.profesor_jefe])
    total_asignaturas_asignadas = sum(curso.asignaturas.count() for curso in cursos)
    
    # Obtener total de asignaturas disponibles en el sistema
    total_asignaturas_disponibles = Asignatura.objects.count()
    
    # Obtener estudiantes pendientes (no asignados a ningún curso del año actual)
    estudiantes_asignados_ids = set()
    for curso in cursos_queryset:
        estudiantes_curso = list(curso.estudiantes.values_list('id', flat=True))
        estudiantes_asignados_ids.update(estudiantes_curso)
    
    estudiantes_pendientes = Estudiante.objects.exclude(
        id__in=estudiantes_asignados_ids
    ).order_by('primer_nombre', 'apellido_paterno')
    
    # Crear formulario para asignar estudiantes pendientes
    form_asignar = AsignarEstudianteForm()
    
    # Verificar permisos del usuario
    puede_editar = (hasattr(request.user, 'perfil') and 
                   request.user.perfil.tipo_usuario in ['director', 'administrador', 'profesor_jefe'])
    
    context = {
        'cursos': cursos,
        'total_cursos': total_cursos,
        'total_estudiantes': total_estudiantes,
        'total_estudiantes_asignados': total_estudiantes_asignados,
        'profesores_jefe_asignados': profesores_jefe_asignados,
        'total_asignaturas_asignadas': total_asignaturas_asignadas,
        'total_asignaturas_disponibles': total_asignaturas_disponibles,
        'estudiantes_pendientes': estudiantes_pendientes,
        'total_estudiantes_pendientes': estudiantes_pendientes.count(),
        'form_asignar': form_asignar,
        'puede_editar': puede_editar,
        'anio_actual': timezone.now().year,
    }
    return render(request, 'listar_cursos.html', context)

@login_required
def listar_asignaturas(request):
    """Vista para listar asignaturas con filtros y gestión completa"""
    from django.utils import timezone
    from django.db.models import Q, Count
    
    # Determinar tipo de usuario
    user_type = 'otro'
    if request.user.is_superuser:
        user_type = 'administrador'
    elif hasattr(request.user, 'perfil'):
        user_type = request.user.perfil.tipo_usuario
    elif hasattr(request.user, 'profesor'):
        user_type = 'profesor'
    elif hasattr(request.user, 'estudiante'):
        user_type = 'estudiante'
    
    # Manejar solicitudes POST para asignar/remover profesores y cursos
    if request.method == 'POST' and user_type in ['administrador', 'director']:
        if 'asignar_profesor' in request.POST:
            try:
                asignatura_id = request.POST.get('asignatura_id')
                profesor_id = request.POST.get('profesor_id')
                
                if asignatura_id and profesor_id:
                    asignatura = get_object_or_404(Asignatura, id=asignatura_id)
                    profesor = get_object_or_404(Profesor, id=profesor_id)
                    
                    # Asignar profesor a la asignatura (usando campo individual)
                    asignatura.profesor_responsable = profesor
                    asignatura.save()
                    
                    messages.success(request, f'Profesor {profesor.get_nombre_completo()} asignado exitosamente a {asignatura.nombre}.')
                else:
                    messages.error(request, 'Datos incompletos para asignar profesor.')
                    
            except Exception as e:
                messages.error(request, f'Error al asignar profesor: {str(e)}')
                
        elif 'remover_profesor' in request.POST:
            try:
                asignatura_id = request.POST.get('asignatura_id')
                profesor_id = request.POST.get('profesor_id')
                
                if asignatura_id and profesor_id:
                    asignatura = get_object_or_404(Asignatura, id=asignatura_id)
                    profesor = get_object_or_404(Profesor, id=profesor_id)
                    
                    # Remover profesor de la asignatura
                    if asignatura.profesor_responsable == profesor:
                        asignatura.profesor_responsable = None
                        asignatura.save()
                    
                    messages.success(request, f'Profesor {profesor.get_nombre_completo()} removido exitosamente de {asignatura.nombre}.')
                else:
                    messages.error(request, 'Datos incompletos para remover profesor.')
                    
            except Exception as e:
                messages.error(request, f'Error al remover profesor: {str(e)}')
                
        elif 'asignar_curso' in request.POST:
            try:
                asignatura_id = request.POST.get('asignatura_id')
                curso_id = request.POST.get('curso_id')
                
                if asignatura_id and curso_id:
                    asignatura = get_object_or_404(Asignatura, id=asignatura_id)
                    curso = get_object_or_404(Curso, id=curso_id)
                    
                    # Asignar asignatura al curso
                    curso.asignaturas.add(asignatura)
                    
                    messages.success(request, f'Asignatura {asignatura.nombre} asignada exitosamente al curso {curso}.')
                else:
                    messages.error(request, 'Datos incompletos para asignar curso.')
                    
            except Exception as e:
                messages.error(request, f'Error al asignar curso: {str(e)}')
                
        elif 'remover_curso' in request.POST:
            try:
                asignatura_id = request.POST.get('asignatura_id')
                curso_nombre = request.POST.get('curso_nombre')
                
                if asignatura_id and curso_nombre:
                    asignatura = get_object_or_404(Asignatura, id=asignatura_id)
                    
                    # Buscar el curso por el nombre corto (ej: "1° BásicoA")
                    cursos = asignatura.cursos.all()
                    curso_encontrado = None
                    
                    for curso in cursos:
                        if curso.get_nivel_display() + curso.paralelo == curso_nombre:
                            curso_encontrado = curso
                            break
                    
                    if curso_encontrado:
                        # Remover asignatura del curso
                        curso_encontrado.asignaturas.remove(asignatura)
                        messages.success(request, f'Asignatura {asignatura.nombre} removida exitosamente del curso {curso_encontrado}.')
                    else:
                        messages.error(request, 'No se pudo encontrar el curso especificado.')
                else:
                    messages.error(request, 'Datos incompletos para remover curso.')
                    
            except Exception as e:
                messages.error(request, f'Error al remover curso: {str(e)}')
        
        # Redirigir para evitar reenvío del formulario
        return redirect('listar_asignaturas')
    
    # Obtener filtros
    filtro_codigo = request.GET.get('filtro_codigo', '')
    filtro_profesor = request.GET.get('filtro_profesor', '')
    filtro_sin_profesor = request.GET.get('filtro_sin_profesor', '')
    filtro_nombre = request.GET.get('filtro_nombre', '')
    
    # Base de asignaturas según tipo de usuario
    if user_type == 'estudiante':
        # Estudiantes solo ven sus asignaturas
        try:
            estudiante = request.user.estudiante
            cursos_estudiante = estudiante.cursos.all()
            asignaturas = Asignatura.objects.filter(cursos__in=cursos_estudiante).distinct()
            cursos_alumno_ids = [curso.id for curso in cursos_estudiante]
        except:
            asignaturas = Asignatura.objects.none()
            cursos_alumno_ids = []
    elif user_type == 'profesor':
        # Profesores ven sus asignaturas asignadas
        try:
            profesor = request.user.profesor
            asignaturas = profesor.asignaturas.all()
        except:
            asignaturas = Asignatura.objects.none()
        cursos_alumno_ids = []
    else:
        # Administradores y directores ven todas las asignaturas con información de cursos
        asignaturas = Asignatura.objects.select_related('profesor_responsable').prefetch_related(
            'horarios__curso', 
            'cursos'  # Agregar cursos para mostrar en la tabla
        )
        cursos_alumno_ids = []
        
        # Aplicar filtros para administradores/directores
        if filtro_codigo:
            asignaturas = asignaturas.filter(codigo_asignatura__icontains=filtro_codigo)
        
        if filtro_nombre:
            asignaturas = asignaturas.filter(nombre__icontains=filtro_nombre)
        
        if filtro_profesor:
            asignaturas = asignaturas.filter(
                Q(profesor_responsable__primer_nombre__icontains=filtro_profesor) |
                Q(profesor_responsable__apellido_paterno__icontains=filtro_profesor) |
                Q(profesor_responsable__codigo_profesor__icontains=filtro_profesor)
            )
        
        if filtro_sin_profesor:
            asignaturas = asignaturas.filter(profesor_responsable__isnull=True)
    
    # Ordenar asignaturas
    asignaturas = asignaturas.order_by('nombre')
    
    # Estadísticas mejoradas para administradores/directores
    estadisticas = {}
    total_asignaturas = 0
    asignaturas_con_profesor = 0
    asignaturas_sin_profesor_count = 0
    asignaturas_sin_profesor = []
    asignaturas_con_cursos = 0
    asignaturas_sin_cursos = 0
    
    if user_type in ['administrador', 'director']:
        from django.db.models import Count
        
        total_asignaturas = Asignatura.objects.count()
        
        # Contar asignaturas con/sin profesor
        asignaturas_con_profesor_query = Asignatura.objects.filter(
            profesor_responsable__isnull=False
        ).distinct()
        asignaturas_con_profesor = asignaturas_con_profesor_query.count()
        asignaturas_sin_profesor_count = total_asignaturas - asignaturas_con_profesor
        
        # Asignaturas sin profesor para la sección especial
        asignaturas_sin_profesor = Asignatura.objects.filter(
            profesor_responsable__isnull=True
        ).distinct()
        
        # Contar asignaturas con/sin cursos (solo del año actual)
        from django.utils import timezone
        anio_actual = timezone.now().year
        
        asignaturas_con_cursos = Asignatura.objects.filter(
            cursos__anio=anio_actual
        ).distinct().count()
        asignaturas_sin_cursos = total_asignaturas - asignaturas_con_cursos
        
        # Contar asignaturas con/sin horarios
        con_horarios = Asignatura.objects.filter(horarios__isnull=False).distinct().count()
        sin_horarios = total_asignaturas - con_horarios
        
        estadisticas = {
            'total_asignaturas': total_asignaturas,
            'con_profesor': asignaturas_con_profesor,
            'sin_profesor': asignaturas_sin_profesor_count,
            'con_cursos': asignaturas_con_cursos,
            'sin_cursos': asignaturas_sin_cursos,
            'con_horarios': con_horarios,
            'sin_horarios': sin_horarios
        }
    
    # Obtener profesores para el filtro
    profesores = Profesor.objects.all().order_by('primer_nombre', 'apellido_paterno')
    
    # Obtener cursos disponibles para asignar
    from django.utils import timezone
    anio_actual = timezone.now().year
    cursos_disponibles = Curso.objects.filter(anio=anio_actual).order_by('nivel', 'paralelo')

    context = {
        'asignaturas': asignaturas,
        'tipo_usuario': user_type,
        'cursos_alumno_ids': cursos_alumno_ids,
        'user': request.user,
        'filtro_codigo': filtro_codigo,
        'filtro_profesor': filtro_profesor,
        'filtro_sin_profesor': filtro_sin_profesor,
        'filtro_nombre': filtro_nombre,
        'profesores': profesores,
        'cursos_disponibles': cursos_disponibles,  # Agregado para el modal
        'estadisticas': estadisticas,
        'puede_gestionar': user_type in ['administrador', 'director'],
        'puede_editar': user_type in ['administrador', 'director'],  # Alias para compatibilidad
        'total_asignaturas': total_asignaturas,
        'asignaturas_con_profesor': asignaturas_con_profesor,
        'asignaturas_sin_profesor_count': asignaturas_sin_profesor_count,
        'asignaturas_sin_profesor': asignaturas_sin_profesor,
        'asignaturas_con_cursos': asignaturas_con_cursos,
        'asignaturas_sin_cursos': asignaturas_sin_cursos,
    }
    
    return render(request, 'listar_asignaturas.html', context)

@login_required
def ingresar_notas(request):
    """Vista para ingresar notas - Selección por curso y asignatura"""
    from .forms import CalificacionForm
    from django.utils import timezone
    
    # Verificar permisos
    user_type_obj = getattr(request.user, 'perfil', None)
    user_type = user_type_obj.tipo_usuario if user_type_obj else None
    if not user_type or user_type not in ['director', 'administrador', 'profesor']:
        messages.error(request, 'No tienes permisos para ingresar notas.')
        return redirect('inicio')

    # Inicializar variables
    cursos_disponibles = []
    curso_seleccionado = None
    asignaturas_disponibles = []
    asignatura_seleccionada = None
    estudiantes_curso_asignatura = []

    # Obtener parámetros
    curso_id = request.GET.get('curso_id') or request.POST.get('curso_id')
    asignatura_id = request.GET.get('asignatura_id') or request.POST.get('asignatura_id')

    anio_actual = timezone.now().year

    # Obtener datos según el tipo de usuario
    if user_type in ['director', 'administrador']:
        cursos_disponibles = Curso.objects.filter(anio=anio_actual).order_by('nivel', 'paralelo')
        if curso_id:
            try:
                curso_seleccionado = cursos_disponibles.get(id=curso_id)
                asignaturas_disponibles = curso_seleccionado.asignaturas.all().order_by('nombre')
                if not asignaturas_disponibles.exists():
                    messages.info(request, f'El curso {curso_seleccionado} no tiene asignaturas asignadas. Asigna asignaturas al curso primero desde la gestión de asignaturas.')
            except Curso.DoesNotExist:
                messages.error(request, 'El curso seleccionado no existe.')
    elif user_type == 'profesor':
        try:
            profesor = Profesor.objects.get(user=request.user)
            # Cursos donde es profesor jefe
            cursos_como_jefe = Curso.objects.filter(profesor_jefe=profesor, anio=anio_actual)
            # Cursos donde imparte asignaturas
            cursos_con_asignaturas = Curso.objects.filter(
                asignaturas__profesor_responsable=profesor, anio=anio_actual
            ).distinct()
            # Combinar ambos tipos de cursos
            cursos_disponibles = (cursos_como_jefe | cursos_con_asignaturas).distinct().order_by('nivel', 'paralelo')
            if curso_id:
                try:
                    curso_seleccionado = cursos_disponibles.get(id=curso_id)
                    asignaturas_curso = curso_seleccionado.asignaturas.all()
                    # Filtrar solo las asignaturas donde el profesor es responsable
                    asignaturas_profesor = profesor.asignaturas_responsable.all()
                    asignaturas_profesor_old = Asignatura.objects.filter(profesor_responsable=profesor)
                    asignaturas_jefe = asignaturas_curso if curso_seleccionado.profesor_jefe == profesor else Asignatura.objects.none()
                    ids_asignaturas = set()
                    ids_asignaturas.update(asignaturas_profesor.values_list('id', flat=True))
                    ids_asignaturas.update(asignaturas_profesor_old.values_list('id', flat=True))
                    ids_asignaturas.update(asignaturas_jefe.values_list('id', flat=True))
                    asignaturas_disponibles = asignaturas_curso.filter(id__in=ids_asignaturas).distinct().order_by('nombre')
                    if not asignaturas_disponibles.exists() and asignaturas_curso.exists():
                        messages.info(request, f'No tienes asignaturas asignadas en el curso {curso_seleccionado}.')
                except Curso.DoesNotExist:
                    messages.error(request, 'No tienes permisos para este curso.')
        except Profesor.DoesNotExist:
            messages.error(request, 'No tienes un perfil de profesor asociado.')
            return redirect('inicio')
    else:
        # Si el usuario no es ninguno de los anteriores, igual pasar los filtros vacíos
        cursos_disponibles = []
        asignaturas_disponibles = []

    # Si hay curso y asignatura seleccionados, obtener estudiantes
    if curso_seleccionado and asignatura_id:
        try:
            asignatura_seleccionada = asignaturas_disponibles.get(id=asignatura_id)
            # Obtener o crear grupo para esta asignatura y curso
            periodo_actual = PeriodoAcademico.objects.filter(activo=True).first()
            if not periodo_actual:
                from datetime import date
                periodo_actual = PeriodoAcademico.objects.create(
                    nombre=f"Año Lectivo {anio_actual}",
                    fecha_inicio=date(anio_actual, 3, 1),
                    fecha_fin=date(anio_actual, 12, 15),
                    activo=True
                )
            profesor_asignatura = asignatura_seleccionada.profesor_responsable
            grupo, created = Grupo.objects.get_or_create(
                asignatura=asignatura_seleccionada,
                periodo_academico=periodo_actual,
                profesor=profesor_asignatura,
                defaults={'capacidad_maxima': 50}
            )
            estudiantes_curso = curso_seleccionado.estudiantes.all()
            for estudiante in estudiantes_curso:
                Inscripcion.objects.get_or_create(estudiante=estudiante, grupo=grupo)
            inscripciones_filtradas = Inscripcion.objects.filter(
                estudiante__in=curso_seleccionado.estudiantes.all(),
                grupo__asignatura=asignatura_seleccionada
            ).select_related('estudiante', 'grupo')
            if user_type == 'profesor':
                profesor = Profesor.objects.get(user=request.user)
                inscripciones_filtradas = inscripciones_filtradas.filter(grupo__profesor=profesor)
            estudiantes_curso_asignatura = inscripciones_filtradas.order_by('estudiante__primer_nombre', 'estudiante__apellido_paterno')
        except Asignatura.DoesNotExist:
            messages.error(request, 'La asignatura seleccionada no existe.')

    # Procesar formulario de notas
    if request.method == 'POST' and estudiantes_curso_asignatura:
        notas_creadas = 0
        errores = 0
        for inscripcion in estudiantes_curso_asignatura:
            nombre_evaluacion = request.POST.get(f'nombre_evaluacion_{inscripcion.id}', '').strip()
            puntaje_str = request.POST.get(f'puntaje_{inscripcion.id}', '').strip()
            porcentaje_str = request.POST.get(f'porcentaje_{inscripcion.id}', '0').strip()
            detalle = request.POST.get(f'detalle_{inscripcion.id}', '').strip()
            descripcion = request.POST.get(f'descripcion_{inscripcion.id}', '').strip()
            if nombre_evaluacion and puntaje_str:
                try:
                    puntaje = float(puntaje_str)
                    porcentaje = float(porcentaje_str) if porcentaje_str else 0
                    if puntaje < 1.0 or puntaje > 7.0:
                        messages.error(request, f'El puntaje para {inscripcion.estudiante.primer_nombre} debe estar entre 1.0 y 7.0')
                        errores += 1
                        continue
                    if porcentaje < 0 or porcentaje > 100:
                        messages.error(request, f'El porcentaje para {inscripcion.estudiante.primer_nombre} debe estar entre 0 y 100')
                        errores += 1
                        continue
                    Calificacion.objects.create(
                        inscripcion=inscripcion,
                        nombre_evaluacion=nombre_evaluacion,
                        puntaje=puntaje,
                        porcentaje=porcentaje,
                        detalle=detalle,
                        descripcion=descripcion,
                        fecha_evaluacion=timezone.now().date()
                    )
                    notas_creadas += 1
                except ValueError:
                    messages.error(request, f'Valores inválidos para {inscripcion.estudiante.primer_nombre}')
                    errores += 1
                except Exception as e:
                    messages.error(request, f'Error al crear nota para {inscripcion.estudiante.primer_nombre}: {str(e)}')
                    errores += 1
        if notas_creadas > 0:
            messages.success(request, f'Se crearon {notas_creadas} notas exitosamente.')
            if errores > 0:
                messages.warning(request, f'{errores} notas no se pudieron crear debido a errores.')
            return redirect(f'/notas/ver/?curso_id={curso_id}&asignatura_id={asignatura_id}')
        else:
            if errores > 0:
                messages.error(request, f'No se crearon notas. {errores} intentos fallaron.')
            else:
                messages.warning(request, 'No se ingresaron datos válidos para crear notas.')

    # Siempre pasar los filtros y opciones al contexto, aunque estén vacíos
    context = {
        'cursos_disponibles': cursos_disponibles,
        'curso_seleccionado': curso_seleccionado,
        'asignaturas_disponibles': asignaturas_disponibles,
        'asignatura_seleccionada': asignatura_seleccionada,
        'estudiantes_curso_asignatura': estudiantes_curso_asignatura,
        'user_type': user_type or 'unknown',
    }
    return render(request, 'ingresar_notas.html', context)

@login_required
def ver_notas_curso(request):
    """Vista para ver notas por curso y asignatura, mostrando todas las notas de todos los estudiantes seleccionados"""
    from django.utils import timezone
    from collections import defaultdict, OrderedDict
    anio_actual = timezone.now().year
    user_type_obj = getattr(request.user, 'perfil', None)
    user_type = user_type_obj.tipo_usuario if user_type_obj else None
    cursos_disponibles = []
    curso_seleccionado = None
    asignaturas_disponibles = []
    asignatura_seleccionada = None
    estudiantes_curso_asignatura = []
    notas = []
    notas_por_estudiante = defaultdict(dict)
    evaluaciones_dict = OrderedDict()
    buscar_asignatura_id = request.GET.get('buscar_asignatura_id')

    curso_id = request.GET.get('curso_id') or request.POST.get('curso_id')
    asignatura_id = request.GET.get('asignatura_id') or request.POST.get('asignatura_id')

    # Obtener todas las asignaturas creadas para el filtro global
    todas_las_asignaturas = Asignatura.objects.all().order_by('nombre')

    # Obtener cursos y asignaturas según el tipo de usuario
    if user_type in ['director', 'administrador']:
        cursos_disponibles = Curso.objects.filter(anio=anio_actual).order_by('nivel', 'paralelo')
        if curso_id:
            try:
                curso_seleccionado = cursos_disponibles.get(id=curso_id)
                asignaturas_disponibles = curso_seleccionado.asignaturas.all().order_by('nombre')
            except Curso.DoesNotExist:
                pass
    elif user_type == 'profesor':
        try:
            profesor = Profesor.objects.get(user=request.user)
            cursos_como_jefe = Curso.objects.filter(profesor_jefe=profesor, anio=anio_actual)
            cursos_con_asignaturas = Curso.objects.filter(
                asignaturas__profesor_responsable=profesor, anio=anio_actual
            ).distinct()
            cursos_disponibles = (cursos_como_jefe | cursos_con_asignaturas).distinct().order_by('nivel', 'paralelo')
            if curso_id:
                try:
                    curso_seleccionado = cursos_disponibles.get(id=curso_id)
                    asignaturas_curso = curso_seleccionado.asignaturas.all()
                    asignaturas_profesor = profesor.asignaturas_responsable.all()
                    asignaturas_profesor_old = Asignatura.objects.filter(profesor_responsable=profesor)
                    asignaturas_jefe = asignaturas_curso if curso_seleccionado.profesor_jefe == profesor else Asignatura.objects.none()
                    ids_asignaturas = set()
                    ids_asignaturas.update(asignaturas_profesor.values_list('id', flat=True))
                    ids_asignaturas.update(asignaturas_profesor_old.values_list('id', flat=True))
                    ids_asignaturas.update(asignaturas_jefe.values_list('id', flat=True))
                    asignaturas_disponibles = asignaturas_curso.filter(id__in=ids_asignaturas).distinct().order_by('nombre')
                except Curso.DoesNotExist:
                    pass
        except Profesor.DoesNotExist:
            pass
    else:
        cursos_disponibles = []
        asignaturas_disponibles = []

    # Si hay curso y asignatura seleccionados, obtener estudiantes y todas las notas
    if curso_seleccionado and (asignatura_id or buscar_asignatura_id):
        try:
            filtro_asignatura_id = buscar_asignatura_id or asignatura_id
            asignatura_seleccionada = Asignatura.objects.get(id=filtro_asignatura_id)
            estudiantes_curso = curso_seleccionado.estudiantes.all()
            inscripciones = Inscripcion.objects.filter(
                estudiante__in=estudiantes_curso,
                grupo__asignatura=asignatura_seleccionada
            ).select_related('estudiante', 'grupo')
            if user_type == 'profesor':
                profesor = Profesor.objects.get(user=request.user)
                inscripciones = inscripciones.filter(grupo__profesor=profesor)
            
            # Obtener estudiantes únicos (evitar duplicados)
            estudiantes_ids = set(inscripciones.values_list('estudiante_id', flat=True))
            estudiantes_curso_asignatura = estudiantes_curso.filter(id__in=estudiantes_ids).order_by('primer_nombre', 'apellido_paterno')
            
            notas = Calificacion.objects.filter(inscripcion__in=inscripciones).select_related('inscripcion', 'inscripcion__estudiante')
            
            # Construir lista de evaluaciones únicas (por nombre solamente, evitando duplicados por fecha)
            evaluaciones_nombres = set()
            for nota in notas:
                evaluaciones_nombres.add(nota.nombre_evaluacion)
            evaluaciones = [{'nombre': nombre} for nombre in sorted(evaluaciones_nombres)]
            
            # Agrupar notas por estudiante y por evaluación
            for estudiante in estudiantes_curso_asignatura:
                notas_est = [None] * len(evaluaciones)
                # Obtener todas las notas del estudiante para esta asignatura
                notas_estudiante = notas.filter(inscripcion__estudiante=estudiante)
                
                for idx, ev in enumerate(evaluaciones):
                    # Obtener la nota más reciente para esta evaluación
                    nota = notas_estudiante.filter(nombre_evaluacion=ev['nombre']).order_by('-fecha_evaluacion').first()
                    notas_est[idx] = nota
                notas_por_estudiante[estudiante] = notas_est
        except Asignatura.DoesNotExist:
            evaluaciones = []
            estudiantes_curso_asignatura = []
    elif curso_seleccionado:
        # Mostrar notas de todas las asignaturas del curso cuando no se selecciona una asignatura específica
        estudiantes_curso = curso_seleccionado.estudiantes.all()
        asignaturas_curso = curso_seleccionado.asignaturas.all()
        
        # Obtener todas las inscripciones del curso para todas las asignaturas
        inscripciones = Inscripcion.objects.filter(
            estudiante__in=estudiantes_curso,
            grupo__asignatura__in=asignaturas_curso
        ).select_related('estudiante', 'grupo', 'grupo__asignatura')
        
        if user_type == 'profesor':
            try:
                profesor = Profesor.objects.get(user=request.user)
                inscripciones = inscripciones.filter(grupo__profesor=profesor)
            except Profesor.DoesNotExist:
                pass
        
        # Obtener todas las notas
        notas = Calificacion.objects.filter(inscripcion__in=inscripciones).select_related(
            'inscripcion', 'inscripcion__estudiante', 'inscripcion__grupo__asignatura'
        )
        
        # Construir evaluaciones únicas con formato "Asignatura - Evaluación"
        evaluaciones_set = set()
        for nota in notas:
            eval_name = f"{nota.inscripcion.grupo.asignatura.nombre} - {nota.nombre_evaluacion}"
            evaluaciones_set.add(eval_name)
        
        evaluaciones = [{'nombre': nombre} for nombre in sorted(evaluaciones_set)]
        
        # Obtener estudiantes únicos del curso
        estudiantes_curso_asignatura = estudiantes_curso.order_by('primer_nombre', 'apellido_paterno')
        
        # Agrupar notas por estudiante y por evaluación
        for estudiante in estudiantes_curso_asignatura:
            notas_est = [None] * len(evaluaciones)
            # Obtener todas las notas del estudiante para este curso
            notas_estudiante = notas.filter(inscripcion__estudiante=estudiante)
            
            for idx, ev in enumerate(evaluaciones):
                # Extraer asignatura y evaluación del nombre compuesto
                partes = ev['nombre'].split(' - ', 1)
                if len(partes) == 2:
                    asignatura_nombre, evaluacion_nombre = partes
                    # Buscar la nota más reciente para esta combinación
                    nota = notas_estudiante.filter(
                        inscripcion__grupo__asignatura__nombre=asignatura_nombre,
                        nombre_evaluacion=evaluacion_nombre
                    ).order_by('-fecha_evaluacion').first()
                    notas_est[idx] = nota
            notas_por_estudiante[estudiante] = notas_est
    else:
        evaluaciones = []
        estudiantes_curso_asignatura = []
        # Asegurar que notas_por_estudiante siga siendo un diccionario
        if not isinstance(notas_por_estudiante, dict):
            notas_por_estudiante = {}

    context = {
        'cursos_disponibles': cursos_disponibles,
        'curso_seleccionado': curso_seleccionado,
        'asignaturas_disponibles': asignaturas_disponibles,
        'asignatura_seleccionada': asignatura_seleccionada,
        'estudiantes_curso_asignatura': estudiantes_curso_asignatura,
        'notas': notas,
        'notas_por_estudiante': notas_por_estudiante,
        'evaluaciones': evaluaciones,
        'user_type': user_type or 'unknown',
        'user': request.user,
        'buscar_asignatura_id': buscar_asignatura_id,
    }

    # Para evitar errores en el template, siempre entregar asignaturas_curso
    if curso_seleccionado:
        asignaturas_curso = curso_seleccionado.asignaturas.all().order_by('nombre')
    else:
        asignaturas_curso = []
    context['asignaturas_curso'] = asignaturas_curso

    # Unificar lista de estudiantes para la tabla (ahora siempre son objetos Estudiante)
    estudiantes_tabla = list(estudiantes_curso_asignatura)
    context['estudiantes_tabla'] = estudiantes_tabla

    # Calcular promedios por estudiante y promedio de la asignatura
    promedios_estudiantes = {}
    suma_total = 0
    total_notas_asignatura = 0
    for estudiante in estudiantes_tabla:
        # Asegurar que notas_por_estudiante tenga la estructura correcta
        if estudiante in notas_por_estudiante:
            notas_est = notas_por_estudiante[estudiante]
        else:
            notas_est = []
        
        # Si notas_est es una lista de objetos nota, extraer puntajes
        if isinstance(notas_est, list):
            notas_validas = [n.puntaje for n in notas_est if n is not None and hasattr(n, 'puntaje')]
        else:
            notas_validas = []
            
        total_notas = len(notas_validas)
        promedio = round(sum(notas_validas) / total_notas, 2) if total_notas > 0 else None
        estado = 'Aprobado' if promedio is not None and promedio >= 4.0 else 'Reprobado'
        promedios_estudiantes[estudiante.id] = {
            'estudiante': estudiante,
            'promedio': promedio if promedio is not None else '--',
            'total_notas': total_notas,
            'estado': estado if promedio is not None else '--',
        }
        if promedio is not None:
            suma_total += promedio
            total_notas_asignatura += 1
    promedio_asignatura = round(suma_total / total_notas_asignatura, 2) if total_notas_asignatura > 0 else None
    context['promedios_estudiantes'] = promedios_estudiantes
    context['promedio_asignatura'] = promedio_asignatura

    return render(request, 'ver_notas_curso.html', context)

@login_required
def asignar_asignaturas_curso(request):
    """Vista para asignar asignaturas a cursos"""
    return redirect('listar_cursos')

@login_required
def registrar_asistencia_alumno(request):
    """Vista mejorada para registrar asistencia de alumnos con permisos y filtros"""
    from .forms import RegistroMasivoAsistenciaForm
    from django.contrib import messages
    from django.utils import timezone
    from datetime import date, datetime
    
    # Determinar tipo de usuario y obtener datos
    user_type = None
    profesor_actual = None
    cursos_disponibles = Curso.objects.none()
    
    if hasattr(request.user, 'perfil'):
        user_type = request.user.perfil.tipo_usuario
        
        if user_type in ['director', 'administrador']:
            # Director y admin pueden ver todos los cursos
            cursos_disponibles = Curso.objects.filter(anio=timezone.now().year).order_by('nivel', 'paralelo')
        elif user_type == 'profesor':
            try:
                profesor_actual = request.user.profesor
                # Profesor puede ver cursos donde es jefe o donde tiene asignaturas asignadas
                cursos_jefe = profesor_actual.cursos_jefatura.filter(anio=timezone.now().year)
                cursos_asignaturas = Curso.objects.filter(
                    asignaturas__profesor_responsable=profesor_actual,
                    anio=timezone.now().year
                ).distinct()
                # También incluir cursos donde el profesor tiene asignaturas con profesor_responsable (campo legacy)
                cursos_legacy = Curso.objects.filter(
                    asignaturas__profesor_responsable=profesor_actual,
                    anio=timezone.now().year
                ).distinct()
                cursos_disponibles = (cursos_jefe | cursos_asignaturas | cursos_legacy).distinct().order_by('nivel', 'paralelo')
            except:
                messages.error(request, 'Error al obtener información del profesor.')
                return render(request, 'registrar_asistencia_alumno.html', {'error': True})
        else:
            messages.error(request, 'No tienes permisos para registrar asistencia.')
            return render(request, 'registrar_asistencia_alumno.html', {'error': True})
    else:
        messages.error(request, 'Usuario sin perfil definido.')
        return render(request, 'registrar_asistencia_alumno.html', {'error': True})
    
    # Variables del contexto
    mostrar_lista = False
    curso_seleccionado = None
    estudiantes = []
    asignatura_seleccionada = None
    fecha_seleccionada = timezone.now().date()
    hora_seleccionada = timezone.now().time()
    
    if request.method == 'POST':
        if 'registro_masivo' in request.POST:
            # Procesar registro masivo de asistencia
            curso_id = request.POST.get('curso')
            fecha_str = request.POST.get('fecha')
            hora_str = request.POST.get('hora_registro')
            
            try:
                curso_seleccionado = get_object_or_404(Curso, id=curso_id)
                
                # Procesar fecha con múltiples formatos posibles
                if fecha_str:
                    # Intentar diferentes formatos de fecha
                    formatos_fecha = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']
                    fecha_seleccionada = None
                    
                    for formato in formatos_fecha:
                        try:
                            fecha_seleccionada = datetime.strptime(fecha_str, formato).date()
                            break
                        except ValueError:
                            continue
                    
                    if fecha_seleccionada is None:
                        # Si no se puede parsear la fecha, usar la fecha actual
                        fecha_seleccionada = timezone.now().date()
                        messages.warning(request, f'No se pudo interpretar la fecha "{fecha_str}". Se usará la fecha actual.')
                else:
                    fecha_seleccionada = timezone.now().date()
                
                # Procesar hora
                if hora_str:
                    try:
                        hora_seleccionada = datetime.strptime(hora_str, '%H:%M:%S').time()
                    except ValueError:
                        try:
                            hora_seleccionada = datetime.strptime(hora_str, '%H:%M').time()
                        except ValueError:
                            hora_seleccionada = timezone.now().time()
                            messages.warning(request, f'No se pudo interpretar la hora "{hora_str}". Se usará la hora actual.')
                else:
                    hora_seleccionada = timezone.now().time()
                
                # Verificar permisos para este curso específico
                if user_type not in ['director', 'administrador']:
                    if profesor_actual and curso_seleccionado not in cursos_disponibles:
                        messages.error(request, 'No tienes permisos para registrar asistencia en este curso.')
                        return redirect('registrar_asistencia_alumno')
                
                # Obtener asignatura del profesor para este curso
                if user_type in ['director', 'administrador']:
                    asignatura_seleccionada = curso_seleccionado.asignaturas.first()
                    if not asignatura_seleccionada:
                        # Si no hay asignaturas, crear una genérica
                        asignatura_seleccionada, created = Asignatura.objects.get_or_create(
                            codigo_asignatura='ASIST',
                            defaults={
                                'nombre': 'Asistencia General',
                                'descripcion': 'Asignatura para registro de asistencia general'
                            }
                        )
                        curso_seleccionado.asignaturas.add(asignatura_seleccionada)
                else:
                    # Buscar asignatura del profesor
                    asignatura_seleccionada = curso_seleccionado.asignaturas.filter(
                        profesor_responsable=profesor_actual
                    ).first()
                
                if not asignatura_seleccionada:
                    messages.error(request, 'No se encontró una asignatura válida para registrar asistencia.')
                    return redirect('registrar_asistencia_alumno')
                
                # Procesar cada estudiante
                estudiantes_procesados = 0
                for estudiante in curso_seleccionado.estudiantes.all():
                    presente = request.POST.get(f'presente_{estudiante.id}') == 'on'
                    observacion = request.POST.get(f'observacion_{estudiante.id}', '').strip()
                    justificacion = request.POST.get(f'justificacion_{estudiante.id}', '').strip()
                    
                    # Crear o actualizar registro de asistencia
                    asistencia, created = AsistenciaAlumno.objects.get_or_create(
                        estudiante=estudiante,
                        curso=curso_seleccionado,
                        asignatura=asignatura_seleccionada,
                        fecha=fecha_seleccionada,
                        defaults={
                            'presente': presente,
                            'hora_registro': hora_seleccionada,
                            'profesor_registro': profesor_actual,
                            'observacion': observacion,
                            'justificacion': justificacion if not presente else '',
                        }
                    )
                    
                    if not created:
                        # Actualizar registro existente
                        asistencia.presente = presente
                        asistencia.observacion = observacion
                        asistencia.justificacion = justificacion if not presente else ''
                        asistencia.fecha_modificacion = timezone.now()
                        asistencia.save()
                    
                    estudiantes_procesados += 1
                
                messages.success(
                    request, 
                    f'Asistencia registrada exitosamente para {estudiantes_procesados} estudiantes del curso {curso_seleccionado}.'
                )
                return redirect('ver_asistencia_alumno')
                
            except Exception as e:
                messages.error(request, f'Error al procesar la asistencia: {str(e)}')
                return redirect('registrar_asistencia_alumno')
        
        else:
            # Selección de curso
            form = RegistroMasivoAsistenciaForm(request.POST)
            # Filtrar cursos disponibles según permisos
            form.fields['curso'].queryset = cursos_disponibles
            
            if form.is_valid():
                curso_seleccionado = form.cleaned_data['curso']
                estudiantes = curso_seleccionado.estudiantes.all().order_by('primer_nombre', 'apellido_paterno')
                
                # Determinar asignatura del profesor para este curso
                if user_type in ['director', 'administrador']:
                    asignatura_seleccionada = curso_seleccionado.asignaturas.first()
                    if not asignatura_seleccionada:
                        # Si no hay asignaturas, crear una genérica
                        asignatura_seleccionada, created = Asignatura.objects.get_or_create(
                            codigo_asignatura='ASIST',
                            defaults={
                                'nombre': 'Asistencia General',
                                'descripcion': 'Asignatura para registro de asistencia general'
                            }
                        )
                        curso_seleccionado.asignaturas.add(asignatura_seleccionada)
                else:
                    # Buscar asignatura del profesor
                    asignatura_seleccionada = curso_seleccionado.asignaturas.filter(
                        profesor_responsable=profesor_actual
                    ).first()
                
                if not asignatura_seleccionada:
                    messages.error(request, 'No tienes asignaturas asignadas a este curso.')
                    form = RegistroMasivoAsistenciaForm()
                    form.fields['curso'].queryset = cursos_disponibles
                else:
                    mostrar_lista = True
            else:
                messages.error(request, 'Por favor selecciona un curso válido.')
    else:
        form = RegistroMasivoAsistenciaForm()
        form.fields['curso'].queryset = cursos_disponibles
    
    
    context = {
        'form': form,
        'mostrar_lista': mostrar_lista,
        'curso_seleccionado': curso_seleccionado,
        'estudiantes': estudiantes,
        'asignatura_seleccionada': asignatura_seleccionada,
        'fecha_seleccionada': fecha_seleccionada,
        'hora_seleccionada': hora_seleccionada,
        'profesor_actual': profesor_actual,
        'user_type': user_type,
        'cursos_disponibles': cursos_disponibles,
    }
    
    return render(request, 'registrar_asistencia_alumno.html', context)

@login_required
def ver_asistencia_alumno(request):
    """Vista mejorada para ver asistencia de alumnos con filtros y permisos"""
    from django.utils import timezone
    from datetime import date, datetime, timedelta
    from django.db.models import Q
    from django.contrib import messages
    
    # Determinar tipo de usuario y permisos
    user_type = None
    estudiante_usuario = None
    profesor_actual = None
    cursos_disponibles = Curso.objects.none()
    
    if hasattr(request.user, 'perfil'):
        user_type = request.user.perfil.tipo_usuario
        
        if user_type == 'alumno':
            # Estudiante solo puede ver su propia asistencia
            try:
                estudiante_usuario = request.user.estudiante
                # Obtener cursos del estudiante
                cursos_disponibles = estudiante_usuario.cursos.filter(anio=timezone.now().year)
            except:
                messages.error(request, 'Error al obtener información del estudiante.')
                return render(request, 'ver_asistencia_alumno.html', {'error': True})
        elif user_type in ['director', 'administrador']:
            # Director y admin pueden ver todos los cursos
            cursos_disponibles = Curso.objects.filter(anio=timezone.now().year).order_by('nivel', 'paralelo')
        elif user_type == 'profesor':
            try:
                profesor_actual = request.user.profesor
                # Profesor puede ver cursos donde es jefe o donde tiene asignaturas
                cursos_jefe = profesor_actual.cursos_jefatura.filter(anio=timezone.now().year)
                cursos_asignaturas = Curso.objects.filter(
                    asignaturas__profesor_responsable=profesor_actual,
                    anio=timezone.now().year
                ).distinct()
                cursos_legacy = Curso.objects.filter(
                    asignaturas__profesor_responsable=profesor_actual,
                    anio=timezone.now().year
                ).distinct()
                cursos_disponibles = (cursos_jefe | cursos_asignaturas | cursos_legacy).distinct().order_by('nivel', 'paralelo')
            except:
                messages.error(request, 'Error al obtener información del profesor.')
                return render(request, 'ver_asistencia_alumno.html', {'error': True})
        else:
            messages.error(request, 'No tienes permisos para ver asistencia.')
            return render(request, 'ver_asistencia_alumno.html', {'error': True})
    else:
        messages.error(request, 'Usuario sin perfil definido.')
        return render(request, 'ver_asistencia_alumno.html', {'error': True})
    
    # Filtros
    curso_id = request.GET.get('curso')
    estudiante_id = request.GET.get('estudiante')
    rut_filtro = request.GET.get('rut', '').strip()
    semana_str = request.GET.get('semana')
    
    # Variables para el contexto
    curso_seleccionado = None
    estudiante_seleccionado = None
    estudiantes_curso = []
    asistencias = AsistenciaAlumno.objects.none()
    mensaje = ""
    
    # Configurar fecha de la semana
    if semana_str:
        try:
            fecha_ref = datetime.strptime(semana_str, '%Y-%m-%d').date()
        except:
            fecha_ref = timezone.now().date()
    else:
        fecha_ref = timezone.now().date()
    
    # Calcular lunes y domingo de la semana
    dias_desde_lunes = fecha_ref.weekday()
    fecha_lunes = fecha_ref - timedelta(days=dias_desde_lunes)
    fecha_domingo = fecha_lunes + timedelta(days=6)
    semana_anterior = fecha_lunes - timedelta(days=7)
    semana_siguiente = fecha_lunes + timedelta(days=7)
    
    # Generar info de la semana
    fechas_semana = []
    for i in range(7):
        fecha_dia = fecha_lunes + timedelta(days=i)
        fechas_semana.append({
            'fecha': fecha_dia,
            'dia_nombre': ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][i],
            'es_hoy': fecha_dia == timezone.now().date()
        })
    
    # Procesar filtros
    if curso_id:
        try:
            curso_seleccionado = get_object_or_404(Curso, id=curso_id)
            # Verificar permisos para este curso
            if curso_seleccionado not in cursos_disponibles:
                messages.error(request, 'No tienes permisos para ver este curso.')
                curso_seleccionado = None
            else:
                # Obtener estudiantes del curso
                if user_type == 'alumno':
                    # El estudiante solo se ve a sí mismo
                    estudiantes_curso = [estudiante_usuario] if estudiante_usuario in curso_seleccionado.estudiantes.all() else []
                else:
                    estudiantes_curso = curso_seleccionado.estudiantes.all().order_by('primer_nombre', 'apellido_paterno')
                
                # Aplicar filtro por RUT si se especifica
                if rut_filtro:
                    estudiantes_curso = [e for e in estudiantes_curso if rut_filtro.lower() in e.numero_documento.lower()]
                
                # Filtro por estudiante específico
                if estudiante_id and user_type != 'alumno':
                    try:
                        estudiante_seleccionado = get_object_or_404(Estudiante, id=estudiante_id)
                        if estudiante_seleccionado in estudiantes_curso:
                            estudiantes_filtro = [estudiante_seleccionado]
                        else:
                            estudiantes_filtro = []
                            messages.warning(request, 'El estudiante seleccionado no pertenece al curso.')
                    except:
                        estudiantes_filtro = estudiantes_curso
                else:
                    if user_type == 'alumno':
                        estudiantes_filtro = [estudiante_usuario]
                        estudiante_seleccionado = estudiante_usuario
                    else:
                        estudiantes_filtro = estudiantes_curso
                
                # Obtener asistencias de la semana
                if estudiantes_filtro:
                    asistencias = AsistenciaAlumno.objects.filter(
                        estudiante__in=estudiantes_filtro,
                        curso=curso_seleccionado,
                        fecha__range=[fecha_lunes, fecha_domingo]
                    ).select_related('estudiante', 'asignatura', 'profesor_registro').order_by('fecha', 'estudiante__primer_nombre')
                
        except:
            messages.error(request, 'Curso no encontrado.')
    
    # Calcular estadísticas
    estadisticas = {
        'total': asistencias.count(),
        'presentes': asistencias.filter(presente=True).count(),
        'ausentes': asistencias.filter(presente=False).count(),
        'porcentaje_asistencia': 0
    }
    
    if estadisticas['total'] > 0:
        estadisticas['porcentaje_asistencia'] = round((estadisticas['presentes'] / estadisticas['total']) * 100, 1)
    
    # Mensaje si no hay curso seleccionado
    if not curso_seleccionado:
        if user_type == 'alumno':
            mensaje = "Selecciona uno de tus cursos para ver tu asistencia"
        else:
            mensaje = "Selecciona un curso para ver la asistencia de los estudiantes"
    
    context = {
        'cursos_disponibles': cursos_disponibles,
        'curso_seleccionado': curso_seleccionado,
        'estudiante_seleccionado': estudiante_seleccionado,
        'estudiantes_curso': estudiantes_curso,
        'asistencias': asistencias,
        'estadisticas': estadisticas,
        'fecha_lunes': fecha_lunes,
        'fecha_domingo': fecha_domingo,
        'fechas_semana': fechas_semana,
        'semana_anterior': semana_anterior,
        'semana_siguiente': semana_siguiente,
        'user_type': user_type,
        'estudiante_usuario': estudiante_usuario,
        'mensaje': mensaje,
        'rut_filtro': rut_filtro,
        'anio_actual': timezone.now().year,
    }
    
    return render(request, 'ver_asistencia_alumno.html', context)

@login_required
def registrar_asistencia_profesor(request):
    """Vista para registrar asistencia de profesores"""
    context = {'user': request.user}
    return render(request, 'registrar_asistencia_profesor.html', context)

@login_required
def ver_asistencia_profesor(request):
    """Vista para ver asistencia de profesores"""
    context = {'user': request.user}
    return render(request, 'ver_asistencia_profesor.html', context)

@login_required
def seleccionar_curso_horarios(request):
    """Vista para seleccionar curso para horarios, coherente con listar_cursos"""
    from django.utils import timezone
    anio_actual = timezone.now().year
    cursos_queryset = Curso.objects.filter(anio=anio_actual)
    cursos = sorted(cursos_queryset, key=lambda c: (c.orden_nivel, c.paralelo))

    cursos_info = []
    total_horarios = 0
    total_asignaturas = 0
    for curso in cursos:
        horarios_count = HorarioCurso.objects.filter(curso=curso).count()
        asignaturas_count = curso.asignaturas.count()
        estudiantes_count = curso.estudiantes.count()
        total_horarios += horarios_count
        total_asignaturas += asignaturas_count
        cursos_info.append({
            'curso': curso,
            'horarios_count': horarios_count,
            'asignaturas_count': asignaturas_count,
            'estudiantes_count': estudiantes_count,
        })

    context = {
        'cursos_info': cursos_info,
        'anio_actual': anio_actual,
        'total_horarios': total_horarios,
        'total_asignaturas': total_asignaturas,
        'user': request.user,
    }
    return render(request, 'seleccionar_curso_horarios.html', context)

@login_required
def gestionar_horarios(request, curso_id=None):
    """Vista para gestionar horarios de un curso, mostrando asignaturas, profesores y días"""
    from .models import Curso, Asignatura, Profesor, HorarioCurso
    from django.shortcuts import get_object_or_404
    curso = get_object_or_404(Curso, id=curso_id)
    asignaturas = curso.asignaturas.all().order_by('nombre')
    profesores = Profesor.objects.all().order_by('primer_nombre', 'apellido_paterno')
    dias_semana = HorarioCurso.DIAS_SEMANA
    horarios = HorarioCurso.objects.filter(curso=curso).order_by('dia', 'hora_inicio')

    context = {
        'curso': curso,
        'asignaturas': asignaturas,
        'profesores': profesores,
        'dias_semana': dias_semana,
        'horarios': horarios,
        'user': request.user,
    }
    return render(request, 'gestionar_horarios.html', context)

@login_required
def ajax_crear_horario(request):
    """Vista AJAX para crear horario"""
    return JsonResponse({'success': False, 'error': 'Función no implementada'})

@login_required
def ajax_editar_horario(request):
    """Vista AJAX para editar horario"""
    return JsonResponse({'success': False, 'error': 'Función no implementada'})

@login_required
def ajax_obtener_horario(request):
    """Vista AJAX para obtener horario"""
    return JsonResponse({'success': False, 'error': 'Función no implementada'})

@login_required
def ajax_eliminar_horario_nuevo(request):
    """Vista AJAX para eliminar horario"""
    return JsonResponse({'success': False, 'error': 'Función no implementada'})

@login_required
def asignar_profesor_asignatura(request, asignatura_id):
    """Vista para asignar profesor a asignatura"""
    return JsonResponse({'success': False, 'error': 'Función no implementada'})

@login_required
def obtener_profesores_asignatura(request, asignatura_id):
    """Vista para obtener profesores de asignatura"""
    return JsonResponse({'profesores': []})

@login_required
def editar_evento(request, evento_id):
    """Vista para editar evento"""
    context = {'user': request.user, 'evento_id': evento_id}
    return render(request, 'editar_evento.html', context)

@login_required
def eliminar_evento(request, evento_id):
    """Vista para eliminar evento"""
    context = {'user': request.user, 'evento_id': evento_id}
    return render(request, 'eliminar_evento.html', context)

@login_required
def agregar_curso(request):
    """Vista para agregar curso usando CursoForm"""
    from .forms import CursoForm
    from django.utils import timezone
    
    # Verificar permisos
    user_type = 'otro'
    if request.user.is_superuser:
        user_type = 'administrador'
    elif hasattr(request.user, 'perfil'):
        user_type = request.user.perfil.tipo_usuario
    
    if user_type not in ['administrador', 'director']:
        messages.error(request, 'No tienes permisos para agregar cursos.')
        return redirect('listar_cursos')
    
    if request.method == 'POST':
        form = CursoForm(request.POST)
        if form.is_valid():
            try:
                curso = form.save()
                messages.success(
                    request, 
                    f'Curso {curso.get_nivel_display()}{curso.paralelo} creado exitosamente.'
                )
                return redirect('listar_cursos')
            except Exception as e:
                messages.error(request, f'Error al crear el curso: {str(e)}')
        else:
            # Mostrar errores del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
    else:
        form = CursoForm()
    
    # Calcular estudiantes disponibles para mostrar en el template
    anio_actual = timezone.now().year
    cursos_actuales = Curso.objects.filter(anio=anio_actual)
    estudiantes_asignados_ids = []
    for curso in cursos_actuales:
        estudiantes_curso = list(curso.estudiantes.values_list('id', flat=True))
        estudiantes_asignados_ids.extend(estudiantes_curso)
    
    estudiantes_asignados_ids = set(estudiantes_asignados_ids)
    total_estudiantes_disponibles = Estudiante.objects.exclude(
        id__in=estudiantes_asignados_ids
    ).count()
    
    context = {
        'form': form,
        'anio_actual': anio_actual,
        'total_estudiantes_disponibles': total_estudiantes_disponibles,
        'user': request.user,
    }
    return render(request, 'agregar_curso.html', context)

@login_required
def editar_curso(request, curso_id):
    """Vista para editar curso usando CursoForm"""
    from .forms import CursoForm
    from django.utils import timezone
    
    # Verificar permisos
    user_type = 'otro'
    if request.user.is_superuser:
        user_type = 'administrador'
    elif hasattr(request.user, 'perfil'):
        user_type = request.user.perfil.tipo_usuario
    
    if user_type not in ['administrador', 'director']:
        messages.error(request, 'No tienes permisos para editar cursos.')
        return redirect('listar_cursos')
    
    # Obtener el curso
    curso = get_object_or_404(Curso, id=curso_id)
    
    if request.method == 'POST':
        form = CursoForm(request.POST, instance=curso)
        if form.is_valid():
            try:
                curso_actualizado = form.save()
                messages.success(
                    request, 
                    f'Curso {curso_actualizado.get_nivel_display()}{curso_actualizado.paralelo} actualizado exitosamente.'
                )
                return redirect('listar_cursos')
            except Exception as e:
                messages.error(request, f'Error al actualizar el curso: {str(e)}')
        else:
            # Mostrar errores del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
    else:
        form = CursoForm(instance=curso)
    
    # Calcular estudiantes disponibles
    anio_actual = timezone.now().year
    cursos_actuales = Curso.objects.filter(anio=anio_actual).exclude(id=curso_id)
    estudiantes_asignados_ids = []
    for c in cursos_actuales:
        estudiantes_curso = list(c.estudiantes.values_list('id', flat=True))
        estudiantes_asignados_ids.extend(estudiantes_curso)
    
    estudiantes_asignados_ids = set(estudiantes_asignados_ids)
    total_estudiantes_disponibles = Estudiante.objects.exclude(
        id__in=estudiantes_asignados_ids
    ).count()
    
    context = {
        'form': form,
        'curso': curso,
        'anio_actual': anio_actual,
        'total_estudiantes_disponibles': total_estudiantes_disponibles,
        'user': request.user,
        'editando': True,
    }
    return render(request, 'editar_curso.html', context)

@login_required
def eliminar_curso(request, curso_id):
    """Vista para eliminar curso"""
    context = {'user': request.user, 'curso_id': curso_id}
    return render(request, 'eliminar_curso.html', context)

@login_required
def agregar_asignatura(request):
    """Vista para agregar asignatura"""
    from .forms import AsignaturaForm
    
    # Verificar permisos
    user_type = 'otro'
    if request.user.is_superuser:
        user_type = 'administrador'
    elif hasattr(request.user, 'perfil'):
        user_type = request.user.perfil.tipo_usuario
    
    if user_type not in ['administrador', 'director']:
        messages.error(request, 'No tienes permisos para agregar asignaturas.')
        return redirect('listar_asignaturas')
    
    # Crear formulario básico usando diccionario
    form_data = {
        'nombre': '',
        'codigo_asignatura': '',
        'descripcion': '',
        'profesor_responsable': ''
    }
    
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre', '').strip()
            codigo_asignatura = request.POST.get('codigo_asignatura', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            profesor_id = request.POST.get('profesor_responsable', '')
            
            # Validaciones
            if not nombre:
                messages.error(request, 'El nombre es obligatorio.')
                return render(request, 'agregar_asignatura.html', {
                    'profesores': Profesor.objects.all(),
                    'user': request.user,
                    'form_data': request.POST
                })
            
            if not codigo_asignatura:
                messages.error(request, 'El código de asignatura es obligatorio.')
                return render(request, 'agregar_asignatura.html', {
                    'profesores': Profesor.objects.all(),
                    'user': request.user,
                    'form_data': request.POST
                })
            
            # Verificar si el código ya existe
            if Asignatura.objects.filter(codigo_asignatura=codigo_asignatura).exists():
                messages.error(request, 'Ya existe una asignatura con este código.')
                return render(request, 'agregar_asignatura.html', {
                    'profesores': Profesor.objects.all(),
                    'user': request.user,
                    'form_data': request.POST
                })
            
            # Crear asignatura
            asignatura = Asignatura.objects.create(
                nombre=nombre,
                codigo_asignatura=codigo_asignatura,
                descripcion=descripcion
            )
            
            # Asignar profesor responsable
            if profesor_id:
                try:
                    profesor = Profesor.objects.get(id=profesor_id)
                    asignatura.profesor_responsable = profesor
                    asignatura.save()
                except Profesor.DoesNotExist:
                    pass
            
            messages.success(request, f'Asignatura "{nombre}" creada exitosamente.')
            return redirect('listar_asignaturas')
            
        except Exception as e:
            messages.error(request, f'Error al crear la asignatura: {str(e)}')
    
    # Crear objeto simulado para el formulario
    class FormSimulator:
        def __init__(self):
            self.nombre = type('field', (), {'errors': []})()
            self.codigo_asignatura = type('field', (), {'errors': []})()
            self.descripcion = type('field', (), {'errors': []})()
            self.profesor_responsable = type('field', (), {'errors': []})()
    
    context = {
        'form': FormSimulator(),
        'profesores': Profesor.objects.all().order_by('primer_nombre', 'apellido_paterno'),
        'user': request.user,
        'titulo': 'Agregar Asignatura',
        'accion': 'Crear'
    }
    return render(request, 'agregar_asignatura.html', context)

@login_required
def editar_asignatura(request, asignatura_id):
    """Vista para editar asignatura"""
    context = {'user': request.user, 'asignatura_id': asignatura_id}
    return render(request, 'editar_asignatura.html', context)

@login_required
def eliminar_asignatura(request, asignatura_id):
    """Vista para eliminar asignatura"""
    context = {'user': request.user, 'asignatura_id': asignatura_id}
    return render(request, 'eliminar_asignatura.html', context)

@login_required
def agregar_asignatura_completa(request):
    """Vista para agregar asignatura completa"""
    context = {'user': request.user}
    return render(request, 'agregar_asignatura_completa.html', context)

@login_required
def ver_horario_curso(request):
    """Vista para ver horario de curso"""
    from django.utils import timezone
    from django.db.models import Q
    from django.contrib import messages
    # Determinar tipo de usuario
    user_type = 'otro'
    if request.user.is_superuser:
        user_type = 'administrador'
    elif hasattr(request.user, 'perfil'):
        user_type = request.user.perfil.tipo_usuario
    elif hasattr(request.user, 'profesor'):
        user_type = 'profesor'

    cursos = []
    curso_seleccionado = None
    horarios = []
    es_director = False
    es_profesor = False

    if user_type in ['administrador', 'director']:
        cursos = Curso.objects.filter(anio=timezone.now().year).order_by('nivel', 'paralelo')
        es_director = True
        es_profesor = False
        if request.method == 'POST':
            curso_id = request.POST.get('curso_id')
            if curso_id:
                try:
                    curso_seleccionado = cursos.get(id=curso_id)
                    horarios = HorarioCurso.objects.filter(curso=curso_seleccionado).order_by('dia', 'hora_inicio')
                except Curso.DoesNotExist:
                    messages.error(request, 'Curso no encontrado.')
    elif user_type == 'profesor':
        try:
            profesor = request.user.profesor
            horarios = HorarioCurso.objects.filter(
                Q(asignatura__profesor_responsable=profesor) |
                Q(curso__profesor_jefe=profesor)
            ).distinct().order_by('dia', 'hora_inicio')
            es_director = False
            es_profesor = True
        except Exception:
            messages.error(request, 'No se pudo obtener tu perfil de profesor.')
            es_director = False
            es_profesor = False
    else:
        messages.error(request, 'No tienes permisos para ver horarios.')
        return redirect('inicio')
    
    context = {
        'cursos': cursos,
        'curso_seleccionado': curso_seleccionado,
        'horarios': horarios,
        'es_director': es_director,
        'es_profesor': es_profesor,
        'user': request.user
    }
    return render(request, 'ver_horario_curso.html', context)

@login_required
def api_horarios_cursos(request):
    """API para horarios de cursos"""
    return JsonResponse({'horarios': []})

@login_required
def editar_nota(request, nota_id):
    """Vista para editar nota"""
    from .forms import CalificacionForm
    from django.shortcuts import get_object_or_404
    
    # Obtener la nota (Calificacion) a editar
    nota = get_object_or_404(Calificacion, id=nota_id)
    
    # Obtener estudiante y asignatura relacionados
    estudiante = nota.inscripcion.estudiante
    asignatura = nota.inscripcion.grupo.asignatura
    
    # Verificar permisos del usuario
    user_type_obj = getattr(request.user, 'perfil', None)
    user_type = user_type_obj.tipo_usuario if user_type_obj else None
    
    # Solo admin, director o profesor responsable puede editar
    if user_type not in ['director', 'administrador']:
        if user_type == 'profesor':
            try:
                profesor = request.user.profesor
                if not (asignatura.profesor_responsable == profesor):
                    messages.error(request, 'No tienes permisos para editar esta nota.')
                    return redirect('ver_notas_curso')
            except:
                messages.error(request, 'No tienes permisos para editar esta nota.')
                return redirect('ver_notas_curso')
        else:
            messages.error(request, 'No tienes permisos para editar esta nota.')
            return redirect('ver_notas_curso')
    
    if request.method == 'POST':
        form = CalificacionForm(request.POST, instance=nota)
        if form.is_valid():
            form.save()
            messages.success(request, f'Nota de {estudiante.get_nombre_completo()} actualizada exitosamente.')
            return redirect('ver_notas_curso')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = CalificacionForm(instance=nota)
    
    context = {
        'user': request.user,
        'nota_id': nota_id,
        'nota': nota,
        'estudiante': estudiante,
        'asignatura': asignatura,
        'form': form,
        'titulo': 'Editar Nota'
    }
    return render(request, 'editar_nota.html', context)

@login_required
def eliminar_nota(request, nota_id):
    """Vista para eliminar nota"""
    from django.shortcuts import get_object_or_404
    
    # Obtener la nota (Calificacion) a eliminar
    nota = get_object_or_404(Calificacion, id=nota_id)
    
    # Obtener estudiante y asignatura relacionados
    estudiante = nota.inscripcion.estudiante
    asignatura = nota.inscripcion.grupo.asignatura
    
    # Verificar permisos del usuario
    user_type_obj = getattr(request.user, 'perfil', None)
    user_type = user_type_obj.tipo_usuario if user_type_obj else None
    
    # Solo admin, director o profesor responsable puede eliminar
    if user_type not in ['director', 'administrador']:
        if user_type == 'profesor':
            try:
                profesor = request.user.profesor
                if not (asignatura.profesor_responsable == profesor):
                    messages.error(request, 'No tienes permisos para eliminar esta nota.')
                    return redirect('ver_notas_curso')
            except:
                messages.error(request, 'No tienes permisos para eliminar esta nota.')
                return redirect('ver_notas_curso')
        else:
            messages.error(request, 'No tienes permisos para eliminar esta nota.')
            return redirect('ver_notas_curso')
    
    if request.method == 'POST':
        nombre_evaluacion = nota.nombre_evaluacion
        nota.delete()
        messages.success(request, f'Nota "{nombre_evaluacion}" de {estudiante.get_nombre_completo()} eliminada exitosamente.')
        return redirect('ver_notas_curso')
    
    context = {
        'user': request.user,
        'nota_id': nota_id,
        'nota': nota,
        'estudiante': estudiante,
        'asignatura': asignatura
    }
    return render(request, 'eliminar_nota.html', context)

@login_required
def agregar_nota_individual(request, estudiante_id, asignatura_id, evaluacion_nombre):
    """Vista para agregar una nota individual a un estudiante específico"""
    from .forms import CalificacionForm
    from django.shortcuts import get_object_or_404
    from urllib.parse import unquote
    
    # Obtener el estudiante y asignatura
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    asignatura = get_object_or_404(Asignatura, id=asignatura_id)
    evaluacion_nombre = unquote(evaluacion_nombre)
    
    # Verificar permisos del usuario
    user_type_obj = getattr(request.user, 'perfil', None)
    user_type = user_type_obj.tipo_usuario if user_type_obj else None
    
    # Solo admin, director o profesor responsable puede agregar notas
    if user_type not in ['director', 'administrador']:
        if user_type == 'profesor':
            try:
                profesor = request.user.profesor
                if not (asignatura.profesor_responsable == profesor):
                    messages.error(request, 'No tienes permisos para agregar notas a esta asignatura.')
                    return redirect('ver_notas_curso')
            except:
                messages.error(request, 'No tienes permisos para agregar notas.')
                return redirect('ver_notas_curso')
        else:
            messages.error(request, 'No tienes permisos para agregar notas.')
            return redirect('ver_notas_curso')
    
    # Obtener o crear inscripción del estudiante
    from django.utils import timezone
    anio_actual = timezone.now().year
    periodo_actual = PeriodoAcademico.objects.filter(activo=True).first()
    if not periodo_actual:
        from datetime import date
        periodo_actual = PeriodoAcademico.objects.create(
            nombre=f"Año Lectivo {anio_actual}",
            fecha_inicio=date(anio_actual, 3, 1),
            fecha_fin=date(anio_actual, 12, 15),
            activo=True
        )
    
    # Obtener o crear grupo para esta asignatura
    profesor_asignatura = asignatura.profesor_responsable
    grupo, created = Grupo.objects.get_or_create(
        asignatura=asignatura,
        periodo_academico=periodo_actual,
        profesor=profesor_asignatura,
        defaults={'capacidad_maxima': 50}
    )
    
    # Obtener o crear inscripción
    inscripcion, created = Inscripcion.objects.get_or_create(
        estudiante=estudiante,
        grupo=grupo
    )
    
    if request.method == 'POST':
        form = CalificacionForm(request.POST)
        if form.is_valid():
            calificacion = form.save(commit=False)
            calificacion.inscripcion = inscripcion
            calificacion.nombre_evaluacion = evaluacion_nombre
            calificacion.fecha_evaluacion = timezone.now().date()
            calificacion.save()
            messages.success(request, f'Nota agregada exitosamente para {estudiante.get_nombre_completo()}.')
            return redirect('ver_notas_curso')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        # Pre-llenar el formulario con el nombre de la evaluación
        form = CalificacionForm(initial={'nombre_evaluacion': evaluacion_nombre})
    
    context = {
        'user': request.user,
        'estudiante': estudiante,
        'asignatura': asignatura,
        'evaluacion_nombre': evaluacion_nombre,
        'form': form,
        'titulo': 'Agregar Nota',
        'es_nueva': True
    }
    return render(request, 'editar_nota.html', context)

@login_required
def gestionar_asignaturas_curso_ajax(request):
    """Vista AJAX para gestionar asignaturas de un curso (asignar/desasignar)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    # Verificar permisos
    if not (hasattr(request.user, 'perfil') and 
            request.user.perfil.tipo_usuario in ['director', 'administrador', 'profesor_jefe']):
        return JsonResponse({'success': False, 'error': 'No tienes permisos para gestionar asignaturas'})
    
    try:
        data = json.loads(request.body)
        curso_id = data.get('curso_id')
        asignatura_id = data.get('asignatura_id')
        accion = data.get('accion')  # 'asignar' o 'desasignar'
        
        if not all([curso_id, asignatura_id, accion]):
            return JsonResponse({'success': False, 'error': 'Datos incompletos'})
        
        curso = get_object_or_404(Curso, id=curso_id)
        asignatura = get_object_or_404(Asignatura, id=asignatura_id)
        
        if accion == 'asignar':
            curso.asignaturas.add(asignatura)
            mensaje = f'Asignatura {asignatura.nombre} asignada al curso {curso.get_nivel_display()}{curso.paralelo}'
        elif accion == 'desasignar':
            curso.asignaturas.remove(asignatura)
            mensaje = f'Asignatura {asignatura.nombre} removida del curso {curso.get_nivel_display()}{curso.paralelo}'
        else:
            return JsonResponse({'success': False, 'error': 'Acción no válida'})
        
        # Calcular estadísticas actualizadas
        cursos_queryset = Curso.objects.filter(anio=timezone.now().year)
        total_asignaturas_asignadas = sum(curso.asignaturas.count() for curso in cursos_queryset)
        asignaturas_curso_actual = curso.asignaturas.count()
        
        return JsonResponse({
            'success': True, 
            'mensaje': mensaje,
            'asignaturas_curso': asignaturas_curso_actual,
            'total_asignaturas_asignadas': total_asignaturas_asignadas
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Error en el formato de datos'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'})

@login_required
def obtener_asignaturas_curso_ajax(request, curso_id):
    """Vista AJAX para obtener las asignaturas de un curso específico"""
    try:
        curso = get_object_or_404(Curso, id=curso_id)
        asignaturas_asignadas = curso.asignaturas.all()
        asignaturas_disponibles = Asignatura.objects.exclude(id__in=asignaturas_asignadas.values_list('id', flat=True))
        
        data = {
            'curso': {
                'id': curso.id,
                'nombre': f"{curso.get_nivel_display()}{curso.paralelo}",
                'nivel_display': curso.get_nivel_display(),
                'paralelo': curso.paralelo
            },
            'asignaturas_asignadas': [
                {
                    'id': asig.id,
                    'nombre': asig.nombre,
                    'codigo': asig.codigo_asignatura
                } for asig in asignaturas_asignadas
            ],
            'asignaturas_disponibles': [
                {
                    'id': asig.id,
                    'nombre': asig.nombre,
                    'codigo': asig.codigo_asignatura
                } for asig in asignaturas_disponibles
            ]
        }
        
        return JsonResponse({'success': True, 'data': data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error: {str(e)}'})

@login_required
def editar_asistencia_alumno(request, asistencia_id):
    """Vista para editar un registro individual de asistencia"""
    from .forms import AsistenciaAlumnoForm
    from django.contrib import messages
    
    # Obtener el registro de asistencia
    asistencia = get_object_or_404(AsistenciaAlumno, id=asistencia_id)
    
    # Verificar permisos
    user_type = None
    if hasattr(request.user, 'perfil'):
        user_type = request.user.perfil.tipo_usuario
        
        if user_type == 'alumno':
            # Estudiante no puede editar asistencia
            messages.error(request, 'No tienes permisos para editar registros de asistencia.')
            return redirect('ver_asistencia_alumno')
        elif user_type == 'profesor':
            try:
                profesor_actual = request.user.profesor
                # Profesor solo puede editar si es jefe del curso o responsable de la asignatura
                puede_editar = (
                    asistencia.curso.profesor_jefe == profesor_actual or
                    asistencia.asignatura.profesor_responsable == profesor_actual
                )
                if not puede_editar:
                    messages.error(request, 'No tienes permisos para editar este registro de asistencia.')
                    return redirect('ver_asistencia_alumno')
            except:
                messages.error(request, 'Error al verificar permisos.')
                return redirect('ver_asistencia_alumno')
        elif user_type not in ['director', 'administrador']:
            messages.error(request, 'No tienes permisos para editar registros de asistencia.')
            return redirect('ver_asistencia_alumno')
    else:
        messages.error(request, 'Usuario sin perfil definido.')
        return redirect('ver_asistencia_alumno')
    
    if request.method == 'POST':
        form = AsistenciaAlumnoForm(request.POST, instance=asistencia, editando=True)
        if form.is_valid():
            asistencia_actualizada = form.save(commit=False)
            asistencia_actualizada.fecha_modificacion = timezone.now()
            asistencia_actualizada.save()
            
            messages.success(
                request, 
                f'Asistencia actualizada para {asistencia.estudiante.get_nombre_completo()} - {asistencia.fecha.strftime("%d/%m/%Y")}'
            )
            return redirect('ver_asistencia_alumno')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = AsistenciaAlumnoForm(instance=asistencia, editando=True)
    
    context = {
        'form': form,
        'asistencia': asistencia,
        'titulo': f'Editar Asistencia - {asistencia.estudiante.get_nombre_completo()}',
    }
    
    return render(request, 'editar_asistencia_alumno.html', context)

@login_required
def libro_anotaciones(request):
    """Vista principal del libro de anotaciones con permisos diferenciados"""
    from .models import calcular_puntaje_comportamiento
    from django.db.models import Count, Q
    from django.core.paginator import Paginator
    
    # Determinar tipo de usuario y permisos
    user_type = None
    profesor_actual = None
    estudiante_actual = None
    
    if hasattr(request.user, 'perfil'):
        user_type = request.user.perfil.tipo_usuario
        
        if user_type == 'alumno':
            # Estudiante solo ve sus anotaciones
            try:
                estudiante_actual = request.user.estudiante
                anotaciones_base = Anotacion.objects.filter(estudiante=estudiante_actual)
                cursos_disponibles = estudiante_actual.cursos.filter(anio=timezone.now().year)
                puede_crear = False
            except:
                messages.error(request, 'Error al obtener información del estudiante.')
                return render(request, 'libro_anotaciones.html', {'error': True})
                
        elif user_type == 'profesor':
            # Profesor ve anotaciones de sus cursos y puede crear
            try:
                profesor_actual = request.user.profesor
                cursos_disponibles = profesor_actual.get_cursos_asignados()
                
                # Obtener estudiantes de sus cursos
                estudiantes_ids = set()
                for curso in cursos_disponibles:
                    estudiantes_ids.update(curso.estudiantes.values_list('id', flat=True))
                
                anotaciones_base = Anotacion.objects.filter(estudiante_id__in=estudiantes_ids)
                puede_crear = True
            except:
                messages.error(request, 'Error al obtener información del profesor.')
                return render(request, 'libro_anotaciones.html', {'error': True})
                
        elif user_type in ['director', 'administrador']:
            # Director/Admin ve todas las anotaciones
            anotaciones_base = Anotacion.objects.all()
            cursos_disponibles = Curso.objects.filter(anio=timezone.now().year)
            puede_crear = True
        else:
            messages.error(request, 'No tienes permisos para acceder al libro de anotaciones.')
            return render(request, 'libro_anotaciones.html', {'error': True})
    else:
        messages.error(request, 'Usuario sin perfil definido.')
        return render(request, 'libro_anotaciones.html', {'error': True})
    
    # Procesar filtros
    filtro_form = FiltroAnotacionesForm(request.GET, profesor=profesor_actual)
    anotaciones = anotaciones_base.select_related(
        'estudiante', 'curso', 'asignatura', 'profesor_autor'
    ).order_by('-fecha_creacion')
    
    # Aplicar filtros
    if filtro_form.is_valid():
        if filtro_form.cleaned_data.get('curso'):
            anotaciones = anotaciones.filter(curso=filtro_form.cleaned_data['curso'])
        
        if filtro_form.cleaned_data.get('estudiante'):
            anotaciones = anotaciones.filter(estudiante=filtro_form.cleaned_data['estudiante'])
        
        if filtro_form.cleaned_data.get('tipo'):
            anotaciones = anotaciones.filter(tipo=filtro_form.cleaned_data['tipo'])
        
        if filtro_form.cleaned_data.get('categoria'):
            anotaciones = anotaciones.filter(categoria=filtro_form.cleaned_data['categoria'])
        
        if filtro_form.cleaned_data.get('fecha_desde'):
            anotaciones = anotaciones.filter(fecha_creacion__gte=filtro_form.cleaned_data['fecha_desde'])
        
        if filtro_form.cleaned_data.get('fecha_hasta'):
            fecha_hasta = filtro_form.cleaned_data['fecha_hasta']
            # Incluir todo el día
            fecha_hasta = datetime.combine(fecha_hasta, datetime.max.time())
            anotaciones = anotaciones.filter(fecha_creacion__lte=fecha_hasta)
        
        if filtro_form.cleaned_data.get('solo_graves'):
            anotaciones = anotaciones.filter(es_grave=True)
    
    # Estadísticas generales
    stats_generales = {
        'total': anotaciones.count(),
        'positivas': anotaciones.filter(tipo='positiva').count(),
        'negativas': anotaciones.filter(tipo='negativa').count(),
        'neutras': anotaciones.filter(tipo='neutra').count(),
        'graves': anotaciones.filter(es_grave=True).count(),
    }
    
    # Paginación
    paginator = Paginator(anotaciones, 20)  # 20 anotaciones por página
    page_number = request.GET.get('page')
    anotaciones_paginas = paginator.get_page(page_number)
    
    # Estadísticas por estudiante (solo si no es alumno)
    stats_estudiantes = []
    if user_type != 'alumno':
        # Obtener estudiantes únicos de las anotaciones filtradas
        estudiantes_con_anotaciones = set(anotaciones.values_list('estudiante_id', flat=True))
        
        for estudiante_id in list(estudiantes_con_anotaciones)[:10]:  # Limitar a 10 para rendimiento
            try:
                estudiante = Estudiante.objects.get(id=estudiante_id)
                stats = calcular_puntaje_comportamiento(estudiante)
                stats['estudiante'] = estudiante
                stats_estudiantes.append(stats)
            except:
                continue
        
        # Ordenar por puntaje
        stats_estudiantes.sort(key=lambda x: x['puntaje_total'], reverse=True)
    
    context = {
        'anotaciones': anotaciones_paginas,
        'filtro_form': filtro_form,
        'stats_generales': stats_generales,
        'stats_estudiantes': stats_estudiantes,
        'user_type': user_type,
        'puede_crear': puede_crear,
        'profesor_actual': profesor_actual,
        'estudiante_actual': estudiante_actual,
        'cursos_disponibles': cursos_disponibles,
    }
    
    return render(request, 'libro_anotaciones.html', context)

@login_required
def crear_anotacion(request):
    """Vista para crear una nueva anotación"""
    # Verificar permisos
    user_type = None
    profesor_actual = None
    
    if hasattr(request.user, 'perfil'):
        user_type = request.user.perfil.tipo_usuario
        
        if user_type == 'alumno':
            messages.error(request, 'Los estudiantes no pueden crear anotaciones.')
            return redirect('libro_anotaciones')
        elif user_type == 'profesor':
            try:
                profesor_actual = request.user.profesor
            except:
                messages.error(request, 'Error al obtener información del profesor.')
                return redirect('libro_anotaciones')
        elif user_type not in ['director', 'administrador']:
            messages.error(request, 'No tienes permisos para crear anotaciones.')
            return redirect('libro_anotaciones')
    else:
        messages.error(request, 'Usuario sin perfil definido.')
        return redirect('libro_anotaciones')
    
    if request.method == 'POST':
        form = AnotacionForm(request.POST, profesor=profesor_actual)
        if form.is_valid():
            anotacion = form.save(commit=False)
            
            # Asignar profesor autor
            if profesor_actual:
                anotacion.profesor_autor = profesor_actual
            else:
                # Para admin/director, buscar un profesor por defecto o crear uno
                # (esto podría mejorarse según la lógica de tu sistema)
                anotacion.profesor_autor = Profesor.objects.first()
            
            anotacion.save()
            
            messages.success(
                request, 
                f'Anotación {anotacion.get_tipo_display().lower()} creada para {anotacion.estudiante.get_nombre_completo()}'
            )
            return redirect('libro_anotaciones')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = AnotacionForm(profesor=profesor_actual)
    
    context = {
        'form': form,
        'titulo': 'Crear Nueva Anotación',
        'profesor_actual': profesor_actual,
        'user_type': user_type,
    }
    
    return render(request, 'crear_anotacion.html', context)

@login_required
@login_required
def editar_anotacion(request, anotacion_id):
    """Vista para editar una anotación existente"""
    anotacion = get_object_or_404(Anotacion, id=anotacion_id)
    
    # Verificar permisos
    user_type = None
    profesor_actual = None
    
    if hasattr(request.user, 'perfil'):
        user_type = request.user.perfil.tipo_usuario
        
        if user_type == 'alumno':
            messages.error(request, 'Los estudiantes no pueden editar anotaciones.')
            return redirect('libro_anotaciones')
        elif user_type == 'profesor':
            try:
                profesor_actual = request.user.profesor
                # Profesor solo puede editar sus propias anotaciones o de sus cursos
                if anotacion.profesor_autor != profesor_actual:
                    cursos_profesor = profesor_actual.get_cursos_asignados()
                    if anotacion.curso not in cursos_profesor:
                        messages.error(request, 'No tienes permisos para editar esta anotación.')
                        return redirect('libro_anotaciones')
            except:
                messages.error(request, 'Error al verificar permisos.')
                return redirect('libro_anotaciones')
        elif user_type not in ['director', 'administrador']:
            messages.error(request, 'No tienes permisos para editar anotaciones.')
            return redirect('libro_anotaciones')
    else:
        messages.error(request, 'Usuario sin perfil definido.')
        return redirect('libro_anotaciones')
    
    if request.method == 'POST':
        form = AnotacionForm(request.POST, instance=anotacion, profesor=profesor_actual, editando=True)
        if form.is_valid():
            anotacion_actualizada = form.save()
            
            messages.success(
                request, 
                f'Anotación actualizada para {anotacion.estudiante.get_nombre_completo()}'
            )
            return redirect('libro_anotaciones')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = AnotacionForm(instance=anotacion, profesor=profesor_actual, editando=True)
    
    context = {
        'form': form,
        'anotacion': anotacion,
        'titulo': f'Editar Anotación - {anotacion.estudiante.get_nombre_completo()}',
        'profesor_actual': profesor_actual,
        'user_type': user_type,
    }
    
    return render(request, 'editar_anotacion.html', context)

@login_required
def eliminar_anotacion(request, anotacion_id):
    """Vista para eliminar una anotación"""
    anotacion = get_object_or_404(Anotacion, id=anotacion_id)
    
    # Verificar permisos (solo admin/director o el profesor autor)
    user_type = None
    if hasattr(request.user, 'perfil'):
        user_type = request.user.perfil.tipo_usuario
        
        if user_type not in ['director', 'administrador']:
            if user_type == 'profesor':
                try:
                    profesor_actual = request.user.profesor
                    if anotacion.profesor_autor != profesor_actual:
                        messages.error(request, 'Solo puedes eliminar tus propias anotaciones.')
                        return redirect('libro_anotaciones')
                except:
                    messages.error(request, 'Error al verificar permisos.')
                    return redirect('libro_anotaciones')
            else:
                messages.error(request, 'No tienes permisos para eliminar anotaciones.')
                return redirect('libro_anotaciones')
    else:
        messages.error(request, 'Usuario sin perfil definido.')
        return redirect('libro_anotaciones')
    
    if request.method == 'POST':
        estudiante_nombre = anotacion.estudiante.get_nombre_completo()
        anotacion.delete()
        
        messages.success(request, f'Anotación eliminada para {estudiante_nombre}.')
        return redirect('libro_anotaciones')
    
    context = {
        'anotacion': anotacion,
        'titulo': f'Eliminar Anotación - {anotacion.estudiante.get_nombre_completo()}',
    }
    
    return render(request, 'eliminar_anotacion.html', context)

@login_required
def detalle_comportamiento_estudiante(request, estudiante_id):
    """Vista detallada del comportamiento de un estudiante específico"""
    from .models import calcular_puntaje_comportamiento
    from django.core.paginator import Paginator
    
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    
    # Verificar permisos
    user_type = None
    puede_ver = False
    
    if hasattr(request.user, 'perfil'):
        user_type = request.user.perfil.tipo_usuario
        
        if user_type == 'alumno':
            # Estudiante solo ve su propio comportamiento
            try:
                estudiante_actual = request.user.estudiante
                puede_ver = (estudiante == estudiante_actual)
            except:
                puede_ver = False
        elif user_type == 'profesor':
            # Profesor ve estudiantes de sus cursos
            try:
                profesor_actual = request.user.profesor
                cursos_profesor = profesor_actual.get_cursos_asignados()
                cursos_estudiante = estudiante.cursos.filter(anio=timezone.now().year)
                puede_ver = cursos_profesor.filter(id__in=cursos_estudiante.values_list('id', flat=True)).exists()
            except:
                puede_ver = False
        elif user_type in ['director', 'administrador']:
            puede_ver = True
    
    if not puede_ver:
        messages.error(request, 'No tienes permisos para ver el comportamiento de este estudiante.')
        return redirect('libro_anotaciones')
    
    # Obtener curso actual del estudiante
    curso_actual = estudiante.get_curso_actual()
    
    # Obtener todas las anotaciones del estudiante
    anotaciones = Anotacion.objects.filter(estudiante=estudiante).select_related(
        'curso', 'asignatura', 'profesor_autor'
    ).order_by('-fecha_creacion')
    
    # Filtros opcionales por fecha
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if fecha_desde:
        try:
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            anotaciones = anotaciones.filter(fecha_creacion__gte=fecha_desde_obj)
        except:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            fecha_hasta_obj = datetime.combine(fecha_hasta_obj, datetime.max.time())
            anotaciones = anotaciones.filter(fecha_creacion__lte=fecha_hasta_obj)
        except:
            pass
    
    # Calcular estadísticas
    stats = calcular_puntaje_comportamiento(
        estudiante, 
        curso=curso_actual,
        fecha_desde=datetime.strptime(fecha_desde, '%Y-%m-%d').date() if fecha_desde else None,
        fecha_hasta=datetime.strptime(fecha_hasta, '%Y-%m-%d').date() if fecha_hasta else None
    )
    
    # Paginación
    paginator = Paginator(anotaciones, 15)
    page_number = request.GET.get('page')
    anotaciones_paginas = paginator.get_page(page_number)
    
    # Gráfico de evolución (últimos 30 días)
    from datetime import timedelta
    fecha_inicio_grafico = timezone.now().date() - timedelta(days=30)
    
    anotaciones_grafico = Anotacion.objects.filter(
        estudiante=estudiante,
        fecha_creacion__gte=fecha_inicio_grafico
    ).values('fecha_creacion__date', 'puntos').order_by('fecha_creacion__date')
    
    # Datos para el gráfico
    datos_grafico = {}
    for anotacion in anotaciones_grafico:
        fecha = anotacion['fecha_creacion__date']
        if fecha not in datos_grafico:
            datos_grafico[fecha] = 0
        datos_grafico[fecha] += anotacion['puntos']
    
    context = {
        'estudiante': estudiante,
        'curso_actual': curso_actual,
        'anotaciones': anotaciones_paginas,
        'stats': stats,
        'user_type': user_type,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'datos_grafico': datos_grafico,
    }
    
    return render(request, 'detalle_comportamiento_estudiante.html', context)

@login_required
def ajax_obtener_estudiantes_curso(request):
    """Vista AJAX para obtener estudiantes de un curso"""
    if request.method == 'GET':
        curso_id = request.GET.get('curso_id')
        
        if curso_id:
            try:
                curso = Curso.objects.get(id=curso_id)
                estudiantes = curso.estudiantes.all().order_by('primer_nombre', 'apellido_paterno')
                
                data = {
                    'estudiantes': [
                        {
                            'id': est.id,
                            'nombre': est.get_nombre_completo(),
                            'rut': est.numero_documento
                        }
                        for est in estudiantes
                    ]
                }
                return JsonResponse(data)
            except Curso.DoesNotExist:
                return JsonResponse({'error': 'Curso no encontrado'}, status=404)
        
        return JsonResponse({'error': 'ID de curso requerido'}, status=400)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required  
def ajax_obtener_estudiantes_filtro(request):
    """Vista AJAX para obtener estudiantes por curso en filtros"""
    if request.method == 'GET':
        curso_id = request.GET.get('curso_id')
        
        if curso_id:
            try:
                curso = Curso.objects.get(id=curso_id)
                
                # Verificar permisos según el tipo de usuario
                user_type = None
                profesor_actual = None
                
                if hasattr(request.user, 'perfil'):
                    user_type = request.user.perfil.tipo_usuario
                    
                    if user_type == 'profesor':
                        try:
                            profesor_actual = request.user.profesor
                            cursos_disponibles = profesor_actual.get_cursos_asignados()
                            # Si no tiene el curso asignado, pero es profesor, permitir si tiene estudiantes
                            if curso not in cursos_disponibles:
                                # Verificar si al menos tiene estudiantes en común
                                estudiantes = curso.estudiantes.all()
                                if not estudiantes.exists():
                                    return JsonResponse({'error': 'Sin permisos para este curso'}, status=403)
                        except:
                            # Si hay error obteniendo el profesor, permitir la consulta
                            pass
                
                estudiantes = curso.estudiantes.all().order_by('primer_nombre', 'apellido_paterno')
                
                data = {
                    'estudiantes': [
                        {
                            'id': est.id,
                            'nombre': est.get_nombre_completo(),
                            'rut': est.numero_documento
                        }
                        for est in estudiantes
                    ]
                }
                return JsonResponse(data)
            except Curso.DoesNotExist:
                return JsonResponse({'error': 'Curso no encontrado'}, status=404)
        else:
            # Si no hay curso seleccionado, devolver lista vacía
            return JsonResponse({'estudiantes': []})
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)