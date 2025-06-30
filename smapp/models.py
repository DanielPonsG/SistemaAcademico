from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class Persona(models.Model):
    """
    Clase base abstracta para reusar campos comunes entre Estudiantes, Profesores, etc.
    No se creará una tabla para esta clase en la base de datos, solo sus herederos.
    """
    TIPOS_DOCUMENTO = [
        ('CC', 'Cédula de Ciudadanía'),
        ('TI', 'Tarjeta de Identidad'),
        ('PA', 'Pasaporte'),
        ('CE', 'Cédula de Extranjería'),
    ]

    primer_nombre = models.CharField(max_length=100)
    segundo_nombre = models.CharField(max_length=100, blank=True, null=True)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100, blank=True, null=True)
    tipo_documento = models.CharField(max_length=2, choices=TIPOS_DOCUMENTO, default='CC')
    numero_documento = models.CharField(max_length=12, unique=True, verbose_name="RUT")  # Cambio a máximo 12 caracteres para RUT
    fecha_nacimiento = models.DateField()
    genero = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')])
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(unique=True)

    class Meta:
        abstract = True # Indica que esta es una clase abstracta

    def __str__(self):
        return f"{self.primer_nombre} {self.apellido_paterno}"

class Estudiante(Persona):
    """
    Modelo para los estudiantes. Hereda de Persona.
    """
    codigo_estudiante = models.CharField(max_length=20, unique=True)
    fecha_ingreso = models.DateField(auto_now_add=True) # Se establece automáticamente al crear
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.codigo_estudiante} - {self.primer_nombre} {self.apellido_paterno}"
    
    def get_nombre_completo(self):
        """Retorna el nombre completo del estudiante"""
        nombres = [self.primer_nombre]
        if self.segundo_nombre:
            nombres.append(self.segundo_nombre)
        nombres.append(self.apellido_paterno)
        if self.apellido_materno:
            nombres.append(self.apellido_materno)
        return ' '.join(nombres)
    
    def get_curso_actual(self):
        """Retorna el curso actual del estudiante"""
        from django.utils import timezone
        return self.cursos.filter(anio=timezone.now().year).first()
    
    @property
    def rut(self):
        """Acceso directo al RUT"""
        return self.numero_documento
    
    def get_puntaje_comportamiento(self, curso=None):
        """Obtiene el puntaje de comportamiento del estudiante"""
        return calcular_puntaje_comportamiento(self, curso)

