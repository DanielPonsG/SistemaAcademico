from django.contrib import admin
from .models import *

# Configuración del sitio admin
admin.site.site_header = "Sistema Académico SAM - Administración"
admin.site.site_title = "SAM Admin"
admin.site.index_title = "Panel de Administración"

# ==================== ESTUDIANTES ====================
@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ('codigo_estudiante', 'primer_nombre', 'apellido_paterno', 'email', 'fecha_ingreso')
    list_filter = ('fecha_ingreso', 'genero', 'tipo_documento')
    search_fields = ('codigo_estudiante', 'primer_nombre', 'apellido_paterno', 'numero_documento', 'email')
    readonly_fields = ('fecha_ingreso',)
    ordering = ('codigo_estudiante',)
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('primer_nombre', 'segundo_nombre', 'apellido_paterno', 'apellido_materno')
        }),
        ('Identificación', {
            'fields': ('tipo_documento', 'numero_documento', 'codigo_estudiante')
        }),
        ('Contacto', {
            'fields': ('email', 'telefono', 'direccion')
        }),
        ('Datos Académicos', {
            'fields': ('fecha_ingreso', 'user')
        }),
        ('Información Adicional', {
            'fields': ('fecha_nacimiento', 'genero'),
            'classes': ('collapse',)
        })
    )

# ==================== PROFESORES ====================
@admin.register(Profesor)
class ProfesorAdmin(admin.ModelAdmin):
    list_display = ('codigo_profesor', 'primer_nombre', 'apellido_paterno', 'especialidad', 'fecha_contratacion')
    list_filter = ('especialidad', 'fecha_contratacion')
    search_fields = ('codigo_profesor', 'primer_nombre', 'apellido_paterno', 'numero_documento', 'email')
    readonly_fields = ('fecha_contratacion',)
    filter_horizontal = ('asignaturas',)
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('primer_nombre', 'segundo_nombre', 'apellido_paterno', 'apellido_materno')
        }),
        ('Identificación', {
            'fields': ('tipo_documento', 'numero_documento', 'codigo_profesor')
        }),
        ('Contacto', {
            'fields': ('email', 'telefono', 'direccion')
        }),
        ('Información Profesional', {
            'fields': ('especialidad', 'fecha_contratacion', 'asignaturas')
        }),
        ('Sistema', {
            'fields': ('user',),
            'classes': ('collapse',)
        }),
        ('Información Adicional', {
            'fields': ('fecha_nacimiento', 'genero'),
            'classes': ('collapse',)
        })
    )

# ==================== APODERADOS ====================
@admin.register(Apoderado)
class ApoderadoAdmin(admin.ModelAdmin):
    list_display = ('codigo_apoderado', 'primer_nombre', 'apellido_paterno', 'parentesco_principal', 'activo')
    list_filter = ('parentesco_principal', 'activo', 'ocupacion')
    search_fields = ('codigo_apoderado', 'primer_nombre', 'apellido_paterno', 'numero_documento')
    readonly_fields = ('fecha_registro',)

# ==================== RELACION APODERADO ESTUDIANTE ====================
@admin.register(RelacionApoderadoEstudiante)
class RelacionApoderadoEstudianteAdmin(admin.ModelAdmin):
    list_display = ('apoderado', 'estudiante', 'parentesco', 'es_apoderado_principal', 'activa')
    list_filter = ('parentesco', 'es_apoderado_principal', 'activa')
    search_fields = ('apoderado__primer_nombre', 'estudiante__primer_nombre')

# ==================== CURSOS ====================
@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'nivel', 'paralelo', 'anio', 'profesor_jefe')
    list_filter = ('nivel', 'paralelo', 'anio')
    search_fields = ('nivel', 'paralelo')
    filter_horizontal = ('estudiantes', 'asignaturas')

# ==================== ASIGNATURAS ====================
@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo_asignatura', 'profesor_responsable')
    list_filter = ('profesor_responsable',)
    search_fields = ('nombre', 'codigo_asignatura', 'descripcion')

# ==================== SALONES ====================
@admin.register(Salon)
class SalonAdmin(admin.ModelAdmin):
    list_display = ('numero_salon', 'capacidad', 'ubicacion')
    list_filter = ('capacidad',)
    search_fields = ('numero_salon', 'ubicacion')

# ==================== PERIODO ACADEMICO ====================
@admin.register(PeriodoAcademico)
class PeriodoAcademicoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_inicio', 'fecha_fin', 'activo')
    list_filter = ('activo', 'fecha_inicio')
    search_fields = ('nombre',)

# ==================== GRUPOS ====================
@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = ('asignatura', 'profesor', 'periodo_academico', 'capacidad_maxima')
    list_filter = ('periodo_academico', 'asignatura')
    search_fields = ('asignatura__nombre', 'profesor__primer_nombre')

# ==================== INSCRIPCIONES ====================
@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'grupo', 'fecha_inscripcion', 'calificacion_final')
    list_filter = ('fecha_inscripcion',)
    search_fields = ('estudiante__primer_nombre', 'grupo__asignatura__nombre')

# ==================== CALIFICACIONES ====================
@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ('inscripcion', 'nombre_evaluacion', 'puntaje', 'porcentaje', 'fecha_evaluacion')
    list_filter = ('fecha_evaluacion', 'porcentaje')
    search_fields = ('nombre_evaluacion',)

# ==================== EVENTOS CALENDARIO ====================
@admin.register(EventoCalendario)
class EventoCalendarioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'fecha', 'hora_inicio', 'hora_fin', 'prioridad', 'tipo_evento')
    list_filter = ('prioridad', 'fecha', 'tipo_evento')
    search_fields = ('titulo', 'descripcion')
    date_hierarchy = 'fecha'
    filter_horizontal = ('cursos',)

# ==================== HORARIOS ====================
@admin.register(HorarioCurso)
class HorarioCursoAdmin(admin.ModelAdmin):
    list_display = ('curso', 'asignatura', 'dia', 'hora_inicio', 'hora_fin')
    list_filter = ('dia', 'curso__nivel')
    search_fields = ('curso__nivel', 'asignatura__nombre')

# ==================== PERFILES ====================
@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'tipo_usuario')
    list_filter = ('tipo_usuario',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

# ==================== ASISTENCIA ALUMNOS ====================
@admin.register(AsistenciaAlumno)
class AsistenciaAlumnoAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'curso', 'asignatura', 'presente', 'fecha')
    list_filter = ('presente', 'fecha')
    search_fields = ('estudiante__primer_nombre', 'estudiante__apellido_paterno')
    date_hierarchy = 'fecha'

# ==================== ASISTENCIA PROFESORES ====================
@admin.register(AsistenciaProfesor)
class AsistenciaProfesorAdmin(admin.ModelAdmin):
    list_display = ('profesor', 'asignatura', 'curso', 'fecha', 'presente')
    list_filter = ('fecha', 'presente')
    search_fields = ('profesor__primer_nombre', 'profesor__apellido_paterno')
    date_hierarchy = 'fecha'

# ==================== ANOTACIONES ====================
@admin.register(Anotacion)
class AnotacionAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'tipo', 'categoria', 'titulo', 'profesor_autor', 'fecha_creacion')
    list_filter = ('tipo', 'categoria', 'es_grave', 'fecha_creacion')
    search_fields = ('estudiante__primer_nombre', 'estudiante__apellido_paterno', 'titulo')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    date_hierarchy = 'fecha_creacion'