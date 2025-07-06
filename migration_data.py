
# Datos para migración de apoderados
# Este archivo contiene los códigos que se asignarán a los apoderados existentes

APODERADO_CODES = {2: 'APO-98765432', 3: 'APO-11223344'}

def assign_codes_to_existing_apoderados(apps, schema_editor):
    """Asignar códigos únicos a apoderados existentes"""
    Apoderado = apps.get_model('smapp', 'Apoderado')
    
    for apoderado_id, codigo in APODERADO_CODES.items():
        try:
            apoderado = Apoderado.objects.get(id=apoderado_id)
            apoderado.codigo_apoderado = codigo
            apoderado.save()
            print(f"Código {codigo} asignado al apoderado ID {apoderado_id}")
        except Apoderado.DoesNotExist:
            print(f"Apoderado ID {apoderado_id} no encontrado")
