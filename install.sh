#!/bin/bash

echo "========================================"
echo "   SAM - School Academic Manager"
echo "       Instalación Automática"
echo "========================================"
echo

# Función para mostrar errores
error_exit() {
    echo "ERROR: $1"
    echo "Por favor revisa los requisitos y vuelve a intentar."
    exit 1
}

# Verificar Python
echo "[1/7] Verificando Python..."
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        error_exit "Python no está instalado. Instala Python 3.8+ desde https://python.org"
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi
echo "✓ Python encontrado"

echo
echo "[2/7] Creando entorno virtual..."
$PYTHON_CMD -m venv .venv || error_exit "No se pudo crear el entorno virtual"
echo "✓ Entorno virtual creado"

echo
echo "[3/7] Activando entorno virtual..."
source .venv/bin/activate || error_exit "No se pudo activar el entorno virtual"
echo "✓ Entorno virtual activado"

echo
echo "[4/7] Instalando dependencias..."
pip install -r requirements.txt || error_exit "No se pudieron instalar las dependencias"
echo "✓ Dependencias instaladas"

echo
echo "[5/7] Recolectando archivos estáticos..."
python collect_static.py || {
    echo "WARNING: Error al recolectar archivos estáticos"
    echo "Intentando método alternativo..."
    python manage.py collectstatic --noinput
}
echo "✓ Archivos estáticos recolectados"

echo
echo "[6/7] Realizando migraciones..."
python manage.py makemigrations
python manage.py migrate || error_exit "No se pudieron realizar las migraciones"
echo "✓ Migraciones completadas"

echo
echo "[7/7] ¡Instalación completada!"
echo
echo "========================================"
echo "Para ejecutar el proyecto:"
echo "  1. Activa el entorno virtual: source .venv/bin/activate"
echo "  2. Ejecuta el servidor: python manage.py runserver"
echo "  3. Abre http://127.0.0.1:8000 en tu navegador"
echo "========================================"
echo

read -p "¿Deseas crear un superusuario ahora? (s/n): " crear_superuser
if [[ $crear_superuser =~ ^[Ss]$ ]]; then
    echo
    echo "Creando superusuario..."
    python manage.py createsuperuser
fi

echo
read -p "¿Deseas ejecutar el servidor ahora? (s/n): " ejecutar_servidor
if [[ $ejecutar_servidor =~ ^[Ss]$ ]]; then
    echo
    echo "Iniciando servidor de desarrollo..."
    echo "Presiona Ctrl+C para detener el servidor"
    python manage.py runserver
fi
