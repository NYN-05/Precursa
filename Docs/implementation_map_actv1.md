# Precursa Implementation Map (Docs -> actv1)

Date: 2026-04-22

This file maps the documented chunk plan to the current backend implementation in `actv1`.

## Chunk status summary

- Chunk 1 (Platform foundation): Complete in `actv1`
- Chunk 2 (Ingestion and normalization): Complete in `actv1`
- Chunk 3 (Feature and state layer): Complete in `actv1`
- Chunk 4 (Risk scoring and explainability): Implemented in `actv1` API and service layer

## Mapping details

### Chunk 1: Platform foundation

- Docs source: `Docs/chunks.md`
- Implemented in:
  - `actv1/app/main.py`
  - `actv1/app/api/v1/health.py`
  - `actv1/app/services/readiness.py`
  - `actv1/app/core/security.py`
  - `actv1/app/api/v1/auth.py`
  - `actv1/alembic/versions/20260422_0001_platform_foundation.py`
- Acceptance evidence:
  - Health and readiness endpoints are present.
  - Auth and role-protected routes are active.
  - Migration-backed user/role schema exists.

### Chunk 2: Ingestion and normalization

- Docs source: `Docs/chunks.md`
- Implemented in:
  - `actv1/app/ingestion/normalizer.py`
  - `actv1/app/ingestion/mock_adapters.py`
  - `actv1/app/services/ingestion.py`
  - `actv1/app/api/v1/ingestion.py`
  - `actv1/alembic/versions/20260422_0002_ingestion_and_normalization.py`
- Acceptance evidence:
  - Canonical ingestion event schema is enforced.
  - Source dedupe and timestamp fallback are implemented.
  - All documented mock sources are supported.

### Chunk 3: Feature and state layer

- Docs source: `Docs/chunks.md`
- Required in docs:
  - Feature assembly service
  - Shipment snapshot model
  - Live DRI cache in Redis
  - Event-to-state updates
- Implemented in:
  - `actv1/app/services/feature_state.py`
  - `actv1/app/services/state_cache.py`
  - `actv1/app/services/ingestion.py`
  - `actv1/app/api/v1/state.py`
  - `actv1/alembic/versions/20260422_0003_feature_state_layer.py`
- Completion validation:
  - Snapshot upsert happens on ingestion.
  - Feature vector is persisted per shipment.
  - Live cache is updated from latest snapshot data.
  - Tests confirm snapshot creation, update, fallback key derivation, and cache reads.

### Chunk 4: Risk scoring and explainability

- Docs source: `Docs/chunks.md`
- Required in docs:
  - XGBoost and anomaly model inference
  - DRI normalization to `0-100` integer
  - SHAP top factors API
- Implemented in:
  - `actv1/app/services/risk_scoring.py`
  - `actv1/app/api/v1/risk.py`
  - `actv1/app/api/v1/router.py` (risk router registration)
  - `actv1/tests/test_risk_scoring.py`
- Output contract:
  - Per-shipment DRI response includes `dri`, `xgboost_score`, `anomaly_score`, and `top_factors`.
  - Batch scoring endpoint returns DRI and factors for current snapshots.

## Known documentation drift

- `Docs/context.md` includes stale statements about source availability and should not be used as implementation status truth.
- `Docs/chunks.md` remains the canonical chunk sequence used for this map.
