import subprocess
import sys
import os

def run(cmd):
    print(f"\n[RUNNING]: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"[ERROR]: {cmd}")
        sys.exit(1)

HOTSPOT_INTERFACE = "wlo1" 
HOTSPOT_SSID = "Afribox"
HOTSPOT_PASSWORD = "afribox-lr"


print(f"🚀 Setting up {HOTSPOT_SSID} with Captive Portal...")

# -----------------------------
# 1. Update system
# -----------------------------
run("sudo apt update")
run("sudo apt upgrade -y")

# -----------------------------
# 2. Install packages
# -----------------------------
packages = [
    "dnsmasq",
    "lighttpd",
    "network-manager"
]

run(f"sudo apt install -y {' '.join(packages)}")

# -----------------------------
# 3. Setup Hotspot
# -----------------------------
run("nmcli connection delete Afribox || true")

run(f'nmcli connection add type wifi ifname {HOTSPOT_INTERFACE} con-name {HOTSPOT_SSID} autoconnect yes ssid {HOTSPOT_SSID}')
run(f"nmcli connection modify {HOTSPOT_SSID} 802-11-wireless.mode ap")
run(f"nmcli connection modify {HOTSPOT_SSID} ipv4.method shared")
run(f"nmcli connection modify {HOTSPOT_SSID} wifi-sec.key-mgmt wpa-psk")
run(f'nmcli connection modify {HOTSPOT_SSID} wifi-sec.psk "{HOTSPOT_PASSWORD}"')
run(f"nmcli connection up {HOTSPOT_SSID}")

# -----------------------------
# 4. Configure DNS (FORCE REDIRECT)
# -----------------------------
dns_config = """
interface={HOTSPOT_INTERFACE}
dhcp-range=192.168.12.10,192.168.12.100,12h

# Redirect ALL domains to AfriBox
address=/#/192.168.12.1
""".format(HOTSPOT_INTERFACE=HOTSPOT_INTERFACE)

with open("/tmp/dnsmasq.conf", "w") as f:
    f.write(dns_config)

run("sudo mv /tmp/dnsmasq.conf /etc/dnsmasq.conf")
run("sudo systemctl restart dnsmasq")

# -----------------------------
# 5. Setup Captive Portal Page
# -----------------------------
html = """
<!DOCTYPE html>
<html>
<head>
<title>AfriBox</title>
<style>
body { font-family: Arial; text-align: center; margin-top: 100px; }
h1 { color: #2c3e50; }
</style>
</head>
<body>
<h1>Welcome to AfriBox</h1>
<p>Your offline learning platform</p>
<a href="http://lr.afribox.local">Enter Platform</a>
</body>
</html>
"""

run("sudo mkdir -p /var/www/html")
with open("/tmp/index.html", "w") as f:
    f.write(html)

run("sudo mv /tmp/index.html /var/www/html/index.html")
run("sudo systemctl restart lighttpd")

# -----------------------------
# 6. Enable IP forwarding
# -----------------------------
run("sudo sysctl -w net.ipv4.ip_forward=1")

# -----------------------------
# 7. IPTABLES Redirect (CAPTIVE PORTAL)
# -----------------------------
run("sudo iptables -t nat -F")

# Redirect all HTTP traffic to portal
run(f"sudo iptables -t nat -A PREROUTING -i {HOTSPOT_INTERFACE} -p tcp --dport 80 -j DNAT --to-destination 192.168.12.1:80")

# Allow DNS
run(f"sudo iptables -A INPUT -i {HOTSPOT_INTERFACE} -p udp --dport 53 -j ACCEPT")

# -----------------------------
# 8. Save iptables rules
# -----------------------------
run("sudo apt install -y iptables-persistent")
run("sudo netfilter-persistent save")

# -----------------------------
# 9. Enable services
# -----------------------------
run("sudo systemctl enable dnsmasq")
run("sudo systemctl enable lighttpd")
run("sudo systemctl enable NetworkManager")

print("\n✅ Captive Portal Ready!")
print(f"📡 SSID: {HOTSPOT_SSID}")
print(f"🔐 Password: {HOTSPOT_PASSWORD}")
print("🌐 Portal: http://lr.afribox.local")