class Profesor(Persona):
    """
    Modelo para los profesores. Hereda de Persona.
    """
    codigo_profesor = models.CharField(max_length=20, unique=True)
    especialidad = models.CharField(max_length=100)
    fecha_contratacion = models.DateField(auto_now_add=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    asignaturas = models.ManyToManyField('Asignatura', related_name='profesores', blank=True)

    def __str__(self):
        return f"{self.codigo_profesor} - {self.primer_nombre} {self.apellido_paterno}"
    
    def get_nombre_completo(self):
        """Retorna el nombre completo del profesor"""
        nombres = [self.primer_nombre]
        if self.segundo_nombre:
            nombres.append(self.segundo_nombre)
        nombres.append(self.apellido_paterno)
        if self.apellido_materno:
            nombres.append(self.apellido_materno)
        return ' '.join(nombres)
    
    def get_cursos_jefatura(self):
        """Retorna los cursos donde es profesor jefe"""
        return self.cursos_jefatura.all()
    
    def get_asignaturas_responsable(self):
        """Retorna las asignaturas donde es responsable"""
        return self.asignaturas.all()
    
    def get_cursos_asignados(self):
        """Retorna todos los cursos donde tiene asignaturas o es jefe"""
        from django.utils import timezone
        anio_actual = timezone.now().year
        
        # Cursos donde es jefe
        cursos_jefe = self.cursos_jefatura.filter(anio=anio_actual)
        
        # Cursos donde tiene asignaturas como responsable
        cursos_asignaturas = Curso.objects.filter(
            asignaturas__profesor_responsable=self,
            anio=anio_actual
        ).distinct()
        
        # Combinar ambos conjuntos
        return (cursos_jefe | cursos_asignaturas).distinct().order_by('nivel', 'paralelo')
        
        return (cursos_jefe | cursos_asignaturas | cursos_legacy).distinct()

class Curso(models.Model):
    """
    Modelo para los cursos escolares chilenos - Sistema completo: 1° a 8° Básico y 1° a 4° Medio
    """
    NIVELES = [
        # Educación Básica
        ('1B', '1° Básico'),
        ('2B', '2° Básico'),
        ('3B', '3° Básico'),
        ('4B', '4° Básico'),
        ('5B', '5° Básico'),
        ('6B', '6° Básico'),
        ('7B', '7° Básico'),
        ('8B', '8° Básico'),
        # Educación Media
        ('1M', '1° Medio'),
        ('2M', '2° Medio'),
        ('3M', '3° Medio'),
        ('4M', '4° Medio'),
    ]
    
    PARALELOS = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('E', 'E'),
        ('F', 'F'),
    ]
    
    nivel = models.CharField(max_length=2, choices=NIVELES, verbose_name="Nivel", default='1M')
    paralelo = models.CharField(max_length=1, choices=PARALELOS, verbose_name="Paralelo", default='A')
    anio = models.IntegerField(default=timezone.now().year, verbose_name="Año", editable=False)
    profesor_jefe = models.ForeignKey('Profesor', on_delete=models.SET_NULL, null=True, blank=True, related_name='cursos_jefatura', verbose_name="Profesor Jefe")
    estudiantes = models.ManyToManyField('Estudiante', blank=True, related_name='cursos')
    asignaturas = models.ManyToManyField('Asignatura', blank=True, related_name='cursos')

    class Meta:
        unique_together = ('nivel', 'paralelo', 'anio')
        ordering = ['anio', 'nivel', 'paralelo']
    
    @property
    def orden_nivel(self):
        """Retorna un número para ordenar correctamente básica antes que media"""
        if self.nivel.endswith('B'):  # Básico
            return int(self.nivel[0])  # 1B -> 1, 2B -> 2, etc.
        else:  # Medio
            return 10 + int(self.nivel[0])  # 1M -> 11, 2M -> 12, etc.

    @property
    def nombre(self):
        return f"{self.get_nivel_display()}{self.paralelo}"
    
    def clean(self):
        """Validación personalizada del modelo"""
        from django.core.exceptions import ValidationError
        super().clean()
        
    def add_estudiante(self, estudiante):
        """Método seguro para agregar un estudiante al curso"""
        from django.core.exceptions import ValidationError
        
        # Verificar si el estudiante ya está en otro curso del mismo año
        cursos_existentes = Curso.objects.filter(
            estudiantes=estudiante,
            anio=self.anio
        ).exclude(id=self.id)
        
        if cursos_existentes.exists():
            curso_actual = cursos_existentes.first()
            raise ValidationError(
                f'El estudiante {estudiante} ya está asignado al curso {curso_actual} '
                f'para el año {self.anio}. Un estudiante solo puede estar en un curso por año.'
            )
        
        self.estudiantes.add(estudiante)
    
    def __str__(self):
        return f"{self.get_nivel_display()}{self.paralelo} ({self.anio})"

