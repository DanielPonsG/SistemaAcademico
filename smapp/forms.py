from django import forms
from .models import Estudiante, Profesor, EventoCalendario, Curso, HorarioCurso, Asignatura, Inscripcion, Calificacion, Grupo, PeriodoAcademico, AsistenciaAlumno, AsistenciaProfesor, Anotacion
from datetime import date, timedelta
from django.utils import timezone

def validar_rut(rut):
    """Validar formato y dígito verificador del RUT chileno"""
    # Limpiar el RUT
    rut = rut.replace(".", "").replace("-", "").upper()
    
    if len(rut) < 2:
        return False
    
    # Separar número y dígito verificador
    numero = rut[:-1]
    dv = rut[-1]
    
    # Validar que el número contenga solo dígitos
    if not numero.isdigit():
        return False
    
    # Calcular dígito verificador
    suma = 0
    multiplicador = 2
    
    for digit in reversed(numero):
        suma += int(digit) * multiplicador
        multiplicador += 1
        if multiplicador > 7:
            multiplicador = 2
    
    resto = suma % 11
    dv_calculado = 11 - resto
    
    if dv_calculado == 11:
        dv_calculado = '0'
    elif dv_calculado == 10:
        dv_calculado = 'K'
    else:
        dv_calculado = str(dv_calculado)
    
    return dv == dv_calculado

def formatear_rut(rut):
    """Formatear RUT con puntos y guión"""
    # Limpiar el RUT
    rut = rut.replace(".", "").replace("-", "").upper()
    
    if len(rut) < 2:
        return rut
    
    # Separar número y dígito verificador
    numero = rut[:-1]
    dv = rut[-1]
    
    # Formatear con puntos
    numero_formateado = ""
    for i, digit in enumerate(reversed(numero)):
        if i > 0 and i % 3 == 0:
            numero_formateado = "." + numero_formateado
        numero_formateado = digit + numero_formateado
    
    return f"{numero_formateado}-{dv}"

def calcular_edad(fecha_nacimiento):
    """Calcular edad en años a partir de la fecha de nacimiento"""
    hoy = date.today()
    edad = hoy.year - fecha_nacimiento.year
    
    # Ajustar si aún no ha cumplido años este año
    if hoy.month < fecha_nacimiento.month or (hoy.month == fecha_nacimiento.month and hoy.day < fecha_nacimiento.day):
        edad -= 1
    
    return edad

class EstudianteForm(forms.ModelForm):
    username = forms.CharField(
        label="Nombre de usuario",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese nombre de usuario'
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese contraseña'
        })
    )

    class Meta:
        model = Estudiante
        fields = [
            'primer_nombre', 'segundo_nombre', 'apellido_paterno', 'apellido_materno',
            'tipo_documento', 'numero_documento', 'fecha_nacimiento', 'genero',
            'direccion', 'telefono', 'email', 'codigo_estudiante'
        ]
        widgets = {
            'primer_nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Primer nombre'
            }),
            'segundo_nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Segundo nombre (opcional)'
            }),
            'apellido_paterno': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido paterno'
            }),
            'apellido_materno': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido materno (opcional)'
            }),
            'tipo_documento': forms.Select(attrs={
                'class': 'form-control'
            }),
            'numero_documento': forms.TextInput(attrs={
                'class': 'form-control rut-input',
                'placeholder': '12345678-9',
                'maxlength': '12',
                'pattern': '[0-9]{1,2}[0-9]{3}[0-9]{3}-[0-9kK]{1}'
            }),
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'genero': forms.Select(attrs={
                'class': 'form-control'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección completa'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+56912345678'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'codigo_estudiante': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'EST001'
            })
        }
        labels = {
            'numero_documento': 'RUT',
            'codigo_estudiante': 'Código de Estudiante'
        }

    def clean_numero_documento(self):
        rut = self.cleaned_data.get('numero_documento')
        if rut:
            # Validar formato y dígito verificador del RUT
            if not validar_rut(rut):
                raise forms.ValidationError('RUT inválido. Formato esperado: 12345678-9')
            # Formatear correctamente
            rut = formatear_rut(rut)
        return rut

    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        if fecha_nacimiento:
            edad = calcular_edad(fecha_nacimiento)
            # Validar edad mínima (3 años) y máxima (25 años) para estudiantes
            if edad < 3:
                raise forms.ValidationError(
                    f"El estudiante debe tener al menos 3 años. Edad actual: {edad} años."
                )
            elif edad > 25:
                raise forms.ValidationError(
                    f"El estudiante no puede tener más de 25 años. Edad actual: {edad} años."
                )
                
        return fecha_nacimiento

