from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import Estudiante, Profesor, Apoderado, RelacionApoderadoEstudiante, EventoCalendario, Curso, HorarioCurso, Asignatura, PeriodoAcademico, Anotacion
from .forms import EstudianteForm, ProfesorForm, ApoderadoForm, DirectorForm, EventoCalendarioForm, CursoForm, HorarioCursoForm, AsignaturaForm, AsignaturaCompletaForm, SeleccionCursoAlumnoForm, CalificacionForm, AsistenciaAlumnoForm, AsistenciaProfesorForm, RegistroMasivoAsistenciaForm, AnotacionForm, FiltroAnotacionesForm
from django.db import models
from django.db.models import Q, Avg, Count
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Perfil
from django.http import HttpResponseForbidden, JsonResponse
from django.forms import formset_factory
from .models import Inscripcion, Grupo, Calificacion, AsistenciaAlumno, AsistenciaProfesor
from datetime import date, datetime, timedelta
from .decorators import admin_required, profesor_admin_required, all_users_required, profesor_con_asignaturas_required
from django.views.decorators.http import require_POST
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

@admin_required
def agregar(request):
    tipo = request.GET.get('tipo', 'estudiante')
    mensaje = ""
    
    # Si es una petición GET (cambio de tipo), crear formulario vacío
    if request.method == 'GET':
        if tipo == 'profesor':
            form = ProfesorForm()
        elif tipo == 'apoderado':
            form = ApoderadoForm()
        elif tipo == 'director':
            form = DirectorForm()
        else:
            form = EstudianteForm()
    else:
        # Es una petición POST (envío del formulario)
        if tipo == 'profesor':
            form = ProfesorForm(request.POST)
            if form.is_valid():
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
        elif tipo == 'apoderado':
            form = ApoderadoForm(request.POST)
            if form.is_valid():
                # El formulario maneja la creación del usuario y las relaciones
                apoderado = form.save()
                mensaje = f"Apoderado {apoderado.get_nombre_completo()} agregado correctamente."
                form = ApoderadoForm()  # Limpiar formulario
        elif tipo == 'director':
            form = DirectorForm(request.POST)
            if form.is_valid():
                try:
                    # El formulario maneja la creación del usuario y perfil
                    user, perfil = form.save()
                    mensaje = f"Director {user.get_full_name()} agregado correctamente."
                    form = DirectorForm()  # Limpiar formulario
                except Exception as e:
                    # Log del error para debugging
                    import traceback
                    print(f"Error al crear director: {e}")
                    print(f"Traceback: {traceback.format_exc()}")
                    mensaje = f"Error al crear director: {str(e)}"
            else:
                # Log de errores del formulario para debugging
                print(f"Errores del formulario DirectorForm: {form.errors}")
                print(f"Errores no específicos de campo: {form.non_field_errors()}")
                
                # Los errores del formulario se mostrarán automáticamente en el template
                # No necesitamos crear un mensaje personalizado aquí
        else:
            form = EstudianteForm(request.POST)
            if form.is_valid():
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
    codigo = request.GET.get('codigo', '')
    seleccionado_id = request.GET.get('id')
    mensaje = ""
    form = None
    resultados = []

    if tipo == 'profesor':
        # Construir filtros para la búsqueda
        filtros = Q()
        if query:
            filtros |= (
                Q(primer_nombre__icontains=query) |
                Q(segundo_nombre__icontains=query) |
                Q(apellido_paterno__icontains=query) |
                Q(apellido_materno__icontains=query) |
                Q(email__icontains=query)
            )
        if codigo:
            filtros |= Q(codigo_profesor__icontains=codigo)
        if seleccionado_id:
            filtros |= Q(id__exact=seleccionado_id)
        
        # Aplicar filtros solo si hay criterios de búsqueda
        if query or codigo or seleccionado_id:
            resultados = Profesor.objects.filter(filtros).distinct()
        else:
            resultados = Profesor.objects.none()
            
        # Si hay un profesor seleccionado para modificar
        if seleccionado_id:
            try:
                seleccionado = Profesor.objects.get(id=seleccionado_id)
                if request.method == 'POST':
                    form = ProfesorForm(request.POST, instance=seleccionado)
                    if form.is_valid():
                        profesor_guardado = form.save()
                        
                        # Manejar usuario del profesor si se proporcionaron datos
                        username = form.cleaned_data.get('username')
                        password = form.cleaned_data.get('password')
                        
                        # Si hay usuario existente y no se especificó username, usar el actual
                        if not username and profesor_guardado.user:
                            username = profesor_guardado.user.username

                        if username:
                            if profesor_guardado.user:
                                # Actualizar usuario existente
                                user = profesor_guardado.user
                                user.username = username
                                user.first_name = profesor_guardado.primer_nombre
                                user.last_name = profesor_guardado.apellido_paterno
                                user.email = profesor_guardado.email
                                if password:  # Solo actualizar contraseña si se proporcionó una nueva
                                    user.set_password(password)
                                user.save()
                            else:
                                # Crear nuevo usuario
                                from django.contrib.auth.models import User
                                user = User.objects.create_user(
                                    username=username,
                                    email=profesor_guardado.email,
                                    password=password or 'temp123',
                                    first_name=profesor_guardado.primer_nombre,
                                    last_name=profesor_guardado.apellido_paterno
                                )
                                profesor_guardado.user = user
                                profesor_guardado.save()
                        
                        # Verificar si ahora es apoderado
                        try:
                            apoderado = profesor_guardado.apoderado_profile
                            if apoderado:
                                messages.success(request, f"Profesor modificado correctamente. También se actualizó su perfil de apoderado (Código: {apoderado.codigo_apoderado}).")
                            else:
                                messages.success(request, "Profesor modificado correctamente.")
                        except:
                            messages.success(request, "Profesor modificado correctamente.")
                        
                        # Redireccionar para evitar reenvío del formulario
                        return redirect(f'/modificar?tipo=profesor&id={profesor_guardado.id}')
                            
                else:
                    form = ProfesorForm(instance=seleccionado)
            except Profesor.DoesNotExist:
                mensaje = "El profesor seleccionado no existe."
                seleccionado_id = None
                
    else:  # estudiante
        # Construir filtros para la búsqueda
        filtros = Q()
        if query:
            filtros |= (
                Q(primer_nombre__icontains=query) |
                Q(segundo_nombre__icontains=query) |
                Q(apellido_paterno__icontains=query) |
                Q(apellido_materno__icontains=query) |
                Q(email__icontains=query)
            )
        if codigo:
            filtros |= Q(codigo_estudiante__icontains=codigo)
        if seleccionado_id:
            filtros |= Q(id__exact=seleccionado_id)
        
        # Aplicar filtros solo si hay criterios de búsqueda
        if query or codigo or seleccionado_id:
            resultados = Estudiante.objects.filter(filtros).distinct()
        else:
            resultados = Estudiante.objects.none()
            
        # Si hay un estudiante seleccionado para modificar
        if seleccionado_id:
            try:
                seleccionado = Estudiante.objects.get(id=seleccionado_id)
                if request.method == 'POST':
                    form = EstudianteForm(request.POST, instance=seleccionado)
                    if form.is_valid():
                        estudiante_guardado = form.save()
                        
                        # Manejar usuario del estudiante si se proporcionaron datos
                        username = form.cleaned_data.get('username')
                        password = form.cleaned_data.get('password')
                        
                        # Si hay usuario existente y no se especificó username, usar el actual
                        if not username and estudiante_guardado.user:
                            username = estudiante_guardado.user.username

                        if username:
                            if estudiante_guardado.user:
                                # Actualizar usuario existente
                                user = estudiante_guardado.user
                                user.username = username
                                user.first_name = estudiante_guardado.primer_nombre
                                user.last_name = estudiante_guardado.apellido_paterno
                                user.email = estudiante_guardado.email or ''
                                if password:  # Solo actualizar contraseña si se proporcionó una nueva
                                    user.set_password(password)
                                user.save()
                            else:
                                # Crear nuevo usuario
                                from django.contrib.auth.models import User
                                user = User.objects.create_user(
                                    username=username,
                                    email=estudiante_guardado.email or '',
                                    password=password or 'temp123',
                                    first_name=estudiante_guardado.primer_nombre,
                                    last_name=estudiante_guardado.apellido_paterno
                                )
                                estudiante_guardado.user = user
                                estudiante_guardado.save()
                                
                                # Crear perfil de estudiante si no existe
                                from .models import Perfil
                                if not hasattr(user, 'perfil'):
                                    Perfil.objects.create(user=user, tipo_usuario='estudiante')
                        
                        messages.success(request, "Estudiante modificado correctamente.")
                        
                        # Redireccionar para evitar reenvío del formulario
                        return redirect(f'/modificar?tipo=estudiante&id={estudiante_guardado.id}')
                else:
                    form = EstudianteForm(instance=seleccionado)
            except Estudiante.DoesNotExist:
                mensaje = "El estudiante seleccionado no existe."
                seleccionado_id = None

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
    
    estudiantes = Estudiante.objects.select_related('user').all()

    if q_estudiante:
        estudiantes = estudiantes.filter(
            Q(primer_nombre__icontains=q_estudiante) |
            Q(apellido_paterno__icontains=q_estudiante) |
            Q(codigo_estudiante__icontains=q_estudiante)
        )
    
    if genero_estudiante:
        estudiantes = estudiantes.filter(genero=genero_estudiante)
        
    if tipo_doc_estudiante:
        estudiantes = estudiantes.filter(tipo_documento=tipo_doc_estudiante)

    # Estadísticas
    total_estudiantes = Estudiante.objects.count()
    estudiantes_activos = Estudiante.objects.filter(user__is_active=True).count()
    estudiantes_sin_curso = Estudiante.objects.filter(cursos__isnull=True).count()
    cursos_count = Curso.objects.filter(anio=timezone.now().year).count()

    context = {
        'estudiantes': estudiantes,
        'q_estudiante': q_estudiante,
        'genero_estudiante': genero_estudiante,
        'tipo_doc_estudiante': tipo_doc_estudiante,
        'total_estudiantes': total_estudiantes,
        'estudiantes_activos': estudiantes_activos,
        'estudiantes_sin_curso': estudiantes_sin_curso,
        'cursos_count': cursos_count,
    }
    return render(request, 'listar_estudiantes.html', context)

@admin_required
def listar_profesores(request):
    q_profesor = request.GET.get('q_profesor', '')
    genero_profesor = request.GET.get('genero_profesor', '')
    especialidad_profesor = request.GET.get('especialidad_profesor', '')

    profesores = Profesor.objects.select_related('user').all()

    if q_profesor:
        profesores = profesores.filter(
            Q(primer_nombre__icontains=q_profesor) |
            Q(apellido_paterno__icontains=q_profesor) |
            Q(codigo_profesor__icontains=q_profesor)
        )
    
    if genero_profesor:
        profesores = profesores.filter(genero=genero_profesor)
        
    if especialidad_profesor:
        profesores = profesores.filter(especialidad__icontains=especialidad_profesor)

    # Estadísticas
    total_profesores = Profesor.objects.count()
    profesores_activos = Profesor.objects.filter(user__is_active=True).count()
    profesores_con_asignaturas = Profesor.objects.filter(asignaturas__isnull=False).distinct().count()
    asignaturas_count = Asignatura.objects.count()

    context = {
        'profesores': profesores,
        'q_profesor': q_profesor,
        'genero_profesor': genero_profesor,
        'especialidad_profesor': especialidad_profesor,
        'total_profesores': total_profesores,
        'profesores_activos': profesores_activos,
        'profesores_con_asignaturas': profesores_con_asignaturas,
        'asignaturas_count': asignaturas_count,
    }
    return render(request, 'listar_profesores.html', context)

@admin_required
def gestionar_profesor(request, profesor_id=None):
    profesor = None
    if profesor_id:
        profesor = get_object_or_404(Profesor, id=profesor_id)

    if request.method == 'POST':
        form = ProfesorForm(request.POST, request.FILES, instance=profesor)
        if form.is_valid():
            try:
                # Si es nuevo profesor, crear usuario primero
                if not profesor:
                    username = form.cleaned_data.get('username')
                    email = form.cleaned_data.get('email')
                    password = form.cleaned_data.get('password')
                    
                    if User.objects.filter(username=username).exists():
                        messages.error(request, 'El nombre de usuario ya existe.')
                        return render(request, 'gestionar_profesor.html', {'form': form, 'profesor': profesor})
                        
                    user = User.objects.create_user(username=username, email=email, password=password)
                    Perfil.objects.create(user=user, tipo_usuario='profesor')
                    
                    profesor_obj = form.save(commit=False)
                    profesor_obj.user = user
                    profesor_obj.save()
                    form.save_m2m() # Guardar relaciones ManyToMany
                    messages.success(request, 'Profesor creado exitosamente.')
                else:
                    # Actualizar profesor existente
                    profesor_obj = form.save()
                    
                    # Actualizar datos de usuario si se proporcionaron
                    user = profesor_obj.user
                    if user:
                        username = form.cleaned_data.get('username')
                        email = form.cleaned_data.get('email')
                        password = form.cleaned_data.get('password')
                        is_active = form.cleaned_data.get('is_active')
                        
                        if username and username != user.username:
                            if User.objects.filter(username=username).exclude(id=user.id).exists():
                                messages.warning(request, 'El nombre de usuario ya está en uso. No se actualizó.')
                            else:
                                user.username = username
                        
                        if email:
                            user.email = email
                        if password:
                            user.set_password(password)
                            
                        # Actualizar estado activo
                        if is_active is not None:
                            user.is_active = is_active
                            
                        user.save()
                    
                    messages.success(request, 'Profesor actualizado exitosamente.')
                
                return redirect('listar_profesores')
            except Exception as e:
                messages.error(request, f'Error al guardar: {str(e)}')
    else:
        form = ProfesorForm(instance=profesor)
        # Pre-llenar datos del usuario si existe
        if profesor and profesor.user:
            form.initial['username'] = profesor.user.username
            form.initial['email'] = profesor.user.email
            form.initial['is_active'] = profesor.user.is_active

    return render(request, 'gestionar_profesor.html', {'form': form, 'profesor': profesor})

@admin_required
def gestionar_estudiante(request, estudiante_id=None):
    estudiante = None
    if estudiante_id:
        estudiante = get_object_or_404(Estudiante, id=estudiante_id)

    if request.method == 'POST':
        form = EstudianteForm(request.POST, request.FILES, instance=estudiante)
        if form.is_valid():
            try:
                # Si es nuevo estudiante, crear usuario primero
                if not estudiante:
                    username = form.cleaned_data.get('username')
                    email = form.cleaned_data.get('email')
                    password = form.cleaned_data.get('password')
                    
                    if User.objects.filter(username=username).exists():
                        messages.error(request, 'El nombre de usuario ya existe.')
                        return render(request, 'gestionar_estudiante.html', {'form': form, 'estudiante': estudiante})
                        
                    user = User.objects.create_user(username=username, email=email, password=password)
                    Perfil.objects.create(user=user, tipo_usuario='alumno')
                    
                    estudiante_obj = form.save(commit=False)
                    estudiante_obj.user = user
                    estudiante_obj.save()
                    messages.success(request, 'Estudiante creado exitosamente.')
                else:
                    # Actualizar estudiante existente
                    estudiante_obj = form.save()
                    
                    # Actualizar datos de usuario si se proporcionaron
                    user = estudiante_obj.user
                    if user:
                        username = form.cleaned_data.get('username')
                        email = form.cleaned_data.get('email')
                        password = form.cleaned_data.get('password')
                        is_active = form.cleaned_data.get('is_active')
                        
                        if username and username != user.username:
                            if User.objects.filter(username=username).exclude(id=user.id).exists():
                                messages.warning(request, 'El nombre de usuario ya está en uso. No se actualizó.')
                            else:
                                user.username = username
                        
                        if email:
                            user.email = email
                            
                        if password:
                            user.set_password(password)
                            
                        # Actualizar estado activo
                        if is_active is not None:
                            user.is_active = is_active
                            
                        user.save()
                    
                    messages.success(request, 'Estudiante actualizado exitosamente.')
                
                return redirect('listar_estudiantes')
            except Exception as e:
                messages.error(request, f'Error al guardar: {str(e)}')
    else:
        form = EstudianteForm(instance=estudiante)
        if not estudiante:
             form.initial['is_active'] = True
        elif estudiante.user:
            form.initial['username'] = estudiante.user.username
            form.initial['email'] = estudiante.user.email
            form.initial['is_active'] = estudiante.user.is_active

    return render(request, 'gestionar_estudiante.html', {'form': form, 'estudiante': estudiante})

