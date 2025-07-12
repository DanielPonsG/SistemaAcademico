from django.shortcuts import redirect
from django.urls import reverse

class ApoderadoRedirectMiddleware:
    """
    Middleware para redirigir automáticamente a apoderados y profesor-apoderados 
    a su dashboard correspondiente cuando accedan a la página de inicio
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Lista de rutas que NO deben ser redirigidas para evitar bucles
        excluded_paths = [
            '/dashboard-apoderado/',
            '/dashboard-profesor-apoderado/',
            '/inicio-apoderado/',
            '/logout/',
            '/admin/',          # Panel de administración
            '/login/',          # Página de login
            '/static/',         # Archivos estáticos
            '/media/',          # Archivos de media
        ]
        
        # Solo procesar si es la página raíz/inicio y el usuario está autenticado
        # EXCLUIR superusuarios y staff para que puedan acceder libremente
        if (request.path == '/' and 
            request.user.is_authenticated and 
            request.method == 'GET' and
            not request.user.is_superuser and  # ← NUEVO: Excluir superusuarios
            not request.user.is_staff and      # ← NUEVO: Excluir staff
            not any(request.path.startswith(path) for path in excluded_paths)):
            
            # Verificar si el usuario es un apoderado directo
            try:
                if hasattr(request.user, 'apoderado'):
                    apoderado = request.user.apoderado
                    if apoderado:
                        return redirect('dashboard_apoderado')
            except AttributeError:
                pass
            
            # Verificar si es un profesor que también es apoderado
            try:
                if hasattr(request.user, 'profesor'):
                    profesor = request.user.profesor
                    if hasattr(profesor, 'apoderado_profile') and profesor.apoderado_profile:
                        return redirect('dashboard_profesor_apoderado')
            except AttributeError:
                pass

        response = self.get_response(request)
        return response