class ProfesorForm(forms.ModelForm):
    username = forms.CharField(
        label="Nombre de usuario",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese nombre de usuario'
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese contraseña'
        })
    )

    class Meta:
        model = Profesor
        fields = [
            'primer_nombre', 'segundo_nombre', 'apellido_paterno', 'apellido_materno',
            'tipo_documento', 'numero_documento', 'fecha_nacimiento', 'genero',
            'direccion', 'telefono', 'email', 'codigo_profesor', 'especialidad'
        ]
        widgets = {
            'primer_nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Primer nombre'
            }),
            'segundo_nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Segundo nombre (opcional)'
            }),
            'apellido_paterno': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido paterno'
            }),
            'apellido_materno': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido materno (opcional)'
            }),
            'tipo_documento': forms.Select(attrs={
                'class': 'form-control'
            }),
            'numero_documento': forms.TextInput(attrs={
                'class': 'form-control rut-input',
                'placeholder': '12345678-9',
                'maxlength': '12',
                'pattern': '[0-9]{1,2}[0-9]{3}[0-9]{3}-[0-9kK]{1}'
            }),
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'genero': forms.Select(attrs={
                'class': 'form-control'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección completa'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+56912345678'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'codigo_profesor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'PROF001'
            }),
            'especialidad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Matemáticas, Historia, etc.'
            })
        }
        labels = {
            'numero_documento': 'RUT',
            'codigo_profesor': 'Código de Profesor'
        }

    def clean_numero_documento(self):
        rut = self.cleaned_data.get('numero_documento')
        if rut:
            # Validar formato y dígito verificador del RUT
            if not validar_rut(rut):
                raise forms.ValidationError('RUT inválido. Formato esperado: 12345678-9')
            # Formatear correctamente
            rut = formatear_rut(rut)
        return rut

    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        if fecha_nacimiento:
            edad = calcular_edad(fecha_nacimiento)
            # Validar edad mínima (22 años) y máxima (70 años) para profesores
            if edad < 22:
                raise forms.ValidationError(
                    f"El profesor debe tener al menos 22 años (título universitario). Edad actual: {edad} años."
                )
            elif edad > 70:
                raise forms.ValidationError(
                    f"El profesor no puede tener más de 70 años (edad de jubilación). Edad actual: {edad} años."
                )
            
            # Validar que la fecha no sea futura
            if fecha_nacimiento > date.today():
                raise forms.ValidationError("La fecha de nacimiento no puede ser en el futuro.")
                
        return fecha_nacimiento

class EventoCalendarioForm(forms.ModelForm):
    # Campo para seleccionar cursos específicos
    cursos_especificos = forms.ModelMultipleChoiceField(
        queryset=Curso.objects.none(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'multiple': True,
            'size': '6'
        }),
        label='Cursos específicos',
        required=False,
        help_text='Selecciona los cursos que verán este evento (opcional si es para todos)'
    )
    
    class Meta:
        model = EventoCalendario
        fields = ['titulo', 'descripcion', 'fecha', 'hora_inicio', 'hora_fin', 
                 'tipo_evento', 'prioridad', 'para_todos_los_cursos']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del evento'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada del evento'
            }),
            'fecha': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'hora_inicio': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'hora_fin': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'tipo_evento': forms.Select(attrs={
                'class': 'form-select'
            }),
            'prioridad': forms.Select(attrs={
                'class': 'form-select'
            }),
            'para_todos_los_cursos': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Configurar cursos disponibles según el tipo de usuario
            anio_actual = timezone.now().year
            
            if user.is_superuser or user.groups.filter(name='Director').exists():
                # Admin y Director ven todos los cursos
                cursos_disponibles = Curso.objects.filter(anio=anio_actual)
            elif hasattr(user, 'profesor'):
                # Profesores solo ven sus cursos (como jefe o con asignaturas)
                cursos_jefe = user.profesor.cursos_jefatura.filter(anio=anio_actual)
                cursos_asignaturas = Curso.objects.filter(
                    asignaturas__profesor_responsable=user.profesor,
                    anio=anio_actual
                )
                cursos_disponibles = (cursos_jefe | cursos_asignaturas).distinct()
            else:
                cursos_disponibles = Curso.objects.none()
            
            self.fields['cursos_especificos'].queryset = cursos_disponibles.order_by('nivel', 'paralelo')
    
    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')
        para_todos = cleaned_data.get('para_todos_los_cursos')
        cursos_especificos = cleaned_data.get('cursos_especificos')
        
        # Validar fecha no sea en el pasado
        if fecha and fecha < timezone.now().date():
            raise forms.ValidationError(
                'La fecha del evento no puede ser en el pasado.'
            )
        
        # Validar horarios
        if hora_inicio and hora_fin and hora_inicio >= hora_fin:
            raise forms.ValidationError(
                'La hora de inicio debe ser anterior a la hora de fin.'
            )
        
        # Validar asignación de cursos
        if not para_todos and not cursos_especificos:
            raise forms.ValidationError(
                'Debes seleccionar al menos un curso específico o marcar "Para todos los cursos".'
            )
        
        return cleaned_data
    
    def save(self, commit=True, user=None):
        evento = super().save(commit=False)
        
        if user:
            evento.creado_por = user
        
        if commit:
            evento.save()
            
            # Asignar cursos específicos si no es para todos
            if not evento.para_todos_los_cursos:
                cursos_especificos = self.cleaned_data.get('cursos_especificos', [])
                evento.cursos.set(cursos_especificos)
            else:
                evento.cursos.clear()
        
        return evento

