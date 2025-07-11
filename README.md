# 📚 SAM - School Academic Manager

Sistema integral de gestión académica desarrollado en Django para la administración de estudiantes, profesores y contenido educativo.

## 🚀 Instalación y Configuración

### Prerequisitos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Git

### 1. Clonar el repositorio
```bash
git clone <url-del-repositorio>
cd SAM-main
```

### 2. Crear entorno virtual
```bash
python -m venv .venv
```

### 3. Activar entorno virtual
**Windows:**
```bash
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 4. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 5. **IMPORTANTE: Recolectar archivos estáticos**
```bash
python collect_static.py
```
O alternativamente:
```bash
python manage.py collectstatic --noinput
```

### 6. Realizar migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Crear superusuario (opcional)
```bash
python manage.py createsuperuser
```

### 8. Ejecutar servidor de desarrollo
```bash
python manage.py runserver
```

## ⚠️ Solución de Problemas Comunes

### Los estilos no se cargan correctamente
Si después de instalar el proyecto los estilos CSS no se ven:

1. **Asegúrate de haber ejecutado el paso 5** (recolectar archivos estáticos)
2. Verifica que existe la carpeta `staticfiles/` en la raíz del proyecto
3. Ejecuta nuevamente:
   ```bash
   python manage.py collectstatic --clear --noinput
   ```

### Error 404 en archivos estáticos
Si aparecen errores 404 para archivos CSS/JS:

1. Verifica que `DEBUG = True` en `settings.py` para desarrollo
2. Asegúrate de que la carpeta `static/` existe
3. Ejecuta: `python collect_static.py`

### Base de datos no encontrada
```bash
python manage.py makemigrations smapp
python manage.py migrate
```

## 📁 Estructura del Proyecto

```
SAM-main/
├── sma/                    # Configuración del proyecto Django
├── smapp/                  # Aplicación principal
├── templates/              # Plantillas HTML
├── static/                 # Archivos estáticos (CSS, JS, imágenes)
├── staticfiles/           # Archivos estáticos recolectados (auto-generado)
├── requirements.txt       # Dependencias Python
├── collect_static.py      # Script para recolectar archivos estáticos
└── manage.py              # Herramienta de gestión Django
```

## 🔧 Configuración de Desarrollo

### Variables de entorno (.env)
Crea un archivo `.env` en la raíz del proyecto (opcional):
```
DEBUG=True
SECRET_KEY=tu-clave-secreta-aqui
```

## 📝 Notas Importantes

- **Siempre ejecutar `python collect_static.py` después de clonar o actualizar el repositorio**
- Los archivos en `staticfiles/` no se suben a GitHub (están en .gitignore)
- Para producción, configurar un servidor web para servir archivos estáticos

## 🆘 Soporte

Si encuentras problemas:
1. Verifica que has seguido todos los pasos de instalación
2. Asegúrate de que el entorno virtual esté activado
3. Confirma que has ejecutado `collect_static.py`
4. Revisa la consola para errores específicos

## 📋 Funcionalidades

- ✅ Gestión de estudiantes y profesores
- ✅ Sistema de horarios y cursos
- ✅ Registro de asistencia
- ✅ Gestión de notas y evaluaciones
- ✅ Panel de apoderados
- ✅ Calendario académico
- ✅ Libro de anotaciones
- ✅ Dashboard administrativo

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

---
**SAM - School Academic Manager** 🎓
