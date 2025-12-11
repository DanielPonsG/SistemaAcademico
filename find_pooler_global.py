import psycopg2
import socket
import sys

PROJECT_ID = "dxnjraijhvumhxvzgioy"
DB_PASS = "inacap"
DB_NAME = "postgres"

# List of known Supabase Pooler endpoints
POOLERS = [
    ("Sao Paulo", "aws-0-sa-east-1.pooler.supabase.com"),
    ("US East (N. Virginia)", "aws-0-us-east-1.pooler.supabase.com"),
    ("US West (N. California)", "aws-0-us-west-1.pooler.supabase.com"),
    ("US West (Oregon)", "aws-0-us-west-2.pooler.supabase.com"),
    ("EU Central (Frankfurt)", "aws-0-eu-central-1.pooler.supabase.com"),
    ("EU West (Ireland)", "aws-0-eu-west-1.pooler.supabase.com"),
    ("EU West (London)", "aws-0-eu-west-2.pooler.supabase.com"),
    ("EU West (Paris)", "aws-0-eu-west-3.pooler.supabase.com"),
    ("Asia Pacific (Singapore)", "aws-0-ap-southeast-1.pooler.supabase.com"),
    ("Asia Pacific (Tokyo)", "aws-0-ap-northeast-1.pooler.supabase.com"),
    ("Asia Pacific (Seoul)", "aws-0-ap-northeast-2.pooler.supabase.com"),
    ("Asia Pacific (Sydney)", "aws-0-ap-southeast-2.pooler.supabase.com"),
    ("Asia Pacific (Mumbai)", "aws-0-ap-south-1.pooler.supabase.com"),
    ("Canada (Central)", "aws-0-ca-central-1.pooler.supabase.com"),
]

def check_pooler(name, host):
    print(f"Checking {name} ({host})...", end=" ")
    
    # 1. DNS Check
    try:
        socket.gethostbyname(host)
    except:
        print("DNS FAILED")
        return False

    # 2. Connection Check
    user = f"postgres.{PROJECT_ID}"
    try:
        conn = psycopg2.connect(
            host=host,
            database=DB_NAME,
            user=user,
            password=DB_PASS,
            port=6543,
            connect_timeout=3
        )
        print("SUCCESS! Connected.")
        conn.close()
        return True
    except psycopg2.OperationalError as e:
        msg = str(e)
        if "Tenant or user not found" in msg:
            print("Tenant not found.")
        elif "password authentication failed" in msg:
            print("FOUND! (Password error)")
            return True
        else:
            print(f"Error: {msg}")
    except Exception as e:
        print(f"Error: {e}")
    
    return False

print(f"--- Searching for Project {PROJECT_ID} ---")
found_host = None
for name, host in POOLERS:
    if check_pooler(name, host):
        found_host = host
        break

if found_host:
    print(f"\n>>> FOUND POOLER: {found_host} <<<")
else:
    print("\n>>> NOT FOUND IN ANY REGION <<<")
