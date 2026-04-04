import subprocess
import sys
import os

def run(cmd, step: str = ""):
    print(f"\n {step.upper()} [RUNNING]: {cmd}")
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
run("sudo apt update", "STEP 1: UPDATE")
run("sudo apt upgrade -y", "STEP 1: UPDATE")

# -----------------------------
# 2. Install packages
# -----------------------------
packages = [
    "dnsmasq",
    "lighttpd",
    "network-manager"
]

run(f"sudo apt install -y {' '.join(packages)}", "STEP 2: INSTALL PACKAGES")

# -----------------------------
# 3. Setup Hotspot
# -----------------------------
run("nmcli connection delete Afribox || true", "STEP 3: SETUP HOTSPOT")

run(f'nmcli connection add type wifi ifname {HOTSPOT_INTERFACE} con-name {HOTSPOT_SSID} autoconnect yes ssid {HOTSPOT_SSID}', "STEP 3: SETUP HOTSPOT")
run(f"nmcli connection modify {HOTSPOT_SSID} 802-11-wireless.mode ap", "STEP 3: SETUP HOTSPOT")
run(f"nmcli connection modify {HOTSPOT_SSID} ipv4.method shared", "STEP 3: SETUP HOTSPOT")
run(f"nmcli connection modify {HOTSPOT_SSID} wifi-sec.key-mgmt wpa-psk", "STEP 3: SETUP HOTSPOT")
run(f'nmcli connection modify {HOTSPOT_SSID} wifi-sec.psk "{HOTSPOT_PASSWORD}"', "STEP 3: SETUP HOTSPOT")
run(f"nmcli connection up {HOTSPOT_SSID}", "STEP 3: SETUP HOTSPOT")

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

run("sudo mv /tmp/dnsmasq.conf /etc/dnsmasq.conf", "STEP 4: CONFIGURE DNS")
run("sudo systemctl restart dnsmasq", "STEP 4: CONFIGURE DNS")

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

run("sudo mv /tmp/index.html /var/www/html/index.html", "STEP 5: SETUP CAPTIVE PORTAL")
run("sudo systemctl restart lighttpd", "STEP 5: SETUP CAPTIVE PORTAL")

# -----------------------------
# 6. Enable IP forwarding
# -----------------------------
run("sudo sysctl -w net.ipv4.ip_forward=1", "STEP 6: ENABLE IP FORWARDING")

# -----------------------------
# 7. IPTABLES Redirect (CAPTIVE PORTAL)
# -----------------------------
run("sudo iptables -t nat -F", "STEP 7: IPTABLES REDIRECT")

# Redirect all HTTP traffic to portal
run(f"sudo iptables -t nat -A PREROUTING -i {HOTSPOT_INTERFACE} -p tcp --dport 80 -j DNAT --to-destination 192.168.12.1:80", "STEP 7: IPTABLES REDIRECT")

# Allow DNS
run(f"sudo iptables -A INPUT -i {HOTSPOT_INTERFACE} -p udp --dport 53 -j ACCEPT", "STEP 7: IPTABLES REDIRECT")

# -----------------------------
# 8. Save iptables rules
# -----------------------------
run("sudo apt install -y iptables-persistent", "STEP 8: SAVE IPTABLES")
run("sudo netfilter-persistent save", "STEP 8: SAVE IPTABLES")

# -----------------------------
# 9. Enable services
# -----------------------------
run("sudo systemctl enable dnsmasq", "STEP 9: ENABLE SERVICES")
run("sudo systemctl enable lighttpd", "STEP 9: ENABLE SERVICES")
run("sudo systemctl enable NetworkManager", "STEP 9: ENABLE SERVICES")

print("\n✅ Captive Portal Ready!")
print(f"📡 SSID: {HOTSPOT_SSID}")
print(f"🔐 Password: {HOTSPOT_PASSWORD}")
print("🌐 Portal: http://lr.afribox.local")