class CursoForm(forms.ModelForm):
    # Campo para crear nueva asignatura directamente (opcional)
    nueva_asignatura = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Opcional: Crear nueva asignatura'
        }),
        label='Nueva Asignatura',
        help_text='Si especificas una nueva asignatura, se creará automáticamente y se asignará al curso'
    )
    
    class Meta:
        model = Curso
        fields = ['nivel', 'paralelo', 'profesor_jefe', 'estudiantes', 'asignaturas']
        widgets = {
            'nivel': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'paralelo': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'profesor_jefe': forms.Select(attrs={
                'class': 'form-select'
            }),
            'estudiantes': forms.SelectMultiple(attrs={
                'class': 'form-select curso-estudiantes',
                'size': '12',
                'style': 'height: 300px;'
            }),
            'asignaturas': forms.SelectMultiple(attrs={
                'class': 'form-select curso-asignaturas',
                'size': '8',
                'style': 'height: 200px;'
            })
        }
        labels = {
            'nivel': 'Nivel *',
            'paralelo': 'Paralelo *',
            'profesor_jefe': 'Profesor Jefe',
            'estudiantes': 'Estudiantes del Curso',
            'asignaturas': 'Asignaturas del Curso'
        }
        help_texts = {
            'estudiantes': 'Mantén presionado Ctrl (Cmd en Mac) para seleccionar múltiples estudiantes',
            'asignaturas': 'Mantén presionado Ctrl (Cmd en Mac) para seleccionar múltiples asignaturas'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar queryset para mostrar información más útil
        self.fields['profesor_jefe'].queryset = Profesor.objects.all().order_by('primer_nombre', 'apellido_paterno')
        self.fields['profesor_jefe'].empty_label = "-- Seleccionar Profesor Jefe (Opcional) --"
        
        # Filtrar estudiantes para mostrar solo los que NO están asignados a ningún curso del año actual
        anio_actual = timezone.now().year
        
        # Obtener IDs de estudiantes que ya están en algún curso del año actual
        # Usando la relación ManyToMany correctamente
        cursos_actuales = Curso.objects.filter(anio=anio_actual)
        
        # Si estamos editando un curso existente, excluirlo del filtro
        if self.instance and self.instance.pk:
            cursos_actuales = cursos_actuales.exclude(pk=self.instance.pk)
        
        # Obtener todos los estudiantes asignados a estos cursos
        estudiantes_asignados_ids = []
        for curso in cursos_actuales:
            estudiantes_curso = list(curso.estudiantes.values_list('id', flat=True))
            estudiantes_asignados_ids.extend(estudiantes_curso)
        
        # Convertir a set para eliminar duplicados
        estudiantes_asignados_ids = set(estudiantes_asignados_ids)
        
        # Filtrar estudiantes disponibles (no asignados)
        estudiantes_disponibles = Estudiante.objects.exclude(
            id__in=estudiantes_asignados_ids
        ).order_by('primer_nombre', 'apellido_paterno')
        
        # Si estamos editando un curso existente, incluir también sus estudiantes actuales
        if self.instance and self.instance.pk:
            estudiantes_del_curso = self.instance.estudiantes.all()
            estudiantes_disponibles = (estudiantes_disponibles | estudiantes_del_curso).distinct().order_by('primer_nombre', 'apellido_paterno')
        
        self.fields['estudiantes'].queryset = estudiantes_disponibles
        self.fields['asignaturas'].queryset = Asignatura.objects.all().order_by('nombre')
        
        # Hacer que ciertos campos no sean requeridos
        self.fields['profesor_jefe'].required = False
        self.fields['estudiantes'].required = False
        self.fields['asignaturas'].required = False
        
        # Campos requeridos
        self.fields['nivel'].required = True
        self.fields['paralelo'].required = True

    def clean(self):
        cleaned_data = super().clean()
        nivel = cleaned_data.get('nivel')
        paralelo = cleaned_data.get('paralelo')
        estudiantes = cleaned_data.get('estudiantes')
        anio_actual = timezone.now().year
        
        if nivel and paralelo:
            # Verificar que no exista otro curso con la misma combinación en el año actual
            existing_curso = Curso.objects.filter(
                nivel=nivel,
                paralelo=paralelo,
                anio=anio_actual
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing_curso.exists():
                raise forms.ValidationError(
                    f'Ya existe un curso {dict(Curso.NIVELES)[nivel]}{paralelo} para el año {anio_actual}. '
                    'Cada curso debe tener una combinación única de nivel y paralelo.'
                )
        
        # Validación adicional por seguridad (aunque el formulario ya filtra estudiantes disponibles)
        if estudiantes:
            estudiantes_con_curso = []
            for estudiante in estudiantes:
                # Buscar si el estudiante ya está en otro curso del año actual
                cursos_existentes = Curso.objects.filter(
                    estudiantes=estudiante,
                    anio=anio_actual
                ).exclude(pk=self.instance.pk if self.instance else None)
                
                if cursos_existentes.exists():
                    curso_actual = cursos_existentes.first()
                    estudiantes_con_curso.append(
                        f'{estudiante.primer_nombre} {estudiante.apellido_paterno} '
                        f'(ya está en {curso_actual.get_nivel_display()}{curso_actual.paralelo})'
                    )
            
            if estudiantes_con_curso:
                # Esto no debería suceder si el formulario está funcionando correctamente
                error_msg = 'Error interno: Se seleccionaron estudiantes ya asignados. Por favor, recarga la página e intenta nuevamente.'
                raise forms.ValidationError(error_msg)
        
        return cleaned_data
    
    def clean_nueva_asignatura(self):
        nueva_asignatura = self.cleaned_data.get('nueva_asignatura')
        if nueva_asignatura:
            nueva_asignatura = nueva_asignatura.strip()
            # Verificar que no exista ya una asignatura con ese nombre
            if Asignatura.objects.filter(nombre__iexact=nueva_asignatura).exists():
                raise forms.ValidationError('Ya existe una asignatura con este nombre. Selecciónala de la lista en lugar de crear una nueva.')
        return nueva_asignatura
    
    def save(self, commit=True):
        curso = super().save(commit=commit)
        
        if commit:
            # Crear nueva asignatura si se especificó
            nueva_asignatura_nombre = self.cleaned_data.get('nueva_asignatura')
            if nueva_asignatura_nombre:
                # Generar código automático para la nueva asignatura
                import re
                codigo_base = re.sub(r'[^A-Z0-9]', '', nueva_asignatura_nombre.upper())[:6]
                contador = 1
                codigo_asignatura = f"{codigo_base}{contador:02d}"
                
                # Asegurar que el código sea único
                while Asignatura.objects.filter(codigo_asignatura=codigo_asignatura).exists():
                    contador += 1
                    codigo_asignatura = f"{codigo_base}{contador:02d}"
                
                # Crear la nueva asignatura
                nueva_asignatura = Asignatura.objects.create(
                    nombre=nueva_asignatura_nombre,
                    codigo_asignatura=codigo_asignatura,
                    descripcion=f"Asignatura creada desde el curso {curso}",
                    profesor_responsable=curso.profesor_jefe
                )
                
                # Agregar la nueva asignatura al curso
                curso.asignaturas.add(nueva_asignatura)
        
        return curso

# Formularios básicos adicionales
class HorarioCursoForm(forms.ModelForm):
    class Meta:
        model = HorarioCurso
        fields = ['dia', 'hora_inicio', 'hora_fin', 'asignatura']

class AsignarEstudianteForm(forms.Form):
    """Formulario para asignar estudiantes pendientes a cursos"""
    estudiante = forms.ModelChoiceField(
        queryset=Estudiante.objects.none(),
        label="Estudiante",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        help_text='Selecciona el estudiante que deseas asignar al curso'
    )
    
    curso = forms.ModelChoiceField(
        queryset=Curso.objects.none(),
        label="Curso de destino",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        help_text='Selecciona el curso al que asignar el estudiante'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        anio_actual = timezone.now().year
        
        # Obtener estudiantes no asignados a ningún curso del año actual
        cursos_actuales = Curso.objects.filter(anio=anio_actual)
        estudiantes_asignados_ids = set()
        
        for curso in cursos_actuales:
            estudiantes_curso = list(curso.estudiantes.values_list('id', flat=True))
            estudiantes_asignados_ids.update(estudiantes_curso)
        
        # Estudiantes disponibles (no asignados)
        estudiantes_disponibles = Estudiante.objects.exclude(
            id__in=estudiantes_asignados_ids
        ).order_by('primer_nombre', 'apellido_paterno')
        
        self.fields['estudiante'].queryset = estudiantes_disponibles
        self.fields['estudiante'].empty_label = "-- Seleccionar estudiante --"
        
        # Cursos del año actual
        cursos_actuales = Curso.objects.filter(anio=anio_actual).order_by('nivel', 'paralelo')
        self.fields['curso'].queryset = cursos_actuales
        self.fields['curso'].empty_label = "-- Seleccionar curso --"

    def clean(self):
        cleaned_data = super().clean()
        estudiante = cleaned_data.get('estudiante')
        curso = cleaned_data.get('curso')
        
        if estudiante and curso:
            # Verificar que el estudiante no esté ya en otro curso del año actual
            anio_actual = timezone.now().year
            cursos_existentes = Curso.objects.filter(
                estudiantes=estudiante,
                anio=anio_actual
            )
            
            if cursos_existentes.exists():
                curso_actual = cursos_existentes.first()
                raise forms.ValidationError(
                    f'El estudiante {estudiante.primer_nombre} {estudiante.apellido_paterno} '
                    f'ya está asignado al curso {curso_actual.get_nivel_display()}{curso_actual.paralelo}.'
                )
        
        return cleaned_data

class AsignaturaForm(forms.ModelForm):
    # Campo para seleccionar cursos
    cursos = forms.ModelMultipleChoiceField(
        queryset=Curso.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'multiple': True,
            'size': '6'
        }),
        label='Cursos Asociados',
        required=False,
        help_text='Mantén presionada Ctrl (o Cmd en Mac) para seleccionar varios cursos'
    )
    
    class Meta:
        model = Asignatura
        fields = ['codigo_asignatura', 'nombre', 'descripcion', 'profesor_responsable', 'cursos']
        widgets = {
            'codigo_asignatura': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: MAT001',
                'maxlength': '10'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Matemáticas'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada de la asignatura'
            }),
            'profesor_responsable': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'codigo_asignatura': 'Código de Asignatura',
            'nombre': 'Nombre de la Asignatura',
            'descripcion': 'Descripción',
            'profesor_responsable': 'Profesor Responsable'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar queryset de profesores
        self.fields['profesor_responsable'].queryset = Profesor.objects.select_related('user').order_by('primer_nombre', 'apellido_paterno')
        self.fields['profesor_responsable'].empty_label = "Seleccionar profesor..."
        
        # Configurar queryset de cursos
        self.fields['cursos'].queryset = Curso.objects.all().order_by('nivel', 'paralelo')
        
        # Si estamos editando, cargar cursos asociados
        if self.instance.pk:
            self.fields['cursos'].initial = self.instance.cursos.all()
    
    def save(self, commit=True):
        asignatura = super().save(commit=commit)
        if commit:
            # Guardar cursos asociados
            cursos_seleccionados = self.cleaned_data.get('cursos', [])
            asignatura.cursos.set(cursos_seleccionados)
        return asignatura

