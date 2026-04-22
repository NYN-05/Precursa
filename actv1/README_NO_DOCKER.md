# Running Precursa Without Docker

This guide shows you how to run the Precursa backend without Docker containers.

## Quick Start (Recommended - SQLite + In-Memory Cache)

This is the **easiest method** - no external dependencies required!

### Step 1: Update .env file

Edit `c:\Users\JHASHANK\Downloads\Precursa\actv1\.env`:

```env
PROJECT_NAME=Precursa Platform Foundation
ENVIRONMENT=development
API_V1_PREFIX=/api/v1
DATABASE_URL=sqlite:///./precursa.db
REDIS_URL=
JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123
SEED_ON_STARTUP=true
```

**Key changes:**
- `DATABASE_URL=sqlite:///./precursa.db` - Uses a local SQLite file
- `REDIS_URL=` (empty) - Uses in-memory cache instead of Redis

### Step 2: Install Dependencies

```powershell
cd c:\Users\JHASHANK\Downloads\Precursa\actv1
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

### Step 3: Run Database Migrations

```powershell
python -m alembic upgrade head
```

This creates the `precursa.db` SQLite database file with all tables.

### Step 4: Start the API Server

```powershell
python -m uvicorn app.main:app --reload
```

The API will be available at: **http://localhost:8000**

### Step 5: Verify

Visit:
- **Health Check**: http://localhost:8000/health
- **Readiness**: http://localhost:8000/ready
- **API Docs**: http://localhost:8000/docs

---

## Alternative: Use PostgreSQL (Without Docker)

If you have PostgreSQL installed locally:

### Step 1: Install PostgreSQL

Download from: https://www.postgresql.org/download/windows/

Or use Chocolatey:
```powershell
choco install postgresql
```

### Step 2: Create Database

Open psql and run:
```sql
CREATE DATABASE precursa;
CREATE USER precursa WITH PASSWORD 'precursa';
GRANT ALL PRIVILEGES ON DATABASE precursa TO precursa;
```

### Step 3: Update .env file

```env
DATABASE_URL=postgresql+psycopg://precursa:precursa@localhost:5432/precursa
REDIS_URL=
```

### Step 4: Run Migrations and Start

```powershell
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

---

## Alternative: Use PostgreSQL + Redis (Without Docker)

For full production-like setup:

### Step 1: Install PostgreSQL and Redis

```powershell
choco install postgresql
choco install redis-64
```

### Step 2: Start Redis Service

```powershell
redis-server --service-start
```

### Step 3: Create PostgreSQL Database

```sql
CREATE DATABASE precursa;
CREATE USER precursa WITH PASSWORD 'precursa';
GRANT ALL PRIVILEGES ON DATABASE precursa TO precursa;
```

### Step 4: Update .env file

```env
DATABASE_URL=postgresql+psycopg://precursa:precursa@localhost:5432/precursa
REDIS_URL=redis://localhost:6379/0
```

### Step 5: Run Migrations and Start

```powershell
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

---

## Code Changes Made

The following modifications enable Docker-free operation:

1. **Redis is now optional** - Falls back to in-memory cache when `REDIS_URL` is empty
2. **SQLite support added** - Works with `sqlite:///` URLs
3. **Readiness check updated** - Doesn't fail when Redis is unavailable
4. **Graceful degradation** - All features work without Redis, just uses process-local cache

---

## Feature Comparison

| Feature | SQLite + In-Memory | PostgreSQL Only | PostgreSQL + Redis |
|---------|-------------------|-----------------|-------------------|
| Database | SQLite file | PostgreSQL | PostgreSQL |
| Cache | In-memory | In-memory | Redis |
| Persistence | ✅ (file-based) | ✅ | ✅ |
| Multi-process | ❌ | ✅ | ✅ |
| Production-ready | ❌ | ⚠️ | ✅ |
| Setup complexity | Easy | Medium | Hard |
| Best for | Development/Testing | Development | Production |

---

## Troubleshooting

### Issue: "Module not found: aiosqlite"
```powershell
python -m pip install aiosqlite
```

### Issue: "Database not found"
Make sure you ran migrations:
```powershell
python -m alembic upgrade head
```

### Issue: "Port 8000 already in use"
Change the port:
```powershell
python -m uvicorn app.main:app --reload --port 8001
```

### Issue: "psycopg not found"
```powershell
python -m pip install psycopg[binary]
```

---

## Testing the API

### Get Auth Token
```powershell
curl -X POST http://localhost:8000/api/v1/auth/token `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=admin&password=admin123"
```

### Test Protected Endpoint
```powershell
curl http://localhost:8000/api/v1/protected/admin `
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Create Mock Ingestion Event
```powershell
curl -X POST http://localhost:8000/api/v1/ingestion/mock/weather?count=5
```

### Get Dashboard Summary
```powershell
curl http://localhost:8000/api/v1/realtime/dashboard `
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## Notes

- **SQLite is not recommended for production** - Use PostgreSQL + Redis for production deployments
- **In-memory cache is process-local** - Data is lost when the server restarts (but database persists)
- **Migrations work with both PostgreSQL and SQLite** - Alembic handles both dialects
- **All tests should pass** - The code changes maintain backward compatibility

---

## Next Steps

Once the server is running:

1. Visit http://localhost:8000/docs to explore the API
2. Use the Swagger UI to test endpoints interactively
3. Run the war game simulation: `POST /api/v1/wargame/start`
4. Run Ever Given backtest: `POST /api/v1/backtests/ever-given`
5. Generate mock events: `POST /api/v1/ingestion/mock/{source}`

Enjoy developing with Precursa! 🚀
