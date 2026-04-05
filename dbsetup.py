#!/usr/bin/env python3
"""
create_postgres_db.py

Installs PostgreSQL and Redis on Ubuntu 25.xx, ensures services are running,
creates a PostgreSQL role and database if they do not already exist, and
installs Debian-packaged Python dependencies commonly used by Celery/Redis.

Usage:
  sudo python3 create_postgres_db.py

Edit configuration below as needed.
"""

import subprocess
import sys
import os
import shlex
import time

# -------------------------
# Config: change these
# -------------------------
PG_VERSION = ""  # use distro 'postgresql' package
DB_SUPERUSER = "dbadmin"
DB_SUPERUSER_PW = "ChangeMe123!"
DB_NAME = "my_database"
DB_ENCODING = "UTF8"
DB_COLLATION = "en_US.UTF-8"
DB_CTYPE = "en_US.UTF-8"
DB_TEMPLATE = "template0"
CREATE_IF_MISSING = True
INSTALL_PY_PKGS = True  # install Debian-packaged python3 libs (best-effort)
DEBIAN_PY_PKGS = [
    "python3-venv",
    "python3-pip",
    "python3-dev",
    "build-essential",
    # Celery/AMQP related (may not exist on all releases)
    "python3-kombu",
    "python3-amqp",
    "python3-billiard",
    # Redis client
    "python3-redis",
]
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

def apt_install_best_effort(packages):
    """
    Try installing packages one-by-one so missing package names don't abort the whole script.
    Prints warnings for packages that fail to install.
    """
    run("apt-get update")
    for pkg in packages:
        try:
            print(f"Installing package: {pkg}")
            run(["apt-get", "install", "-y", pkg])
        except subprocess.CalledProcessError:
            print(f"Warning: failed to install package '{pkg}'. It may not exist in distro repos.", file=sys.stderr)

def is_root():
    return os.geteuid() == 0

def install_postgres():
    packages = ["postgresql", "postgresql-client", "postgresql-contrib", "ca-certificates"]
    apt_install(packages)

def install_redis():
    apt_install(["redis-server"])
    run(["systemctl", "enable", "--now", "redis-server"])

def install_python_packages_debian():
    """
    Install Debian-packaged Python dependencies for Celery/Redis.
    Uses best-effort per-package install so missing names won't abort.
    """
    apt_install_best_effort(DEBIAN_PY_PKGS)
    print("\nNote: If some packages were not available, create a virtualenv and install remaining packages inside it:")
    print("  python3 -m venv /opt/elearn/venv")
    print("  source /opt/elearn/venv/bin/activate")
    print("  pip install --upgrade pip setuptools")
    print("  pip install celery redis django\n")

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

    print(f"Checking/creating role '{DB_SUPERUSER}'...")
    create_role_or_update(DB_SUPERUSER, DB_SUPERUSER_PW)

    print(f"Checking/creating database '{DB_NAME}'...")
    create_database(DB_NAME, DB_SUPERUSER, DB_ENCODING, DB_COLLATION, DB_CTYPE, DB_TEMPLATE)

    print("Installing Redis...")
    install_redis()

    if INSTALL_PY_PKGS:
        print("Installing Debian-packaged Python libraries for Celery/Redis (best-effort)...")
        install_python_packages_debian()

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
    print("- Debian package names vary by Ubuntu release; missing names are skipped with a warning.")
    print("- Recommended: create a virtualenv for your app and install any remaining packages with pip inside it.")
    print("- Secure printed passwords and do not commit .env to version control.")

if __name__ == "__main__":
    main()