@login_required
def calendario(request):
    from datetime import datetime
    
    # Filtros
    fecha_filtro = request.GET.get('fecha', '')
    curso_filtro = request.GET.get('curso', '')
    estudiante_id = request.GET.get('estudiante_id', '')
    
    # Determinar tipo de usuario
    user_type = 'otro'
    if hasattr(request.user, 'perfil'):
        user_type = request.user.perfil.tipo_usuario
    elif request.user.is_superuser:
        user_type = 'administrador'
        
    puede_crear_eventos = user_type in ['administrador', 'director', 'profesor']
    
    # Obtener cursos para el modal (si tiene permisos)
    cursos_modal = []
    if puede_crear_eventos:
        if user_type in ['administrador', 'director']:
            cursos_modal = Curso.objects.all().order_by('nivel', 'paralelo', 'anio')
        elif user_type == 'profesor':
            try:
                profesor = request.user.profesor
                cursos_modal = Curso.objects.filter(
                    Q(profesor_jefe=profesor) | Q(asignaturas__profesores=profesor)
                ).distinct().order_by('nivel', 'paralelo', 'anio')
            except:
                cursos_modal = []
    
    # Obtener eventos base
    eventos = EventoCalendario.objects.all()
    
    # Filtrar por permisos
    if user_type == 'estudiante':
        try:
            estudiante = request.user.estudiante
            curso = estudiante.get_curso_actual()
            eventos = eventos.filter(
                Q(para_todos_los_cursos=True) | 
                Q(cursos=curso)
            ).distinct()
        except:
            eventos = eventos.none()
    elif user_type == 'profesor':
        try:
            profesor = request.user.profesor
            cursos_profesor = profesor.get_cursos_asignados()
            eventos = eventos.filter(
                Q(para_todos_los_cursos=True) | 
                Q(cursos__in=cursos_profesor) |
                Q(solo_profesores=True) |
                Q(creado_por=request.user)
            ).distinct()
        except:
            eventos = eventos.none()
    elif user_type == 'apoderado':
        # Lógica para apoderado
        eventos = eventos.filter(
            Q(para_todos_los_cursos=True) | 
            Q(solo_apoderados=True)
        ).distinct()

    # Aplicar filtros de UI
    if fecha_filtro:
        try:
            fecha_obj = datetime.strptime(fecha_filtro, '%Y-%m-%d').date()
            eventos = eventos.filter(fecha=fecha_obj)
        except:
            pass
            
    if curso_filtro:
        eventos = eventos.filter(cursos__id=curso_filtro)

    # Preparar JSON (usando todos los eventos filtrados)
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
            'tipo': evento.tipo_evento,
            'extendedProps': {
                'description': evento.descripcion or '',
                'responsable': evento.creado_por.get_full_name() if evento.creado_por else 'Sistema',
                'tipo': evento.get_tipo_evento_display(),
                'prioridad': evento.get_prioridad_display()
            }
        })
    
    # Filtrar eventos para la lista lateral (solo futuros y ordenados)
    from django.utils import timezone
    from datetime import timedelta
    
    hoy = timezone.now().date()
    eventos_futuros = eventos.filter(fecha__gte=hoy).order_by('fecha', 'hora_inicio')
    
    # Calcular métricas
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)
    
    eventos_count = {
        'hoy': eventos.filter(fecha=hoy).count(),
        'semana': eventos.filter(fecha__range=[inicio_semana, fin_semana]).count()
    }
    
    context = {
        'eventos_json': json.dumps(eventos_json),
        'eventos': eventos_futuros, # Lista de próximos eventos
        'eventos_count': eventos_count, # Métricas
        'user_type': user_type,
        'puede_crear_eventos': puede_crear_eventos,
        'tipos_evento': EventoCalendario.TIPO_EVENTO_CHOICES,
        'prioridades': EventoCalendario.PRIORIDAD_CHOICES,
        'cursos': cursos_modal,
    }
    return render(request, 'calendario_alternativo.html', context)

