#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para descargar FullCalendar localmente y evitar problemas de CDN
"""
import os
import requests
from urllib.parse import urlparse

def descargar_archivo(url, ruta_destino):
    """Descargar archivo desde URL a ruta local"""
    try:
        print(f"📥 Descargando: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)
        
        # Escribir archivo
        with open(ruta_destino, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Descargado: {ruta_destino}")
        return True
    except Exception as e:
        print(f"❌ Error descargando {url}: {e}")
        return False

def descargar_fullcalendar():
    """Descargar archivos de FullCalendar"""
    
    # URLs de FullCalendar
    urls = {
        'css': 'https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/main.min.css',
        'js': 'https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/main.min.js',
        'locale_es': 'https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/locales/es.min.js'
    }
    
    # Directorio de destino
    base_dir = 'static/fullcalendar'
    
    # Descargar archivos
    exito = True
    for nombre, url in urls.items():
        extension = 'css' if nombre == 'css' else 'js'
        ruta_destino = os.path.join(base_dir, f'{nombre}.{extension}')
        
        if not descargar_archivo(url, ruta_destino):
            exito = False
    
    if exito:
        print("\n✅ FullCalendar descargado exitosamente")
        print(f"📁 Archivos en: {base_dir}/")
        
        # Crear template que use archivos locales
        crear_template_local()
    else:
        print("\n❌ Hubo errores al descargar FullCalendar")

def crear_template_local():
    """Crear template que use FullCalendar local"""
    template_content = '''{% load static %}
{% extends "index_master.html" %}

{% block content %}
<div class="right_col" role="main">
  <div class="container-fluid">
    
    <!-- Header -->
    <div class="row mb-4">
      <div class="col-12">
        <div class="bg-white p-4 rounded shadow-sm border">
          <h1 class="h3 mb-3 text-dark">📅 Calendario Académico Local</h1>
          <p class="text-muted">
            Usuario: {{ user.first_name|default:user.username }} | 
            Tipo: {{ user_type|capfirst }} | 
            Eventos: {{ eventos.count }}
          </p>
        </div>
      </div>
    </div>
    
    <!-- Calendario -->
    <div class="row">
      <div class="col-12">
        <div class="card">
          <div class="card-header">
            <h5>📅 Calendario de Eventos</h5>
          </div>
          <div class="card-body">
            <div id="calendar-loading" class="text-center p-4">
              <i class="fas fa-spinner fa-spin fa-3x text-primary mb-3"></i>
              <p>Cargando calendario local...</p>
            </div>
            <div id="calendar" style="height: 600px; display: none;"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- FullCalendar Local CSS -->
<link href="{% static 'fullcalendar/css.css' %}" rel="stylesheet">

<style>
#calendar {
  border: 1px solid #ddd;
  border-radius: 5px;
}

.fc-event {
  border-radius: 4px !important;
  border: none !important;
  font-weight: 600;
}
</style>

<!-- FullCalendar Local JavaScript -->
<script src="{% static 'fullcalendar/js.js' %}"></script>
<script src="{% static 'fullcalendar/locale_es.js' %}"></script>

<script>
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Inicializando calendario local...');
    
    const calendarEl = document.getElementById('calendar');
    const loadingEl = document.getElementById('calendar-loading');
    
    if (typeof FullCalendar === 'undefined') {
        console.error('❌ FullCalendar local no disponible');
        loadingEl.innerHTML = '<div class="alert alert-danger">❌ Error: FullCalendar local no disponible</div>';
        return;
    }
    
    const eventosData = {{ eventos_json|safe|default:"[]" }};
    console.log('📅 Eventos:', eventosData.length);
    
    try {
        const calendar = new FullCalendar.Calendar(calendarEl, {
            locale: 'es',
            initialView: 'dayGridMonth',
            height: 550,
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,listWeek'
            },
            events: eventosData,
            eventClick: function(info) {
                alert('📅 ' + info.event.title + '\\n📆 ' + info.event.start.toLocaleDateString('es-ES'));
            }
        });
        
        calendar.render();
        loadingEl.style.display = 'none';
        calendarEl.style.display = 'block';
        
        console.log('✅ Calendario local renderizado');
        
    } catch (error) {
        console.error('❌ Error:', error);
        loadingEl.innerHTML = '<div class="alert alert-danger">❌ Error: ' + error.message + '</div>';
    }
});
</script>

{% endblock %}'''
    
    with open('templates/calendario_local.html', 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print("📄 Template local creado: templates/calendario_local.html")

if __name__ == "__main__":
    print("🔧 DESCARGADOR DE FULLCALENDAR LOCAL")
    print("=" * 50)
    
    # Verificar si requests está disponible
    try:
        import requests
    except ImportError:
        print("❌ Error: Se requiere la librería 'requests'")
        print("Instalar con: pip install requests")
        exit(1)
    
    descargar_fullcalendar()
