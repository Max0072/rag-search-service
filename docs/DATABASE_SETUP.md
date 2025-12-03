# Database Setup Guide

## PostgreSQL Setup

### Option 1: Local PostgreSQL Installation

#### macOS (using Homebrew)
```bash
# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Create database
createdb conference_db

# Connect to database
psql conference_db
```

#### Ubuntu/Debian
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database
sudo -u postgres createdb conference_db

# Create user (optional)
sudo -u postgres psql
CREATE USER your_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE conference_db TO your_user;
```

### Option 2: Docker

```bash
# Run PostgreSQL in Docker
docker run -d \
  --name conference-postgres \
  -e POSTGRES_DB=conference_db \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15

# Check if running
docker ps

# Connect to database
docker exec -it conference-postgres psql -U user -d conference_db
```

### Option 3: Cloud PostgreSQL (Supabase, Railway, etc.)

Use a managed PostgreSQL service and get the connection string.

## Configure .env

Update your `.env` file with the database URL:

```bash
# For local PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/conference_db

# For Docker
DATABASE_URL=postgresql://user:password@localhost:5432/conference_db

# For cloud service (example)
DATABASE_URL=postgresql://user:password@host.example.com:5432/conference_db
```

## Initialize Database

Once PostgreSQL is running and configured:

```bash
# Install dependencies (if not already done)
pip install -r requirements.txt

# Initialize database (create tables)
python scripts/init_db.py

# Or test the connection directly
python -m app.database.metadata_db
```

## Verify Setup

```bash
# Check if tables are created
psql conference_db -c "\dt"

# Should show:
#  Schema |  Name  | Type  |  Owner
# --------+--------+-------+---------
#  public | calls  | table | user
```

## Test Connection

```python
# Python test
from app.database.metadata_db import get_metadata_db

db = get_metadata_db()
stats = db.get_stats()
print(f"Database is working! Stats: {stats}")
```

## Troubleshooting

### Connection refused
- Check if PostgreSQL is running: `brew services list` or `systemctl status postgresql`
- Verify port 5432 is available: `lsof -i :5432`

### Authentication failed
- Check username/password in DATABASE_URL
- Verify user has permissions on the database

### Table doesn't exist
- Run initialization script: `python scripts/init_db.py`
- Check if tables exist: `psql conference_db -c "\dt"`

### psycopg2 installation issues
```bash
# macOS
brew install postgresql
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
pip install psycopg2-binary

# Ubuntu
sudo apt-get install libpq-dev
pip install psycopg2-binary
```
