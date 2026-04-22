# Precursa Implementation Map (Docs -> actv1)

Date: 2026-04-23

This file maps the documented chunk plan to the current backend implementation in `actv1`.

## Chunk status summary

- Chunk 1 (Platform foundation): Complete in `actv1`
- Chunk 2 (Ingestion and normalization): Complete in `actv1`
- Chunk 3 (Feature and state layer): Complete in `actv1`
- Chunk 4 (Risk scoring and explainability): Implemented in `actv1` API and service layer
- Chunk 5 (Route intelligence and constraint solver): Complete in `actv1`
- Chunk 6 (Autonomous agent and audit): Complete in `actv1`
- Chunk 7 (Realtime API, dashboard, and notifications): Backend slice complete in `actv1`
- Chunk 8 (Copilot and what-if simulation): Complete in `actv1`
- Chunk 9 (Proof loops and production hardening): Backend proof/hardening slice complete in `actv1`

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

### Chunk 5: Route intelligence and constraint solver

- Docs source: `Docs/chunks.md`
- Required in docs:
  - NetworkX candidate paths
  - PuLP constraint validation
  - Tariff and policy scoring
  - SLA, sanctions, cold-chain, and weight-limit checks
  - Clear rejection reasons
- Implemented in:
  - `actv1/app/services/route_intelligence.py`
  - `actv1/app/api/v1/routes.py`
  - `actv1/app/db/models.py`
  - `actv1/alembic/versions/20260423_0004_chunks_5_to_9.py`
  - `actv1/tests/test_route_intelligence.py`
- Completion validation:
  - Top feasible routes are returned and persisted.
  - Invalid routes are rejected with explicit reasons.
  - PuLP selects the feasible optimum instead of shortest path alone.

### Chunk 6: Autonomous agent and audit

- Docs source: `Docs/chunks.md`
- Required in docs:
  - Assess, decide, reroute, notify, log flow
  - Override and approval workflow
  - Immutable agent action log
- Implemented in:
  - `actv1/app/services/agent_service.py`
  - `actv1/app/api/v1/agent.py`
  - `actv1/app/services/notifications.py`
  - `actv1/app/db/models.py`
  - `actv1/tests/test_agent_copilot.py`
- Completion validation:
  - Red-alert shipments trigger reroute actions.
  - Ops overrides block autonomous execution and are audit-logged.
  - Agent actions, selected routes, ROI defended, replay data, and notifications are persisted.

### Chunk 7: Realtime API, dashboard, and notifications

- Docs source: `Docs/chunks.md`
- Required in docs:
  - REST APIs
  - WebSocket streams
  - Dashboard panels
  - Notification connectors
- Implemented in:
  - `actv1/app/api/v1/realtime.py`
  - `actv1/app/api/v1/notifications.py`
  - `actv1/app/websocket/broadcaster.py`
  - `actv1/app/services/notifications.py`
- Completion validation:
  - Dashboard summary returns shipment, route, notification, and agent-log data.
  - Agent and wargame events are published into the live WebSocket broadcaster.
  - Notifications are durable in the database.

### Chunk 8: Copilot and what-if simulation

- Docs source: `Docs/chunks.md`
- Required in docs:
  - Grounded copilot responses from SHAP and route data
  - Proactive red-alert brief
  - What-if scenario API
- Implemented in:
  - `actv1/app/services/copilot.py`
  - `actv1/app/services/simulation.py`
  - `actv1/app/api/v1/copilot.py`
  - `actv1/tests/test_agent_copilot.py`
- Completion validation:
  - Copilot explanations use only SHAP factors and LP constraint logs.
  - Tests ensure carbon is not invented as a reason when it is not grounded.
  - What-if projections reuse the same risk and route intelligence layers.

### Chunk 9: Proof loops and production hardening

- Docs source: `Docs/chunks.md`
- Required in docs:
  - Ever Given replay
  - Disturber vs Healer war game
  - Observability, retry/DLQ, idempotency, mock-mode streaming fallback
- Implemented in:
  - `actv1/app/services/backtesting.py`
  - `actv1/app/services/wargame.py`
  - `actv1/app/services/observability.py`
  - `actv1/app/services/resilience.py`
  - `actv1/app/services/streaming.py`
  - `actv1/app/api/v1/backtests.py`
  - `actv1/app/api/v1/wargame.py`
  - `actv1/app/api/v1/ops.py`
  - `actv1/tests/test_proof_hardening.py`
- Completion validation:
  - Ever Given replay stores a database result and flags at least 10 minutes before grounding.
  - War game fires at least 8 Disturber events and records Healer responses.
  - Mock streaming mode, metrics, and DLQ tables are available for failure-safe operation.

## Known documentation drift

- `Docs/context.md` includes stale statements about source availability and should not be used as implementation status truth.
- `Docs/chunks.md` remains the canonical chunk sequence used for this map.