class Asignatura(models.Model):
    """
    Modelo para las asignaturas o materias que componen un curso.
    Un Curso puede tener varias Asignaturas (ej. Matemáticas: Álgebra, Geometría).
    O bien, Asignatura puede ser el nivel más bajo (Matemáticas I, Matemáticas II).
    Si tu escuela tiene "materias" que no son lo mismo que un "curso" general.
    Si no, puedes simplificar y usar solo 'Curso' como la materia a impartir.
    Por simplicidad, vamos a usar 'Asignatura' como la materia que se imparte en un 'Grupo'.
    """
    nombre = models.CharField(max_length=100)
    codigo_asignatura = models.CharField(max_length=10, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    profesor_responsable = models.ForeignKey(
        'Profesor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asignaturas_responsable'  # <-- Cambia esto
    )

    def __str__(self):
        return self.nombre
    
    def get_profesores_display(self):
        """Retorna los profesores asociados a esta asignatura"""
        profesores = []
        
        # Agregar el profesor responsable si existe
        if self.profesor_responsable:
            profesores.append(self.profesor_responsable)
        
        return profesores
    
    def get_cursos_asignados(self):
        """Retorna los cursos del año actual donde está asignada esta asignatura"""
        from django.utils import timezone
        anio_actual = timezone.now().year
        return self.cursos.filter(anio=anio_actual).order_by('nivel', 'paralelo')
    
    def get_cursos_count(self):
        """Retorna el número de cursos del año actual donde está asignada esta asignatura"""
        return self.get_cursos_asignados().count()
    
    def tiene_profesor(self):
        """Retorna True si la asignatura tiene al menos un profesor asignado"""
        return self.profesor_responsable is not None

class Salon(models.Model):
    """
    Modelo para los salones o aulas donde se imparten las clases.
    """
    numero_salon = models.CharField(max_length=10, unique=True)
    capacidad = models.IntegerField()
    ubicacion = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Salón {self.numero_salon}"

class PeriodoAcademico(models.Model):
    """
    Modelo para los periodos académicos (ej. Semestre I 2024, Año Escolar 2024-2025).
    """
    nombre = models.CharField(max_length=100, unique=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Grupo(models.Model):
    """
    Representa una instancia de una Asignatura impartida en un Periodo Académico por un Profesor
    en un Salón, a un conjunto de Estudiantes.
    """
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE)
    profesor = models.ForeignKey(Profesor, on_delete=models.SET_NULL, null=True, blank=True)
    periodo_academico = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE)
    salon = models.ForeignKey(Salon, on_delete=models.SET_NULL, null=True, blank=True)
    estudiantes = models.ManyToManyField(Estudiante, through='Inscripcion') # Relación N:M a través de Inscripcion
    capacidad_maxima = models.IntegerField(default=30)

    def __str__(self):
        return f"{self.asignatura.nombre} - {self.periodo_academico.nombre} ({self.profesor.primer_nombre} {self.profesor.apellido_paterno if self.profesor else 'Sin Profesor'})"

class Inscripcion(models.Model):
    """
    Modelo para registrar la inscripción de un estudiante a un grupo.
    También puede almacenar la calificación final.
    """
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE)
    fecha_inscripcion = models.DateField(auto_now_add=True)
    calificacion_final = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('estudiante', 'grupo') # Un estudiante no puede inscribirse dos veces al mismo grupo

    def __str__(self):
        return f"Inscripción de {self.estudiante} en {self.grupo}"

class Calificacion(models.Model):
    """
    Modelo para registrar calificaciones específicas dentro de un grupo para un estudiante.
    Podría ser para parciales, tareas, exámenes, etc.
    """
    inscripcion = models.ForeignKey(Inscripcion, on_delete=models.CASCADE)
    nombre_evaluacion = models.CharField(max_length=100) # Ej. 'Primer Parcial', 'Tarea 1', etc.
    puntaje = models.DecimalField(max_digits=5, decimal_places=2)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Nuevo campo
    detalle = models.CharField(max_length=255, blank=True, null=True)            # Nuevo campo
    descripcion = models.TextField(blank=True, null=True)                        # Nuevo campo
    fecha_evaluacion = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.inscripcion.estudiante} - {self.inscripcion.grupo.asignatura.nombre} - {self.nombre_evaluacion}: {self.puntaje}"

class EventoCalendario(models.Model):
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
    ]
    
    TIPO_EVENTO_CHOICES = [
        ('general', 'Evento General'),
        ('evaluacion', 'Evaluación/Prueba'),
        ('reunion', 'Reunión'),
        ('actividad', 'Actividad Escolar'),
        ('administrativo', 'Administrativo'),
        ('otro', 'Otro'),
    ]
    
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    fecha = models.DateField()
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fin = models.TimeField(null=True, blank=True)
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='media')
    tipo_evento = models.CharField(max_length=15, choices=TIPO_EVENTO_CHOICES, default='general')
    
    # Asignación a cursos
    cursos = models.ManyToManyField('Curso', blank=True, related_name='eventos')
    para_todos_los_cursos = models.BooleanField(default=False, verbose_name='Para todos los cursos')
    solo_profesores = models.BooleanField(default=False, verbose_name='Solo para profesores')
    
    # Quien creó el evento
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='eventos_creados', null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha', '-hora_inicio']
        verbose_name = "Evento de Calendario"
        verbose_name_plural = "Eventos de Calendario"

    def __str__(self):
        return f"{self.titulo} ({self.fecha})"
    
    @property
    def es_evaluacion(self):
        """Indica si el evento es una evaluación"""
        return self.tipo_evento == 'evaluacion'
    
    @property
    def color_por_tipo(self):
        """Retorna color para el calendario según el tipo"""
        colores = {
            'evaluacion': '#e74c3c',     # Rojo suave para evaluaciones
            'reunion': '#3498db',        # Azul suave para reuniones
            'actividad': '#2ecc71',      # Verde suave para actividades
            'general': '#9b59b6',        # Púrpura suave para eventos generales
            'administrativo': '#f39c12', # Naranja suave para administrativo
            'otro': '#95a5a6'            # Gris suave para otros
        }
        return colores.get(self.tipo_evento, '#95a5a6')

