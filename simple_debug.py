from smapp.models import Profesor, Perfil
from django.contrib.auth.models import User

print("DIAGNOSTICO PROFESORES")

perfiles = Perfil.objects.filter(tipo_usuario='profesor')
print(f"Perfiles profesor: {perfiles.count()}")

for perfil in perfiles:
    user = perfil.user
    print(f"Usuario: {user.username}")
    try:
        prof = Profesor.objects.get(user=user)
        print(f"  SI tiene modelo Profesor: {prof.get_nombre_completo()}")
    except:
        print(f"  NO tiene modelo Profesor")

print(f"Profesores totales: {Profesor.objects.count()}")
print(f"Profesores con user: {Profesor.objects.filter(user__isnull=False).count()}")
