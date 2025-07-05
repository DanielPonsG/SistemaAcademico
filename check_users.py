from smapp.models import Profesor, Perfil
from django.contrib.auth.models import User

# Crear un usuario de prueba para el profesor si no existe
username = 'profesor_test'
user_test = User.objects.filter(username=username).first()

if user_test:
    print(f"Usuario {username} ya existe")
    print(f"Email: {user_test.email}")
    print(f"Activo: {user_test.is_active}")
    print(f"Tiene perfil: {hasattr(user_test, 'perfil')}")
    if hasattr(user_test, 'perfil'):
        print(f"Tipo perfil: {user_test.perfil.tipo_usuario}")
    print(f"Tiene profesor: {hasattr(user_test, 'profesor')}")
    if hasattr(user_test, 'profesor'):
        print(f"Profesor: {user_test.profesor.get_nombre_completo()}")
        print(f"Cursos: {user_test.profesor.get_cursos_asignados().count()}")
else:
    print(f"Usuario {username} no existe")

# Mostrar todos los usuarios con perfil profesor
print("\nTodos los usuarios profesor:")
usuarios_prof = User.objects.filter(perfil__tipo_usuario='profesor')
for user in usuarios_prof:
    print(f"- {user.username} | Activo: {user.is_active}")
