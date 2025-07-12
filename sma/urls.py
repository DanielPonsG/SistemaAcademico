"""
URL configuration for sma project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from smapp.views import (
    index_master, index, agregar, modificar, eliminar,
    listar_estudiantes, listar_profesores, gestionar_profesor,
    calendario, inicio, login_view, logout_view, mis_horarios, mi_curso,
    listar_cursos, listar_asignaturas, ingresar_notas, ver_notas_curso,
    asignar_asignaturas_curso,
    registrar_asistencia_alumno, ver_asistencia_alumno, registrar_asistencia_profesor,
    seleccionar_curso_horarios, gestionar_horarios,
    ajax_crear_horario, ajax_editar_horario, ajax_obtener_horario, ajax_eliminar_horario_nuevo,
    asignar_profesor_asignatura, obtener_profesores_asignatura,
    # Funciones adicionales que pueden estar referenciadas
    agregar_evento, editar_evento, eliminar_evento, agregar_curso, editar_curso, eliminar_curso,
    agregar_asignatura, editar_asignatura, eliminar_asignatura, agregar_asignatura_completa,
    ver_horario_curso, api_horarios_cursos, editar_nota, eliminar_nota, agregar_nota_individual,
    ver_asistencia_profesor,
    # Nuevas vistas AJAX para gestión de asignaturas
    gestionar_asignaturas_curso_ajax, obtener_asignaturas_curso_ajax,
    # Nueva vista para editar asistencia
    editar_asistencia_alumno, # editar_asistencia_profesor - Deshabilitada (Implementación futura)
    # Vistas del libro de anotaciones
    libro_anotaciones, crear_anotacion, editar_anotacion, eliminar_anotacion,
    detalle_comportamiento_estudiante, ajax_obtener_estudiantes_curso, ajax_obtener_estudiantes_filtro
)
# Importaciones para vistas de apoderados
from smapp.views_apoderados import (
    listar_apoderados, gestionar_apoderado, eliminar_apoderado, detalle_apoderado,
    dashboard_apoderado, dashboard_profesor_apoderado, inicio_apoderado,
    estudiantes_a_cargo_profesor_apoderado, ver_notas_estudiante_apoderado,
    ver_anotaciones_estudiante_apoderado, ver_horario_estudiante_apoderado
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('index_master', index_master, name='index_master'),
    path('login/', login_view, name='login'),
    path('', inicio, name='inicio'),
    path('logout/', logout_view, name='logout'),
    
    # CRUD de Administrador
    path('agregar/', agregar, name='agregar'),
    path('modificar', modificar, name='modificar'),
    path('eliminar', eliminar, name='eliminar'),
    path('estudiantes/listar/', listar_estudiantes, name='listar_estudiantes'),
    
    # Gestión de Profesores (solo administrador)
    path('profesores/', listar_profesores, name='listar_profesores'),
    path('profesores/agregar/', gestionar_profesor, name='gestionar_profesor'),
    path('profesores/editar/<int:profesor_id>/', gestionar_profesor, name='gestionar_profesor'),
    
    # Gestión de Apoderados (solo administrador y director)
    path('apoderados/', listar_apoderados, name='listar_apoderados'),
    path('apoderados/agregar/', gestionar_apoderado, name='gestionar_apoderado'),
    path('apoderados/editar/<int:apoderado_id>/', gestionar_apoderado, name='gestionar_apoderado'),
    path('apoderados/eliminar/<int:apoderado_id>/', eliminar_apoderado, name='eliminar_apoderado'),
    path('apoderados/detalle/<int:apoderado_id>/', detalle_apoderado, name='detalle_apoderado'),
    
    # Dashboards de Apoderados
    path('dashboard-apoderado/', dashboard_apoderado, name='dashboard_apoderado'),
    path('dashboard-profesor-apoderado/', dashboard_profesor_apoderado, name='dashboard_profesor_apoderado'),
    path('inicio-apoderado/', inicio_apoderado, name='inicio_apoderado'),
    
    # Vista específica para profesores-apoderados
    path('mis-estudiantes-a-cargo/', estudiantes_a_cargo_profesor_apoderado, name='estudiantes_a_cargo_profesor_apoderado'),
    path('estudiante/<int:estudiante_id>/notas/', ver_notas_estudiante_apoderado, name='ver_notas_estudiante_apoderado'),
    path('estudiante/<int:estudiante_id>/anotaciones/', ver_anotaciones_estudiante_apoderado, name='ver_anotaciones_estudiante_apoderado'),
    path('estudiante/<int:estudiante_id>/horario/', ver_horario_estudiante_apoderado, name='ver_horario_estudiante_apoderado'),
    
    # Calendario
    path('calendario/', calendario, name='calendario'),
    path('calendario/agregar/', agregar_evento, name='agregar_evento'),
    path('calendario/editar/<int:evento_id>/', editar_evento, name='editar_evento'),
    path('calendario/eliminar/<int:evento_id>/', eliminar_evento, name='eliminar_evento'),
    
    # Gestión de Cursos
    path('cursos/', listar_cursos, name='listar_cursos'),
    path('cursos/agregar/', agregar_curso, name='agregar_curso'),
    path('cursos/editar/<int:curso_id>/', editar_curso, name='editar_curso'),
    path('cursos/eliminar/<int:curso_id>/', eliminar_curso, name='eliminar_curso'),
    path('cursos/ver-horario/', ver_horario_curso, name='ver_horario_curso'),
    
    # Sistema de horarios
    path('horarios/', seleccionar_curso_horarios, name='seleccionar_curso_horarios'),
    path('cursos/<int:curso_id>/horarios/', gestionar_horarios, name='gestionar_horarios'),

    # Gestión de Asignaturas
    path('asignaturas/', listar_asignaturas, name='listar_asignaturas'),
    path('asignaturas/agregar/', agregar_asignatura, name='agregar_asignatura'),
    path('asignaturas/editar/<int:asignatura_id>/', editar_asignatura, name='editar_asignatura'),
    path('asignaturas/eliminar/<int:asignatura_id>/', eliminar_asignatura, name='eliminar_asignatura'),
    path('asignaturas/agregar-completa/', agregar_asignatura_completa, name='agregar_asignatura_completa'),
    
    # Gestión de Notas
    path('notas/ingresar/', ingresar_notas, name='ingresar_notas'),
    path('notas/ver/', ver_notas_curso, name='ver_notas_curso'),
    path('notas/asignar-asignaturas-curso/', asignar_asignaturas_curso, name='asignar_asignaturas_curso'),
    path('notas/editar/<int:nota_id>/', editar_nota, name='editar_nota'),
    path('notas/eliminar/<int:nota_id>/', eliminar_nota, name='eliminar_nota'),
    path('notas/agregar/<int:estudiante_id>/<int:asignatura_id>/<str:evaluacion_nombre>/', agregar_nota_individual, name='agregar_nota_individual'),
    
    # Vistas de usuario
    path('mis-horarios/', mis_horarios, name='mis_horarios'),
    path('mi-curso/', mi_curso, name='mi_curso'),
    
    # Gestión de Asistencia
    path('asistencia/alumno/registrar/', registrar_asistencia_alumno, name='registrar_asistencia_alumno'),
    path('asistencia/alumno/ver/', ver_asistencia_alumno, name='ver_asistencia_alumno'),
    path('asistencia/alumno/editar/<int:asistencia_id>/', editar_asistencia_alumno, name='editar_asistencia_alumno'),
    path('asistencia/profesor/registrar/', registrar_asistencia_profesor, name='registrar_asistencia_profesor'),
    path('asistencia/profesor/ver/', ver_asistencia_profesor, name='ver_asistencia_profesor'),
    
    # APIs y AJAX
    path('api/horarios_cursos/', api_horarios_cursos, name='api_horarios_cursos'),
    path('ajax/asignar-profesor/<int:asignatura_id>/', asignar_profesor_asignatura, name='asignar_profesor_asignatura'),
    path('api/asignatura/<int:asignatura_id>/profesores/', obtener_profesores_asignatura, name='obtener_profesores_asignatura'),
    path('ajax/crear-horario/', ajax_crear_horario, name='ajax_crear_horario'),
    path('ajax/editar-horario/', ajax_editar_horario, name='ajax_editar_horario'),
    path('ajax/obtener-horario/', ajax_obtener_horario, name='ajax_obtener_horario'),
    path('ajax/eliminar-horario-nuevo/', ajax_eliminar_horario_nuevo, name='ajax_eliminar_horario_nuevo'),
    
    # Gestión de asignaturas por curso (AJAX)
    path('ajax/gestionar-asignaturas-curso/', gestionar_asignaturas_curso_ajax, name='gestionar_asignaturas_curso_ajax'),
    path('ajax/obtener-asignaturas-curso/<int:curso_id>/', obtener_asignaturas_curso_ajax, name='obtener_asignaturas_curso_ajax'),
    
    # Libro de Anotaciones
    path('anotaciones/', libro_anotaciones, name='libro_anotaciones'),
    path('anotaciones/crear/', crear_anotacion, name='crear_anotacion'),
    path('anotaciones/editar/<int:anotacion_id>/', editar_anotacion, name='editar_anotacion'),
    path('anotaciones/eliminar/<int:anotacion_id>/', eliminar_anotacion, name='eliminar_anotacion'),
    path('anotaciones/estudiante/<int:estudiante_id>/', detalle_comportamiento_estudiante, name='detalle_comportamiento_estudiante'),
    
    # AJAX para anotaciones  
    path('ajax/obtener-estudiantes-curso/', ajax_obtener_estudiantes_curso, name='ajax_obtener_estudiantes_curso'),
    path('ajax/obtener-estudiantes-filtro/', ajax_obtener_estudiantes_filtro, name='ajax_obtener_estudiantes_filtro'),
    # Ruta de edición de asistencia de profesores deshabilitada - Implementación futura
    # path('profesor/asistencia/editar/<int:asistencia_id>/', editar_asistencia_profesor, name='profesor_editar_asistencia'),
]

# Configuración para servir archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) if hasattr(settings, 'MEDIA_ROOT') else []
