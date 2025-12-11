import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from django.contrib.auth.models import User
from smapp.models import Perfil

username = 'admin_test'
password = 'admin_password'
email = 'admin@test.com'

if User.objects.filter(username=username).exists():
    print(f"User {username} already exists. Updating password.")
    user = User.objects.get(username=username)
    user.set_password(password)
    user.is_staff = True
    user.is_superuser = True
    user.save()
else:
    print(f"Creating user {username}.")
    user = User.objects.create_user(username=username, email=email, password=password)
    user.is_staff = True
    user.is_superuser = True
    user.save()

# Ensure profile exists
if not hasattr(user, 'perfil'):
    Perfil.objects.create(user=user, tipo_usuario='administrador')
else:
    user.perfil.tipo_usuario = 'administrador'
    user.perfil.save()

print(f"User {username} ready with password {password}")
