"""
Script para verificar que el contexto se está generando correctamente
para la vista inicio del usuario asd
"""
from smapp.models import Estudiante, HorarioCurso, Curso
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta

def simular_vista_inicio(username):
    """Simula la lógica de la vista inicio para un usuario específico"""
    try:
        user = User.objects.get(username=username)
        estudiante = user.estudiante
        anio_actual = timezone.now().year
        
        # Obtener curso actual
        curso_actual = estudiante.cursos.filter(anio=anio_actual).order_by('-nivel').first()
        
        if not curso_actual or estudiante.cursos.filter(anio=anio_actual).count() > 1:
            cursos_anio = estudiante.cursos.filter(anio=anio_actual)
            cursos_medio = cursos_anio.filter(nivel__endswith='M').order_by('-nivel')
            cursos_basico = cursos_anio.filter(nivel__endswith='B').order_by('-nivel')
            
            if cursos_medio.exists():
                curso_actual = cursos_medio.first()
            elif cursos_basico.exists():
                curso_actual = cursos_basico.first()
            else:
                curso_actual = cursos_anio.first()
        
        if not curso_actual:
            curso_actual = estudiante.cursos.order_by('-anio', '-nivel').first()
        
        print(f"✅ Usuario: {username}")
        print(f"✅ Estudiante: {estudiante}")
        print(f"✅ Curso actual: {curso_actual}")
        
        if curso_actual:
            # Lógica de horarios
            hoy = timezone.now().date()
            
            # Mapeo de días
            dias_weekday_a_codigo = {
                0: 'LU', 1: 'MA', 2: 'MI', 3: 'JU', 4: 'VI', 5: 'SA', 6: 'DO'
            }
            
            # Próximos horarios
            proximos_horarios = []
            for i in range(3):
                fecha = hoy + timedelta(days=i)
                dia_semana = fecha.weekday()
                codigo_dia = dias_weekday_a_codigo[dia_semana]
                
                horarios_dia = HorarioCurso.objects.filter(
                    curso=curso_actual,
                    dia=codigo_dia
                ).order_by('hora_inicio')
                
                if horarios_dia.exists():
                    proximos_horarios.append({
                        'fecha': fecha,
                        'dia_nombre': ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][dia_semana],
                        'horarios': horarios_dia
                    })
            
            # Horario semanal completo
            horarios_semana = HorarioCurso.objects.filter(curso=curso_actual).order_by('dia', 'hora_inicio')
            
            dias_codigo_a_info = {
                'LU': {'numero': 1, 'nombre': 'Lunes'},
                'MA': {'numero': 2, 'nombre': 'Martes'},
                'MI': {'numero': 3, 'nombre': 'Miércoles'},
                'JU': {'numero': 4, 'nombre': 'Jueves'},
                'VI': {'numero': 5, 'nombre': 'Viernes'},
                'SA': {'numero': 6, 'nombre': 'Sábado'},
                'DO': {'numero': 7, 'nombre': 'Domingo'}
            }
            
            horario_semanal_completo = []
            for codigo_dia, info_dia in dias_codigo_a_info.items():
                horarios_del_dia = horarios_semana.filter(dia=codigo_dia)
                if horarios_del_dia.exists():
                    horario_semanal_completo.append({
                        'dia_numero': info_dia['numero'],
                        'dia_nombre': info_dia['nombre'],
                        'horarios': horarios_del_dia
                    })
            
            # Horas disponibles
            horas_set = set()
            for horario in horarios_semana:
                horas_set.add(horario.hora_inicio.strftime('%H:%M'))
            horas_disponibles = sorted(list(horas_set))
            
            print(f"✅ Próximos horarios: {len(proximos_horarios)} días")
            print(f"✅ Horario semanal completo: {len(horario_semanal_completo)} días")
            print(f"✅ Horas disponibles: {horas_disponibles}")
            
            # Verificar condiciones del template
            tiene_proximos = len(proximos_horarios) > 0
            tiene_horario_completo = len(horario_semanal_completo) > 0
            
            print(f"\n📊 CONDICIONES DEL TEMPLATE:")
            print(f"   proximos_horarios existe: {tiene_proximos}")
            print(f"   horario_semanal_completo existe: {tiene_horario_completo}")
            print(f"   curso_actual existe: {curso_actual is not None}")
            
            if tiene_proximos and tiene_horario_completo and curso_actual:
                print("✅ ¡LA TABLA DE HORARIOS DEBERÍA MOSTRARSE!")
            else:
                print("❌ La tabla NO se mostrará")
                
            return True
            
        else:
            print("❌ No se encontró curso actual")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# Ejecutar la simulación
simular_vista_inicio('asd')
