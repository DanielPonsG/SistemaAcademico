#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from smapp.models import Apoderado

print("=== REVISIÓN DE APODERADOS EXISTENTES ===")
apoderados = Apoderado.objects.all()
print(f"Total de apoderados: {apoderados.count()}")

for apoderado in apoderados:
    codigo = getattr(apoderado, 'codigo_apoderado', 'No definido')
    nombre_completo = f"{apoderado.primer_nombre} {apoderado.apellido_paterno}"
    print(f"ID: {apoderado.id}, Documento: {apoderado.numero_documento}, Nombre: {nombre_completo}, Código: {codigo}")

print("\n=== VERIFICACIÓN DE DUPLICADOS ===")
# Verificar si hay códigos duplicados
try:
    codigos = [a.codigo_apoderado for a in apoderados if hasattr(a, 'codigo_apoderado') and a.codigo_apoderado]
    duplicados = [c for c in set(codigos) if codigos.count(c) > 1]
    if duplicados:
        print(f"Códigos duplicados encontrados: {duplicados}")
    else:
        print("No se encontraron códigos duplicados")
        print(f"Códigos únicos: {codigos}")
except Exception as e:
    print(f"Error al verificar duplicados: {e}")

print("\n=== VERIFICACIÓN DE MODELO RELACIONAPODERADOESTUDIANTE ===")
try:
    from smapp.models import RelacionApoderadoEstudiante
    relaciones = RelacionApoderadoEstudiante.objects.all()
    print(f"Total de relaciones apoderado-estudiante: {relaciones.count()}")
    for relacion in relaciones:
        print(f"Apoderado: {relacion.apoderado.codigo_apoderado} - Estudiante: {relacion.estudiante.primer_nombre}")
except Exception as e:
    print(f"Error al verificar relaciones: {e}")
