# SAM - Sistema de Administración y Matrícula

SAM es un sistema de gestión escolar completo desarrollado en Django, diseñado para facilitar la administración académica de instituciones educativas chilenas.

## Características Principales

### 👥 Gestión de Usuarios
- **Estudiantes**: Registro completo con RUT, datos personales y académicos
- **Profesores**: Gestión de personal docente con especialidades
- **Administradores**: Control total del sistema

### 📚 Gestión Académica
- **Cursos**: Organización por niveles (Básica y Media) con paralelos
- **Asignaturas**: Asignación de materias a cursos y profesores
- **Notas**: Sistema completo de calificaciones y promedios
- **Asistencia**: Registro diario de asistencia de estudiantes y profesores

### 📅 Sistema de Calendario
- **Eventos**: Creación y gestión de eventos escolares
- **Visualización**: Calendario interactivo con FullCalendar
- **Permisos**: Control de acceso según tipo de usuario

### ⏰ Gestión de Horarios
- **Horarios por Curso**: Asignación de horarios semanales
- **Profesores**: Gestión de horarios de clases
- **Visualización**: Interface intuitiva para horarios

### 📖 Libro de Anotaciones
- **Comportamiento**: Registro de anotaciones positivas y negativas
- **Seguimiento**: Sistema de puntuación de comportamiento
- **Comunicación**: Notificación a apoderados

## Tecnologías Utilizadas

- **Backend**: Django 4.2.7
- **Frontend**: HTML5, CSS3, JavaScript
- **Base de Datos**: SQLite (desarrollo), PostgreSQL (producción)
- **UI Framework**: Gentella Admin Template
- **Calendario**: FullCalendar.js
- **Estilos**: Bootstrap 4

## Requisitos del Sistema

- Python 3.8+
- Django 4.2+
- SQLite3 (incluido con Python)

## Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/tu-usuario/SAM.git
   cd SAM
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar base de datos**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Crear superusuario**
   ```bash
   python manage.py createsuperuser
   ```

6. **Ejecutar servidor**
   ```bash
   python manage.py runserver
   ```

7. **Acceder al sistema**
   - Abrir navegador en `http://localhost:8000`
   - Admin panel: `http://localhost:8000/admin`

## Estructura del Proyecto

```
SAM/
├── manage.py                 # Script principal de Django
├── sma/                     # Configuración del proyecto
│   ├── settings.py          # Configuraciones
│   ├── urls.py             # URLs principales
│   └── wsgi.py             # Configuración WSGI
├── smapp/                   # Aplicación principal
│   ├── models.py           # Modelos de datos
│   ├── views.py            # Vistas
│   ├── forms.py            # Formularios
│   ├── admin.py            # Configuración admin
│   └── migrations/         # Migraciones de BD
├── templates/               # Plantillas HTML
├── static/                  # Archivos estáticos
└── requirements.txt         # Dependencias
```

## Uso del Sistema

### Tipos de Usuario

1. **Administrador/Director**
   - Acceso completo al sistema
   - Gestión de usuarios, cursos y asignaturas
   - Configuración general

2. **Profesor**
   - Gestión de sus cursos asignados
   - Registro de notas y asistencia
   - Creación de eventos

3. **Estudiante**
   - Visualización de horarios y notas
   - Acceso a calendario de eventos

### Flujo de Trabajo Típico

1. **Configuración Inicial**
   - Crear profesores y estudiantes
   - Configurar cursos y paralelos
   - Asignar asignaturas a cursos

2. **Gestión Diaria**
   - Registro de asistencia
   - Ingreso de notas
   - Creación de eventos

3. **Seguimiento**
   - Monitoreo de promedios
   - Libro de anotaciones
   - Reportes de asistencia

## Contribuir

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Soporte

Para reportar bugs o solicitar features, por favor crear un issue en el repositorio de GitHub.

## Estado del Proyecto

🟢 **Activo** - En desarrollo continuo

### Últimas Actualizaciones
- ✅ Sistema de calendario funcional
- ✅ Gestión completa de notas
- ✅ Libro de anotaciones implementado
- ✅ Sistema de asistencia operativo
- ✅ Gestión de horarios funcional

---

**Desarrollado con ❤️ para la educación chilena**
