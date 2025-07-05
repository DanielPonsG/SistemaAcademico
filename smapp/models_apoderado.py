from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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
    numero_documento = models.CharField(max_length=12, unique=True, verbose_name="RUT")
    fecha_nacimiento = models.DateField()
    genero = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')])
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.primer_nombre} {self.apellido_paterno}"


class Apoderado(Persona):
    """
    Modelo para los apoderados de estudiantes. Hereda de Persona.
    Un apoderado puede tener múltiples pupilos (estudiantes) a cargo.
    También puede ser un profesor que tiene estudiantes bajo su cuidado.
    """
    TIPOS_APODERADO = [
        ('padre', 'Padre'),
        ('madre', 'Madre'),
        ('abuelo', 'Abuelo/a'),
        ('tio', 'Tío/a'),
        ('hermano', 'Hermano/a'),
        ('tutor', 'Tutor Legal'),
        ('profesor', 'Profesor Responsable'),
        ('otro', 'Otro'),
    ]
    
    ESTADOS_CIVIL = [
        ('soltero', 'Soltero/a'),
        ('casado', 'Casado/a'),
        ('divorciado', 'Divorciado/a'),
        ('viudo', 'Viudo/a'),
        ('union_libre', 'Unión Libre'),
    ]
    
    tipo_apoderado = models.CharField(max_length=15, choices=TIPOS_APODERADO, default='padre')
    estado_civil = models.CharField(max_length=15, choices=ESTADOS_CIVIL, default='soltero')
    profesion = models.CharField(max_length=100, blank=True, null=True)
    lugar_trabajo = models.CharField(max_length=200, blank=True, null=True)
    telefono_trabajo = models.CharField(max_length=20, blank=True, null=True)
    telefono_emergencia = models.CharField(max_length=20, blank=True, null=True)
    contacto_emergencia = models.CharField(max_length=200, blank=True, null=True, 
                                         help_text="Nombre y relación del contacto de emergencia")
    
    # Usuario para acceso al sistema (opcional)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True,
                               related_name='apoderado')
    
    # Campos de control
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    notas_adicionales = models.TextField(blank=True, null=True,
                                       help_text="Información adicional sobre el apoderado")
    
    class Meta:
        verbose_name = "Apoderado"
        verbose_name_plural = "Apoderados"
        ordering = ['apellido_paterno', 'primer_nombre']
    
    def __str__(self):
        tipo_display = self.get_tipo_apoderado_display()
        return f"{self.primer_nombre} {self.apellido_paterno} ({tipo_display})"
    
    def get_nombre_completo(self):
        """Retorna el nombre completo del apoderado"""
        nombres = [self.primer_nombre]
        if self.segundo_nombre:
            nombres.append(self.segundo_nombre)
        nombres.append(self.apellido_paterno)
        if self.apellido_materno:
            nombres.append(self.apellido_materno)
        return ' '.join(nombres)
    
    def get_telefono_principal(self):
        """Retorna el teléfono principal (celular o fijo)"""
        return self.telefono if self.telefono else self.telefono_trabajo
    
    def get_contacto_completo(self):
        """Retorna información completa de contacto"""
        contacto = f"{self.get_nombre_completo()}\n"
        if self.telefono:
            contacto += f"Tel: {self.telefono}\n"
        if self.email:
            contacto += f"Email: {self.email}\n"
        if self.direccion:
            contacto += f"Dir: {self.direccion}\n"
        return contacto.strip()
