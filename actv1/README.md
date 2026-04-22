# Precursa Backend Slice (Chunks 1-4)

This folder contains the implemented backend scope for Precursa Chunks 1 through 4.

## Delivered scope

- Chunk 1: Platform foundation
   - FastAPI service skeleton
   - Health and readiness endpoints
   - PostgreSQL schema and Alembic migrations
   - Redis connectivity and readiness checks
   - Basic role-based authentication (token + role guards)
- Chunk 2: Ingestion and normalization
   - Source adapters for mock ingest (`ais`, `weather`, `customs`, `tariff`, `news`)
   - Canonical event schema normalization
   - Dedupe and timestamp fallback behavior
- Chunk 3: Feature and state layer
   - Shipment snapshot model and feature vector assembly
   - Provisional DRI update on each new event
   - Live shipment state cache in Redis (with process fallback)
- Chunk 4: Risk scoring and explainability
   - XGBoost inference over shipment snapshot features
   - Isolation Forest anomaly signal
   - DRI normalization to `0-100` integer
   - Top SHAP factors API per shipment

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
- `POST /api/v1/ingestion/events`
- `POST /api/v1/ingestion/mock/{source}?count=...`
- `GET /api/v1/ingestion/events?source=...&limit=...`
- `GET /api/v1/state/snapshots?limit=...`
- `GET /api/v1/state/snapshots/{shipment_key}`
- `GET /api/v1/state/cache/{shipment_key}`
- `GET /api/v1/risk/shipments?limit=...&top_k=...`
- `GET /api/v1/risk/shipments/{shipment_key}?top_k=...`

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
