"""
Script to setup the backend server for Afribox, including Daphne and Nginx configuration.
sudo cp deployment/websocket/afriboxdaphne.service /etc/systemd/system/afriboxdaphne.service
sudo systemctl daemon-reload
sudo systemctl enable afriboxdaphne
sudo systemctl start afriboxdaphne

"""


import subprocess
import sys

def run(cmd, step: str = ""):
    print(f"\n🔹 {step.upper()} [RUNNING]: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ ERROR: {cmd}")
        print(f"Working directory: {subprocess.run('pwd', shell=True, capture_output=True).stdout.decode().strip()}")
        sys.exit(1)

# pull latest code
print("🚀 Pulling latest code from GitHub...")
run("cd /afribox/elearncore && git pull origin main", "PULL LATEST CODE")

# activate virtualenv and install requirements
print("\n📦 Installing Python dependencies...")
run("cd /afribox/elearncore && sudo apt install python3-venv -y", "INSTALL PYTHON3 VENV")
run("cd /afribox/elearncore && python3 -m venv venv && source venv/bin/activate", "CREATE AND ACTIVATE VIRTUAL ENV")
run("cd /afribox/elearncore && pip install --upgrade pip setuptools", "UPGRADE PIP")
run("cd /afribox/elearncore && pip install -r requirements.txt", "INSTALL REQUIREMENTS")
print("🚀 Setting up Afribox Backend Server...")
run("sudo apt update", "STEP 1: UPDATE")
run("sudo apt install -y python3-pip nginx", "STEP 2: INSTALL PACKAGES")
run("sudo pip3 install daphne", "STEP 3: INSTALL DAPHNE")

print("\n🔧 Configuring Daphne and Nginx...")
run("sudo cp deployment/websocket/afriboxdaphne.service /etc/systemd/system/afriboxdaphne.service", "STEP 4: CONFIGURE DAPHNE")
run("sudo systemctl daemon-reload", "STEP 4: CONFIGURE DAPHNE")
run("sudo systemctl enable afriboxdaphne", "STEP 4: CONFIGURE DAPHNE")
run("sudo systemctl start afriboxdaphne", "STEP 4: CONFIGURE DAPHNE")

print("\n✅ Afribox Backend Server setup complete!")