@login_required
def inicio(request):
    """Vista del panel de inicio personalizado por tipo de usuario"""
    from django.utils import timezone
    from django.db.models import Avg, Count, Q, F
    from django.db.models.functions import TruncMonth
    
    template_name = 'inicio.html'
    context = {
        'user': request.user,
        'es_alumno': False,
        'es_profesor': False,
    }
    
    # Datos específicos según el tipo de usuario
    user_type = None
    if hasattr(request.user, 'perfil'):
        user_type = request.user.perfil.tipo_usuario
    elif request.user.is_superuser:
        user_type = 'administrador'

    if user_type:
        if user_type == 'alumno':
            try:
                estudiante = request.user.estudiante
                anio_actual = timezone.now().year
                
                # Información del curso actual (tomar el más avanzado si hay varios)
                curso_actual = estudiante.cursos.filter(anio=anio_actual).order_by('-nivel').first()
                
                # Si el ordenamiento por nivel no es efectivo, usar orden personalizado
                if not curso_actual or estudiante.cursos.filter(anio=anio_actual).count() > 1:
                    # Crear orden personalizado: primero medio, luego básico
                    cursos_anio = estudiante.cursos.filter(anio=anio_actual)
                    cursos_medio = cursos_anio.filter(nivel__endswith='M').order_by('-nivel')
                    cursos_basico = cursos_anio.filter(nivel__endswith='B').order_by('-nivel')
                    
                    # Preferir medio sobre básico
                    if cursos_medio.exists():
                        curso_actual = cursos_medio.first()
                    elif cursos_basico.exists():
                        curso_actual = cursos_basico.first()
                    else:
                        curso_actual = cursos_anio.first()
                
                # Si no hay curso del año actual, tomar el más reciente
                if not curso_actual:
                    curso_actual = estudiante.cursos.order_by('-anio', '-nivel').first()
                
                # Asignaturas del estudiante
                asignaturas = []
                asignaturas_con_profesores = []
                if curso_actual:
                    asignaturas = curso_actual.asignaturas.all()
                    # Crear lista con información de asignaturas y sus profesores
                    for asignatura in asignaturas:
                        asignaturas_con_profesores.append({
                            'asignatura': asignatura,
                            'profesor': asignatura.profesor_responsable
                        })
                
                # Estadísticas de notas
                from .models import Calificacion, Inscripcion
                
                # Usar el sistema de inscripciones y calificaciones
                inscripciones = Inscripcion.objects.filter(estudiante=estudiante)
                calificaciones = Calificacion.objects.filter(inscripcion__in=inscripciones)
                
                # Calcular promedio desde calificaciones
                if calificaciones.exists():
                    promedio_general = calificaciones.aggregate(Avg('puntaje'))['puntaje__avg']
                    total_notas = calificaciones.count()
                else:
                    promedio_general = None
                    total_notas = 0
                
                # Estadísticas de asistencia
                from .models import AsistenciaAlumno
                asistencias = AsistenciaAlumno.objects.filter(estudiante=estudiante)
                total_asistencias = asistencias.count()
                presentes = asistencias.filter(presente=True).count()
                porcentaje_asistencia = (presentes / total_asistencias * 100) if total_asistencias > 0 else 0
                
                # Anotaciones recientes
                from .models import Anotacion
                anotaciones_recientes = Anotacion.objects.filter(
                    estudiante=estudiante
                ).order_by('-fecha_creacion')[:5]
                
                # Próximos horarios (próximos 3 días)
                from datetime import datetime, timedelta
                from .models import HorarioCurso
                hoy = timezone.now().date()
                proximos_horarios = []
                horario_semanal_completo = []
                horas_disponibles = []
                horario_tabla_estudiante = []
                dias_codigo_a_info = {
                    'LU': {'numero': 1, 'nombre': 'Lunes'},
                    'MA': {'numero': 2, 'nombre': 'Martes'},
                    'MI': {'numero': 3, 'nombre': 'Miércoles'},
                    'JU': {'numero': 4, 'nombre': 'Jueves'},
                    'VI': {'numero': 5, 'nombre': 'Viernes'},
                    'SA': {'numero': 6, 'nombre': 'Sábado'},
                    'DO': {'numero': 7, 'nombre': 'Domingo'},
                }
                dias_estudiante_tabla = [
                    {
                        'codigo': codigo,
                        'nombre': info['nombre'],
                        'numero': info['numero'],
                    }
                    for codigo, info in dias_codigo_a_info.items()
                    if info['numero'] <= 6
                ]
                
                if curso_actual:
                    # Mapeo de días: weekday() a códigos del modelo
                    dias_weekday_a_codigo = {
                        0: 'LU',  # Lunes
                        1: 'MA',  # Martes  
                        2: 'MI',  # Miércoles
                        3: 'JU',  # Jueves
                        4: 'VI',  # Viernes
                        5: 'SA',  # Sábado
                        6: 'DO'   # Domingo
                    }
                    
                    # Próximos 3 días
                    for i in range(3):  # Próximos 3 días
                        fecha = hoy + timedelta(days=i)
                        dia_semana = fecha.weekday()  # 0=Lunes, 6=Domingo
                        codigo_dia = dias_weekday_a_codigo[dia_semana]
                        
                        horarios_dia = HorarioCurso.objects.filter(
                            curso=curso_actual,
                            dia=codigo_dia
                        ).order_by('hora_inicio')
                        
                        if horarios_dia.exists():
                            proximos_horarios.append({
                                'fecha': fecha,
                                'dia_nombre': ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][dia_semana],
                                'horarios': horarios_dia
                            })
                    
                    # Horario completo de la semana (todos los días)
                    horarios_semana = HorarioCurso.objects.filter(
                        curso=curso_actual
                    ).order_by('dia', 'hora_inicio')
                    
                    for codigo_dia, info_dia in dias_codigo_a_info.items():
                        horarios_del_dia = horarios_semana.filter(dia=codigo_dia)
                        if horarios_del_dia.exists():
                            horario_semanal_completo.append({
                                'dia_numero': info_dia['numero'],
                                'dia_nombre': info_dia['nombre'],
                                'horarios': horarios_del_dia
                            })
                    
                    # Generar lista de horas disponibles para la tabla
                    if horarios_semana.exists():
                        horas_set = set()
                        horarios_por_clave = {}
                        for horario in horarios_semana:
                            horas_set.add(horario.hora_inicio.strftime('%H:%M'))
                            hora_str = horario.hora_inicio.strftime('%H:%M')
                            if hora_str not in horarios_por_clave:
                                horarios_por_clave[hora_str] = {}
                            horarios_por_clave[hora_str][horario.dia] = horario
                        horas_disponibles = sorted(list(horas_set))
                        for hora in horas_disponibles:
                            fila = {
                                'hora': hora,
                                'dias': []
                            }
                            for dia_info in dias_estudiante_tabla:
                                codigo = dia_info['codigo']
                                fila['dias'].append({
                                    'codigo': codigo,
                                    'horario': horarios_por_clave.get(hora, {}).get(codigo)
                                })
                            horario_tabla_estudiante.append(fila)
                
                # Información adicional del estudiante
                todos_cursos = estudiante.cursos.all().order_by('-anio', '-nivel')
                
                context.update({
                    'estudiante': estudiante,
                    'curso_actual': curso_actual,
                    'todos_cursos': todos_cursos,
                    'asignaturas': asignaturas,
                    'asignaturas_con_profesores': asignaturas_con_profesores,
                    'promedio_general': round(promedio_general, 2) if promedio_general else None,
                    'total_notas': total_notas,
                    'total_asistencias': total_asistencias,
                    'presentes': presentes,
                    'porcentaje_asistencia': round(porcentaje_asistencia, 1),
                    'anotaciones_recientes': anotaciones_recientes,
                    'proximos_horarios': proximos_horarios[:3],  # Solo 3 días
                    'horario_semanal_completo': horario_semanal_completo,
                    'horas_disponibles': horas_disponibles,
                    'horario_tabla_estudiante': horario_tabla_estudiante,
                    'dias_estudiante_tabla': dias_estudiante_tabla,
                    'dias_codigo_a_info': dias_codigo_a_info,
                })
                
            except Estudiante.DoesNotExist:
                context['error_estudiante'] = "No se encontró información del estudiante asociada a este usuario."
            except Exception as e:
                context['error_estudiante'] = f"Error al cargar datos del estudiante: {str(e)}"
                # Para debug, agregar más información
                import traceback
                print(f"Error en vista inicio (alumno): {traceback.format_exc()}")
                
        elif user_type == 'profesor':
            try:
                profesor = request.user.profesor
                anio_actual = timezone.now().year
                
                # Cursos donde es jefe
                cursos_jefe = profesor.cursos_jefatura.filter(anio=anio_actual)
                
                # Cursos donde tiene asignaturas
                cursos_asignados_qs = profesor.get_cursos_asignados().prefetch_related('estudiantes', 'asignaturas')
                cursos_con_asignaturas = []
                for curso in cursos_asignados_qs:
                    estudiantes_total = curso.estudiantes.count()
                    mis_asignaturas_count = curso.asignaturas.filter(profesor_responsable=profesor).count()
                    curso.estudiantes_total = estudiantes_total
                    curso.mis_asignaturas_count = mis_asignaturas_count
                    curso.total_asignaturas = curso.asignaturas.count()
                    cursos_con_asignaturas.append(curso)
                
                # Asignaturas que enseña
                asignaturas_profesor = profesor.asignaturas.all().order_by('nombre')
                
                # Estadísticas de anotaciones creadas
                from .models import Anotacion
                anotaciones_creadas = Anotacion.objects.filter(profesor_autor=profesor)
                anotaciones_recientes = anotaciones_creadas.order_by('-fecha_creacion')[:5]
                
                # Estadísticas por tipo de anotación
                stats_anotaciones = {
                    'total': anotaciones_creadas.count(),
                    'positivas': anotaciones_creadas.filter(tipo='positiva').count(),
                    'negativas': anotaciones_creadas.filter(tipo='negativa').count(),
                    'neutras': anotaciones_creadas.filter(tipo='neutra').count(),
                }
                
                # Próximos horarios del profesor
                from .models import HorarioCurso
                from datetime import datetime, timedelta
                hoy = timezone.now().date()
                proximos_horarios_profesor = []
                
                # Mapeo de días
                dias_weekday_a_codigo = {
                    0: 'LU', 1: 'MA', 2: 'MI', 3: 'JU', 4: 'VI', 5: 'SA', 6: 'DO'
                }
                
                # Próximos 3 días de horarios
                for i in range(3):
                    fecha = hoy + timedelta(days=i)
                    dia_semana = fecha.weekday()
                    codigo_dia = dias_weekday_a_codigo[dia_semana]
                    
                    horarios_dia = HorarioCurso.objects.filter(
                        curso__in=cursos_con_asignaturas,
                        dia=codigo_dia
                    ).order_by('hora_inicio')
                    
                    if horarios_dia.exists():
                        proximos_horarios_profesor.append({
                            'fecha': fecha,
                            'dia_nombre': ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][dia_semana],
                            'horarios': horarios_dia
                        })
                
                # Total de estudiantes bajo su responsabilidad
                total_estudiantes = 0
                for curso in cursos_con_asignaturas:
                    total_estudiantes += getattr(curso, 'estudiantes_total', curso.estudiantes.count())
                
                # Asistencia reciente de profesores
                from .models import AsistenciaProfesor
                asistencias_profesor = AsistenciaProfesor.objects.filter(
                    profesor=profesor
                ).order_by('-fecha')[:10]
                
                context.update({
                    'profesor': profesor,
                    'cursos_jefe': cursos_jefe,
                    'cursos_con_asignaturas': cursos_con_asignaturas,
                    'asignaturas_profesor': asignaturas_profesor,
                    'anotaciones_creadas': anotaciones_creadas,
                    'anotaciones_recientes': anotaciones_recientes,
                    'stats_anotaciones': stats_anotaciones,
                    'proximos_horarios_profesor': proximos_horarios_profesor,
                    'total_estudiantes': total_estudiantes,
                    'asistencias_profesor': asistencias_profesor,
                })
                
            except AttributeError:
                context['error_profesor'] = "No se encontró información del profesor asociada a este usuario."
            except Exception as e:
                context['error_profesor'] = f"Error al cargar datos del profesor: {str(e)}"
                import traceback
                print(f"Error en vista inicio (profesor): {traceback.format_exc()}")
                
        elif user_type == 'apoderado':
            try:
                # Verificar si es un apoderado directo
                apoderado = None
                es_profesor_apoderado = False
                
                if hasattr(request.user, 'apoderado'):
                    apoderado = request.user.apoderado
                elif hasattr(request.user, 'profesor') and hasattr(request.user.profesor, 'apoderado_profile'):
                    apoderado = request.user.profesor.apoderado_profile
                    es_profesor_apoderado = True
                
                if apoderado:
                    # Redirigir a la vista específica de apoderados
                    if es_profesor_apoderado:
                        return redirect('dashboard_profesor_apoderado')
                    else:
                        return redirect('dashboard_apoderado')
                else:
                    context['error_apoderado'] = "No se encontró información del apoderado asociada a este usuario."
                    
            except Exception as e:
                context['error_apoderado'] = f"Error al cargar datos del apoderado: {str(e)}"
                import traceback
                print(f"Error en vista inicio (apoderado): {traceback.format_exc()}")
                
        elif user_type in ['administrador', 'director']:
            try:
                # Estadísticas generales del sistema
                from .models import Estudiante, Profesor, Curso, Asignatura, EventoCalendario, Anotacion, AsistenciaAlumno, Calificacion
                anio_actual = timezone.now().year
                
                # Contadores principales
                total_estudiantes_sistema = Estudiante.objects.count()
                total_profesores_sistema = Profesor.objects.count()
                total_cursos_activos = Curso.objects.filter(anio=anio_actual).count()
                total_asignaturas_sistema = Asignatura.objects.count()
                
                # Estadísticas de cursos por nivel
                cursos_por_nivel = {}
                cursos_activos = Curso.objects.filter(anio=anio_actual)
                cursos_activos_director = cursos_activos.annotate(
                    total_estudiantes=Count('estudiantes', distinct=True),
                    total_asignaturas=Count('asignaturas', distinct=True)
                ).select_related('profesor_jefe')
                for curso in cursos_activos:
                    nivel = curso.get_nivel_display()
                    if nivel not in cursos_por_nivel:
                        cursos_por_nivel[nivel] = {'cursos': 0, 'estudiantes': 0}
                    cursos_por_nivel[nivel]['cursos'] += 1
                    cursos_por_nivel[nivel]['estudiantes'] += curso.estudiantes.count()
                
                # Eventos próximos
                from datetime import datetime, timedelta
                hoy = timezone.now().date()
                proximos_eventos = EventoCalendario.objects.filter(
                    fecha__gte=hoy,
                    fecha__lte=hoy + timedelta(days=7)
                ).order_by('fecha')[:5]
                
                # Anotaciones recientes del sistema
                anotaciones_recientes_sistema = Anotacion.objects.all().order_by('-fecha_creacion')[:10]
                
                # Estadísticas de anotaciones
                stats_anotaciones_sistema = {
                    'total': Anotacion.objects.count(),
                    'positivas': Anotacion.objects.filter(tipo='positiva').count(),
                    'negativas': Anotacion.objects.filter(tipo='negativa').count(),
                    'neutras': Anotacion.objects.filter(tipo='neutra').count(),
                }
                
                # Estadísticas de asistencia general
                asistencias_hoy = AsistenciaAlumno.objects.filter(fecha=hoy)
                total_asistencias_hoy = asistencias_hoy.count()
                presentes_hoy = asistencias_hoy.filter(presente=True).count()
                porcentaje_asistencia_hoy = (presentes_hoy / total_asistencias_hoy * 100) if total_asistencias_hoy > 0 else 0
                ausentes_hoy = max(total_asistencias_hoy - presentes_hoy, 0)
                
                # Cursos recientes (últimos creados)
                cursos_recientes = Curso.objects.filter(anio=anio_actual).order_by('-id')[:5]
                
                # Profesores recientes (últimos agregados)
                profesores_recientes = Profesor.objects.order_by('-id')[:5]
                
                # Estudiantes recientes (últimos agregados)
                estudiantes_recientes = Estudiante.objects.order_by('-id')[:5]

                niveles_dict = dict(Curso.NIVELES)

                # Analítica de calificaciones globales
                calificaciones_query = Calificacion.objects.filter(
                    inscripcion__grupo__asignatura__cursos__anio=anio_actual
                )

                resumen_promedios = calificaciones_query.aggregate(
                    promedio_global=Avg('puntaje'),
                    total_evaluaciones=Count('id'),
                    aprobaciones=Count('id', filter=Q(puntaje__gte=4))
                )
                promedio_global = float(resumen_promedios.get('promedio_global') or 0)
                total_evaluaciones = resumen_promedios.get('total_evaluaciones') or 0
                aprobaciones = resumen_promedios.get('aprobaciones') or 0
                tasa_aprobacion = round((aprobaciones / total_evaluaciones) * 100, 1) if total_evaluaciones else 0

                calificaciones_por_curso_raw = calificaciones_query.values(
                    'inscripcion__grupo__asignatura__cursos__id',
                    'inscripcion__grupo__asignatura__cursos__nivel',
                    'inscripcion__grupo__asignatura__cursos__paralelo'
                ).annotate(
                    promedio=Avg('puntaje'),
                    evaluaciones=Count('id', distinct=True),
                    estudiantes=Count('inscripcion__estudiante', distinct=True),
                    asignaturas=Count('inscripcion__grupo__asignatura', distinct=True)
                )

                promedios_por_curso = []
                for fila in calificaciones_por_curso_raw:
                    curso_id = fila.get('inscripcion__grupo__asignatura__cursos__id')
                    if not curso_id:
                        continue
                    nivel_codigo = fila.get('inscripcion__grupo__asignatura__cursos__nivel')
                    paralelo = fila.get('inscripcion__grupo__asignatura__cursos__paralelo') or ''
                    nombre_nivel = niveles_dict.get(nivel_codigo, nivel_codigo)
                    promedio_curso = float(fila.get('promedio') or 0)
                    promedios_por_curso.append({
                        'curso_id': curso_id,
                        'curso': f"{nombre_nivel}{paralelo}",
                        'promedio': round(promedio_curso, 2),
                        'evaluaciones': fila.get('evaluaciones') or 0,
                        'estudiantes': fila.get('estudiantes') or 0,
                        'asignaturas': fila.get('asignaturas') or 0,
                    })

                promedios_por_curso.sort(key=lambda item: item.get('promedio', 0), reverse=True)

                calificaciones_mensual_raw = calificaciones_query.annotate(
                    mes=TruncMonth('fecha_evaluacion')
                ).values('mes').annotate(
                    promedio=Avg('puntaje'),
                    evaluaciones=Count('id')
                ).order_by('mes')

                meses_nombres = {
                    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
                    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
                    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
                }

                tendencia_notas = []
                for fila in calificaciones_mensual_raw:
                    mes = fila.get('mes')
                    if mes:
                        promedio_mes = round(float(fila.get('promedio') or 0), 2)
                        porcentaje_barra = 0
                        if promedio_mes > 0:
                            porcentaje_barra = max(0, min(100, round((promedio_mes / 7) * 100)))
                        tendencia_notas.append({
                            'label': meses_nombres.get(mes.month, mes.strftime('%b')),
                            'porcentaje': promedio_mes,
                            'barra': porcentaje_barra,
                            'total': fila.get('evaluaciones') or 0,
                        })

                variacion_promedio = None
                if len(tendencia_notas) >= 2:
                    variacion_promedio = round(
                        tendencia_notas[-1]['porcentaje'] - tendencia_notas[-2]['porcentaje'], 2
                    )

                asistencia_query = AsistenciaAlumno.objects.filter(curso__anio=anio_actual)
                resumen_asistencia = asistencia_query.aggregate(
                    total=Count('id'),
                    presentes=Count('id', filter=Q(presente=True))
                )
                total_asistencias_registradas = resumen_asistencia.get('total') or 0
                presentes_registrados = resumen_asistencia.get('presentes') or 0
                tasa_asistencia_global = round(
                    (presentes_registrados / total_asistencias_registradas) * 100, 1
                ) if total_asistencias_registradas else 0

                asistencia_por_curso_raw = asistencia_query.values(
                    'curso__id', 'curso__nivel', 'curso__paralelo'
                ).annotate(
                    total=Count('id'),
                    presentes=Count('id', filter=Q(presente=True)),
                    ausentes=Count('id', filter=Q(presente=False)),
                    estudiantes=Count('estudiante', distinct=True)
                )

                asistencia_por_curso = []
                asistencia_por_curso_map = {}
                for fila in asistencia_por_curso_raw:
                    curso_id = fila.get('curso__id')
                    if not curso_id:
                        continue
                    total_registros = fila.get('total') or 0
                    presentes = fila.get('presentes') or 0
                    ausentes = fila.get('ausentes') or 0
                    porcentaje = round((presentes / total_registros) * 100, 1) if total_registros else 0
                    nombre_nivel = niveles_dict.get(fila.get('curso__nivel'), fila.get('curso__nivel'))
                    paralelo = fila.get('curso__paralelo') or ''
                    info = {
                        'curso_id': curso_id,
                        'curso': f"{nombre_nivel}{paralelo}",
                        'porcentaje': porcentaje,
                        'presentes': presentes,
                        'ausentes': ausentes,
                        'total': total_registros,
                        'estudiantes': fila.get('estudiantes') or 0,
                    }
                    asistencia_por_curso.append(info)
                    asistencia_por_curso_map[curso_id] = info

                asistencia_por_curso.sort(key=lambda item: item.get('porcentaje', 0), reverse=True)

                asistencia_mensual_raw = asistencia_query.annotate(
                    mes=TruncMonth('fecha')
                ).values('mes').annotate(
                    total=Count('id'),
                    presentes=Count('id', filter=Q(presente=True))
                ).order_by('mes')

                tendencia_asistencia = []
                for fila in asistencia_mensual_raw:
                    mes = fila.get('mes')
                    if mes:
                        total_mes = fila.get('total') or 0
                        presentes_mes = fila.get('presentes') or 0
                        porcentaje_mes = round((presentes_mes / total_mes) * 100, 1) if total_mes else 0
                        tendencia_asistencia.append({
                            'label': meses_nombres.get(mes.month, mes.strftime('%b')),
                            'porcentaje': porcentaje_mes,
                            'total': total_mes,
                        })

                variacion_asistencia = None
                if len(tendencia_asistencia) >= 2:
                    variacion_asistencia = round(
                        tendencia_asistencia[-1]['porcentaje'] - tendencia_asistencia[-2]['porcentaje'], 1
                    )

                promedios_por_curso_map = {item['curso_id']: item for item in promedios_por_curso}
                cursos_alerta_ids = set(promedios_por_curso_map.keys()) | set(asistencia_por_curso_map.keys())

                alertas_academicas = []
                for curso_id in cursos_alerta_ids:
                    datos_notas = promedios_por_curso_map.get(curso_id)
                    datos_asistencia = asistencia_por_curso_map.get(curso_id)
                    curso_nombre = (datos_notas or datos_asistencia or {}).get('curso', 'Sin curso')
                    promedio_curso = datos_notas.get('promedio') if datos_notas else None
                    asistencia_curso = datos_asistencia.get('porcentaje') if datos_asistencia else None
                    motivos = []
                    if promedio_curso is not None and promedio_curso < 4.0:
                        motivos.append('Promedio bajo 4.0')
                    if asistencia_curso is not None and asistencia_curso < 85.0:
                        motivos.append('Asistencia bajo 85%')
                    if motivos:
                        alertas_academicas.append({
                            'curso': curso_nombre,
                            'promedio': promedio_curso if promedio_curso is not None else '--',
                            'asistencia': asistencia_curso if asistencia_curso is not None else '--',
                            'estudiantes': (datos_notas or datos_asistencia or {}).get('estudiantes', 0),
                            'evaluaciones': datos_notas.get('evaluaciones') if datos_notas else 0,
                            'motivos': motivos,
                        })

                alertas_academicas.sort(
                    key=lambda item: (
                        1 if isinstance(item.get('promedio'), str) else item.get('promedio', 10),
                        item.get('asistencia') if isinstance(item.get('asistencia'), (int, float)) else 100
                    )
                )

                cursos_en_riesgo = len(alertas_academicas)

                director_academic_kpis = [
                    {
                        'title': 'Promedio global',
                        'value': f"{promedio_global:.2f}",
                        'description': 'Media de todas las evaluaciones registradas este año.',
                        'icon': 'fas fa-chart-line',
                        'delta': variacion_promedio,
                        'delta_positive': (variacion_promedio or 0) >= 0,
                        'delta_suffix': 'pts' if variacion_promedio is not None else '',
                        'delta_precision': 2,
                    },
                    {
                        'title': 'Tasa de aprobación',
                        'value': f"{tasa_aprobacion:.1f}%",
                        'description': 'Porcentaje de calificaciones iguales o superiores a 4.0.',
                        'icon': 'fas fa-graduation-cap',
                        'delta': None,
                        'delta_positive': True,
                        'delta_suffix': '',
                        'delta_precision': None,
                    },
                    {
                        'title': 'Asistencia anual',
                        'value': f"{tasa_asistencia_global:.1f}%",
                        'description': 'Promedio de asistencia del estudiantado en el año.',
                        'icon': 'fas fa-user-check',
                        'delta': variacion_asistencia,
                        'delta_positive': (variacion_asistencia or 0) >= 0,
                        'delta_suffix': 'pp' if variacion_asistencia is not None else '',
                        'delta_precision': 1,
                    },
                    {
                        'title': 'Cursos en riesgo',
                        'value': str(cursos_en_riesgo),
                        'description': 'Cursos con alertas por asistencia o rendimiento.',
                        'icon': 'fas fa-exclamation-triangle',
                        'delta': None,
                        'delta_positive': False,
                        'delta_suffix': '',
                        'delta_precision': None,
                    },
                ]

                mensaje_proyeccion = (
                    f"Con un promedio general de {promedio_global:.2f} y una asistencia global de "
                    f"{tasa_asistencia_global:.1f}%, la proyección institucional sugiere "
                    f"{'estabilidad' if promedio_global >= 5 and tasa_asistencia_global >= 90 else 'riesgos moderados'} para el cierre del año académico."
                )

                recomendaciones_proyeccion = []
                if variacion_promedio is not None and variacion_promedio < 0:
                    recomendaciones_proyeccion.append('Refuerza tutorías o reforzamientos en los cursos con descenso de promedio mensual.')
                if variacion_asistencia is not None and variacion_asistencia < 0:
                    recomendaciones_proyeccion.append('Activa campañas de asistencia y seguimiento personalizado en los cursos con mayor ausentismo.')
                if cursos_en_riesgo:
                    curso_prioritario = alertas_academicas[0]
                    recomendaciones_proyeccion.append(
                        f"Prioriza acciones correctivas en {curso_prioritario['curso']}, el curso con mayor alerta activa."
                    )
                if tasa_aprobacion < 70:
                    recomendaciones_proyeccion.append('Evalúa planes remediales para elevar la tasa de aprobación por sobre el 70%.')
                if not recomendaciones_proyeccion:
                    recomendaciones_proyeccion.append('Mantén los planes de seguimiento actuales y consolida buenas prácticas docentes.')

                chart_promedios_labels = [item['curso'] for item in promedios_por_curso[:6]]
                chart_promedios_data = [item['promedio'] for item in promedios_por_curso[:6]]

                chart_matricula_labels = []
                chart_matricula_data = []
                for nivel, datos in cursos_por_nivel.items():
                    chart_matricula_labels.append(nivel)
                    chart_matricula_data.append(datos.get('estudiantes', 0))

                context.update({
                    'total_estudiantes_sistema': total_estudiantes_sistema,
                    'total_profesores_sistema': total_profesores_sistema,
                    'total_cursos_activos': total_cursos_activos,
                    'total_asignaturas_sistema': total_asignaturas_sistema,
                    'cursos_por_nivel': cursos_por_nivel,
                    'proximos_eventos': proximos_eventos,
                    'anotaciones_recientes_sistema': anotaciones_recientes_sistema,
                    'stats_anotaciones_sistema': stats_anotaciones_sistema,
                    'total_asistencias_hoy': total_asistencias_hoy,
                    'presentes_hoy': presentes_hoy,
                    'ausentes_hoy': ausentes_hoy,
                    'porcentaje_asistencia_hoy': round(porcentaje_asistencia_hoy, 1),
                    'cursos_recientes': cursos_recientes,
                    'profesores_recientes': profesores_recientes,
                    'estudiantes_recientes': estudiantes_recientes,
                    'anio_actual': anio_actual,
                    'cursos_activos_director': cursos_activos_director,
                    'director_academic_kpis': director_academic_kpis,
                    'director_tabla_promedios': promedios_por_curso,
                    'director_tabla_asistencias': asistencia_por_curso,
                    'director_tendencia_notas': tendencia_notas,
                    'director_tendencia_asistencia': tendencia_asistencia,
                    'director_alertas_academicas': alertas_academicas,
                    'director_mensaje_proyeccion': mensaje_proyeccion,
                    'director_recomendaciones_proyeccion': recomendaciones_proyeccion,
                    'director_chart_promedios_labels': chart_promedios_labels,
                    'director_chart_promedios_data': chart_promedios_data,
                    'director_chart_matricula_labels': chart_matricula_labels,
                    'director_chart_matricula_data': chart_matricula_data,
                })

                if user_type in ['director', 'administrador']:
                    template_name = 'director_dashboard_full.html'
                
            except Exception as e:
                context['error_admin'] = f"Error al cargar datos del sistema: {str(e)}"
                import traceback
                print(f"Error en vista inicio (admin/director): {traceback.format_exc()}")
    
    return render(request, template_name, context)

