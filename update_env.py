
content = """DATABASE_URL=postgresql://postgres:inacap@db.dxnjraijhvumhxvzgioy.supabase.co:5432/postgres
DEBUG=True
SECRET_KEY=django-insecure-m#4xd(+=97eyuwi7bt5sw_h#^j9)8pb2m&p)vaajgq3t%0r$ll
"""
with open('.env', 'w') as f:
    f.write(content)
print("Updated .env")