class HorarioCurso(models.Model):
    DIAS_SEMANA = [
        ('LU', 'Lunes'),
        ('MA', 'Martes'),
        ('MI', 'Miércoles'),
        ('JU', 'Jueves'),
        ('VI', 'Viernes'),
        ('SA', 'Sábado'),
        ('DO', 'Domingo'),
    ]
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='horarios')
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='horarios', null=True, blank=True)  # <-- AGREGAR ESTA LÍNEA
    dia = models.CharField(max_length=2, choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    def __str__(self):
        return f"{self.get_dia_display()} {self.hora_inicio} - {self.hora_fin} ({self.curso.nombre})"

class Perfil(models.Model):
    TIPOS_USUARIO = [
        ('director', 'Director'),
        ('profesor', 'Profesor'),
        ('alumno', 'Alumno'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tipo_usuario = models.CharField(max_length=10, choices=TIPOS_USUARIO)

    def __str__(self):
        return f"{self.user.username} ({self.get_tipo_usuario_display()})"

class AsistenciaAlumno(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='asistencias')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='asistencias_alumnos')
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='asistencias_alumnos')
    fecha = models.DateField(default=timezone.now)
    presente = models.BooleanField(default=True)
    observacion = models.CharField(max_length=255, blank=True, null=True)
    justificacion = models.TextField(blank=True, null=True, help_text='Justificación en caso de ausencia')
    
    # Campos de registro
    hora_registro = models.TimeField(default=timezone.now)
    profesor_registro = models.ForeignKey(Profesor, on_delete=models.CASCADE, related_name='asistencias_registradas', null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('estudiante', 'curso', 'asignatura', 'fecha')
        ordering = ['-fecha', 'estudiante__primer_nombre']

    def __str__(self):
        return f"{self.estudiante} - {self.asignatura} - {self.fecha} - {'Presente' if self.presente else 'Ausente'}"
    
    @property
    def rut(self):
        """Acceso directo al RUT del estudiante"""
        return self.estudiante.numero_documento

class AsistenciaProfesor(models.Model):
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE)
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, null=True, blank=True)  # <--- Cambia aquí
    fecha = models.DateField(default=timezone.now)
    presente = models.BooleanField(default=True)
    observacion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('profesor', 'asignatura', 'fecha')

    def __str__(self):
        return f"{self.profesor} - {self.asignatura} - {self.fecha} - {'Presente' if self.presente else 'Ausente'}"

