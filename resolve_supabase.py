import socket
import subprocess
import re

hostname = "db.kmmhawvuosfnszhrnrbh.supabase.co"

print(f"Resolving {hostname}...")

# Method 1: Socket (System DNS)
try:
    ip = socket.gethostbyname(hostname)
    print(f"Standard DNS: {hostname} -> {ip}")
except Exception as e:
    print(f"Standard DNS failed: {e}")

# Method 2: nslookup with Google DNS
print("Attempting resolution via Google DNS (8.8.8.8)...")
try:
    # Run nslookup command forcing IPv4 (A record)
    result = subprocess.run(['nslookup', '-type=A', hostname, '8.8.8.8'], capture_output=True, text=True)
    output = result.stdout
    print("nslookup output:")
    print(output)
    
    # Extract IP from output
    # Look for "Address: <IP>" lines, skipping the first one (which is the DNS server itself)
    # Regex to find IPs
    ips = re.findall(r'Address:\s+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', output)
    
    target_ip = None
    if len(ips) > 0:
        # Usually the last one is the answer, the first one is the server
        for ip in reversed(ips):
            if not ip.startswith('8.8.8.8') and not ip.startswith('8.8.4.4'):
                target_ip = ip
                break
    
    if target_ip:
        print(f"Found IP via nslookup: {target_ip}")
    else:
        print("Could not parse IP from nslookup output")

except Exception as e:
    print(f"nslookup failed: {e}")