def login_view(request):
    """Vista de login personalizada"""
    mensaje = ""
    
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        
        print(f"DEBUG LOGIN - Usuario: '{username}', Password: {'*' * len(password)}")
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            print(f"DEBUG LOGIN - Usuario autenticado: {user}")
            
            if user is not None:
                print(f"DEBUG LOGIN - Usuario activo: {user.is_active}")
                print(f"DEBUG LOGIN - Tiene perfil: {hasattr(user, 'perfil')}")
                
                if hasattr(user, 'perfil'):
                    print(f"DEBUG LOGIN - Tipo usuario: {user.perfil.tipo_usuario}")
                
                login(request, user)
                
                # Redirección personalizada según tipo de usuario
                if hasattr(user, 'perfil'):
                    user_type = user.perfil.tipo_usuario
                    print(f"DEBUG LOGIN - Redirigiendo a inicio para tipo: {user_type}")
                    if user_type == 'alumno':
                        return redirect('inicio')  # Redirigir al panel de estudiante
                    elif user_type == 'profesor':
                        return redirect('inicio')  # Redirigir al panel de profesor
                    elif user_type == 'apoderado':
                        return redirect('inicio')  # Redirigir al panel de apoderado
                    elif user_type in ['administrador', 'director']:
                        return redirect('inicio')  # Redirigir al panel personalizado
                    else:
                        return redirect('index_master')  # Otros usuarios
                else:
                    print("DEBUG LOGIN - Sin perfil, redirigiendo a inicio por defecto")
                    return redirect('inicio')  # Por defecto
            else:
                print("DEBUG LOGIN - Autenticación falló")
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
    from django.http import JsonResponse
    
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
    
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not puede_crear_eventos:
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'No tienes permisos para crear eventos.'}, status=403)
        
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
                if is_ajax: return JsonResponse({'success': False, 'error': 'El título es obligatorio'})
                messages.error(request, 'El título es obligatorio')
                return render(request, 'agregar_evento.html', {'cursos': cursos})
            if not fecha:
                if is_ajax: return JsonResponse({'success': False, 'error': 'La fecha es obligatoria'})
                messages.error(request, 'La fecha es obligatoria')
                return render(request, 'agregar_evento.html', {'cursos': cursos})
            
            # Validar horas
            if hora_inicio and hora_fin:
                from datetime import datetime
                try:
                    inicio = datetime.strptime(hora_inicio, '%H:%M').time()
                    fin = datetime.strptime(hora_fin, '%H:%M').time()
                    if inicio >= fin:
                        if is_ajax: return JsonResponse({'success': False, 'error': 'La hora de inicio debe ser menor que la hora de fin'})
                        messages.error(request, 'La hora de inicio debe ser menor que la hora de fin')
                        return render(request, 'agregar_evento.html', {'cursos': cursos})
                except ValueError:
                    if is_ajax: return JsonResponse({'success': False, 'error': 'Formato de hora inválido'})
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
                solo_apoderados=dirigido_a == 'solo_apoderados',
                creado_por=request.user
            )
            
            # Asignar cursos específicos si es necesario
            if dirigido_a == 'cursos_especificos':
                cursos_ids = request.POST.getlist('cursos_especificos')
                if not cursos_ids:
                    if is_ajax: return JsonResponse({'success': False, 'error': 'Debes seleccionar al menos un curso específico'})
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
                        if is_ajax: return JsonResponse({'success': False, 'error': 'No tienes permisos para crear eventos en algunos de los cursos seleccionados'})
                        messages.error(request, 'No tienes permisos para crear eventos en algunos de los cursos seleccionados')
                        evento.delete()
                        return render(request, 'agregar_evento.html', {'cursos': cursos})
                
                evento.cursos.set(cursos_ids)
            
            if is_ajax:
                return JsonResponse({'success': True, 'message': f'Evento "{titulo}" creado exitosamente'})
            
            messages.success(request, f'Evento "{titulo}" creado exitosamente')
            return redirect('calendario')
            
        except Exception as e:
            if is_ajax: return JsonResponse({'success': False, 'error': f'Error al crear el evento: {str(e)}'})
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
    """Vista para mostrar horarios detallados del curso del estudiante o horarios del profesor"""
    from django.utils import timezone
    from collections import defaultdict
    from datetime import timedelta
    
    context = {
        'user': request.user,
    }
    
    # Determinar tipo de usuario
    user_type = 'otro'
    if hasattr(request.user, 'perfil'):
        user_type = request.user.perfil.tipo_usuario
    elif hasattr(request.user, 'profesor'):
        user_type = 'profesor'
    elif hasattr(request.user, 'estudiante'):
        user_type = 'alumno'
    
    # VISTA PARA ESTUDIANTES
    if user_type == 'alumno':
        context['es_alumno'] = True
        try:
            estudiante = request.user.estudiante
            anio_actual = timezone.now().year
            
            # Obtener curso actual del estudiante
            curso_actual = estudiante.cursos.filter(anio=anio_actual).order_by('-nivel').first()
            
            # Si no hay curso del año actual, tomar el más reciente
            if not curso_actual:
                curso_actual = estudiante.cursos.order_by('-anio', '-nivel').first()
            
            if curso_actual:
                # Obtener horarios del curso con información de asignaturas y profesores
                horarios_curso_queryset = HorarioCurso.objects.filter(
                    curso=curso_actual
                ).select_related('asignatura', 'asignatura__profesor_responsable').order_by('dia', 'hora_inicio')
                horarios_curso = list(horarios_curso_queryset)
                
                # Organizar horarios y crear matriz
                horario_semanal_matriz, dias_semana, total_clases_semana, clases_por_asignatura = organizar_horarios_matriz(horarios_curso)
                clases_por_asignatura_dict = dict(clases_por_asignatura)
                
                # Estadísticas del curso y métricas del horario
                asignaturas_curso = curso_actual.asignaturas.all()
                clases_por_dia = defaultdict(list)
                total_minutos_semana = 0
                for horario in horarios_curso:
                    clases_por_dia[horario.dia].append(horario)
                    if horario.hora_inicio and horario.hora_fin:
                        inicio_dt = datetime.combine(date.today(), horario.hora_inicio)
                        fin_dt = datetime.combine(date.today(), horario.hora_fin)
                        total_minutos_semana += int((fin_dt - inicio_dt).total_seconds() // 60)
                horas_totales_semana = round(total_minutos_semana / 60, 1) if total_minutos_semana else 0
                bloques_sin_asignatura = clases_por_asignatura_dict.pop(None, 0) if None in clases_por_asignatura_dict else 0
                dias_con_clases = len({horario.dia for horario in horarios_curso})
                
                # Información formateada de asignaturas
                asignaturas_resumen = []
                for asignatura in asignaturas_curso:
                    bloques = clases_por_asignatura_dict.get(asignatura, 0)
                    porcentaje = (bloques / total_clases_semana * 100) if total_clases_semana else 0
                    asignaturas_resumen.append({
                        'obj': asignatura,
                        'nombre': asignatura.nombre,
                        'codigo': getattr(asignatura, 'codigo_asignatura', ''),
                        'profesor': asignatura.profesor_responsable,
                        'bloques': bloques,
                        'porcentaje': round(porcentaje, 1),
                    })
                asignaturas_resumen.sort(key=lambda item: item['nombre'])
                if bloques_sin_asignatura:
                    asignaturas_resumen.append({
                        'obj': None,
                        'nombre': 'Bloques sin asignatura',
                        'codigo': '',
                        'profesor': None,
                        'bloques': bloques_sin_asignatura,
                        'porcentaje': round((bloques_sin_asignatura / total_clases_semana * 100), 1) if total_clases_semana else 0,
                    })
                
                # Preparar información de días y próximos bloques
                dias_nombres = {
                    'LU': 'Lunes',
                    'MA': 'Martes',
                    'MI': 'Miércoles',
                    'JU': 'Jueves',
                    'VI': 'Viernes',
                    'SA': 'Sábado',
                    'DO': 'Domingo',
                }
                dias_abreviados = {
                    'LU': 'Lun', 'MA': 'Mar', 'MI': 'Mié', 'JU': 'Jue', 'VI': 'Vie', 'SA': 'Sáb', 'DO': 'Dom'
                }
                dias_weekday_a_codigo = {
                    0: 'LU',
                    1: 'MA',
                    2: 'MI',
                    3: 'JU',
                    4: 'VI',
                    5: 'SA',
                    6: 'DO',
                }
                hoy = timezone.localdate()
                ahora = timezone.localtime().time()
                dia_actual_codigo = dias_weekday_a_codigo[hoy.weekday()]
                dias_semana_display = []
                for codigo in dias_semana:
                    dias_semana_display.append({
                        'codigo': codigo,
                        'nombre': dias_nombres.get(codigo, codigo),
                        'abreviado': dias_abreviados.get(codigo, codigo),
                        'total': len(clases_por_dia.get(codigo, [])),
                        'es_hoy': codigo == dia_actual_codigo,
                    })
                
                proximas_clases = []
                if horarios_curso:
                    for offset in range(7):
                        fecha = hoy + timedelta(days=offset)
                        codigo_dia = dias_weekday_a_codigo[fecha.weekday()]
                        bloques_dia = [h for h in horarios_curso if h.dia == codigo_dia]
                        for horario in bloques_dia:
                            if offset == 0 and horario.hora_fin and horario.hora_fin <= ahora:
                                continue
                            proximas_clases.append({
                                'fecha': fecha,
                                'dia_codigo': codigo_dia,
                                'dia_nombre': dias_nombres.get(codigo_dia, codigo_dia),
                                'hora_inicio': horario.hora_inicio,
                                'hora_fin': horario.hora_fin,
                                'asignatura': horario.asignatura,
                                'profesor': horario.asignatura.profesor_responsable if horario.asignatura else None,
                                'es_hoy': offset == 0,
                            })
                            if len(proximas_clases) >= 6:
                                break
                        if len(proximas_clases) >= 6:
                            break
                
                primer_bloque = horario_semanal_matriz[0]['hora_inicio'] if horario_semanal_matriz else None
                ultimo_bloque = horario_semanal_matriz[-1]['hora_fin'] if horario_semanal_matriz else None
                
                context.update({
                    'estudiante': estudiante,
                    'curso_actual': curso_actual,
                    'es_alumno': True,
                    'horarios_curso': horarios_curso,
                    'horario_semanal_matriz': horario_semanal_matriz,
                    'dias_semana': dias_semana,
                    'dias_semana_display': dias_semana_display,
                    'total_clases_semana': total_clases_semana,
                    'horas_totales_semana': horas_totales_semana,
                    'asignaturas_curso': asignaturas_curso,
                    'asignaturas_resumen': asignaturas_resumen,
                    'clases_por_asignatura': clases_por_asignatura_dict,
                    'proximas_clases_estudiante': proximas_clases,
                    'dia_actual_codigo': dia_actual_codigo,
                    'dias_con_clases': dias_con_clases,
                    'primer_bloque': primer_bloque,
                    'ultimo_bloque': ultimo_bloque,
                })
                
            else:
                context['error_curso'] = "No tienes un curso asignado actualmente."
                
        except Exception as e:
            context['error_horarios'] = f"Error al cargar horarios: {str(e)}"
            import traceback
            print(f"Error en mis_horarios (estudiante): {traceback.format_exc()}")
    
    # VISTA PARA PROFESORES
    elif user_type == 'profesor':
        context['es_profesor'] = True
        try:
            profesor = request.user.profesor
            anio_actual = timezone.now().year

            context['anio_actual'] = anio_actual
            context['profesor'] = profesor
            
            # Obtener horarios donde el profesor está asignado directamente O es responsable de la asignatura
            horarios_profesor_qs = HorarioCurso.objects.filter(
                Q(profesor=profesor) | Q(asignatura__profesor_responsable=profesor),
                curso__anio=anio_actual
            ).select_related('curso', 'asignatura').order_by('dia', 'hora_inicio').distinct()
            
            horarios_profesor = list(horarios_profesor_qs)

            # Obtener asignaturas basadas en los horarios encontrados
            asignaturas_ids = set(h.asignatura.id for h in horarios_profesor if h.asignatura)
            # También incluir asignaturas donde es responsable aunque no tenga horario
            asignaturas_responsable_ids = Asignatura.objects.filter(profesor_responsable=profesor).values_list('id', flat=True)
            asignaturas_ids.update(asignaturas_responsable_ids)
            
            asignaturas_profesor = Asignatura.objects.filter(id__in=asignaturas_ids).prefetch_related('cursos').order_by('nombre')
            
            context['asignaturas_profesor'] = asignaturas_profesor
            context.setdefault('total_asignaturas', asignaturas_profesor.count())
            context.setdefault('total_horas_semanales', 0)
            context.setdefault('total_cursos', 0)
            context.setdefault('total_estudiantes', 0)
            context.setdefault('proximas_clases', [])
            context.setdefault('horarios_por_curso', [])
            context.setdefault('asignaturas_resumen', [])
            context.setdefault('dias_semana_display', [])
            
            if horarios_profesor:
                # Organizar horarios y crear matriz
                horario_semanal_matriz, dias_semana, total_clases_semana, clases_por_asignatura = organizar_horarios_matriz(horarios_profesor)
                
                # Obtener cursos donde enseña (basado en los horarios)
                cursos_ids = set(h.curso.id for h in horarios_profesor)
                cursos_profesor = Curso.objects.filter(id__in=cursos_ids).order_by('nivel', 'paralelo')
                
                # Estadísticas del profesor
                total_estudiantes = sum(curso.estudiantes.count() for curso in cursos_profesor)
                total_asignaturas = asignaturas_profesor.count()
                total_horas_semanales = total_clases_semana

                # Preparar datos complementarios para la vista
                from datetime import timedelta

                dias_nombres = {
                    'LU': 'Lunes',
                    'MA': 'Martes',
                    'MI': 'Miércoles',
                    'JU': 'Jueves',
                    'VI': 'Viernes',
                    'SA': 'Sábado',
                    'DO': 'Domingo',
                }
                dias_orden = {codigo: idx for idx, codigo in enumerate(['LU', 'MA', 'MI', 'JU', 'VI', 'SA', 'DO'])}

                curso_horarios_map = {}
                for horario in horarios_profesor:
                    curso_horarios_map.setdefault(horario.curso, []).append(horario)

                horarios_por_curso = []
                for curso in cursos_profesor:
                    bloques = curso_horarios_map.get(curso, [])
                    bloques.sort(key=lambda h: (dias_orden.get(h.dia, 99), h.hora_inicio))
                    horarios_por_curso.append({
                        'curso': curso,
                        'bloques': bloques,
                        'total_bloques': len(bloques),
                        'total_estudiantes': curso.estudiantes.count(),
                        'es_profesor_jefe': curso.profesor_jefe_id == profesor.id,
                    })

                horarios_por_curso.sort(key=lambda item: (item['curso'].orden_nivel, item['curso'].paralelo))

                # Próximas clases basadas en la semana actual
                hoy = timezone.localdate()
                hoy_idx = hoy.weekday()
                sorted_horarios = sorted(
                    horarios_profesor,
                    key=lambda h: ((dias_orden.get(h.dia, 99) - hoy_idx) % 7, h.hora_inicio)
                )

                proximas_clases = []
                for horario in sorted_horarios:
                    dia_idx = dias_orden.get(horario.dia)
                    if dia_idx is None:
                        continue
                    delta = (dia_idx - hoy_idx) % 7
                    fecha_estimada = hoy + timedelta(days=delta)
                    proximas_clases.append({
                        'fecha': fecha_estimada,
                        'dia_nombre': dias_nombres.get(horario.dia, horario.get_dia_display()),
                        'hora_inicio': horario.hora_inicio,
                        'hora_fin': horario.hora_fin,
                        'curso': horario.curso,
                        'asignatura': horario.asignatura,
                        'es_hoy': delta == 0,
                    })
                    if len(proximas_clases) >= 6:
                        break

                clases_por_asignatura_dict = dict(clases_por_asignatura)
                asignaturas_resumen = []
                for asignatura, cantidad in clases_por_asignatura_dict.items():
                    if asignatura:
                        cursos_relacionados = sorted({
                            f"{curso.get_nivel_display()}{curso.paralelo}"
                            for curso in asignatura.cursos.filter(anio=anio_actual)
                        })
                        codigo = getattr(asignatura, 'codigo_asignatura', None)
                        nombre = asignatura.nombre
                    else:
                        cursos_relacionados = []
                        codigo = None
                        nombre = 'Bloque sin asignatura'
                    asignaturas_resumen.append({
                        'obj': asignatura,
                        'nombre': nombre,
                        'codigo': codigo,
                        'cantidad': cantidad,
                        'cursos': cursos_relacionados,
                    })

                asignaturas_resumen.sort(key=lambda item: item['nombre'])

                dias_semana_display = [
                    {'codigo': codigo, 'nombre': dias_nombres.get(codigo, codigo)}
                    for codigo in dias_semana
                ]
                
                context.update({
                    'asignaturas_resumen': asignaturas_resumen,
                    'horarios_profesor': horarios_profesor,
                    'horario_semanal_matriz': horario_semanal_matriz,
                    'horarios_matriz': horario_semanal_matriz,  # Alias para compatibilidad con template
                    'dias_semana': dias_semana,
                    'dias_semana_display': dias_semana_display,
                    'dias_nombres': dias_nombres,
                    'total_clases_semana': total_clases_semana,
                    'clases_por_asignatura': clases_por_asignatura_dict,
                    'cursos_profesor': cursos_profesor,
                    'horarios_por_curso': horarios_por_curso,
                    'proximas_clases': proximas_clases,
                    'total_estudiantes': total_estudiantes,
                    'total_cursos': len(cursos_profesor),
                    'total_asignaturas': total_asignaturas,
                    'total_horas_semanales': total_horas_semanales,
                })
                
            else:
                context['error_profesor'] = "No tienes asignaturas asignadas actualmente."
                
        except Exception as e:
            context['error_horarios'] = f"Error al cargar horarios del profesor: {str(e)}"
            import traceback
            print(f"Error en mis_horarios (profesor): {traceback.format_exc()}")
    
    else:
        # Para otros tipos de usuario, mostrar mensaje informativo
        context['no_es_alumno'] = True
    
    return render(request, 'mis_horarios.html', context)

def organizar_horarios_matriz(horarios_queryset):
    """Función auxiliar para organizar horarios en matriz para la tabla"""
    from collections import defaultdict
    
    DIAS_SEMANA = ['LU', 'MA', 'MI', 'JU', 'VI']
    
    # Organizar horarios por día
    horarios_organizados = defaultdict(list)
    bloques_horarios = set()
    
    for horario in horarios_queryset:
        horarios_organizados[horario.dia].append(horario)
        bloques_horarios.add((horario.hora_inicio, horario.hora_fin))
    
    # Ordenar bloques horarios
    bloques_horarios = sorted(list(bloques_horarios))
    
    # Crear matriz de horarios para la tabla
    horario_semanal_matriz = []
    for hora_inicio, hora_fin in bloques_horarios:
        fila = {
            'hora_inicio': hora_inicio,
            'hora_fin': hora_fin,
            'clases': {}
        }
        
        for dia in DIAS_SEMANA:
            # Buscar clase en este día y hora
            clase = None
            for horario in horarios_organizados[dia]:
                if horario.hora_inicio == hora_inicio and horario.hora_fin == hora_fin:
                    clase = horario
                    break
            fila['clases'][dia] = clase
        
        horario_semanal_matriz.append(fila)
    
    # Estadísticas
    total_clases_semana = sum(len(clases) for clases in horarios_organizados.values())
    
    # Contar clases por asignatura
    clases_por_asignatura = defaultdict(int)
    for horario in horarios_queryset:
        if horario.asignatura:
            clases_por_asignatura[horario.asignatura] += 1
    
    return horario_semanal_matriz, DIAS_SEMANA, total_clases_semana, clases_por_asignatura

@login_required  
def mi_curso(request):
    """Vista para mostrar información del curso del estudiante"""
    from django.utils import timezone
    from django.contrib import messages
    
    context = {
        'user': request.user,
    }
    context.setdefault('es_alumno', False)
    context.setdefault('es_profesor', False)
    
    tipo_usuario = None
    if hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario:
        tipo_usuario = request.user.perfil.tipo_usuario
    elif hasattr(request.user, 'estudiante'):
        tipo_usuario = 'alumno'
    elif hasattr(request.user, 'profesor'):
        tipo_usuario = 'profesor'
    
    # Verificar que el usuario sea estudiante
    if tipo_usuario == 'alumno':
        try:
            estudiante = request.user.estudiante
            anio_actual = timezone.now().year
            
            # Obtener curso actual del estudiante
            curso_actual = estudiante.cursos.filter(anio=anio_actual).order_by('-nivel').first()
            
            # Si no hay curso del año actual, tomar el más reciente
            if not curso_actual:
                curso_actual = estudiante.cursos.order_by('-anio', '-nivel').first()
            
            if curso_actual:
                # Obtener compañeros de curso (excluyendo al propio estudiante)
                companeros = curso_actual.estudiantes.exclude(id=estudiante.id).order_by('primer_nombre', 'apellido_paterno')
                
                # Obtener asignaturas del curso
                asignaturas_curso = curso_actual.asignaturas.all().order_by('nombre')
                
                # Obtener profesor jefe
                profesor_jefe = curso_actual.profesor_jefe
                
                # Métricas académicas del estudiante
                inscripciones = Inscripcion.objects.filter(estudiante=estudiante)
                calificaciones = Calificacion.objects.filter(inscripcion__in=inscripciones)
                if calificaciones.exists():
                    promedio_general = calificaciones.aggregate(Avg('puntaje'))['puntaje__avg']
                    total_notas = calificaciones.count()
                else:
                    promedio_general = None
                    total_notas = 0

                asistencias = AsistenciaAlumno.objects.filter(estudiante=estudiante)
                total_asistencias = asistencias.count()
                presentes = asistencias.filter(presente=True).count()
                porcentaje_asistencia = (presentes / total_asistencias * 100) if total_asistencias else 0

                # Resumen de asignaturas y docentes activos
                asignaturas_resumen = []
                profesores_activos_set = set()
                asignaturas_sin_profesor = 0
                for asignatura in asignaturas_curso:
                    profesor_responsable = asignatura.profesor_responsable
                    if profesor_responsable:
                        profesores_activos_set.add(profesor_responsable)
                    else:
                        asignaturas_sin_profesor += 1
                    asignaturas_resumen.append({
                        'obj': asignatura,
                        'codigo': getattr(asignatura, 'codigo_asignatura', ''),
                        'profesor': profesor_responsable,
                    })

                profesores_activos = sorted(
                    profesores_activos_set,
                    key=lambda prof: (
                        getattr(prof, 'apellido_paterno', '') or '',
                        getattr(prof, 'apellido_materno', '') or '',
                        getattr(prof, 'primer_nombre', '') or ''
                    )
                )

                total_companeros = companeros.count()
                companeros_destacados = list(companeros[:6])
                historial_cursos = estudiante.cursos.exclude(id=curso_actual.id).order_by('-anio', '-nivel')[:4]

                # Estadísticas del curso
                total_estudiantes = curso_actual.estudiantes.count()
                total_asignaturas = asignaturas_curso.count()
                
                context.update({
                    'estudiante': estudiante,
                    'curso_actual': curso_actual,
                    'companeros': companeros,
                    'asignaturas_curso': asignaturas_curso,
                    'profesor_jefe': profesor_jefe,
                    'total_estudiantes': total_estudiantes,
                    'total_asignaturas': total_asignaturas,
                    'promedio_general': round(promedio_general, 1) if promedio_general is not None else None,
                    'total_notas': total_notas,
                    'total_asistencias': total_asistencias,
                    'presentes': presentes,
                    'porcentaje_asistencia': round(porcentaje_asistencia, 1),
                    'asignaturas_resumen': asignaturas_resumen,
                    'asignaturas_sin_profesor': asignaturas_sin_profesor,
                    'companeros_destacados': companeros_destacados,
                    'total_companeros': total_companeros,
                    'historial_cursos': historial_cursos,
                    'profesores_activos': profesores_activos,
                    'es_alumno': True,
                })
                
            else:
                context['error_curso'] = "No tienes un curso asignado actualmente."
                
        except Exception as e:
            context['error_curso'] = f"Error al cargar información del curso: {str(e)}"
            import traceback
            print(f"Error en mi_curso (alumno): {traceback.format_exc()}")
    
    elif tipo_usuario == 'profesor':
        try:
            from .models import HorarioCurso  # Importar modelo necesario
            profesor = request.user.profesor
            anio_actual = timezone.now().year
            cursos_jefe_qs = profesor.cursos_jefatura.filter(anio=anio_actual).order_by('nivel', 'paralelo')
            cursos_jefe = list(cursos_jefe_qs)

            cursos_asignados_qs = profesor.get_cursos_asignados().prefetch_related('estudiantes', 'asignaturas')
            cursos_profesor = []
            total_estudiantes = 0
            total_mis_asignaturas = 0

            for curso in cursos_asignados_qs:
                estudiantes_total = curso.estudiantes.count()
                
                # Obtener asignaturas donde el profesor enseña en este curso
                # 1. Por ser responsable de la asignatura
                asignaturas_ids = set(curso.asignaturas.filter(profesor_responsable=profesor).values_list('id', flat=True))
                # 2. Por tener horarios asignados en este curso
                horarios_asignaturas_ids = HorarioCurso.objects.filter(curso=curso, profesor=profesor).values_list('asignatura_id', flat=True)
                asignaturas_ids.update(horarios_asignaturas_ids)
                
                mis_asignaturas_qs = Asignatura.objects.filter(id__in=asignaturas_ids).order_by('nombre')
                
                otros_profesores_raw = curso.asignaturas.exclude(id__in=asignaturas_ids) \
                    .exclude(profesor_responsable__isnull=True) \
                    .values_list('profesor_responsable__primer_nombre', 'profesor_responsable__apellido_paterno') \
                    .distinct()
                otros_profesores = sorted({
                    f"{nombre or ''} {apellido or ''}".strip()
                    for nombre, apellido in otros_profesores_raw
                    if (nombre or apellido)
                })

                curso_info = {
                    'obj': curso,
                    'nombre': f"{curso.get_nivel_display()}{curso.paralelo}",
                    'anio': curso.anio,
                    'soy_profesor_jefe': curso.profesor_jefe_id == profesor.id,
                    'profesor_jefe': curso.profesor_jefe,
                    'total_estudiantes': estudiantes_total,
                    'total_asignaturas': curso.asignaturas.count(),
                    'mis_asignaturas': list(mis_asignaturas_qs),
                    'mis_asignaturas_count': mis_asignaturas_qs.count(),
                    'otros_profesores': otros_profesores,
                }

                curso.estudiantes_total = estudiantes_total
                curso.mis_asignaturas_count = curso_info['mis_asignaturas_count']
                curso.total_asignaturas = curso_info['total_asignaturas']

                cursos_profesor.append(curso_info)
                total_estudiantes += estudiantes_total
                total_mis_asignaturas += curso_info['mis_asignaturas_count']

            curso_destacado = None
            if cursos_profesor:
                if cursos_jefe:
                    curso_jefe_id = cursos_jefe[0].id
                    for info in cursos_profesor:
                        if info['obj'].id == curso_jefe_id:
                            curso_destacado = info
                            break
                if not curso_destacado:
                    curso_destacado = cursos_profesor[0]

            cursos_objs = [info['obj'] for info in cursos_profesor]

            proximas_clases = []
            eventos_proximos = []
            if cursos_objs:
                from datetime import timedelta
                from django.db.models import Q
                from .models import HorarioCurso, EventoCalendario

                hoy = timezone.localdate()
                dias_weekday_a_codigo = {0: 'LU', 1: 'MA', 2: 'MI', 3: 'JU', 4: 'VI', 5: 'SA', 6: 'DO'}
                dias_nombre = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

                for offset in range(7):
                    fecha = hoy + timedelta(days=offset)
                    codigo_dia = dias_weekday_a_codigo[fecha.weekday()]
                    horarios = HorarioCurso.objects.filter(
                        curso__in=cursos_objs,
                        dia=codigo_dia
                    ).filter(
                        Q(profesor=profesor) | Q(asignatura__profesor_responsable=profesor)
                    ).select_related('curso', 'asignatura').order_by('hora_inicio')
                    if horarios.exists():
                        proximas_clases.append({
                            'fecha': fecha,
                            'dia_nombre': dias_nombre[fecha.weekday()],
                            'horarios': horarios,
                        })
                    if len(proximas_clases) >= 3:
                        break

                eventos_proximos = EventoCalendario.objects.filter(
                    Q(para_todos_los_cursos=True) | Q(cursos__in=cursos_objs),
                    fecha__gte=hoy
                ).distinct().order_by('fecha')[:5]

            context.update({
                'es_profesor': True,
                'profesor': profesor,
                'anio_actual': anio_actual,
                'cursos_jefe': cursos_jefe,
                'cursos_profesor': cursos_profesor,
                'curso_destacado': curso_destacado,
                'resumen_profesor': {
                    'total_cursos': len(cursos_profesor),
                    'total_estudiantes': total_estudiantes,
                    'total_asignaturas_propias': total_mis_asignaturas,
                    'total_cursos_jefe': len(cursos_jefe),
                },
                'proximas_clases': proximas_clases,
                'eventos_proximos': eventos_proximos,
                'asignaturas_profesor': profesor.asignaturas.all().order_by('nombre'),
            })

            if not cursos_profesor:
                context['error_curso'] = "No tienes cursos asignados actualmente."

        except Exception as e:
            context['error_curso'] = f"Error al cargar información del profesor: {str(e)}"
            import traceback
            print(f"Error en mi_curso (profesor): {traceback.format_exc()}")

    else:
        # Para otros tipos de usuario (profesores, admin)
        messages.info(request, 'Esta vista está diseñada específicamente para estudiantes.')
        context['error_curso'] = "Esta sección es exclusiva para estudiantes."
    
    return render(request, 'mi_curso.html', context)

@login_required
def listar_cursos(request):
    """Vista para listar cursos y gestionar estudiantes pendientes"""
    from .forms import AsignarEstudianteForm
    from django.contrib import messages
    from django.utils import timezone
    
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
    
    # Manejar la asignación de estudiantes pendientes (solo para administradores)
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
    
    # Obtener datos de cursos según tipo de usuario
    if user_type == 'profesor':
        # Para profesores: solo cursos donde tiene asignaturas asignadas
        try:
            profesor = request.user.profesor
            
            # Obtener asignaturas del profesor
            asignaturas_profesor = Asignatura.objects.filter(
                profesor_responsable=profesor
            )
            
            # Obtener cursos donde tiene asignaturas asignadas
            cursos_queryset = Curso.objects.filter(
                anio=timezone.now().year,
                asignaturas__in=asignaturas_profesor
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
            
            cursos = sorted(cursos_con_asignaturas_profesor, key=lambda c: (c.orden_nivel, c.paralelo))
            
        except Exception as e:
            cursos_queryset = Curso.objects.none()
            cursos = []
    else:
        # Para administradores y otros: todos los cursos
        cursos_queryset = Curso.objects.filter(anio=timezone.now().year)
        # Ordenar correctamente: básica antes que media
        cursos = sorted(cursos_queryset, key=lambda c: (c.orden_nivel, c.paralelo))
    
    total_cursos = len(cursos)
    
    # Calcular estadísticas según tipo de usuario
    if user_type == 'profesor':
        # Estadísticas específicas para el profesor
        total_estudiantes = sum(curso.estudiantes.count() for curso in cursos)
        total_estudiantes_asignados = total_estudiantes  # Para profesores son los mismos
        total_asignaturas_profesor = sum(len(getattr(curso, 'asignaturas_profesor', [])) for curso in cursos)
        
        # Variables específicas para profesores
        estudiantes_pendientes = []  # Los profesores no ven estudiantes pendientes
        total_estudiantes_pendientes = 0
        total_asignaturas_asignadas = total_asignaturas_profesor
        total_asignaturas_disponibles = total_asignaturas_profesor
        profesores_jefe_asignados = len([curso for curso in cursos if curso.profesor_jefe])
        
    else:
        # Estadísticas para administradores
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
        
        total_estudiantes_pendientes = estudiantes_pendientes.count()
    
    # Crear formulario para asignar estudiantes pendientes (solo para administradores)
    form_asignar = AsignarEstudianteForm() if user_type != 'profesor' else None
    
    # Verificar permisos del usuario
    puede_editar = (hasattr(request.user, 'perfil') and 
                   request.user.perfil.tipo_usuario in ['director', 'administrador', 'profesor_jefe'])
    
    context = {
        'cursos': cursos,
        'tipo_usuario': user_type,
        'total_cursos': total_cursos,
        'total_estudiantes': total_estudiantes,
        'total_estudiantes_asignados': total_estudiantes_asignados,
        'profesores_jefe_asignados': profesores_jefe_asignados,
        'total_asignaturas_asignadas': total_asignaturas_asignadas,
        'total_asignaturas_disponibles': total_asignaturas_disponibles,
        'estudiantes_pendientes': estudiantes_pendientes,
        'total_estudiantes_pendientes': total_estudiantes_pendientes,
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
    if user_type == 'estudiante' or user_type == 'alumno':
        # Estudiantes solo ven las asignaturas de su curso actual
        try:
            estudiante = Estudiante.objects.get(user=request.user)
            anio_actual = timezone.now().year
            
            # Obtener curso actual del estudiante usando el método del modelo
            curso_actual = estudiante.get_curso_actual()
            
            if curso_actual:
                # Solo las asignaturas asignadas al curso actual del estudiante
                asignaturas = curso_actual.asignaturas.select_related('profesor_responsable').order_by('nombre')
                cursos_alumno_ids = [curso_actual.id]
                
                # Información adicional para el estudiante
                context_estudiante = {
                    'estudiante': estudiante,
                    'curso_actual': curso_actual,
                    'total_asignaturas_curso': asignaturas.count(),
                    'asignaturas_con_profesor': asignaturas.filter(profesor_responsable__isnull=False).count(),
                    'asignaturas_sin_profesor_count': asignaturas.filter(profesor_responsable__isnull=True).count(),
                }
            else:
                asignaturas = Asignatura.objects.none()
                cursos_alumno_ids = []
                context_estudiante = {
                    'error_curso': 'No tienes un curso asignado actualmente.'
                }
        except Estudiante.DoesNotExist:
            asignaturas = Asignatura.objects.none()
            cursos_alumno_ids = []
            context_estudiante = {
                'error_estudiante': 'No se encontró tu información de estudiante. Contacta al administrador.'
            }
        except Exception as e:
            asignaturas = Asignatura.objects.none()
            cursos_alumno_ids = []
            context_estudiante = {
                'error_estudiante': f'Error al cargar información del estudiante: {str(e)}'
            }
    elif user_type == 'profesor':
        # Asignaturas del profesor logueado
        try:
            profesor = request.user.profesor
            
            # Solo asignaturas donde es responsable (profesor_responsable)
            asignaturas = Asignatura.objects.filter(
                profesor_responsable=profesor
            ).select_related('profesor_responsable').prefetch_related(
                'cursos__estudiantes'
            ).order_by('nombre')
            
            # Estadísticas específicas para el profesor
            total_asignaturas = asignaturas.count()
            asignaturas_como_responsable = total_asignaturas  # Todas las que ve son de su responsabilidad
            
            # Calcular total de cursos y estudiantes para este profesor
            total_cursos_profesor = 0
            total_estudiantes_profesor = 0
            cursos_unicos = set()
            
            for asignatura in asignaturas:
                cursos_asignatura = asignatura.cursos.all()
                for curso in cursos_asignatura:
                    if curso.id not in cursos_unicos:
                        cursos_unicos.add(curso.id)
                        # Solo contar estudiantes una vez por curso
                        total_estudiantes_profesor += curso.estudiantes.count()
            
            total_cursos_profesor = len(cursos_unicos)
            
            # Variables para el contexto del profesor
            asignaturas_con_profesor = total_asignaturas  # Todas las suyas tienen profesor (él mismo)
            asignaturas_sin_profesor_count = 0
            
        except Exception as e:
            print(f"ERROR en cálculo de profesor: {e}")
            asignaturas = Asignatura.objects.none()
            total_asignaturas = 0
            asignaturas_con_profesor = 0
            asignaturas_sin_profesor_count = 0
            total_cursos_profesor = 0
            total_estudiantes_profesor = 0
            asignaturas_como_responsable = 0
            
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
    # Inicializar variables solo si no son profesores
    if user_type != 'profesor':
        total_asignaturas = 0
        asignaturas_con_profesor = 0
        asignaturas_sin_profesor_count = 0
        asignaturas_sin_profesor = []
        asignaturas_con_cursos = 0
        asignaturas_sin_cursos = 0
        total_cursos_profesor = 0
        total_estudiantes_profesor = 0
    else:
        # Para profesores, mantener las variables ya calculadas
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
        'asignaturas_sin_profesor': asignaturas_sin_profesor if user_type in ['administrador', 'director'] else [],
        'asignaturas_con_cursos': asignaturas_con_cursos if user_type in ['administrador', 'director'] else 0,
        'asignaturas_sin_cursos': asignaturas_sin_cursos if user_type in ['administrador', 'director'] else 0,
        # Variables específicas para profesores
        'total_cursos_profesor': total_cursos_profesor if user_type == 'profesor' else 0,
        'total_estudiantes_profesor': total_estudiantes_profesor if user_type == 'profesor' else 0,
        'asignaturas_como_responsable': asignaturas_como_responsable if user_type == 'profesor' else 0,
    }
    
    # Agregar contexto específico para estudiantes
    if (user_type == 'estudiante' or user_type == 'alumno') and 'context_estudiante' in locals():
        context.update(context_estudiante)
    
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
            
            # Obtener cursos donde imparte asignaturas (usando ambas relaciones)
            # 1. Como profesor responsable de asignaturas
            cursos_por_responsabilidad = Curso.objects.filter(
                asignaturas__profesor_responsable=profesor, anio=anio_actual
            ).distinct()
            
            # 2. A través de la relación ManyToMany
            asignaturas_manytomany = profesor.asignaturas.all()
            if asignaturas_manytomany.exists():
                cursos_por_manytomany = Curso.objects.filter(
                    asignaturas__in=asignaturas_manytomany, anio=anio_actual
                ).distinct()
            else:
                cursos_por_manytomany = Curso.objects.none()
            
            # Combinar todos los tipos de cursos usando IDs para evitar error de combinación
            ids_jefe = list(cursos_como_jefe.values_list('id', flat=True))
            ids_responsabilidad = list(cursos_por_responsabilidad.values_list('id', flat=True))
            ids_manytomany = list(cursos_por_manytomany.values_list('id', flat=True))
            todos_ids = list(set(ids_jefe + ids_responsabilidad + ids_manytomany))
            
            cursos_disponibles = Curso.objects.filter(
                id__in=todos_ids, anio=anio_actual
            ).distinct().order_by('nivel', 'paralelo')
            if curso_id:
                try:
                    curso_seleccionado = cursos_disponibles.get(id=curso_id)
                    asignaturas_curso = curso_seleccionado.asignaturas.all()
                    
                    # Determinar qué asignaturas puede ver el profesor
                    if curso_seleccionado.profesor_jefe == profesor:
                        # Si es profesor jefe del curso, puede ver todas las asignaturas
                        asignaturas_disponibles = asignaturas_curso.order_by('nombre')
                    else:
                        # Si no es profesor jefe, solo ve asignaturas donde es responsable o tiene asignadas
                        ids_asignaturas = set()
                        
                        # Asignaturas donde es responsable (ForeignKey)
                        asignaturas_responsable = profesor.asignaturas_responsable.all()
                        ids_asignaturas.update(asignaturas_responsable.values_list('id', flat=True))
                        
                        # Asignaturas asignadas (ManyToMany)
                        asignaturas_manytomany = profesor.asignaturas.all()
                        ids_asignaturas.update(asignaturas_manytomany.values_list('id', flat=True))
                        
                        # Filtrar solo las asignaturas del curso que tiene asignadas
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
            
            # Obtener estudiantes del curso directamente
            estudiantes_curso = curso_seleccionado.estudiantes.all()
            
            if estudiantes_curso.exists():
                # Obtener o crear período académico
                periodo_actual = PeriodoAcademico.objects.filter(activo=True).first()
                if not periodo_actual:
                    from datetime import date
                    periodo_actual = PeriodoAcademico.objects.create(
                        nombre=f"Año Lectivo {anio_actual}",
                        fecha_inicio=date(anio_actual, 3, 1),
                        fecha_fin=date(anio_actual, 12, 15),
                        activo=True
                    )
                
                # Determinar el profesor del grupo
                if user_type == 'profesor':
                    profesor_actual = Profesor.objects.get(user=request.user)
                    # Si el profesor actual puede dar esta asignatura, usar el profesor actual
                    puede_dar_asignatura = (
                        asignatura_seleccionada.profesor_responsable == profesor_actual or
                        profesor_actual.asignaturas.filter(id=asignatura_seleccionada.id).exists() or
                        curso_seleccionado.profesor_jefe == profesor_actual
                    )
                    if puede_dar_asignatura:
                        profesor_grupo = profesor_actual
                    else:
                        profesor_grupo = asignatura_seleccionada.profesor_responsable
                else:
                    profesor_grupo = asignatura_seleccionada.profesor_responsable
                
                # Obtener o crear grupo para esta asignatura y curso
                grupo, created = Grupo.objects.get_or_create(
                    asignatura=asignatura_seleccionada,
                    periodo_academico=periodo_actual,
                    profesor=profesor_grupo,
                    defaults={'capacidad_maxima': 50}
                )
                
                # Crear inscripciones para todos los estudiantes del curso
                for estudiante in estudiantes_curso:
                    Inscripcion.objects.get_or_create(estudiante=estudiante, grupo=grupo)
                
                # Obtener inscripciones
                inscripciones_filtradas = Inscripcion.objects.filter(
                    estudiante__in=estudiantes_curso,
                    grupo__asignatura=asignatura_seleccionada
                ).select_related('estudiante', 'grupo')
                
                # Para profesores, aplicar filtros adicionales
                if user_type == 'profesor':
                    profesor_actual = Profesor.objects.get(user=request.user)
                    # Un profesor puede ver estudiantes si:
                    # 1. Es el profesor del grupo
                    # 2. Es el profesor responsable de la asignatura
                    # 3. Es el profesor jefe del curso
                    # 4. Tiene la asignatura asignada (ManyToMany)
                    inscripciones_filtradas = inscripciones_filtradas.filter(
                        models.Q(grupo__profesor=profesor_actual) |
                        models.Q(grupo__asignatura__profesor_responsable=profesor_actual) |
                        models.Q(estudiante__cursos__profesor_jefe=profesor_actual) |
                        models.Q(grupo__asignatura__profesores=profesor_actual)
                    ).distinct()
                
                estudiantes_curso_asignatura = inscripciones_filtradas.order_by('estudiante__primer_nombre', 'estudiante__apellido_paterno')
                
                # Debug: Verificar que realmente hay estudiantes
                if not estudiantes_curso_asignatura.exists():
                    messages.warning(request, f'No se encontraron estudiantes para el curso {curso_seleccionado} en la asignatura {asignatura_seleccionada.nombre}.')
                else:
                    messages.success(request, f'Se encontraron {estudiantes_curso_asignatura.count()} estudiantes para ingresar notas.')
            else:
                messages.info(request, f'El curso {curso_seleccionado} no tiene estudiantes asignados.')
                estudiantes_curso_asignatura = []
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
        'anio_actual': anio_actual,
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

    # Lógica especial para estudiantes - mostrar automáticamente sus propias notas
    if user_type == 'alumno':
        try:
            estudiante = Estudiante.objects.get(user=request.user)
            curso_seleccionado = estudiante.get_curso_actual()
            
            if curso_seleccionado:
                # Para estudiantes, simplemente mostrar su curso actual
                cursos_disponibles = [curso_seleccionado]
                asignaturas_disponibles = curso_seleccionado.asignaturas.all().order_by('nombre')
                estudiantes_curso_asignatura = [estudiante]  # Solo el estudiante actual
                
                # Si se especifica una asignatura, filtrar por ella
                if asignatura_id:
                    try:
                        asignatura_seleccionada = Asignatura.objects.get(id=asignatura_id)
                    except Asignatura.DoesNotExist:
                        asignatura_seleccionada = None
                
        except Estudiante.DoesNotExist:
            # Si no existe el estudiante asociado al usuario, no mostrar nada
            curso_seleccionado = None
            estudiantes_curso_asignatura = []
    
    # Obtener cursos y asignaturas según el tipo de usuario (profesores y administradores)
    elif user_type in ['director', 'administrador']:
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
            # Cursos donde es profesor jefe
            cursos_como_jefe = Curso.objects.filter(profesor_jefe=profesor, anio=anio_actual)
            
            # Obtener cursos donde imparte asignaturas (usando ambas relaciones)
            # 1. Como profesor responsable de asignaturas
            cursos_por_responsabilidad = Curso.objects.filter(
                asignaturas__profesor_responsable=profesor, anio=anio_actual
            ).distinct()
            
            # 2. A través de la relación ManyToMany
            asignaturas_manytomany = profesor.asignaturas.all()
            if asignaturas_manytomany.exists():
                cursos_por_manytomany = Curso.objects.filter(
                    asignaturas__in=asignaturas_manytomany, anio=anio_actual
                ).distinct()
            else:
                cursos_por_manytomany = Curso.objects.none()
            
            # Combinar todos los tipos de cursos usando IDs para evitar error de combinación
            ids_jefe = list(cursos_como_jefe.values_list('id', flat=True))
            ids_responsabilidad = list(cursos_por_responsabilidad.values_list('id', flat=True))
            ids_manytomany = list(cursos_por_manytomany.values_list('id', flat=True))
            todos_ids = list(set(ids_jefe + ids_responsabilidad + ids_manytomany))
            
            cursos_disponibles = Curso.objects.filter(
                id__in=todos_ids, anio=anio_actual
            ).distinct().order_by('nivel', 'paralelo')
            if curso_id:
                try:
                    curso_seleccionado = cursos_disponibles.get(id=curso_id)
                    asignaturas_curso = curso_seleccionado.asignaturas.all()
                    
                    # Determinar qué asignaturas puede ver el profesor
                    if curso_seleccionado.profesor_jefe == profesor:
                        # Si es profesor jefe del curso, puede ver todas las asignaturas
                        asignaturas_disponibles = asignaturas_curso.order_by('nombre')
                    else:
                        # Si no es profesor jefe, solo ve asignaturas donde es responsable o tiene asignadas
                        ids_asignaturas = set()
                        
                        # Asignaturas donde es responsable (ForeignKey)
                        asignaturas_responsable = profesor.asignaturas_responsable.all()
                        ids_asignaturas.update(asignaturas_responsable.values_list('id', flat=True))
                        
                        # Asignaturas asignadas (ManyToMany)
                        asignaturas_manytomany = profesor.asignaturas.all()
                        ids_asignaturas.update(asignaturas_manytomany.values_list('id', flat=True))
                        
                        # Filtrar solo las asignaturas del curso que tiene asignadas
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
            
            # Para estudiantes, filtrar solo sus propias notas
            if user_type == 'alumno':
                estudiante = Estudiante.objects.get(user=request.user)
                estudiantes_curso_asignatura = [estudiante]
                inscripciones = Inscripcion.objects.filter(
                    estudiante=estudiante,
                    grupo__asignatura=asignatura_seleccionada
                ).select_related('estudiante', 'grupo')
            else:
                estudiantes_curso = curso_seleccionado.estudiantes.all()
                inscripciones = Inscripcion.objects.filter(
                    estudiante__in=estudiantes_curso,
                    grupo__asignatura=asignatura_seleccionada
                ).select_related('estudiante', 'grupo')
                
                # Para profesores, aplicar filtros más amplios
                if user_type == 'profesor':
                    profesor_actual = Profesor.objects.get(user=request.user)
                    # Un profesor puede ver estudiantes si:
                    # 1. Es el profesor del grupo
                    # 2. Es el profesor responsable de la asignatura
                    # 3. Es el profesor jefe del curso
                    # 4. Tiene la asignatura asignada (ManyToMany)
                    inscripciones = inscripciones.filter(
                        models.Q(grupo__profesor=profesor_actual) |
                        models.Q(grupo__asignatura__profesor_responsable=profesor_actual) |
                        models.Q(estudiante__cursos__profesor_jefe=profesor_actual) |
                        models.Q(grupo__asignatura__profesores=profesor_actual)
                    ).distinct()
                
                # Obtener estudiantes únicos (evitar duplicados)
                estudiantes_ids = set(inscripciones.values_list('estudiante_id', flat=True))
                estudiantes_curso_asignatura = estudiantes_curso.filter(id__in=estudiantes_ids).order_by('primer_nombre', 'apellido_paterno')
            
            notas = Calificacion.objects.filter(inscripcion__in=inscripciones).select_related('inscripcion', 'inscripcion__estudiante')
            
            # Construir lista de evaluaciones individuales (no agrupadas por nombre)
            if user_type == 'alumno':
                # Para alumnos, mostrar todas las evaluaciones individuales ordenadas por fecha
                evaluaciones = []
                notas_ordenadas = notas.order_by('fecha_evaluacion', 'nombre_evaluacion', 'id')
                for nota in notas_ordenadas:
                    # Crear un identificador único para cada evaluación
                    eval_id = f"{nota.nombre_evaluacion}_{nota.fecha_evaluacion}_{nota.id}"
                    evaluaciones.append({
                        'nombre': nota.nombre_evaluacion,
                        'fecha': nota.fecha_evaluacion,
                        'id_unico': eval_id,
                        'nota_obj': nota
                    })
            else:
                # Para profesores/administradores, mantener lógica original (agrupadas por nombre)
                evaluaciones_nombres = set()
                for nota in notas:
                    evaluaciones_nombres.add(nota.nombre_evaluacion)
                evaluaciones = [{'nombre': nombre} for nombre in sorted(evaluaciones_nombres)]
            
            # Agrupar notas por estudiante y por evaluación
            for estudiante in estudiantes_curso_asignatura:
                if user_type == 'alumno':
                    # Para alumnos, crear lista de notas directamente ordenadas
                    notas_estudiante = notas.filter(inscripcion__estudiante=estudiante).order_by('fecha_evaluacion', 'nombre_evaluacion', 'id')
                    notas_est = list(notas_estudiante)
                else:
                    # Para otros usuarios, mantener lógica original
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
        if user_type == 'alumno':
            # Para estudiantes, mostrar solo sus notas de todas las asignaturas
            estudiante = Estudiante.objects.get(user=request.user)
            estudiantes_curso_asignatura = [estudiante]
            asignaturas_curso = curso_seleccionado.asignaturas.all()
            
            # Obtener inscripciones solo del estudiante actual
            inscripciones = Inscripcion.objects.filter(
                estudiante=estudiante,
                grupo__asignatura__in=asignaturas_curso
            ).select_related('estudiante', 'grupo', 'grupo__asignatura')
        else:
            # Para profesores y administradores, mantener lógica original
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
            
            # Obtener estudiantes únicos del curso
            estudiantes_curso_asignatura = estudiantes_curso.order_by('primer_nombre', 'apellido_paterno')
        
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

    # Calcular promedios por asignatura específicamente para estudiantes
    promedios_por_asignatura = {}
    promedio_general_estudiante = None
    
    if user_type == 'alumno' and curso_seleccionado and estudiantes_tabla:
        estudiante = estudiantes_tabla[0]  # Solo hay un estudiante (el actual)
        
        # Obtener todas las asignaturas del curso del estudiante
        asignaturas_curso = curso_seleccionado.asignaturas.all()
        
        # Calcular promedio por cada asignatura
        suma_promedios_asignaturas = 0
        asignaturas_con_notas = 0
        
        for asignatura in asignaturas_curso:
            # Obtener todas las notas del estudiante para esta asignatura
            inscripciones_asignatura = Inscripcion.objects.filter(
                estudiante=estudiante,
                grupo__asignatura=asignatura
            )
            notas_asignatura = Calificacion.objects.filter(
                inscripcion__in=inscripciones_asignatura
            )
            
            if notas_asignatura.exists():
                puntajes = [nota.puntaje for nota in notas_asignatura]
                promedio_asignatura_actual = round(sum(puntajes) / len(puntajes), 2)
                estado_asignatura = 'Aprobado' if promedio_asignatura_actual >= 4.0 else 'Reprobado'
                
                promedios_por_asignatura[asignatura.id] = {
                    'asignatura': asignatura,
                    'promedio': promedio_asignatura_actual,
                    'total_notas': len(puntajes),
                    'estado': estado_asignatura,
                }
                
                suma_promedios_asignaturas += promedio_asignatura_actual
                asignaturas_con_notas += 1
            else:
                promedios_por_asignatura[asignatura.id] = {
                    'asignatura': asignatura,
                    'promedio': '--',
                    'total_notas': 0,
                    'estado': '--',
                }
        
        # Calcular promedio general del estudiante
        if asignaturas_con_notas > 0:
            promedio_general_estudiante = round(suma_promedios_asignaturas / asignaturas_con_notas, 2)
    
    context['promedios_por_asignatura'] = promedios_por_asignatura
    context['promedio_general_estudiante'] = promedio_general_estudiante

    # Generar ranking de mejores estudiantes (solo para admin, director, profesor)
    ranking_estudiantes = []
    estadisticas_curso = {}
    
    if user_type in ['administrador', 'director', 'profesor'] and curso_seleccionado:
        if asignatura_seleccionada:
            # Ranking para una asignatura específica
            ranking_data = []
            for estudiante in estudiantes_tabla:
                promedio_data = promedios_estudiantes.get(estudiante.id, {})
                promedio = promedio_data.get('promedio')
                total_notas = promedio_data.get('total_notas', 0)
                
                if promedio != '--' and promedio is not None:
                    ranking_data.append({
                        'estudiante': estudiante,
                        'promedio': promedio,
                        'total_notas': total_notas,
                        'total_asignaturas': 1  # Solo una asignatura
                    })
            
            # Ordenar por promedio descendente
            ranking_estudiantes = sorted(ranking_data, key=lambda x: x['promedio'], reverse=True)
            
            # Estadísticas de la asignatura
            if promedios_estudiantes:
                aprobados = sum(1 for p in promedios_estudiantes.values() 
                               if p['promedio'] != '--' and p['promedio'] >= 4.0)
                reprobados = sum(1 for p in promedios_estudiantes.values() 
                                if p['promedio'] != '--' and p['promedio'] < 4.0)
                estadisticas_curso = {
                    'aprobados': aprobados,
                    'reprobados': reprobados,
                    'promedio_curso': promedio_asignatura or 0,
                    'total_estudiantes': len(estudiantes_tabla)
                }
        else:
            # Ranking por promedio general del curso (todas las asignaturas)
            ranking_data = []
            for estudiante in estudiantes_tabla:
                # Calcular promedio general del estudiante en todas las asignaturas del curso
                asignaturas_curso = curso_seleccionado.asignaturas.all()
                suma_promedios = 0
                asignaturas_con_notas = 0
                
                for asignatura in asignaturas_curso:
                    inscripciones_asignatura = Inscripcion.objects.filter(
                        estudiante=estudiante,
                        grupo__asignatura=asignatura
                    )
                    notas_asignatura = Calificacion.objects.filter(
                        inscripcion__in=inscripciones_asignatura
                    )
                    
                    if notas_asignatura.exists():
                        puntajes = [nota.puntaje for nota in notas_asignatura]
                        promedio_asignatura = sum(puntajes) / len(puntajes)
                        suma_promedios += promedio_asignatura
                        asignaturas_con_notas += 1
                
                if asignaturas_con_notas > 0:
                    promedio_general = suma_promedios / asignaturas_con_notas
                    ranking_data.append({
                        'estudiante': estudiante,
                        'promedio': round(promedio_general, 2),
                        'total_notas': asignaturas_con_notas,
                        'total_asignaturas': asignaturas_con_notas
                    })
            
            # Ordenar por promedio descendente
            ranking_estudiantes = sorted(ranking_data, key=lambda x: x['promedio'], reverse=True)
            
            # Estadísticas del curso completo
            if ranking_data:
                promedios_validos = [r['promedio'] for r in ranking_data]
                aprobados = sum(1 for p in promedios_validos if p >= 4.0)
                reprobados = sum(1 for p in promedios_validos if p < 4.0)
                promedio_curso = sum(promedios_validos) / len(promedios_validos)
                
                estadisticas_curso = {
                    'aprobados': aprobados,
                    'reprobados': reprobados,
                    'promedio_curso': round(promedio_curso, 2),
                    'total_estudiantes': len(estudiantes_tabla)
                }
    
    context['ranking_estudiantes'] = ranking_estudiantes
    context['estadisticas_curso'] = estadisticas_curso

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
                # USAR LA MISMA LÓGICA QUE EN NOTAS - Filtrado mejorado para profesores
                # 1. Cursos donde es jefe
                cursos_como_jefe = Curso.objects.filter(
                    profesor_jefe=profesor_actual,
                    anio=timezone.now().year
                )
                
                # 2. Cursos donde tiene asignaturas (como responsable)
                cursos_con_asignaturas_responsable = Curso.objects.filter(
                    asignaturas__profesor_responsable=profesor_actual,
                    anio=timezone.now().year
                ).distinct()
                
                # 3. Cursos donde tiene asignaturas (ManyToMany)
                cursos_con_asignaturas_asignadas = Curso.objects.filter(
                    asignaturas__profesores=profesor_actual,
                    anio=timezone.now().year
                ).distinct()

                # 4. Cursos donde tiene horarios asignados
                cursos_con_horarios = Curso.objects.filter(
                    horarios__profesor=profesor_actual,
                    anio=timezone.now().year
                ).distinct()
                
                # Combinar usando IDs para evitar el error de QuerySet
                cursos_ids = list(set(
                    list(cursos_como_jefe.values_list('id', flat=True)) +
                    list(cursos_con_asignaturas_responsable.values_list('id', flat=True)) +
                    list(cursos_con_asignaturas_asignadas.values_list('id', flat=True)) +
                    list(cursos_con_horarios.values_list('id', flat=True))
                ))
                
                cursos_disponibles = Curso.objects.filter(id__in=cursos_ids).order_by('nivel', 'paralelo')
                
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
                    # 1. Como responsable
                    asignatura_seleccionada = curso_seleccionado.asignaturas.filter(
                        profesor_responsable=profesor_actual
                    ).first()
                    
                    # 2. Si no, buscar en ManyToMany
                    if not asignatura_seleccionada:
                        asignatura_seleccionada = curso_seleccionado.asignaturas.filter(
                            profesores=profesor_actual
                        ).first()
                        
                    # 3. Si no, buscar en Horarios (priorizar horarios con asignatura)
                    if not asignatura_seleccionada:
                        horario = HorarioCurso.objects.filter(
                            curso=curso_seleccionado,
                            profesor=profesor_actual,
                            asignatura__isnull=False
                        ).first()
                        if horario:
                            asignatura_seleccionada = horario.asignatura
                
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
                    # 1. Como responsable
                    asignatura_seleccionada = curso_seleccionado.asignaturas.filter(
                        profesor_responsable=profesor_actual
                    ).first()
                    
                    # 2. Si no, buscar en ManyToMany
                    if not asignatura_seleccionada:
                        asignatura_seleccionada = curso_seleccionado.asignaturas.filter(
                            profesores=profesor_actual
                        ).first()
                        
                    # 3. Si no, buscar en Horarios (priorizar horarios con asignatura)
                    if not asignatura_seleccionada:
                        horario = HorarioCurso.objects.filter(
                            curso=curso_seleccionado,
                            profesor=profesor_actual,
                            asignatura__isnull=False
                        ).first()
                        if horario:
                            asignatura_seleccionada = horario.asignatura
                
                if not asignatura_seleccionada:
                    messages.error(request, 'No tienes asignaturas asignadas a este curso.')
                    form = RegistroMasivoAsistenciaForm()
                    form.fields['curso'].queryset = cursos_disponibles
                else:
                    mostrar_lista = True
            else:
                messages.error(request, f'Por favor selecciona un curso válido. {form.errors}')
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
                # USAR LA MISMA LÓGICA QUE EN NOTAS - Filtrado mejorado para profesores
                # 1. Cursos donde es jefe
                cursos_como_jefe = Curso.objects.filter(
                    profesor_jefe=profesor_actual,
                    anio=timezone.now().year
                )
                
                # 2. Cursos donde tiene asignaturas (como responsable)
                cursos_con_asignaturas_responsable = Curso.objects.filter(
                    asignaturas__profesor_responsable=profesor_actual,
                    anio=timezone.now().year
                ).distinct()
                
                # 3. Cursos donde tiene asignaturas (ManyToMany)
                cursos_con_asignaturas_asignadas = Curso.objects.filter(
                    asignaturas__profesores=profesor_actual,
                    anio=timezone.now().year
                ).distinct()

                # 4. Cursos donde tiene horarios asignados
                cursos_con_horarios = Curso.objects.filter(
                    horarios__profesor=profesor_actual,
                    anio=timezone.now().year
                ).distinct()
                
                # Combinar usando IDs para evitar el error de QuerySet
                cursos_ids = list(set(
                    list(cursos_como_jefe.values_list('id', flat=True)) +
                    list(cursos_con_asignaturas_responsable.values_list('id', flat=True)) +
                    list(cursos_con_asignaturas_asignadas.values_list('id', flat=True)) +
                    list(cursos_con_horarios.values_list('id', flat=True))
                ))
                
                cursos_disponibles = Curso.objects.filter(id__in=cursos_ids).order_by('nivel', 'paralelo')
                
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
    
    # Para estudiantes, seleccionar automáticamente su curso actual
    if user_type == 'alumno' and estudiante_usuario:
        # Buscar el curso actual del estudiante
        curso_actual = cursos_disponibles.first()  # Obtener el primer curso del estudiante
        if curso_actual:
            curso_seleccionado = curso_actual
            estudiante_seleccionado = estudiante_usuario
            estudiantes_curso = [estudiante_usuario]
        else:
            mensaje = "No estás asignado a ningún curso este año"
    
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
    
    # Procesar filtros - Solo para profesores y administradores
    if curso_id and user_type != 'alumno':
        try:
            curso_seleccionado = get_object_or_404(Curso, id=curso_id)
            # Verificar permisos para este curso
            if curso_seleccionado not in cursos_disponibles:
                messages.error(request, 'No tienes permisos para ver este curso.')
                curso_seleccionado = None
            else:
                # Obtener estudiantes del curso
                estudiantes_curso = curso_seleccionado.estudiantes.all().order_by('primer_nombre', 'apellido_paterno')
                
                # Aplicar filtro por RUT si se especifica
                if rut_filtro:
                    estudiantes_curso = [e for e in estudiantes_curso if rut_filtro.lower() in e.numero_documento.lower()]
                
                # Filtro por estudiante específico
                if estudiante_id:
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
    
    # Para estudiantes, obtener asistencias automáticamente si tienen curso
    elif user_type == 'alumno' and curso_seleccionado:
        asistencias = AsistenciaAlumno.objects.filter(
            estudiante=estudiante_usuario,
            curso=curso_seleccionado,
            fecha__range=[fecha_lunes, fecha_domingo]
        ).select_related('asignatura', 'profesor_registro').order_by('fecha')
    
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
    """Vista para mostrar que la funcionalidad está en implementación futura"""
    from django.contrib import messages
    
    # Verificar permisos
    user_type = None
    if hasattr(request.user, 'perfil'):
        user_type = request.user.perfil.tipo_usuario
        if user_type not in ['director', 'administrador', 'profesor']:
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('inicio')
            
        # Si es profesor, redirigir a asistencia de alumnos
        if user_type == 'profesor':
            return redirect('registrar_asistencia_alumno')
    else:
        messages.error(request, 'Usuario sin perfil definido.')
        return redirect('inicio')
    
    # Mostrar mensaje informativo
    messages.info(request, 'La funcionalidad de registro de asistencia de profesores estará disponible en una futura actualización.')
    
    context = {
        'titulo': 'Asistencia de Profesores - Implementación Futura',
        'user': request.user,
        'implementacion_futura': True
    }
    return render(request, 'registrar_asistencia_profesor.html', context)

@login_required
def ver_asistencia_profesor(request):
    """Vista para mostrar que la funcionalidad de visualización está en implementación futura"""
    from django.contrib import messages
    
    # Verificar permisos
    user_type = None
    if hasattr(request.user, 'perfil'):
        user_type = request.user.perfil.tipo_usuario
        if user_type not in ['director', 'administrador', 'profesor']:
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('inicio')
    else:
        messages.error(request, 'Usuario sin perfil definido.')
        return redirect('inicio')
    
    # Mostrar mensaje informativo
    messages.info(request, 'La visualización de asistencia de profesores estará disponible en una futura actualización.')
    
    context = {
        'titulo': 'Ver Asistencia de Profesores - Implementación Futura',
        'user': request.user,
        'implementacion_futura': True,
        'total_asistencias': 0,
        'total_presentes': 0,
        'total_ausentes': 0,
        'porcentaje_asistencia': 0,
        'asistencias': [],
        'page_obj': None
    }
    
    return render(request, 'ver_asistencia_profesor.html', context)
    
    return render(request, 'ver_asistencia_profesor.html', context)

# Función de editar asistencia de profesores deshabilitada - Implementación futura
"""
@login_required
def editar_asistencia_profesor(request, asistencia_id):
    # Vista para editar un registro individual de asistencia de profesor
    # Implementación futura
    pass
"""

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
    # Si el curso no tiene asignaturas asignadas, mostrar todas (fallback)
    if not asignaturas.exists():
        asignaturas = Asignatura.objects.all().order_by('nombre')
        
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
    from .forms import HorarioCursoForm
    from django.http import JsonResponse
    import json
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        # Obtener datos del POST
        curso_id = request.POST.get('curso')
        if not curso_id:
            return JsonResponse({'success': False, 'error': 'ID de curso requerido'})
        
        curso = get_object_or_404(Curso, id=curso_id)
        
        # Crear formulario con los datos
        form = HorarioCursoForm(request.POST, curso=curso)
        
        if form.is_valid():
            horario = form.save(commit=False)
            horario.curso = curso
            horario.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Horario creado exitosamente',
                'horario': {
                    'id': horario.id,
                    'dia': horario.get_dia_display(),
                    'hora_inicio': horario.hora_inicio.strftime('%H:%M'),
                    'hora_fin': horario.hora_fin.strftime('%H:%M'),
                    'asignatura': horario.asignatura.nombre if horario.asignatura else 'Sin asignatura',
                    'profesor': horario.profesor.get_nombre_completo() if horario.profesor else 'Sin asignar'
                }
            })
        else:
            errors = []
            for field, error_list in form.errors.items():
                field_label = field
                if field in form.fields and hasattr(form.fields[field], 'label') and form.fields[field].label:
                    field_label = form.fields[field].label
                for error in error_list:
                    errors.append(f"{field_label}: {error}")
            
            return JsonResponse({
                'success': False,
                'error': 'Error de validación',
                'errors': errors
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'})

@login_required
def ajax_editar_horario(request):
    """Vista AJAX para editar horario"""
    from .forms import HorarioCursoForm
    from django.http import JsonResponse
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        horario_id = request.POST.get('horario_id')
        if not horario_id:
            return JsonResponse({'success': False, 'error': 'ID de horario requerido'})
        
        horario = get_object_or_404(HorarioCurso, id=horario_id)
        
        # Crear formulario con los datos del horario existente
        form = HorarioCursoForm(request.POST, instance=horario, curso=horario.curso)
        
        if form.is_valid():
            horario_actualizado = form.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Horario actualizado exitosamente',
                'horario': {
                    'id': horario_actualizado.id,
                    'dia': horario_actualizado.get_dia_display(),
                    'hora_inicio': horario_actualizado.hora_inicio.strftime('%H:%M'),
                    'hora_fin': horario_actualizado.hora_fin.strftime('%H:%M'),
                    'asignatura': horario_actualizado.asignatura.nombre if horario_actualizado.asignatura else 'Sin asignatura',
                    'profesor': horario_actualizado.profesor.get_nombre_completo() if horario_actualizado.profesor else 'Sin asignar'
                }
            })
        else:
            errors = []
            for field, error_list in form.errors.items():
                field_label = field
                if field in form.fields and hasattr(form.fields[field], 'label') and form.fields[field].label:
                    field_label = form.fields[field].label
                for error in error_list:
                    errors.append(f"{field_label}: {error}")
            
            return JsonResponse({
                'success': False,
                'error': 'Error de validación',
                'errors': errors
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'})

@login_required
def ajax_obtener_horario(request):
    """Vista AJAX para obtener datos de un horario"""
    from django.http import JsonResponse
    
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        horario_id = request.GET.get('horario_id')
        if not horario_id:
            return JsonResponse({'success': False, 'error': 'ID de horario requerido'})
        
        horario = get_object_or_404(HorarioCurso, id=horario_id)
        
        return JsonResponse({
            'success': True,
            'horario': {
                'id': horario.id,
                'dia': horario.dia,
                'hora_inicio': horario.hora_inicio.strftime('%H:%M'),
                'hora_fin': horario.hora_fin.strftime('%H:%M'),
                'asignatura_id': horario.asignatura.id if horario.asignatura else '',
                'profesor_id': horario.profesor.id if horario.profesor else '',
                'asignatura_nombre': horario.asignatura.nombre if horario.asignatura else 'Sin asignatura',
                'profesor_nombre': horario.profesor.get_nombre_completo() if horario.profesor else 'Sin asignar'
            }
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'})

@login_required
def ajax_eliminar_horario_nuevo(request):
    """Vista AJAX para eliminar horario"""
    from django.http import JsonResponse
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        horario_id = request.POST.get('horario_id')
        if not horario_id:
            return JsonResponse({'success': False, 'error': 'ID de horario requerido'})
        
        horario = get_object_or_404(HorarioCurso, id=horario_id)
        horario_info = f"{horario.asignatura.nombre if horario.asignatura else 'Sin asignatura'} - {horario.get_dia_display()}"
        horario.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Horario "{horario_info}" eliminado exitosamente'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'})

@login_required
def asignar_profesor_asignatura(request, asignatura_id):
    """Vista para asignar profesor a asignatura"""
    return JsonResponse({'success': False, 'error': 'Función no implementada'})

@login_required
def obtener_profesores_asignatura(request, asignatura_id):
    """Vista para obtener profesores de asignatura"""
    try:
        asignatura = get_object_or_404(Asignatura, id=asignatura_id)
        profesores = asignatura.profesores.all().order_by('primer_nombre', 'apellido_paterno')
        
        profesores_data = []
        for profesor in profesores:
            profesores_data.append({
                'id': profesor.id,
                'nombre': profesor.get_nombre_completo()
            })
        
        return JsonResponse({
            'success': True,
            'profesores': profesores_data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error: {str(e)}'})

@login_required
def editar_evento(request, evento_id):
    """Vista para editar evento"""
    from .forms import EventoCalendarioForm
    from django.contrib import messages
    from django.shortcuts import get_object_or_404, redirect
    from django.utils import timezone
    
    # Verificar permisos
    user_type = 'otro'
    if request.user.is_superuser:
        user_type = 'administrador'
    elif hasattr(request.user, 'perfil') and request.user.perfil:
        user_type = request.user.perfil.tipo_usuario
    elif hasattr(request.user, 'profesor'):
        user_type = 'profesor'
    
    # Obtener el evento
    evento = get_object_or_404(EventoCalendario, id=evento_id)
    
    # Verificar permisos para editar
    puede_editar = False
    if user_type in ['administrador', 'director']:
        puede_editar = True
    elif user_type == 'profesor' and evento.creado_por == request.user:
        puede_editar = True
    
    if not puede_editar:
        messages.error(request, 'No tienes permisos para editar este evento.')
        return redirect('calendario')
    
    if request.method == 'POST':
        form = EventoCalendarioForm(request.POST, instance=evento, editando=True, user=request.user)
        if form.is_valid():
            try:
                evento_actualizado = form.save()
                messages.success(
                    request, 
                    f'Evento "{evento_actualizado.titulo}" actualizado exitosamente.'
                )
                return redirect('calendario')
            except Exception as e:
                messages.error(request, f'Error al actualizar el evento: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = EventoCalendarioForm(instance=evento, editando=True, user=request.user)
    
    # Obtener cursos disponibles para el contexto
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
        'user': request.user,
        'evento': evento,
        'form': form,
        'cursos': cursos,
        'user_type': user_type,
        'puede_editar': puede_editar,
        'tipos_evento': EventoCalendario.TIPO_EVENTO_CHOICES,
        'prioridades': EventoCalendario.PRIORIDAD_CHOICES,
    }
    
    return render(request, 'editar_evento.html', context)

@login_required
def eliminar_evento(request, evento_id):
    """Vista para eliminar evento"""
    from django.http import JsonResponse
    from django.shortcuts import get_object_or_404
    from .models import EventoCalendario
    
    if request.method == 'POST':
        evento = get_object_or_404(EventoCalendario, id=evento_id)
        
        # Verificar permisos
        puede_eliminar = False
        if request.user.is_superuser:
            puede_eliminar = True
        elif hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario in ['administrador', 'director']:
            puede_eliminar = True
        elif hasattr(request.user, 'profesor') and evento.creado_por == request.user:
            puede_eliminar = True
            
        if not puede_eliminar:
             return JsonResponse({'success': False, 'error': 'No tienes permisos para eliminar este evento'})

        try:
            evento.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
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
    asignatura = get_object_or_404(Asignatura, id=asignatura_id)
    
    if request.method == 'POST':
        form = AsignaturaForm(request.POST, instance=asignatura)
        if form.is_valid():
            form.save()
            messages.success(request, 'Asignatura actualizada exitosamente.')
            return redirect('listar_asignaturas')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = AsignaturaForm(instance=asignatura)
    
    profesores = Profesor.objects.all().order_by('primer_nombre', 'apellido_paterno')
    
    context = {
        'user': request.user, 
        'asignatura': asignatura,
        'form': form,
        'profesores': profesores,
        'titulo': 'Editar Asignatura'
    }
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
                # USAR LA MISMA LÓGICA QUE EN NOTAS - Verificar si tiene acceso al curso
                # 1. Es jefe del curso
                es_jefe_curso = asistencia.curso.profesor_jefe == profesor_actual
                
                # 2. Es responsable de la asignatura
                es_responsable_asignatura = asistencia.asignatura.profesor_responsable == profesor_actual
                
                # 3. Está asignado a la asignatura (ManyToMany)
                esta_asignado_asignatura = asistencia.asignatura.profesores.filter(id=profesor_actual.id).exists()
                
                puede_editar = es_jefe_curso or es_responsable_asignatura or esta_asignado_asignatura
                
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
    from datetime import datetime
    
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
            except AttributeError:
                messages.error(request, 'No se encontró un perfil de estudiante asociado a tu usuario.')
                return render(request, 'libro_anotaciones.html', {'error': True})
            except Exception as e:
                messages.error(request, f'Error al obtener información del estudiante: {str(e)}')
                return render(request, 'libro_anotaciones.html', {'error': True})
                
        elif user_type == 'profesor':
            # Profesor ve anotaciones de sus cursos y puede crear
            try:
                # Usar la relación directa user.profesor
                profesor_actual = request.user.profesor
                cursos_disponibles = profesor_actual.get_cursos_asignados()
                
                # Obtener estudiantes de sus cursos
                estudiantes_ids = set()
                for curso in cursos_disponibles:
                    estudiantes_ids.update(curso.estudiantes.values_list('id', flat=True))
                
                # Incluir anotaciones de estudiantes Y anotaciones generales de los cursos
                cursos_ids = list(cursos_disponibles.values_list('id', flat=True))
                anotaciones_base = Anotacion.objects.filter(
                    Q(estudiante_id__in=estudiantes_ids) |  # Anotaciones de estudiantes
                    Q(estudiante__isnull=True, curso_id__in=cursos_ids)  # Anotaciones generales del curso
                )
                puede_crear = True
            except AttributeError:
                messages.error(request, 'No se encontró un perfil de profesor asociado a tu usuario.')
                return render(request, 'libro_anotaciones.html', {'error': True})
            except Exception as e:
                messages.error(request, f'Error al obtener información del profesor: {str(e)}')
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
        if filtro_form.cleaned_data.get('curso') and user_type != 'alumno':
            anotaciones = anotaciones.filter(curso=filtro_form.cleaned_data['curso'])
        
        if filtro_form.cleaned_data.get('estudiante') and user_type != 'alumno':
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
    
    # Información específica para estudiantes
    estadisticas_estudiante = None
    if user_type == 'alumno' and estudiante_actual:
        estadisticas_estudiante = calcular_puntaje_comportamiento(estudiante_actual)
        # Agregar información adicional del curso actual
        curso_actual = estudiante_actual.get_curso_actual()
        if curso_actual:
            estadisticas_estudiante['curso_actual'] = curso_actual
            
    # Preparar datos para gráficos (JSON)
    import json
    chart_data_cursos = []
    if user_type != 'alumno':
        # Agrupar por curso (quitando ordenamiento previo para agrupar correctamente)
        datos_curso = anotaciones.order_by().values('curso__nivel', 'curso__paralelo').annotate(
            total=Count('id'),
            positivas=Count('id', filter=Q(tipo='positiva')),
            negativas=Count('id', filter=Q(tipo='negativa')),
            graves=Count('id', filter=Q(es_grave=True))
        ).order_by('curso__nivel', 'curso__paralelo')
        
        for d in datos_curso:
            if d['curso__nivel'] and d['curso__paralelo']:
                nombre_curso = f"{d['curso__nivel']} {d['curso__paralelo']}"
                chart_data_cursos.append({
                    'curso': nombre_curso,
                    'total': d['total'],
                    'positivas': d['positivas'],
                    'negativas': d['negativas'],
                    'graves': d['graves']
                })
    
    context = {
        'anotaciones': anotaciones_paginas,
        'filtro_form': filtro_form,
        'stats_generales': stats_generales,
        'stats_estudiantes': stats_estudiantes,
        'estadisticas_estudiante': estadisticas_estudiante,
        'user_type': user_type,
        'puede_crear': puede_crear,
        'profesor_actual': profesor_actual,
        'estudiante_actual': estudiante_actual,
        'cursos_disponibles': cursos_disponibles,
        'resumen_cursos': chart_data_cursos,
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
            except AttributeError:
                messages.error(request, 'No se encontró un perfil de profesor asociado a tu usuario.')
                return redirect('libro_anotaciones')
            except Exception as e:
                messages.error(request, f'Error al obtener información del profesor: {str(e)}')
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
            
            if anotacion.estudiante:
                messages.success(
                    request, 
                    f'Anotación {anotacion.get_tipo_display().lower()} creada para {anotacion.estudiante.get_nombre_completo()}'
                )
            else:
                messages.success(
                    request, 
                    f'Anotación {anotacion.get_tipo_display().lower()} general creada para el curso {anotacion.curso}'
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
        fecha_str = fecha.strftime('%Y-%m-%d')
        if fecha_str not in datos_grafico:
            datos_grafico[fecha_str] = 0
        datos_grafico[fecha_str] += anotacion['puntos']
    
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
    """Vista AJAX para buscar estudiantes por nombre o RUT"""
    if request.method == 'GET':
        query = request.GET.get('q', '')
        
        if query:
            estudiantes = Estudiante.objects.filter(
                Q(primer_nombre__icontains=query) |
                Q(apellido_paterno__icontains=query) |
                Q(numero_documento__icontains=query)
            ).order_by('primer_nombre', 'apellido_paterno')[:20]  # Limit results
            
            data = {
                'estudiantes': [
                    {
                        'id': est.id,
                        'nombre': est.get_nombre_completo(),
                        'rut': est.numero_documento,
                        'curso': str(est.get_curso_actual()) if est.get_curso_actual() else 'Sin curso'
                    }
                    for est in estudiantes
                ]
            }
            return JsonResponse(data)
        
        return JsonResponse({'estudiantes': []})
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def reporte_comportamiento_cursos(request):
    """
    Vista para generar un reporte gráfico del comportamiento por curso.
    """
    # Obtener cursos del año actual
    anio_actual = timezone.now().year
    cursos = Curso.objects.filter(anio=anio_actual).order_by('nivel', 'paralelo')
    datos_cursos = []

    for curso in cursos:
        positivas = Anotacion.objects.filter(curso=curso, tipo='positiva').count()
        negativas = Anotacion.objects.filter(curso=curso, tipo='negativa').count()
        
        datos_cursos.append({
            'curso': str(curso),
            'positivas': positivas,
            'negativas': negativas,
            'total': positivas + negativas,
            'indice': positivas - negativas
        })

    context = {
        'datos_cursos': datos_cursos
    }
    return render(request, 'reporte_comportamiento_cursos.html', context)

@admin_required
@require_POST
def reset_password_profesor(request, profesor_id):
    """
    Resetea la contraseña de un profesor y devuelve la nueva contraseña.
    """
    try:
        profesor = get_object_or_404(Profesor, id=profesor_id)
        if not profesor.user:
             return JsonResponse({'success': False, 'error': 'El profesor no tiene un usuario asociado.'})
        
        # Generar contraseña aleatoria segura
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        new_password = ''.join(secrets.choice(alphabet) for i in range(10))
        
        profesor.user.set_password(new_password)
        profesor.user.save()
        
        return JsonResponse({'success': True, 'new_password': new_password})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})