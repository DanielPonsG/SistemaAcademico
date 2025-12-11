
content = """DATABASE_URL=postgresql://postgres.dxnjraijhvumhxvzgioy:inacap@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
DEBUG=True
SECRET_KEY=django-insecure-m#4xd(+=97eyuwi7bt5sw_h#^j9)8pb2m&p)vaajgq3t%0r$ll
"""
with open('.env', 'w') as f:
    f.write(content)
print("Updated .env to use Pooler")
