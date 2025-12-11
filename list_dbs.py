import psycopg2

try:
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="inacap",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()
    cur.execute("SELECT datname FROM pg_database;")
    rows = cur.fetchall()
    print("Databases:")
    for row in rows:
        print(f"- {row[0]}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
