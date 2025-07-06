#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from django.db import connection

def prepare_apoderado_data():
    print("=== PREPARANDO DATOS DE APODERADOS PARA MIGRACIÓN ===")
    
    with connection.cursor() as cursor:
        # Obtener todos los apoderados actuales
        cursor.execute("SELECT id, numero_documento, primer_nombre, apellido_paterno FROM smapp_apoderado")
        apoderados = cursor.fetchall()
        
        print(f"Apoderados encontrados: {len(apoderados)}")
        
        # Generar códigos únicos para cada apoderado
        codes_to_assign = {}
        used_codes = set()
        
        for apoderado_id, numero_doc, nombre, apellido in apoderados:
            print(f"Procesando: ID={apoderado_id}, Doc={numero_doc}, Nombre={nombre} {apellido}")
            
            # Generar código basado en documento
            if numero_doc:
                # Limpiar el documento y usar los primeros caracteres
                doc_clean = numero_doc.replace('.', '').replace('-', '').replace(' ', '')[:8]
                base_code = f"APO-{doc_clean}"
            else:
                base_code = f"APO-{apoderado_id:04d}"
            
            # Asegurar que el código sea único
            final_code = base_code
            counter = 1
            while final_code in used_codes:
                final_code = f"{base_code}-{counter}"
                counter += 1
            
            codes_to_assign[apoderado_id] = final_code
            used_codes.add(final_code)
            print(f"  Código asignado: {final_code}")
        
        print(f"\n=== CÓDIGOS GENERADOS ===")
        for apoderado_id, codigo in codes_to_assign.items():
            print(f"ID {apoderado_id}: {codigo}")
        
        return codes_to_assign

def create_migration_data_file():
    """Crear un archivo con los datos para la migración personalizada"""
    codes = prepare_apoderado_data()
    
    print("\n=== CREANDO ARCHIVO DE DATOS PARA MIGRACIÓN ===")
    
    migration_content = f"""
# Datos para migración de apoderados
# Este archivo contiene los códigos que se asignarán a los apoderados existentes

APODERADO_CODES = {codes}

def assign_codes_to_existing_apoderados(apps, schema_editor):
    \"\"\"Asignar códigos únicos a apoderados existentes\"\"\"
    Apoderado = apps.get_model('smapp', 'Apoderado')
    
    for apoderado_id, codigo in APODERADO_CODES.items():
        try:
            apoderado = Apoderado.objects.get(id=apoderado_id)
            apoderado.codigo_apoderado = codigo
            apoderado.save()
            print(f"Código {{codigo}} asignado al apoderado ID {{apoderado_id}}")
        except Apoderado.DoesNotExist:
            print(f"Apoderado ID {{apoderado_id}} no encontrado")
"""
    
    with open(r"c:\Users\Danie\Desktop\Estudios\SAM-main\migration_data.py", "w", encoding="utf-8") as f:
        f.write(migration_content)
    
    print("Archivo migration_data.py creado")

if __name__ == "__main__":
    create_migration_data_file()
