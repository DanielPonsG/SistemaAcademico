import os
import sys
import django
import random

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from smapp.models import Estudiante, Profesor, Apoderado

def calcular_dv(rut_numero):
    """Calcula el dígito verificador para un número de RUT"""
    rut_str = str(rut_numero)
    suma = 0
    multiplicador = 2
    
    for digit in reversed(rut_str):
        suma += int(digit) * multiplicador
        multiplicador += 1
        if multiplicador > 7:
            multiplicador = 2
    
    resto = suma % 11
    dv = 'K' if resto == 1 else '0' if resto == 0 else str(11 - resto)
    return dv

def fix_ruts():
    print("Iniciando corrección de RUTs inválidos...")
    
    # Corregir Estudiantes
    estudiantes = Estudiante.objects.all()
    count_est = 0
    for est in estudiantes:
        rut_raw = est.numero_documento
        if not rut_raw:
            continue
            
        # Limpiar
        rut_limpio = rut_raw.replace(".", "").replace("-", "").replace(" ", "").upper()
        if len(rut_limpio) < 2:
            continue
            
        numero = rut_limpio[:-1]
        dv_actual = rut_limpio[-1]
        
        if not numero.isdigit():
            continue
            
        dv_correcto = calcular_dv(numero)
        
        if dv_actual != dv_correcto:
            nuevo_rut = f"{numero}-{dv_correcto}"
            print(f"Corrigiendo Estudiante {est.id}: {rut_raw} -> {nuevo_rut}")
            est.numero_documento = nuevo_rut
            est.save()
            
            # También actualizar perfil si existe
            if est.user and hasattr(est.user, 'perfil'):
                est.user.perfil.numero_documento = nuevo_rut
                est.user.perfil.save()
            count_est += 1
            
    print(f"Estudiantes corregidos: {count_est}")

    # Corregir Profesores
    profesores = Profesor.objects.all()
    count_prof = 0
    for prof in profesores:
        rut_raw = prof.numero_documento
        if not rut_raw:
            continue
            
        rut_limpio = rut_raw.replace(".", "").replace("-", "").replace(" ", "").upper()
        if len(rut_limpio) < 2:
            continue
            
        numero = rut_limpio[:-1]
        dv_actual = rut_limpio[-1]
        
        if not numero.isdigit():
            continue
            
        dv_correcto = calcular_dv(numero)
        
        if dv_actual != dv_correcto:
            nuevo_rut = f"{numero}-{dv_correcto}"
            print(f"Corrigiendo Profesor {prof.id}: {rut_raw} -> {nuevo_rut}")
            prof.numero_documento = nuevo_rut
            prof.save()
            
            if prof.user and hasattr(prof.user, 'perfil'):
                prof.user.perfil.numero_documento = nuevo_rut
                prof.user.perfil.save()
            count_prof += 1
            
    print(f"Profesores corregidos: {count_prof}")

    # Corregir Apoderados
    apoderados = Apoderado.objects.all()
    count_apo = 0
    for apo in apoderados:
        rut_raw = apo.numero_documento
        if not rut_raw:
            continue
            
        rut_limpio = rut_raw.replace(".", "").replace("-", "").replace(" ", "").upper()
        if len(rut_limpio) < 2:
            continue
            
        numero = rut_limpio[:-1]
        dv_actual = rut_limpio[-1]
        
        if not numero.isdigit():
            continue
            
        dv_correcto = calcular_dv(numero)
        
        if dv_actual != dv_correcto:
            nuevo_rut = f"{numero}-{dv_correcto}"
            print(f"Corrigiendo Apoderado {apo.id}: {rut_raw} -> {nuevo_rut}")
            apo.numero_documento = nuevo_rut
            apo.save()
            
            if apo.user and hasattr(apo.user, 'perfil'):
                apo.user.perfil.numero_documento = nuevo_rut
                apo.user.perfil.save()
            count_apo += 1
            
    print(f"Apoderados corregidos: {count_apo}")
    print("Corrección finalizada.")

if __name__ == "__main__":
    fix_ruts()
