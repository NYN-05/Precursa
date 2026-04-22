# Precursa Chunk 1 Platform Foundation

This folder contains the full Week 1 foundation for Precursa.

## Delivered scope

- FastAPI service skeleton
- Health and readiness endpoints
- PostgreSQL schema and Alembic migrations
- Redis connectivity for readiness checks
- Basic role-based authentication (token + role guards)
- CI pipeline configuration

## Local setup (no virtual environment required)

1. Start PostgreSQL and Redis:
   - `docker compose up -d`
2. Install dependencies globally for your current Python:
   - `python -m pip install -r requirements-dev.txt`
3. Copy env file and adjust if needed:
   - `copy .env.example .env` (Windows)
4. Run database migration:
   - `python -m alembic upgrade head`
5. Start the API:
   - `python -m uvicorn app.main:app --reload`

## Important endpoints

- `GET /health`
- `GET /ready`
- `POST /api/v1/auth/token`
- `GET /api/v1/auth/me`
- `GET /api/v1/protected/admin`

## Auth bootstrap behavior

If `SEED_ON_STARTUP=true`, the service seeds default roles and a default admin user.

Default roles:
- admin
- ops_analyst
- logistics_manager
- auditor

Default admin credentials come from:
- `DEFAULT_ADMIN_USERNAME`
- `DEFAULT_ADMIN_PASSWORD`

## Run tests and lint

- `python -m pytest`
- `python -m ruff check .`
