#!/usr/bin/env python3
"""
create_postgres_db.py

Installs PostgreSQL (on Ubuntu 25.xx), ensures the service is running,
and creates a PostgreSQL role and database if they do not already exist.

Usage:
  sudo python3 create_postgres_db.py

Configuration (edit below):
  PG_VERSION        = "18"           
  DB_SUPERUSER      = "dbadmin" 
  DB_SUPERUSER_PW   = "ChangeMe123!" 
  DB_NAME           = "my_database"
  DB_ENCODING       = "UTF8"
  DB_COLLATION      = "en_US.UTF-8"
  DB_CTYPE          = "en_US.UTF-8"
  DB_TEMPLATE       = "template0"
  CREATE_IF_MISSING = True            # if False, script will exit when DB or role exists
"""

import subprocess
import sys
import os
import shlex
import time

# -------------------------
# Config: change these
# -------------------------
PG_VERSION = "18"
DB_SUPERUSER = "dbadmin"
DB_SUPERUSER_PW = "ChangeMe123!"
DB_NAME = "my_database"
DB_ENCODING = "UTF8"
DB_COLLATION = "en_US.UTF-8"
DB_CTYPE = "en_US.UTF-8"
DB_TEMPLATE = "template0"
CREATE_IF_MISSING = True
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
    # Install PostgreSQL server and client
    packages = [f"postgresql-{PG_VERSION}", f"postgresql-client-{PG_VERSION}", "postgresql-contrib", "ca-certificates"]
    apt_install(packages)

def ensure_service_running():
    run(["systemctl", "enable", "--now", f"postgresql"])

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

def create_role(role, password):
    # Create role with login and createdb privileges
    sql = f"CREATE ROLE {role} WITH LOGIN ENCRYPTED PASSWORD %s CREATEDB;"
    # Use psql with -v assignment to avoid shell interpolation of password
    # We'll run psql and provide the SQL using sudo -u postgres psql -c with shell-escaped password literal
    escaped_pw = password.replace("'", "''")
    sql = f"CREATE ROLE {role} WITH LOGIN ENCRYPTED PASSWORD '{escaped_pw}' CREATEDB;"
    run(["sudo", "-u", "postgres", "psql", "-c", sql])

def create_database(dbname, owner, encoding, lc_collate, lc_ctype, template):
    sql = (
        "CREATE DATABASE {dbname} OWNER {owner} "
        "ENCODING '{encoding}' LC_COLLATE '{lc_collate}' LC_CTYPE '{lc_ctype}' TEMPLATE {template};"
    ).format(dbname=dbname, owner=owner, encoding=encoding, lc_collate=lc_collate, lc_ctype=lc_ctype, template=template)
    run(["sudo", "-u", "postgres", "psql", "-c", sql])

def main():
    if not is_root():
        print("This script must be run as root (use sudo). Exiting.", file=sys.stderr)
        sys.exit(2)

    print("Installing PostgreSQL (packages may already be present)...")
    install_postgres()
    ensure_service_running()

    # Wait briefly for postgres to initialize
    time.sleep(1)

    print(f"Checking for role '{DB_SUPERUSER}'...")
    if role_exists(DB_SUPERUSER):
        print(f"Role '{DB_SUPERUSER}' already exists.")
        if not CREATE_IF_MISSING:
            print("CREATE_IF_MISSING is False — exiting to avoid changes.")
            return
    else:
        print(f"Creating role '{DB_SUPERUSER}'...")
        create_role(DB_SUPERUSER, DB_SUPERUSER_PW)
        print("Role created.")

    print(f"Checking for database '{DB_NAME}'...")
    if db_exists(DB_NAME):
        print(f"Database '{DB_NAME}' already exists — no action taken.")
        return
    else:
        print(f"Creating database '{DB_NAME}' owned by '{DB_SUPERUSER}'...")
        create_database(DB_NAME, DB_SUPERUSER, DB_ENCODING, DB_COLLATION, DB_CTYPE, DB_TEMPLATE)
        print("Database created.")

    print("Done.")

if __name__ == "__main__":
    main()
