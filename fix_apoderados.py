#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from smapp.models import Apoderado
from django.db import connection

def fix_apoderado_data():
    print("=== CORRIGIENDO DATOS DE APODERADOS ===")
    
    # Primero, veamos qué apoderados existen sin usar el campo codigo_apoderado
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, rut, nombres, apellidos FROM smapp_apoderado")
        apoderados_data = cursor.fetchall()
    
    print(f"Apoderados encontrados: {len(apoderados_data)}")
    
    for row in apoderados_data:
        apoderado_id, rut, nombres, apellidos = row
        print(f"ID: {apoderado_id}, RUT: {rut}, Nombre: {nombres} {apellidos}")
    
    # Ahora vamos a generar códigos únicos para cada apoderado
    print("\n=== GENERANDO CÓDIGOS ÚNICOS ===")
    
    for i, row in enumerate(apoderados_data, 1):
        apoderado_id, rut, nombres, apellidos = row
        # Generar código único basado en el RUT o un contador
        if rut:
            codigo_nuevo = f"APO-{rut.replace('.', '').replace('-', '')[:8]}"
        else:
            codigo_nuevo = f"APO-{apoderado_id:04d}"
        
        print(f"Asignando código '{codigo_nuevo}' al apoderado ID {apoderado_id}")
        
        # Actualizar directamente en la base de datos sin usar el modelo
        # (porque el campo puede no existir todavía)
        try:
            with connection.cursor() as cursor:
                # Verificar si la columna codigo_apoderado existe
                cursor.execute("PRAGMA table_info(smapp_apoderado)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'codigo_apoderado' in columns:
                    cursor.execute(
                        "UPDATE smapp_apoderado SET codigo_apoderado = ? WHERE id = ?",
                        [codigo_nuevo, apoderado_id]
                    )
                    print(f"  ✓ Código actualizado en BD")
                else:
                    print(f"  ⚠ Campo codigo_apoderado no existe aún")
        except Exception as e:
            print(f"  ✗ Error al actualizar: {e}")
    
    print("\n=== VERIFICACIÓN FINAL ===")
    # Verificar si hay duplicados después de la corrección
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(smapp_apoderado)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'codigo_apoderado' in columns:
            cursor.execute("""
                SELECT codigo_apoderado, COUNT(*) 
                FROM smapp_apoderado 
                GROUP BY codigo_apoderado 
                HAVING COUNT(*) > 1
            """)
            duplicados = cursor.fetchall()
            
            if duplicados:
                print("⚠ DUPLICADOS ENCONTRADOS:")
                for codigo, count in duplicados:
                    print(f"  - Código '{codigo}': {count} veces")
            else:
                print("✓ No se encontraron duplicados")
        else:
            print("Campo codigo_apoderado no existe, se creará en la migración")

if __name__ == "__main__":
    fix_apoderado_data()
