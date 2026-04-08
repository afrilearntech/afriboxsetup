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
SETUP_REPO = "https://github.com/afrilearntech/afriboxsetup.git"
FRONTEND_REPO = "https://github.com/afrilearntech/elearnui.git"
BACKEND_REPO = "https://github.com/afrilearntech/elearncore.git"
PROJECT_DIR = "/afribox"
DATA_DIR = "/afriboxdata"

# -----------------------------
# 1. SYSTEM UPDATE
# 2. MAKE PROJECT DIR IF NOT EXISTS
# 3. CLONE REPOSITORIES
# -----------------------------
run("sudo apt update", "STEP 1: UPDATE")
run("sudo apt upgrade -y", "STEP 1: UPDATE")
run(f"sudo mkdir -p {PROJECT_DIR}", "STEP 2: MAKE PROJECT DIR")
run(f"sudo mkdir -p {DATA_DIR}", "STEP 2: MAKE DATA DIR")
run(f"sudo mkdir -p {DATA_DIR}/logs", "STEP 2: MAKE LOGS DIR")

if SETUP_REPO:
    run(f"cd {PROJECT_DIR} && sudo git clone {SETUP_REPO}", "STEP 3: CLONE SETUP REPO")
if FRONTEND_REPO:
    run(f"cd {PROJECT_DIR} && sudo git clone {FRONTEND_REPO}", "STEP 3: CLONE FRONTEND REPO")
if BACKEND_REPO:
    run(f"cd {PROJECT_DIR} && sudo git clone {BACKEND_REPO}", "STEP 3: CLONE BACKEND REPO")

print("\n✅ Repositories setup complete!")