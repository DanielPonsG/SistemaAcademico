
import os
import psycopg2
from urllib.parse import urlparse

# Read .env manually to get DATABASE_URL
with open('.env', 'r') as f:
    for line in f:
        if line.startswith('DATABASE_URL='):
            db_url = line.strip().split('=', 1)[1]
            break

print(f"Connecting to: {db_url}")

try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT to_regclass('smapp_perfil');")
    if cursor.fetchone()[0] is None:
        print("Table smapp_perfil does not exist.")
    else:
        print("Table smapp_perfil exists. Checking values...")
        cursor.execute("SELECT DISTINCT tipo_usuario, LENGTH(tipo_usuario) FROM smapp_perfil;")
        rows = cursor.fetchall()
        print("Distinct values in tipo_usuario:")
        for row in rows:
            print(f"Value: '{row[0]}', Length: {row[1]}")
            
    conn.close()

except Exception as e:
    print(f"Error: {e}")