class AsignaturaCompletaForm(forms.ModelForm):
    # Campo para seleccionar cursos
    cursos = forms.ModelMultipleChoiceField(
        queryset=Curso.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'multiple': True,
            'size': '5'
        }),
        label='Cursos asignados',
        required=False,
        help_text='Mantén presionada Ctrl (o Cmd en Mac) para seleccionar varios cursos'
    )
    
    # Campo para días de la semana
    DIAS_CHOICES = [
        ('LU', 'Lunes'),
        ('MA', 'Martes'),
        ('MI', 'Miércoles'),
        ('JU', 'Jueves'),
        ('VI', 'Viernes'),
        ('SA', 'Sábado'),
        ('DO', 'Domingo'),
    ]
    
    dias = forms.MultipleChoiceField(
        choices=DIAS_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Días de la semana',
        required=False
    )
    
    class Meta:
        model = Asignatura
        fields = ['nombre', 'codigo_asignatura', 'descripcion', 'profesor_responsable']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Matemáticas, Historia, Ciencias, etc.'
            }),
            'codigo_asignatura': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: MAT001, HIS001, etc.'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción opcional de la asignatura'
            }),
            'profesor_responsable': forms.Select(attrs={
                'class': 'form-select'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar profesores que NO tengan asignaturas asignadas o permitir vacío
        profesores_sin_asignatura = Profesor.objects.filter(
            asignaturas_responsable__isnull=True
        ).distinct().order_by('primer_nombre', 'apellido_paterno')
        
        # Si estamos editando, incluir el profesor actual si lo tiene
        if self.instance and self.instance.pk and self.instance.profesor_responsable:
            profesores_disponibles = (profesores_sin_asignatura | 
                                    Profesor.objects.filter(id=self.instance.profesor_responsable.id)
                                    ).distinct().order_by('primer_nombre', 'apellido_paterno')
        else:
            profesores_disponibles = profesores_sin_asignatura
        
        self.fields['profesor_responsable'].queryset = profesores_disponibles
        self.fields['profesor_responsable'].empty_label = "-- Sin profesor asignado --"
        self.fields['profesor_responsable'].required = False
        
        # Configurar cursos disponibles
        anio_actual = timezone.now().year
        self.fields['cursos'].queryset = Curso.objects.filter(
            anio=anio_actual
        ).order_by('nivel', 'paralelo')
        
        # Hacer campos no requeridos
        self.fields['descripcion'].required = False
        self.fields['cursos'].required = False
        self.fields['dias'].required = False
    
    def clean_codigo_asignatura(self):
        codigo = self.cleaned_data.get('codigo_asignatura')
        if codigo:
            # Verificar que el código no exista (excepto si estamos editando)
            existing = Asignatura.objects.filter(codigo_asignatura=codigo)
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError(
                    f'Ya existe una asignatura con el código "{codigo}". '
                    'Por favor, usa un código diferente.'
                )
        return codigo
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            # Verificar que el nombre no exista (excepto si estamos editando)
            existing = Asignatura.objects.filter(nombre__iexact=nombre)
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError(
                    f'Ya existe una asignatura con el nombre "{nombre}". '
                    'Por favor, usa un nombre diferente.'
                )
        return nombre
    
    def save(self, commit=True):
        asignatura = super().save(commit=commit)
        
        if commit:
            # Asignar la asignatura a los cursos seleccionados
            cursos_seleccionados = self.cleaned_data.get('cursos', [])
            if cursos_seleccionados:
                for curso in cursos_seleccionados:
                    curso.asignaturas.add(asignatura)
        
        return asignatura

class SeleccionCursoAlumnoForm(forms.Form):
    curso = forms.ModelChoiceField(queryset=Curso.objects.all(), label="Curso")
    asignatura = forms.ModelChoiceField(queryset=Asignatura.objects.none(), label="Asignatura", required=False)
    alumno = forms.ModelChoiceField(queryset=Estudiante.objects.none(), label="Alumno", required=False)

class CalificacionForm(forms.ModelForm):
    class Meta:
        model = Calificacion
        fields = ['nombre_evaluacion', 'puntaje', 'descripcion']

class AsistenciaAlumnoForm(forms.ModelForm):
    class Meta:
        model = AsistenciaAlumno
        fields = ['estudiante', 'asignatura', 'fecha', 'presente', 'observacion']

class AsistenciaProfesorForm(forms.ModelForm):
    class Meta:
        model = AsistenciaProfesor
        fields = ['profesor', 'asignatura', 'fecha', 'presente', 'observacion']

class AnotacionForm(forms.ModelForm):
    """Formulario para crear y editar anotaciones del libro de comportamiento"""
    
    class Meta:
        model = Anotacion
        fields = [
            'estudiante', 'curso', 'asignatura', 'tipo', 'categoria', 
            'titulo', 'descripcion', 'puntos', 'es_grave', 
            'requiere_atencion_apoderado'
        ]
        widgets = {
            'estudiante': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'curso': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'asignatura': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
                'onchange': 'actualizarPuntos()'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título descriptivo de la anotación',
                'maxlength': 200,
                'required': True
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción detallada de la situación...',
                'required': True
            }),
            'puntos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': -20,
                'max': 20,
                'step': 1
            }),
            'es_grave': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'requiere_atencion_apoderado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'estudiante': 'Estudiante',
            'curso': 'Curso',
            'asignatura': 'Asignatura (opcional)',
            'tipo': 'Tipo de Anotación',
            'categoria': 'Categoría',
            'titulo': 'Título',
            'descripcion': 'Descripción',
            'puntos': 'Puntos',
            'es_grave': 'Anotación Grave',
            'requiere_atencion_apoderado': 'Requiere Atención del Apoderado',
        }
        help_texts = {
            'asignatura': 'Opcional: Selecciona la asignatura relacionada',
            'puntos': 'Puntos automáticos según tipo: Positiva(+5), Negativa(-3), Neutra(0)',
            'es_grave': 'Marcar si es una falta grave que requiere atención especial',
            'requiere_atencion_apoderado': 'Marcar si se debe comunicar al apoderado',
        }
    
    def __init__(self, *args, **kwargs):
        profesor = kwargs.pop('profesor', None)
        super().__init__(*args, **kwargs)
        
        from django.utils import timezone
        anio_actual = timezone.now().year
        
        # Filtrar cursos según el tipo de usuario
        if profesor:
            # Profesor: solo sus cursos donde es jefe o tiene asignaturas
            cursos_ids = set()
            
            # Cursos donde es jefe
            cursos_jefe = profesor.cursos_jefatura.filter(anio=anio_actual)
            cursos_ids.update(cursos_jefe.values_list('id', flat=True))
            
            # Obtener cursos donde el profesor tiene asignaturas asignadas
            try:
                # Usar solo la relación profesor_responsable
                cursos_asignaturas = Curso.objects.filter(
                    asignaturas__profesor_responsable=profesor,
                    anio=anio_actual
                ).distinct()
                cursos_ids.update(cursos_asignaturas.values_list('id', flat=True))
            except:
                pass
            
            try:
                # Intentar usar la relación legacy si existe
                cursos_legacy = Curso.objects.filter(
                    asignaturas__profesor_responsable=profesor,
                    anio=anio_actual
                ).distinct()
                cursos_ids.update(cursos_legacy.values_list('id', flat=True))
            except:
                pass
            
            # Si no tiene cursos asignados, permitir ver todos los cursos con estudiantes
            if not cursos_ids:
                cursos_disponibles = Curso.objects.filter(
                    anio=anio_actual,
                    estudiantes__isnull=False
                ).distinct()
            else:
                cursos_disponibles = Curso.objects.filter(
                    id__in=cursos_ids,
                    estudiantes__isnull=False
                ).distinct()
            
            self.fields['curso'].queryset = cursos_disponibles.order_by('nivel', 'paralelo')
            
            # Filtrar asignaturas del profesor
            try:
                asignaturas_ids = set()
                
                # Asignaturas donde el profesor es responsable
                asignaturas_responsable = Asignatura.objects.filter(profesor_responsable=profesor)
                asignaturas_ids.update(asignaturas_responsable.values_list('id', flat=True))
                
                # Si el profesor tiene una relación many-to-many con asignaturas, incluirlas también
                try:
                    asignaturas_profesor = profesor.asignaturas.all()
                    asignaturas_ids.update(asignaturas_profesor.values_list('id', flat=True))
                except:
                    pass
                
                if asignaturas_ids:
                    asignaturas_disponibles = Asignatura.objects.filter(id__in=asignaturas_ids)
                else:
                    # Si no tiene asignaturas específicas, mostrar todas
                    asignaturas_disponibles = Asignatura.objects.all()
            except:
                asignaturas_disponibles = Asignatura.objects.all()
            
            self.fields['asignatura'].queryset = asignaturas_disponibles.order_by('nombre')
        else:
            # Admin/Director: todos los cursos del año actual con estudiantes
            cursos_con_estudiantes = Curso.objects.filter(
                anio=anio_actual,
                estudiantes__isnull=False
            ).distinct().order_by('nivel', 'paralelo')
            
            self.fields['curso'].queryset = cursos_con_estudiantes
            self.fields['asignatura'].queryset = Asignatura.objects.all().order_by('nombre')
        
        # Hacer que el campo estudiante se filtre dinámicamente por AJAX
        self.fields['estudiante'].queryset = Estudiante.objects.none()
        
        # Si estamos editando una anotación existente, configurar los campos
        if self.instance.pk:  # Editando anotación existente
            # Hacer que curso y estudiante no sean editables
            self.fields['curso'].widget.attrs['disabled'] = True
            self.fields['estudiante'].widget.attrs['disabled'] = True
            
            # Configurar el queryset del estudiante para mostrar solo el actual
            if self.instance.estudiante:
                self.fields['estudiante'].queryset = Estudiante.objects.filter(id=self.instance.estudiante.id)
            
            # Configurar el queryset del curso para mostrar solo el actual
            if self.instance.curso:
                self.fields['curso'].queryset = Curso.objects.filter(id=self.instance.curso.id)
        else:
            # Configurar valores por defecto para nuevas anotaciones
            self.fields['puntos'].initial = 0
    
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        es_grave = cleaned_data.get('es_grave')
        estudiante = cleaned_data.get('estudiante')
        
        # Si estamos editando, preservar los valores originales de curso y estudiante
        if self.instance.pk:
            cleaned_data['curso'] = self.instance.curso
            cleaned_data['estudiante'] = self.instance.estudiante
        curso = cleaned_data.get('curso')
        
        # Validar que el estudiante pertenezca al curso seleccionado
        if estudiante and curso:
            if not curso.estudiantes.filter(id=estudiante.id).exists():
                raise forms.ValidationError(
                    f'El estudiante {estudiante.get_nombre_completo()} no pertenece al curso {curso}.',
                    code='estudiante_no_pertenece_curso'
                )
        
        # Ajustar puntos automáticamente si no se especificaron
        puntos = cleaned_data.get('puntos')
        if puntos == 0 and tipo:
            if tipo == 'positiva':
                cleaned_data['puntos'] = 5
            elif tipo == 'negativa':
                cleaned_data['puntos'] = -3 * (2 if es_grave else 1)
            else:  # neutra
                cleaned_data['puntos'] = 0
        
        return cleaned_data

