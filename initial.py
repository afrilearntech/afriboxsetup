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
HOTSPOT_IP = "192.168.12.1"

print(f"🚀 Setting up {HOTSPOT_SSID} with Captive Portal...")

# -----------------------------
# 1. SYSTEM UPDATE
# -----------------------------
run("sudo apt update", "STEP 1: UPDATE")
run("sudo apt upgrade -y", "STEP 1: UPDATE")

# -----------------------------
# 2. INSTALL PACKAGES
# -----------------------------
packages = [
    "lighttpd",
    "network-manager",
    "iptables-persistent"
]

run(f"sudo apt install -y {' '.join(packages)}", "STEP 2: INSTALL PACKAGES")

# -----------------------------
# 3. CONFIGURE NETWORKMANAGER DNS (FIX CONFLICT)
# -----------------------------
print("\n🌐 Configuring NetworkManager DNS...")

dns_config = f"""
# AfriBox DNS config
dhcp-range=192.168.12.10,192.168.12.100,12h
address=/#/{HOTSPOT_IP}
"""

with open("/tmp/afribox-dns.conf", "w") as f:
    f.write(dns_config)

run("sudo mkdir -p /etc/NetworkManager/dnsmasq.d", "STEP 3: DNS SETUP")
run("sudo mv /tmp/afribox-dns.conf /etc/NetworkManager/dnsmasq.d/afribox.conf", "STEP 3: DNS SETUP")

nm_conf = """
[main]
dns=dnsmasq
"""

with open("/tmp/NetworkManager.conf", "w") as f:
    f.write(nm_conf)

run("sudo mv /tmp/NetworkManager.conf /etc/NetworkManager/NetworkManager.conf", "STEP 3: DNS SETUP")

run("sudo systemctl restart NetworkManager", "STEP 3: DNS SETUP")

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
# 5. SETUP CAPTIVE PORTAL PAGE
# -----------------------------
print("\n🌍 Setting up captive portal page...")

html = f"""
<!DOCTYPE html>
<html>
<head>
<title>AfriBox</title>
<style>
body {{
    font-family: Arial;
    text-align: center;
    margin-top: 100px;
}}
h1 {{ color: #2c3e50; }}
</style>
</head>
<body>
<h1>Welcome to AfriBox</h1>
<p>Your offline learning platform</p>
<a href="http://{HOTSPOT_IP}">Enter Platform</a>
</body>
</html>
"""

run("sudo mkdir -p /var/www/html", "STEP 5: PORTAL")

with open("/tmp/index.html", "w") as f:
    f.write(html)

run("sudo mv /tmp/index.html /var/www/html/index.html", "STEP 5: PORTAL")
run("sudo systemctl restart lighttpd", "STEP 5: PORTAL")

# -----------------------------
# 5B. CAPTIVE PORTAL AUTO POPUP
# -----------------------------
print("\n📲 Enabling captive portal auto-popup...")

portal_conf = """
server.modules += ("mod_rewrite")

$HTTP["host"] =~ "captive.apple.com" {
    url.rewrite = (".*" => "http://192.168.12.1")
}

$HTTP["host"] =~ "connectivitycheck.gstatic.com" {
    url.rewrite = (".*" => "http://192.168.12.1")
}

$HTTP["host"] =~ "www.msftconnecttest.com" {
    url.rewrite = (".*" => "http://192.168.12.1")
}

$HTTP["host"] =~ "msftconnecttest.com" {
    url.rewrite = (".*" => "http://192.168.12.1")
}

$HTTP["host"] =~ "clients3.google.com" {
    url.rewrite = (".*" => "http://192.168.12.1")
}
"""

with open("/tmp/captive.conf", "w") as f:
    f.write(portal_conf)

run("sudo mkdir -p /etc/lighttpd/conf-available", "STEP 5B: CAPTIVE")
run("sudo mv /tmp/captive.conf /etc/lighttpd/conf-available/99-afribox-captive.conf", "STEP 5B: CAPTIVE")

# run("sudo lighty-enable-mod redirect", "STEP 5B: CAPTIVE")
# run("sudo lighty-enable-mod setenv", "STEP 5B: CAPTIVE")
run("sudo apt install -y lighttpd-modules-simple", "STEP 5B: INSTALL MODULES")
run("sudo lighty-enable-mod rewrite", "STEP 5B: CAPTIVE")

# Enable config
run("sudo ln -sf /etc/lighttpd/conf-available/99-afribox-captive.conf /etc/lighttpd/conf-enabled/", "STEP 5B: CAPTIVE")

run("sudo systemctl restart lighttpd", "STEP 5B: CAPTIVE")

# -----------------------------
# 6. ENABLE IP FORWARDING
# -----------------------------
run("sudo sysctl -w net.ipv4.ip_forward=1", "STEP 6: IP FORWARDING")

# Persist it
run('echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf', "STEP 6: IP FORWARDING")

# -----------------------------
# 7. IPTABLES (CAPTIVE PORTAL REDIRECT)
# -----------------------------
print("\n🔁 Setting up traffic redirect...")

run("sudo iptables -t nat -F", "STEP 7: IPTABLES")

# Redirect all HTTP traffic to portal
run(
    f"sudo iptables -t nat -A PREROUTING -i {HOTSPOT_INTERFACE} "
    f"-p tcp --dport 80 -j DNAT --to-destination {HOTSPOT_IP}:80",
    "STEP 7: IPTABLES"
)

# Allow DNS traffic
run(
    f"sudo iptables -A INPUT -i {HOTSPOT_INTERFACE} -p udp --dport 53 -j ACCEPT",
    "STEP 7: IPTABLES"
)

# Save rules
run("sudo netfilter-persistent save", "STEP 7: IPTABLES")

# -----------------------------
# 8. ENABLE SERVICES
# -----------------------------
run("sudo systemctl enable NetworkManager", "STEP 8: SERVICES")
run("sudo systemctl enable lighttpd", "STEP 8: SERVICES")

# -----------------------------
# DONE
# -----------------------------
print("\n✅ AfriBox Captive Portal Ready!")
print(f"📡 SSID: {HOTSPOT_SSID}")
print(f"🔐 Password: {HOTSPOT_PASSWORD}")
print(f"🌐 Portal: http://{HOTSPOT_IP}")