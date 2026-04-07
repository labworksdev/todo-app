# Database Migration: SQLite → Cosmos DB PostgreSQL

## Overview

The todo-app currently uses SQLite (in-memory/local file). A Cosmos DB for PostgreSQL
instance has been pre-staged and is ready to connect. This guide covers how to wire it up.

## Pre-Staged Infrastructure

| Setting | Value |
|---------|-------|
| Cluster | `todo-app-db` |
| Host | `c-todo-app-db.qhb3l52muuda2z.postgres.cosmos.azure.com` |
| Port | `5432` |
| Database | `citus` (default) |
| Admin user | `citus` |
| Password | `PSEA-Lab-2026!` |
| SSL | Required |
| Resource Group | `rg-todo-app` |
| Firewall | Azure services + all IPs (workshop only) |

## Connection String

```
postgresql://citus:PSEA-Lab-2026!@c-todo-app-db.qhb3l52muuda2z.postgres.cosmos.azure.com:5432/citus?sslmode=require
```

## Step 1: Add psycopg2 to requirements.txt

```
psycopg2-binary==2.9.9
```

## Step 2: Update app.py — Database Connection

Replace the SQLite connection logic with:

```python
import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///todos.db"  # fallback to SQLite for local dev
)

def get_db():
    """Get a database connection."""
    if DATABASE_URL.startswith("postgresql"):
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        conn.autocommit = True
        return conn
    else:
        # Original SQLite logic
        import sqlite3
        conn = sqlite3.connect("todos.db")
        conn.row_factory = sqlite3.Row
        return conn
```

## Step 3: Update Schema (PostgreSQL version)

Create `schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS todos (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Add an init function:

```python
def init_db():
    """Initialize the database schema."""
    conn = get_db()
    if DATABASE_URL.startswith("postgresql"):
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.close()
        conn.close()
    else:
        # Original SQLite init
        pass
```

## Step 4: Update SQL Queries

Key differences from SQLite to PostgreSQL:

| SQLite | PostgreSQL |
|--------|-----------|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `SERIAL PRIMARY KEY` |
| `?` parameter placeholder | `%s` parameter placeholder |
| `datetime('now')` | `CURRENT_TIMESTAMP` |
| `BOOLEAN` stored as 0/1 | `BOOLEAN` stored as true/false |

Example — insert:
```python
# SQLite
cur.execute("INSERT INTO todos (title) VALUES (?)", (title,))

# PostgreSQL
cur.execute("INSERT INTO todos (title) VALUES (%s) RETURNING id", (title,))
```

Example — fetch:
```python
# SQLite (returns sqlite3.Row)
todos = cur.execute("SELECT * FROM todos").fetchall()

# PostgreSQL (returns dicts via RealDictCursor)
cur.execute("SELECT * FROM todos ORDER BY created_at DESC")
todos = cur.fetchall()
```

## Step 5: Update Dockerfile

Add PostgreSQL client library:

```dockerfile
# Add before pip install
RUN apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*
```

## Step 6: Set Environment Variable on Container App

```bash
az containerapp update \
  --resource-group rg-todo-app \
  --name todo-app \
  --set-env-vars \
    DATABASE_URL="postgresql://citus:PSEA-Lab-2026!@c-todo-app-db.qhb3l52muuda2z.postgres.cosmos.azure.com:5432/citus?sslmode=require"
```

## Step 7: Deploy

Push to main — CI/CD will build and deploy automatically. The app will:
1. Read `DATABASE_URL` from environment
2. Connect to Cosmos DB PostgreSQL
3. Create the `todos` table if it doesn't exist
4. All todos persist across redeploys

## Testing Locally

You can connect to the database from any student VM or local machine:

```bash
# Using psql
psql "postgresql://citus:PSEA-Lab-2026!@c-todo-app-db.qhb3l52muuda2z.postgres.cosmos.azure.com:5432/citus?sslmode=require"

# Test query
SELECT * FROM todos;
```

Or run the app locally with the env var:
```bash
export DATABASE_URL="postgresql://citus:PSEA-Lab-2026!@c-todo-app-db.qhb3l52muuda2z.postgres.cosmos.azure.com:5432/citus?sslmode=require"
python app.py
```

Without `DATABASE_URL`, the app falls back to SQLite for local development.

## Workshop Notes

This migration is a great exercise for students — it touches:
- Environment variables and configuration
- SQL dialect differences
- Docker dependencies
- Cloud database connectivity
- CI/CD (change deploys automatically)

Consider making this a Sprint 1 issue for students to tackle with Claude Code.

## Cleanup

After the workshop, delete the database to stop charges:
```bash
az cosmosdb postgres cluster delete \
  --resource-group rg-todo-app \
  --cluster-name todo-app-db \
  --yes
```