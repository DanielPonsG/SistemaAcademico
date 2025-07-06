#!/usr/bin/env python
"""
Script para desasociar estudiantes de un apoderado específico,
permitiendo así que pueda ser eliminado.
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sma.settings')
django.setup()

from smapp.models import Apoderado, RelacionApoderadoEstudiante

def main():
    print("🔧 HERRAMIENTA PARA DESASOCIAR ESTUDIANTES DE APODERADO")
    print("=" * 65)
    
    try:
        # Mostrar apoderados con estudiantes
        apoderados_con_estudiantes = []
        
        for apoderado in Apoderado.objects.all():
            relaciones = RelacionApoderadoEstudiante.objects.filter(apoderado=apoderado)
            if relaciones.exists():
                apoderados_con_estudiantes.append({
                    'apoderado': apoderado,
                    'relaciones': relaciones,
                    'count': relaciones.count()
                })
        
        if not apoderados_con_estudiantes:
            print("✅ No hay apoderados con estudiantes asociados.")
            return
        
        print(f"📋 APODERADOS CON ESTUDIANTES ASOCIADOS:")
        print()
        
        for i, data in enumerate(apoderados_con_estudiantes, 1):
            apoderado = data['apoderado']
            relaciones = data['relaciones']
            count = data['count']
            
            print(f"{i}. {apoderado.get_nombre_completo()}")
            print(f"   ID: {apoderado.id}")
            print(f"   RUT: {apoderado.numero_documento}")
            print(f"   Estudiantes: {count}")
            
            for relacion in relaciones:
                estudiante = relacion.estudiante
                print(f"     - {estudiante.get_nombre_completo()} ({estudiante.codigo_estudiante})")
            print()
        
        # Permitir selección
        print("🎯 SELECCIONAR APODERADO PARA DESASOCIAR ESTUDIANTES:")
        print("Ingrese el número del apoderado (1-{}) o 'q' para salir:".format(len(apoderados_con_estudiantes)))
        
        opcion = input("> ").strip()
        
        if opcion.lower() == 'q':
            print("👋 Saliendo...")
            return
        
        try:
            indice = int(opcion) - 1
            if indice < 0 or indice >= len(apoderados_con_estudiantes):
                print("❌ Opción inválida")
                return
        except ValueError:
            print("❌ Debe ingresar un número válido")
            return
        
        # Procesar desasociación
        data_seleccionada = apoderados_con_estudiantes[indice]
        apoderado = data_seleccionada['apoderado']
        relaciones = data_seleccionada['relaciones']
        
        print(f"\n🎯 APODERADO SELECCIONADO: {apoderado.get_nombre_completo()}")
        print(f"📝 Estudiantes a desasociar: {relaciones.count()}")
        print()
        
        confirmacion = input("¿Confirma que desea desasociar TODOS los estudiantes de este apoderado? (si/no): ").strip().lower()
        
        if confirmacion not in ['si', 'sí', 's', 'yes', 'y']:
            print("❌ Operación cancelada")
            return
        
        # Realizar desasociación
        print(f"\n🔄 DESASOCIANDO ESTUDIANTES...")
        
        estudiantes_desasociados = []
        for relacion in relaciones:
            estudiante = relacion.estudiante
            estudiantes_desasociados.append(estudiante.get_nombre_completo())
            relacion.delete()
            print(f"   ✅ {estudiante.get_nombre_completo()} desasociado")
        
        print(f"\n✅ DESASOCIACIÓN COMPLETADA:")
        print(f"   - Apoderado: {apoderado.get_nombre_completo()}")
        print(f"   - Estudiantes desasociados: {len(estudiantes_desasociados)}")
        print(f"   - ✅ Ahora este apoderado se puede eliminar")
        
        # Verificar que ya no tiene estudiantes
        verificacion = RelacionApoderadoEstudiante.objects.filter(apoderado=apoderado)
        if not verificacion.exists():
            print(f"\n🎉 CONFIRMADO: El apoderado ya no tiene estudiantes asociados")
            print(f"🔗 URL para eliminar: /apoderados/eliminar/{apoderado.id}/")
        else:
            print(f"\n❌ ERROR: Aún quedan {verificacion.count()} relaciones")
        
    except Exception as e:
        print(f"❌ Error durante la operación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
