from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render
from functools import wraps

def permission_required(allowed_user_types):
    """
    Decorador para controlar el acceso basado en el tipo de usuario.
    
    Args:
        allowed_user_types (list): Lista de tipos de usuario permitidos
                                 ['estudiante', 'profesor', 'administrador', 'director']
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            try:
                user_type = request.user.perfil.tipo_usuario
                if user_type in allowed_user_types:
                    return view_func(request, *args, **kwargs)
                else:
                    # Renderizar página de acceso denegado personalizada
                    context = {
                        'user_type': user_type,
                        'required_types': allowed_user_types,
                        'error_message': f'Esta funcionalidad requiere permisos de: {", ".join(allowed_user_types)}'
                    }
                    return render(request, 'error_permisos.html', context, status=403)
            except AttributeError:
                # El usuario no tiene perfil asignado
                context = {
                    'error_message': 'Tu cuenta no tiene un perfil asignado. Contacta al administrador.'
                }
                return render(request, 'error_permisos.html', context, status=403)
        return _wrapped_view
    return decorator

# Decoradores específicos para facilitar el uso
admin_required = permission_required(['director', 'administrador'])  # Incluir ambos tipos de admin
profesor_admin_required = permission_required(['profesor', 'director', 'administrador'])
estudiante_required = permission_required(['alumno'])  # 'alumno' es el tipo en nuestro modelo
all_users_required = permission_required(['alumno', 'profesor', 'director', 'administrador'])

def profesor_con_asignaturas_required(view_func):
    """
    Decorador para permitir acceso a profesores que tengan cursos asignados 
    o asignaturas bajo su responsabilidad, además de administradores.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        try:
            user_type = request.user.perfil.tipo_usuario
            
            # Administradores tienen acceso completo
            if user_type in ['administrador', 'director']:
                return view_func(request, *args, **kwargs)
            
            # Verificar si es profesor con asignaturas o cursos
            if user_type == 'profesor':
                try:
                    from .models import Profesor
                    profesor = Profesor.objects.get(user=request.user)
                    
                    # Verificar si tiene cursos como jefe o asignaturas responsables
                    tiene_cursos = profesor.cursos_jefatura.exists()
                    tiene_asignaturas = profesor.asignaturas_responsable.exists()
                    
                    if tiene_cursos or tiene_asignaturas:
                        return view_func(request, *args, **kwargs)
                    else:
                        context = {
                            'error_message': 'Solo profesores con cursos o asignaturas asignadas pueden acceder a esta funcionalidad.'
                        }
                        return render(request, 'error_permisos.html', context, status=403)
                        
                except Profesor.DoesNotExist:
                    context = {
                        'error_message': 'No se encontró información de profesor para tu cuenta.'
                    }
                    return render(request, 'error_permisos.html', context, status=403)
            else:
                context = {
                    'error_message': 'Esta funcionalidad está disponible solo para profesores y administradores.'
                }
                return render(request, 'error_permisos.html', context, status=403)
                
        except AttributeError:
            context = {
                'error_message': 'Tu cuenta no tiene un perfil asignado. Contacta al administrador.'
            }
            return render(request, 'error_permisos.html', context, status=403)
        
    return _wrapped_view

def estudiante_required(view_func):
    """
    Decorador que permite acceso solo a estudiantes
    """
    return permission_required(['alumno'])(view_func)

def admin_required(view_func):
    """
    Decorador que permite acceso solo a administradores y directores
    """
    return permission_required(['director', 'administrador'])(view_func)
