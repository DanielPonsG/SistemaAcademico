
content = """DATABASE_URL=postgresql://postgres.kmmhawvuosfnszhrnrbh:inacap@aws-0-us-west-2.pooler.supabase.com:6543/postgres
DEBUG=True
SECRET_KEY=django-insecure-m#4xd(+=97eyuwi7bt5sw_h#^j9)8pb2m&p)vaajgq3t%0r$ll
"""
with open('.env', 'w') as f:
    f.write(content)
print("Updated .env with correct Pooler connection")
