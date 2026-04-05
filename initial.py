import subprocess
import sys

def run(cmd, step: str = ""):
    print(f"\n🔹 {step.upper()} [RUNNING]: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ ERROR: {cmd}")
        sys.exit(1)

# -----------------------------
# CONFIG
# -----------------------------
HOTSPOT_INTERFACE = "wlo1"
HOTSPOT_SSID = "Afribox"
HOTSPOT_PASSWORD = "afribox-lr"
HOTSPOT_IP = "10.42.0.1"

print(f"🚀 Setting up {HOTSPOT_SSID} with NGINX Captive Portal...")

# -----------------------------
# 1. SYSTEM UPDATE
# -----------------------------
run("sudo apt update", "STEP 1: UPDATE")
run("sudo apt upgrade -y", "STEP 1: UPDATE")

# -----------------------------
# 2. INSTALL PACKAGES
# -----------------------------
packages = [
    "nginx",
    "network-manager",
    "iptables-persistent"
]

run(f"sudo apt install -y {' '.join(packages)}", "STEP 2: INSTALL PACKAGES")

# -----------------------------
# 3. CONFIGURE DNS (NetworkManager dnsmasq)
# -----------------------------
print("\n🌐 Configuring DNS...")

# dhcp-range=192.168.12.10,192.168.12.100,12h
dns_config = f"""
dhcp-range=10.42.0.10,10.42.0.100,12h
address=/#/{HOTSPOT_IP}
address=/afribox.lan/{HOTSPOT_IP}
address=/lr.afribox.lan/{HOTSPOT_IP}

address=/connectivitycheck.gstatic.com/{HOTSPOT_IP}
address=/clients3.google.com/{HOTSPOT_IP}
address=/captive.apple.com/{HOTSPOT_IP}
address=/www.msftconnecttest.com/{HOTSPOT_IP}
"""

with open("/tmp/afribox-dns.conf", "w") as f:
    f.write(dns_config)

run("sudo mkdir -p /etc/NetworkManager/dnsmasq.d", "STEP 3: DNS")
run("sudo mv /tmp/afribox-dns.conf /etc/NetworkManager/dnsmasq.d/afribox.conf", "STEP 3: DNS")

nm_conf = """
[main]
dns=dnsmasq
"""

with open("/tmp/NetworkManager.conf", "w") as f:
    f.write(nm_conf)

run("sudo mv /tmp/NetworkManager.conf /etc/NetworkManager/NetworkManager.conf", "STEP 3: DNS")
run("sudo systemctl restart NetworkManager", "STEP 3: DNS")

# -----------------------------
# 4. SETUP HOTSPOT
# -----------------------------
print("\n📡 Setting up hotspot...")

run(f"nmcli connection delete {HOTSPOT_SSID} || true", "STEP 4: HOTSPOT")

run(
    f'nmcli connection add type wifi ifname {HOTSPOT_INTERFACE} '
    f'con-name {HOTSPOT_SSID} autoconnect yes ssid {HOTSPOT_SSID}',
    "STEP 4: HOTSPOT"
)

run(f"nmcli connection modify {HOTSPOT_SSID} 802-11-wireless.mode ap", "STEP 4: HOTSPOT")
run(f"nmcli connection modify {HOTSPOT_SSID} ipv4.method shared", "STEP 4: HOTSPOT")
run(f"nmcli connection modify {HOTSPOT_SSID} wifi-sec.key-mgmt wpa-psk", "STEP 4: HOTSPOT")
run(f'nmcli connection modify {HOTSPOT_SSID} wifi-sec.psk "{HOTSPOT_PASSWORD}"', "STEP 4: HOTSPOT")

run(f"nmcli connection up {HOTSPOT_SSID}", "STEP 4: HOTSPOT")

# -----------------------------
# 5. CREATE PORTAL PAGE
# -----------------------------
print("\n🌍 Setting up portal page...")

html = f"""
<!DOCTYPE html>
<html>
<head>
<title>AfriBox</title>
<meta http-equiv="refresh" content="0; url=http://lr.afribox.lan">
<style>
body {{
    font-family: Arial;
    text-align: center;
    margin-top: 100px;
}}
</style>
</head>
<body>
<h1>Welcome to AfriBox</h1>
<p>Redirecting...</p>
</body>
</html>
"""

run("sudo mkdir -p /var/www/html", "STEP 5: PORTAL")

with open("/tmp/index.html", "w") as f:
    f.write(html)

run("sudo mv /tmp/index.html /var/www/html/index.html", "STEP 5: PORTAL")

# -----------------------------
# 6. NGINX CONFIG
# -----------------------------
print("\n🌐 Configuring NGINX...")

nginx_conf = f"""
upstream afrilearn_app {{
    server 127.0.0.1:8001;
}}

server {{
    listen 80 default_server;
    server_name _;

    # Captive portal triggers

    location /generate_204 {{
        return 302 http://{HOTSPOT_IP};
    }}

    location /gen_204 {{
        return 302 http://{HOTSPOT_IP};
    }}

    location /hotspot-detect.html {{
        return 302 http://{HOTSPOT_IP};
    }}

    location /connecttest.txt {{
        return 302 http://{HOTSPOT_IP};
    }}

    location /ncsi.txt {{
        return 302 http://{HOTSPOT_IP};
    }}

    # Main routing

    location / {{
        if ($host = "lr.afribox.local") {{
            proxy_pass http://afrilearn_app;
            break;
        }}

        root /var/www/html;
        index index.html;
    }}

    location /staticfiles/ {{
        root /afrilearn/elearncore;
    }}

    location /assets/ {{
        root /afrilearn/elearncore;
    }}
}}
"""

with open("/tmp/afribox_nginx", "w") as f:
    f.write(nginx_conf)

run("sudo mv /tmp/afribox_nginx /etc/nginx/sites-available/afribox", "STEP 6: NGINX")

run("sudo ln -sf /etc/nginx/sites-available/afribox /etc/nginx/sites-enabled/", "STEP 6: NGINX")
run("sudo rm -f /etc/nginx/sites-enabled/default", "STEP 6: NGINX")
run("sudo nginx -t", "STEP 6: NGINX")

run("sudo systemctl restart nginx", "STEP 6: NGINX")

# -----------------------------
# 7. ENABLE SERVICES
# -----------------------------
run("sudo systemctl enable NetworkManager", "STEP 7: SERVICES")
run("sudo systemctl enable nginx", "STEP 7: SERVICES")

# -----------------------------
# DONE
# -----------------------------
print("\n✅ AfriBox Ready (NGINX MODE)!")
print(f"📡 SSID: {HOTSPOT_SSID}")
print(f"🔐 Password: {HOTSPOT_PASSWORD}")
print("🌐 Auto popup enabled")
print("🚀 App: http://lr.afribox.lan")