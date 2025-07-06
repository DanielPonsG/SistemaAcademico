from django.shortcuts import redirect
from django.urls import reverse

class ApoderadoRedirectMiddleware:
    """
    Middleware para redirigir automáticamente a apoderados y profesor-apoderados 
    a sus dashboards correspondientes cuando accedan a la página de inicio
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo procesar si es la página de inicio y el usuario está autenticado
        if (request.path == reverse('inicio') and 
            request.user.is_authenticated and 
            request.method == 'GET'):
            
            # Verificar si el usuario es un apoderado directo
            try:
                apoderado = request.user.apoderado
                if apoderado:
                    return redirect('dashboard_apoderado')
            except:
                pass
            
            # Verificar si es un profesor que también es apoderado
            try:
                if hasattr(request.user, 'profesor'):
                    profesor = request.user.profesor
                    if hasattr(profesor, 'apoderado_profile') and profesor.apoderado_profile:
                        # Para profesor-apoderado, mostrar el dashboard normal de profesor
                        # pero con información adicional de apoderado
                        pass  # Dejamos que la vista original se encargue
            except:
                pass

        response = self.get_response(request)
        return response
