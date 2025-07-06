from django.contrib import admin
from .models import (
    Estudiante, Profesor, Apoderado, RelacionApoderadoEstudiante, Curso, Asignatura, PeriodoAcademico,
    Grupo, Inscripcion, Calificacion, EventoCalendario, HorarioCurso, Perfil, Salon
)

# Register your models here.
admin.site.register(Profesor)
admin.site.register(Curso)
admin.site.register(Asignatura)
admin.site.register(PeriodoAcademico)
admin.site.register(Grupo)
admin.site.register(Inscripcion)
admin.site.register(Calificacion)
admin.site.register(EventoCalendario)
admin.site.register(HorarioCurso)
admin.site.register(Perfil)
admin.site.register(Salon)

class EstudianteAdmin(admin.ModelAdmin):
    list_display = ('codigo_estudiante', 'primer_nombre', 'apellido_paterno', 'email')

admin.site.register(Estudiante, EstudianteAdmin)

class ApoderadoAdmin(admin.ModelAdmin):
    list_display = ('codigo_apoderado', 'primer_nombre', 'apellido_paterno', 'parentesco_principal', 'get_numero_estudiantes', 'activo')
    list_filter = ('parentesco_principal', 'activo', 'fecha_registro')
    search_fields = ('primer_nombre', 'apellido_paterno', 'numero_documento', 'codigo_apoderado', 'email')
    readonly_fields = ('fecha_registro',)
    
    def get_numero_estudiantes(self, obj):
        return obj.get_numero_estudiantes()
    get_numero_estudiantes.short_description = 'Estudiantes a cargo'

admin.site.register(Apoderado, ApoderadoAdmin)

class RelacionApoderadoEstudianteAdmin(admin.ModelAdmin):
    list_display = ('apoderado', 'estudiante', 'parentesco', 'es_apoderado_principal', 'activa', 'fecha_asignacion')
    list_filter = ('parentesco', 'es_apoderado_principal', 'activa', 'fecha_asignacion')
    search_fields = ('apoderado__primer_nombre', 'apoderado__apellido_paterno', 'estudiante__primer_nombre', 'estudiante__apellido_paterno')

admin.site.register(RelacionApoderadoEstudiante, RelacionApoderadoEstudianteAdmin)
