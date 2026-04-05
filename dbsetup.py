#!/usr/bin/env python3
"""
create_postgres_db.py

Installs PostgreSQL and Redis on Ubuntu 25.xx, ensures services are running,
creates a PostgreSQL role and database if they do not already exist, and
installs Python packages required for Celery (into the system Python environment).

Usage:
  sudo python3 create_postgres_db.py

Configuration (edit below):
  PG_VERSION        = ""            # left empty -> use distro 'postgresql' package
  DB_SUPERUSER      = "dbadmin"
  DB_SUPERUSER_PW   = "ChangeMe123!"
  DB_NAME           = "my_database"
  DB_ENCODING       = "UTF8"
  DB_COLLATION      = "en_US.UTF-8"
  DB_CTYPE          = "en_US.UTF-8"
  DB_TEMPLATE       = "template0"
  CREATE_IF_MISSING = True
  INSTALL_PY_PKGS   = True          # install python3-venv, pip and celery/redis client packages system-wide
  PYTHON_PKG_LIST   = ["celery", "redis"]  # pip packages to install (adjust as needed)
"""

import subprocess
import sys
import os
import shlex
import time

# -------------------------
# Config: change these
# -------------------------
PG_VERSION = ""
DB_SUPERUSER = "dbadmin"
DB_SUPERUSER_PW = "ChangeMe123!"
DB_NAME = "my_database"
DB_ENCODING = "UTF8"
DB_COLLATION = "en_US.UTF-8"
DB_CTYPE = "en_US.UTF-8"
DB_TEMPLATE = "template0"
CREATE_IF_MISSING = True
INSTALL_PY_PKGS = True
PYTHON_PKG_LIST = ["celery", "redis"]
# -------------------------

def run(cmd, check=True, capture=False, env=None):
    if isinstance(cmd, (list, tuple)):
        args = cmd
    else:
        args = shlex.split(cmd)
    return subprocess.run(args, check=check, stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None, env=env)

def apt_install(packages):
    run("apt-get update")
    run(["apt-get", "install", "-y"] + packages)

def is_root():
    return os.geteuid() == 0

def install_postgres():
    packages = ["postgresql", "postgresql-client", "postgresql-contrib", "ca-certificates"]
    apt_install(packages)

def install_redis():
    # Install redis-server from distro packages
    apt_install(["redis-server"])
    # Enable and start redis service
    run(["systemctl", "enable", "--now", "redis-server"])

def install_python_packages():
    # Install pip and venv prerequisites, then pip install celery & redis client
    apt_install(["python3-venv", "python3-pip", "python3-dev", "build-essential"])
    # Upgrade pip then install packages
    run(["python3", "-m", "pip", "install", "--upgrade", "pip"])
    run(["python3", "-m", "pip", "install"] + PYTHON_PKG_LIST)

def ensure_service_running(service_name):
    run(["systemctl", "enable", "--now", service_name])

def psql_as_postgres(sql, capture=True):
    cmd = ["sudo", "-u", "postgres", "psql", "-tAc", sql]
    return run(cmd, capture=capture)

def role_exists(role):
    sql = f"SELECT 1 FROM pg_roles WHERE rolname = '{role}';"
    res = psql_as_postgres(sql, capture=True)
    out = res.stdout.decode().strip()
    return out == "1"

def db_exists(dbname):
    sql = f"SELECT 1 FROM pg_database WHERE datname = '{dbname}';"
    res = psql_as_postgres(sql, capture=True)
    out = res.stdout.decode().strip()
    return out == "1"

def create_role_or_update(role, password):
    escaped_pw = password.replace("'", "''")
    proc = run(["sudo", "-u", "postgres", "psql", "-tAc", f"SELECT 1 FROM pg_roles WHERE rolname = '{role}';"], capture=True)
    exists = proc.stdout.decode().strip() == "1"
    if exists:
        print(f"Altering role '{role}' password...")
        run(["sudo", "-u", "postgres", "psql", "-v", "ON_ERROR_STOP=1", "-c",
             f"ALTER ROLE \"{role}\" WITH ENCRYPTED PASSWORD '{escaped_pw}';"])
    else:
        print(f"Creating role '{role}'...")
        run(["sudo", "-u", "postgres", "psql", "-v", "ON_ERROR_STOP=1", "-c",
             f"CREATE ROLE \"{role}\" WITH LOGIN ENCRYPTED PASSWORD '{escaped_pw}' CREATEDB;"])

def create_database(dbname, owner, encoding, lc_collate, lc_ctype, template):
    proc = run(["sudo", "-u", "postgres", "psql", "-tAc", f"SELECT 1 FROM pg_database WHERE datname = '{dbname}';"], capture=True)
    exists = proc.stdout.decode().strip() == "1"
    if exists:
        print(f"Database '{dbname}' exists; changing owner to '{owner}'...")
        run(["sudo", "-u", "postgres", "psql", "-v", "ON_ERROR_STOP=1", "-c",
             f"ALTER DATABASE \"{dbname}\" OWNER TO \"{owner}\";"])
    else:
        print(f"Creating database '{dbname}' owned by '{owner}'...")
        run(["sudo", "-u", "postgres", "psql", "-v", "ON_ERROR_STOP=1", "-c",
             f"CREATE DATABASE \"{dbname}\" OWNER \"{owner}\" ENCODING '{encoding}' LC_COLLATE '{lc_collate}' LC_CTYPE '{lc_ctype}' TEMPLATE {template};"])

def main():
    if not is_root():
        print("This script must be run as root (use sudo). Exiting.", file=sys.stderr)
        sys.exit(2)

    print("Installing PostgreSQL (packages may already be present)...")
    install_postgres()
    ensure_service_running("postgresql")

    # Wait briefly for postgres to initialize
    time.sleep(1)

    print(f"Checking for role '{DB_SUPERUSER}'...")
    create_role_or_update(DB_SUPERUSER, DB_SUPERUSER_PW)

    print(f"Checking/creating database '{DB_NAME}'...")
    create_database(DB_NAME, DB_SUPERUSER, DB_ENCODING, DB_COLLATION, DB_CTYPE, DB_TEMPLATE)

    print("Installing Redis...")
    install_redis()

    if INSTALL_PY_PKGS:
        print("Installing Python packages for Celery/Redis (system-wide pip)...")
        install_python_packages()

    print("\nDone.\n")
    print("Suggested .env entries for your Django app (replace placeholders):")
    print(f"DB_NAME={DB_NAME}")
    print(f"DB_USER={DB_SUPERUSER}")
    print(f"DB_PASSWORD={DB_SUPERUSER_PW}")
    print("DB_HOST=/var/run/postgresql")
    print("DB_PORT=5432")
    print("DB_CONN_MAX_AGE=300")
    print("ENVIRONMENT=AFRIBOX")
    print("")
    print("# Redis / Celery")
    print("REDIS_URL=redis://localhost:6379/0")
    print("REDIS_PASSWORD=")
    print("CELERY_BROKER_URL=${REDIS_URL}")
    print("CELERY_RESULT_BACKEND=django-db")
    print("")
    print("Notes:")
    print("- The script installs celery & redis Python packages system-wide using pip; for production it's recommended to use a virtualenv or container.")
    print("- Secure the printed passwords and move secrets to a safe vault; do not commit .env to VCS.")

if __name__ == "__main__":
    main()
