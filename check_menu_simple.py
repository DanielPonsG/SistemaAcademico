#!/usr/bin/env python
"""
Script simple para verificar el menú ultra-simplificado de apoderados.
"""

def verificar_menu():
    try:
        with open('templates/index_master.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar sección de apoderados
        inicio = content.find("{% elif user.is_authenticated and user.apoderado %}")
        fin = content.find("{% elif", inicio + 1)
        if fin == -1:
            fin = content.find("{% endif %}", inicio)
        
        seccion_apoderados = content[inicio:fin]
        
        print("=== MENÚ PARA APODERADOS ===")
        print(seccion_apoderados)
        print("\n=== VERIFICACIONES ===")
        
        # Contar secciones y enlaces
        secciones = seccion_apoderados.count("menu_section")
        enlaces = seccion_apoderados.count("<a href=")
        
        print(f"✅ Secciones de menú encontradas: {secciones}")
        print(f"✅ Enlaces de navegación encontrados: {enlaces}")
        
        # Verificar contenido específico
        checks = [
            ("MIS ESTUDIANTES", "MIS ESTUDIANTES" in seccion_apoderados),
            ("Ver Mis Estudiantes", "Ver Mis Estudiantes" in seccion_apoderados),
            ("Sin notas", "Ver Notas" not in seccion_apoderados),
            ("Sin asistencia", "Ver Asistencia" not in seccion_apoderados),
            ("Sin anotaciones", "Ver Anotaciones" not in seccion_apoderados),
            ("Sin calendario", "Calendario" not in seccion_apoderados),
            ("Sin horarios", "Ver Horarios" not in seccion_apoderados),
        ]
        
        for desc, check in checks:
            estado = "✅" if check else "❌"
            print(f"{estado} {desc}")
        
        if secciones == 1 and enlaces == 1:
            print("\n🎉 ¡MENÚ ULTRA-SIMPLIFICADO CORRECTO!")
            print("✅ Solo una sección con una opción para apoderados")
        else:
            print(f"\n⚠️ Advertencia: Se esperaba 1 sección y 1 enlace, se encontró {secciones} secciones y {enlaces} enlaces")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verificar_menu()
