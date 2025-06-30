from django import template
from smapp.models import Asignatura

register = template.Library()

@register.filter
def get_item(container, key):
    """
    Template filter robusto para obtener un elemento de un diccionario por clave o de una lista por índice
    Uso: {{ mi_diccionario|get_item:mi_clave }} o {{ mi_lista|get_item:indice }}
    
    Este filtro NUNCA debe lanzar AttributeError, incluso si recibe tipos incorrectos.
    """
    try:
        # Verificar que container no sea None o un tipo no compatible
        if container is None:
            return None
            
        # Manejar diccionarios
        if isinstance(container, dict):
            return container.get(key, None)
            
        # Manejar listas y tuplas
        elif isinstance(container, (list, tuple)):
            # Para listas/tuplas, key debe ser un índice
            # Convertir a entero si es un string numérico
            if isinstance(key, str) and key.isdigit():
                key = int(key)
            if isinstance(key, int) and 0 <= key < len(container):
                return container[key]
            return None
            
        # Intentar acceso como diccionario para objetos que soportan getitem
        elif hasattr(container, '__getitem__'):
            try:
                return container[key]
            except (KeyError, IndexError, TypeError):
                return None
                
        # Para cualquier otro tipo, devolver None
        else:
            return None
            
    except (TypeError, IndexError, KeyError, ValueError, AttributeError):
        # Capturar TODOS los errores posibles, incluyendo AttributeError
        return None

@register.filter
def get_list_item(lista, indice):
    """
    Template filter específico para obtener un elemento de una lista por índice
    Uso: {{ mi_lista|get_list_item:indice }}
    
    Este filtro NUNCA debe lanzar AttributeError, incluso si recibe tipos incorrectos.
    """
    try:
        # Verificar que lista no sea None
        if lista is None:
            return None
            
        # Verificar que sea una lista o tupla
        if not isinstance(lista, (list, tuple)):
            return None
            
        # Convertir índice a entero si es string numérico
        if isinstance(indice, str) and indice.isdigit():
            indice = int(indice)
            
        # Verificar que el índice sea válido
        if isinstance(indice, int) and 0 <= indice < len(lista):
            return lista[indice]
            
        return None
        
    except (TypeError, IndexError, ValueError, AttributeError):
        # Capturar TODOS los errores posibles, incluyendo AttributeError
        return None

@register.simple_tag
def get_asignaturas_no_asignadas_curso(curso):
    """
    Obtiene las asignaturas que no están asignadas a un curso específico
    """
    if not curso:
        return Asignatura.objects.none()
    
    # Obtener todas las asignaturas
    todas_asignaturas = Asignatura.objects.all()
    
    # Obtener asignaturas ya asignadas al curso
    asignaturas_del_curso = curso.asignaturas.all()
    
    # Retornar las que no están asignadas
    asignaturas_no_asignadas = todas_asignaturas.exclude(
        id__in=asignaturas_del_curso.values_list('id', flat=True)
    )
    
    return asignaturas_no_asignadas