class Anotacion(models.Model):
    """
    Modelo para el libro de anotaciones con comportamiento positivo y negativo
    """
    TIPOS_ANOTACION = [
        ('positiva', 'Positiva'),
        ('negativa', 'Negativa'),
        ('neutra', 'Neutra'),
    ]
    
    CATEGORIAS = [
        ('comportamiento', 'Comportamiento'),
        ('rendimiento', 'Rendimiento Académico'),
        ('disciplina', 'Disciplina'),
        ('participacion', 'Participación'),
        ('puntualidad', 'Puntualidad'),
        ('responsabilidad', 'Responsabilidad'),
        ('colaboracion', 'Colaboración'),
        ('actitud', 'Actitud'),
        ('otro', 'Otro'),
    ]
    
    # Puntajes estándar por tipo
    PUNTAJES_ESTANDAR = {
        'positiva': 5,
        'negativa': -3,
        'neutra': 0,
    }
    
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='anotaciones')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='anotaciones')
    asignatura = models.ForeignKey(Asignatura, on_delete=models.SET_NULL, null=True, blank=True, related_name='anotaciones')
    profesor_autor = models.ForeignKey(Profesor, on_delete=models.CASCADE, related_name='anotaciones_creadas')
    
    tipo = models.CharField(max_length=10, choices=TIPOS_ANOTACION, default='neutra')
    categoria = models.CharField(max_length=15, choices=CATEGORIAS, default='comportamiento')
    titulo = models.CharField(max_length=200, verbose_name='Título de la anotación')
    descripcion = models.TextField(verbose_name='Descripción detallada')
    
    # Sistema de puntuación
    puntos = models.IntegerField(
        default=0, 
        help_text='Puntos asignados: positivos para buen comportamiento, negativos para mal comportamiento'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    # Campos adicionales
    es_grave = models.BooleanField(default=False, verbose_name='Anotación grave')
    requiere_atencion_apoderado = models.BooleanField(default=False, verbose_name='Requiere atención del apoderado')
    comunicado_apoderado = models.BooleanField(default=False, verbose_name='Apoderado comunicado')
    fecha_comunicacion_apoderado = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = "Anotación"
        verbose_name_plural = "Anotaciones"
    
    def save(self, *args, **kwargs):
        """Override save para asignar puntos automáticamente si no se especifican"""
        if self.puntos == 0 and self.tipo in self.PUNTAJES_ESTANDAR:
            self.puntos = self.PUNTAJES_ESTANDAR[self.tipo]
            
            # Ajustar puntos si es grave
            if self.es_grave and self.tipo == 'negativa':
                self.puntos = self.puntos * 2  # Duplicar puntos negativos si es grave
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.estudiante.get_nombre_completo()} - {self.get_tipo_display()}: {self.titulo}"
    
    @property
    def color_tipo(self):
        """Retorna color según el tipo de anotación"""
        colores = {
            'positiva': '#28a745',   # Verde
            'negativa': '#dc3545',   # Rojo
            'neutra': '#6c757d'      # Gris
        }
        return colores.get(self.tipo, '#6c757d')
    
    @property
    def icono_tipo(self):
        """Retorna icono Font Awesome según el tipo"""
        iconos = {
            'positiva': 'fa-thumbs-up',
            'negativa': 'fa-thumbs-down',
            'neutra': 'fa-info-circle'
        }
        return iconos.get(self.tipo, 'fa-info-circle')
    
    @property
    def fecha_para_humanos(self):
        """Retorna fecha en formato legible"""
        from django.utils import timezone
        ahora = timezone.now()
        diferencia = ahora - self.fecha_creacion
        
        if diferencia.days == 0:
            if diferencia.seconds < 3600:  # Menos de 1 hora
                minutos = diferencia.seconds // 60
                return f"Hace {minutos} minutos"
            else:
                horas = diferencia.seconds // 3600
                return f"Hace {horas} horas"
        elif diferencia.days == 1:
            return "Ayer"
        elif diferencia.days < 7:
            return f"Hace {diferencia.days} días"
        else:
            return self.fecha_creacion.strftime("%d/%m/%Y")

# Función para calcular puntaje total de comportamiento
def calcular_puntaje_comportamiento(estudiante, curso=None, fecha_desde=None, fecha_hasta=None):
    """
    Calcula el puntaje total de comportamiento de un estudiante
    """
    from django.db.models import Sum
    from django.utils import timezone
    
    anotaciones = Anotacion.objects.filter(estudiante=estudiante)
    
    if curso:
        anotaciones = anotaciones.filter(curso=curso)
    
    if fecha_desde:
        anotaciones = anotaciones.filter(fecha_creacion__gte=fecha_desde)
    
    if fecha_hasta:
        anotaciones = anotaciones.filter(fecha_creacion__lte=fecha_hasta)
    
    puntaje_total = anotaciones.aggregate(total=Sum('puntos'))['total'] or 0
    
    # Obtener estadísticas
    stats = {
        'puntaje_total': puntaje_total,
        'total_anotaciones': anotaciones.count(),
        'positivas': anotaciones.filter(tipo='positiva').count(),
        'negativas': anotaciones.filter(tipo='negativa').count(),
        'neutras': anotaciones.filter(tipo='neutra').count(),
        'graves': anotaciones.filter(es_grave=True).count(),
    }
    
    # Determinar nivel de comportamiento
    if puntaje_total >= 20:
        stats['nivel'] = 'Excelente'
        stats['color'] = '#28a745'
    elif puntaje_total >= 10:
        stats['nivel'] = 'Bueno'
        stats['color'] = '#20c997'
    elif puntaje_total >= 0:
        stats['nivel'] = 'Regular'
        stats['color'] = '#ffc107'
    elif puntaje_total >= -10:
        stats['nivel'] = 'Malo'
        stats['color'] = '#fd7e14'
    else:
        stats['nivel'] = 'Muy Malo'
        stats['color'] = '#dc3545'
    
    return stats


