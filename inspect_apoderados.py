#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from django.db import connection

def inspect_apoderado_table():
    print("=== INSPECCIÓN DE TABLA APODERADO ===")
    
    with connection.cursor() as cursor:
        # Ver estructura de la tabla
        cursor.execute("PRAGMA table_info(smapp_apoderado)")
        columns_info = cursor.fetchall()
        
        print("Columnas en smapp_apoderado:")
        for col in columns_info:
            col_id, name, type_info, not_null, default, pk = col
            print(f"  - {name} ({type_info}) {'NOT NULL' if not_null else 'NULL'} {'PK' if pk else ''}")
        
        # Ver datos existentes
        cursor.execute("SELECT * FROM smapp_apoderado LIMIT 5")
        rows = cursor.fetchall()
        
        print(f"\nRegistros existentes: {len(rows)}")
        column_names = [desc[0] for desc in cursor.description]
        print(f"Columnas: {column_names}")
        
        for i, row in enumerate(rows):
            print(f"Registro {i+1}: {dict(zip(column_names, row))}")

if __name__ == "__main__":
    inspect_apoderado_table()
