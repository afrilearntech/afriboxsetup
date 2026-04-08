# AfriBox Setup Configurations

## Setup Order
`0. Change Directory`
```
cd afribox/afriboxsetup
```

`1. Setup WiFi and Local Network`
```
python3 initial.py
```

`2. Setup Repos and Required Folders`
```
python3 setuprepos.py
```

`3. Setup Postgre Database`
```
python3 dbsetup.py
```

`4. Rename DB and Change Password`
```
python3 dbrename.py <DBNAME> <DBUSER> <DBPASSWORD> 
```

`5. Setup Frontend (NextJS App)`
```
python3 frontendserver.py
```

`6. Setup Backend (Django App)`
```
python3 backendserver.py
```

`7. Setup .env Variables`
`sudo nano /afribox/elearncore/elearncore/.env`
```
DJANGO_SECRET_KEY=...
ARKESEL_SMS_API_KEY=...
SMS_SENDER_ID=...
DEFAULT_FROM_MAIL=...
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_HOST=...
DB_PORT=...
ENVIRONMENT=AFRIBOX

# Sync engine
SYNC_API_BASE_URL=...
SYNC_TOKEN=...
SYNC_LOGIN_KIND=admin
SYNC_LOGIN_IDENTIFIER=...
SYNC_LOGIN_PASSWORD=...
```