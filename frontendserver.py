import subprocess
import sys

def run(cmd, step=""):
    print(f"\n🔹 {step} → {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ FAILED: {cmd}")
        sys.exit(1)

# -----------------------------
# CONFIG
# -----------------------------
APP_DIR = "/afribox/elearnui"
NEXT_PORT = 3001
DJANGO_PORT = 8001
DOMAIN = "lr.afribox.lan"
HOTSPOT_IP = "10.42.0.1"

print("🚀 Deploying Next.js Frontend for AfriBox...")

# -----------------------------
# 1. INSTALL NODE + PM2
# -----------------------------
run("curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -", "Install NodeSource")
run("sudo apt install -y nodejs", "Install Node.js")
run("corepack enable", "Enable Corepack")

# run("sudo npm install -g pm2", "Install PM2")
# run("sudo yarn install -g pm2", "Install PM2")
run("sudo yarn global add pm2", "Install PM2")

# -----------------------------
# 2. INSTALL DEPENDENCIES
# -----------------------------
run(f"cd {APP_DIR} && yarn install", "Install dependencies")

# -----------------------------
# 3. BUILD NEXT APP
# -----------------------------
run(f"cd {APP_DIR} && yarn build", "Build Next.js")

# -----------------------------
# 4. START NEXT WITH PM2
# -----------------------------
run(f"cd {APP_DIR} && pm2 delete afriboxui || true", "Clean old process")

run(
    f"cd {APP_DIR} && pm2 start npm --name afriboxui -- start -- -p {NEXT_PORT}",
    "Start Next.js"
)

run(f"cd {APP_DIR} && pm2 save", "Save PM2 state")
run(f"cd {APP_DIR} && pm2 startup systemd -u $USER --hp $HOME", "Enable PM2 startup")

# -----------------------------
# 5. INSTALL NGINX
# -----------------------------
run(f"cd {APP_DIR} && sudo apt install -y nginx", "Install Nginx")

# -----------------------------
# 6. NGINX CONFIG
# -----------------------------
nginx_config = f"""
server {{
    listen 80;
    server_name {DOMAIN} {HOTSPOT_IP} _;

    client_max_body_size 4G;

    # FRONTEND (Next.js)
    location / {{
        proxy_pass http://127.0.0.1:{NEXT_PORT};
        proxy_http_version 1.1;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    # BACKEND 1 (Django)
    location /api/ {{
        proxy_pass http://127.0.0.1:{DJANGO_PORT};
        proxy_http_version 1.1;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    # BACKEND 2 (Django)
    location /api-v1/ {{
        proxy_pass http://127.0.0.1:{DJANGO_PORT};
        proxy_http_version 1.1;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    # Serve Django MEDIA_URL (/assets/) directly from disk
    location /assets/ {{
        root /afribox/elearncore;
        try_files $uri =404;
    }}

    # (Optional) Serve collected staticfiles if needed
    location /staticfiles/ {{
        root /afribox/elearncore;
        try_files $uri =404;
    }}

}}
"""

# Write config
with open("/tmp/afribox_nginx", "w") as f:
    f.write(nginx_config)

run("sudo mv /tmp/afribox_nginx /etc/nginx/sites-available/afribox", "Write config")

# Enable site
run("sudo ln -sf /etc/nginx/sites-available/afribox /etc/nginx/sites-enabled/", "Enable site")

# Remove default
run("sudo rm -f /etc/nginx/sites-enabled/default", "Remove default")

# Test + restart
run("sudo nginx -t", "Test Nginx")
run("sudo systemctl restart nginx", "Restart Nginx")
run("sudo systemctl enable nginx", "Enable Nginx")

# -----------------------------
# DONE
# -----------------------------
print("\n✅ Frontend deployed successfully!")
print(f"🌐 Access via: http://{HOTSPOT_IP}")
print(f"🌍 Domain: http://{DOMAIN}")