from django.contrib import admin
from .models import (
    Estudiante, Profesor, Curso, Asignatura, PeriodoAcademico,
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
