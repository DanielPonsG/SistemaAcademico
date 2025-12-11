
try:
    with open('.env', 'r') as f:
        print(f.read())
except FileNotFoundError:
    print(".env not found")