class FiltroAnotacionesForm(forms.Form):
    """Formulario para filtrar las anotaciones en el libro"""
    
    curso = forms.ModelChoiceField(
        queryset=Curso.objects.none(),
        required=False,
        empty_label="Todos los cursos",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    estudiante = forms.ModelChoiceField(
        queryset=Estudiante.objects.none(),
        required=False,
        empty_label="Todos los estudiantes",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    tipo = forms.ChoiceField(
        choices=[('', 'Todos los tipos')] + Anotacion.TIPOS_ANOTACION,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    categoria = forms.ChoiceField(
        choices=[('', 'Todas las categorías')] + Anotacion.CATEGORIAS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Desde'
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Hasta'
    )
    
    solo_graves = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Solo anotaciones graves'
    )
    
    def __init__(self, *args, **kwargs):
        profesor = kwargs.pop('profesor', None)
        super().__init__(*args, **kwargs)
        
        from django.utils import timezone
        anio_actual = timezone.now().year
        
        # Configurar opciones según el tipo de usuario
        if profesor:
            # Profesor: solo sus cursos
            cursos_disponibles = profesor.get_cursos_asignados()
            self.fields['curso'].queryset = cursos_disponibles.order_by('nivel', 'paralelo')
            
            # Estudiantes de sus cursos (inicialmente vacío para carga dinámica)
            estudiantes_ids = set()
            for curso in cursos_disponibles:
                estudiantes_ids.update(curso.estudiantes.values_list('id', flat=True))
            
            self.fields['estudiante'].queryset = Estudiante.objects.filter(
                id__in=estudiantes_ids
            ).order_by('primer_nombre', 'apellido_paterno')
        else:
            # Admin/Director: todos los cursos y estudiantes
            self.fields['curso'].queryset = Curso.objects.filter(
                anio=anio_actual
            ).order_by('nivel', 'paralelo')
            
            self.fields['estudiante'].queryset = Estudiante.objects.all().order_by(
                'primer_nombre', 'apellido_paterno'
            )
            
        # Si hay un curso seleccionado en los datos, filtrar estudiantes
        if self.data.get('curso'):
            try:
                curso_id = int(self.data.get('curso'))
                curso = Curso.objects.get(id=curso_id)
                
                # Verificar permisos
                if profesor:
                    cursos_disponibles = profesor.get_cursos_asignados()
                    if curso in cursos_disponibles:
                        estudiantes_curso = curso.estudiantes.all().order_by('primer_nombre', 'apellido_paterno')
                        self.fields['estudiante'].queryset = estudiantes_curso
                else:
                    # Admin/Director pueden ver todos los cursos
                    estudiantes_curso = curso.estudiantes.all().order_by('primer_nombre', 'apellido_paterno')
                    self.fields['estudiante'].queryset = estudiantes_curso
            except (ValueError, Curso.DoesNotExist):
                pass

# Formulario específico para registro masivo de asistencia de alumnos
class RegistroMasivoAsistenciaForm(forms.Form):
    """Formulario simplificado para registro masivo de asistencia solo por curso"""
    
    curso = forms.ModelChoiceField(
        queryset=Curso.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Curso',
        help_text='Selecciona el curso para registrar asistencia'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo cursos del año actual
        from django.utils import timezone
        anio_actual = timezone.now().year
        self.fields['curso'].queryset = Curso.objects.filter(
            anio=anio_actual
        ).order_by('nivel', 'paralelo')
