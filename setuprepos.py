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
    try:
        run(f"cd {PROJECT_DIR} && sudo rm -rf afriboxsetup", "STEP 3: CLEAN OLD SETUP REPO")
    except Exception as e:
        print(f"⚠️ WARNING: Could not clean old setup repo: {e}")
if FRONTEND_REPO:
    try:
        run(f"cd {PROJECT_DIR} && sudo rm -rf elearnui", "STEP 3: CLEAN OLD FRONTEND REPO")
    except Exception as e:
        print(f"⚠️ WARNING: Could not clean old frontend repo: {e}")
if BACKEND_REPO:
    try:
        run(f"cd {PROJECT_DIR} && sudo rm -rf elearncore", "STEP 3: CLEAN OLD BACKEND REPO")
    except Exception as e:
        print(f"⚠️ WARNING: Could not clean old backend repo: {e}")

print("\n✅ Repositories setup complete!")