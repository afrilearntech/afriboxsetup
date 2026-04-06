import subprocess
import sys

PROJECT_DIR = "/afribox/elearncore"
DEPLOYMENT_DIR = f"/afribox/afriboxsetup/deployment"
VENV_DIR = f"{PROJECT_DIR}/venv"
PYTHON = f"{VENV_DIR}/bin/python"
PIP = f"{VENV_DIR}/bin/pip"

def run(cmd, step: str = ""):
    print(f"\n🔹 {step.upper()} [RUNNING]: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ ERROR: {cmd}")
        sys.exit(1)

# -----------------------------
# 1. Pull latest code
# -----------------------------
print("🚀 Pulling latest code from GitHub...")
run(f"cd {PROJECT_DIR} && git pull origin main", "PULL LATEST CODE")

# -----------------------------
# 2. Install system deps
# -----------------------------
run("sudo apt update", "UPDATE")
run("sudo apt install -y python3-venv python3-pip nginx", "INSTALL SYSTEM PACKAGES")

# -----------------------------
# 3. Setup virtualenv
# -----------------------------
print("\n📦 Setting up virtual environment...")

run(f"cd {PROJECT_DIR} && python3 -m venv venv", "CREATE VENV")

run(f"{PIP} install --upgrade pip setuptools", "UPGRADE PIP")
run(f"{PIP} install -r {PROJECT_DIR}/requirements.txt", "INSTALL REQUIREMENTS")

# -----------------------------
# 4. Migrate database
# -----------------------------
print("\n🗄️ Migrating database...")

run(f"{PYTHON} {PROJECT_DIR}/manage.py makemigrations", "MAKEMIGRATIONS")
run(f"{PYTHON} {PROJECT_DIR}/manage.py migrate", "MIGRATE")

# -----------------------------
# collect static files
# -----------------------------
print("\n📦 Collecting static files...")

run(f"{PYTHON} {PROJECT_DIR}/manage.py collectstatic --noinput", "COLLECT STATIC FILES")

# -----------------------------
# 5. Install Daphne
# -----------------------------
run(f"{PIP} install daphne", "INSTALL DAPHNE")

# -----------------------------
# 6. Configure Daphne service
# -----------------------------
print("\n🔧 Configuring Daphne service...")

run(f"sudo cp {DEPLOYMENT_DIR}/websocket/afriboxdaphne.service /etc/systemd/system/", "COPY SERVICE")

run("sudo systemctl daemon-reload", "RELOAD SYSTEMD")
run("sudo systemctl enable afriboxdaphne", "ENABLE DAPHNE")
run("sudo systemctl restart afriboxdaphne", "START DAPHNE")

# -----------------------------
# 7. Restart Nginx
# -----------------------------
run("sudo nginx -t", "TEST NGINX")
run("sudo systemctl restart nginx", "RESTART NGINX")
run("sudo systemctl enable nginx", "ENABLE NGINX")

# -----------------------------
# DONE
# -----------------------------
print("\n✅ Afribox Backend Server setup complete!")