#!/bin/bash
# Script de limpieza para el proyecto SAM

echo "Limpiando proyecto SAM..."

# Eliminar archivos compilados de Python
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Eliminar archivos de log de Django
find . -name "*.log" -delete

# Eliminar archivos temporales del editor
find . -name "*~" -delete
find . -name "*.swp" -delete
find . -name "*.swo" -delete

# Eliminar archivos de backup
find . -name "*_backup*" -delete
find . -name "*.bak" -delete

echo "Limpieza completada."
