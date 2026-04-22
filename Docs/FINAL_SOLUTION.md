# Precursa Production Architecture Blueprint

## 1. Executive Summary

Precursa should be treated as a closed-loop supply chain control plane, not a dashboard.
The core system continuously ingests disruption signals, builds a shipment-level risk model, explains the risk, validates every route against hard cargo constraints, and then executes or recommends action through an autonomous agent.

The strongest architecture in the provided docs is the v2 agent-first loop:
ingest -> score -> explain -> constrain -> reroute -> notify -> audit.
The strongest v3 upgrades are the credibility features that make the platform feel real in a production context:
real AIS data, tariff intelligence, news-driven modifiers, proactive copilot briefs, voice interaction, and what-if simulation.

The production target is therefore:

- Event-driven and service-oriented at the backend.
- Explainable by design, not after the fact.
- Safe by default, with hard constraints always outranking model predictions.
- Observable and auditable end to end.
- Able to run in a mock/demo mode without external keys, while scaling to real streams in production.

## 2. Source Synthesis

The provided docs are internally consistent on the main thesis, but they serve different purposes.

### 2.1 What the docs agree on

- Precursa is a self-healing supply chain intelligence platform.
- The LangGraph agent is the system core, not a side feature.
- DRI is the primary risk score and must remain an integer from 0 to 100.
- SHAP explainability is mandatory for trust.
- NetworkX generates candidate paths and PuLP enforces hard routing constraints.
- The copilot must be grounded in actual model output and route data.
- Ever Given backtesting and the war game are proof mechanisms, not cosmetic demo features.

### 2.2 What v3 improves over v2

- A real AIS feed replaces a 100 percent mocked data story.
- Tariff risk becomes part of the route and DRI calculation.
- News signals become an operational modifier instead of a strategic side panel.
- The copilot becomes proactive, not only reactive.
- Voice input makes the copilot feel modern and natural.
- The what-if engine adds scenario planning.

### 2.3 Main gaps that still need production hardening

- No explicit authentication and authorization architecture.
- No durable event backbone design beyond the hackathon narrative.
- No explicit outbox, idempotency, retry, or dead-letter strategy.
- No geospatial storage recommendation for ports and routes.
- No observability, SLO, or incident management model.
- No multi-tenant data isolation model.
- No formal separation between runtime state, audit state, and analytics state.

## 3. Architectural Principles

1. The agent is authoritative, but never unconstrained.
2. Every autonomous action must be explainable, logged, and replayable.
3. Hard rules override model confidence.
4. The UI is a projection of backend truth, not the source of truth.
5. Real-time paths must degrade gracefully to mock or cached sources.
6. Event-driven processing handles scale; synchronous APIs handle control and query.
7. Production and demo modes should share interfaces, not implementation shortcuts.

## 4. Target High-Level Architecture

```text
                           +---------------------------+
                           |  External Data Sources    |
                           |---------------------------|
                           | AIS / GPS / IoT           |
                           | Weather                   |
                           | Port congestion           |
                           | Customs                   |
                           | Tariff rules              |
                           | News / headlines          |
                           | Geopolitical risk         |
                           +-------------+-------------+
                                         |
                                         v
                     +-------------------+-------------------+
                     | Ingestion Adapters and Normalization   |
                     |----------------------------------------|
                     | validate / dedupe / enrich / timestamp |
                     | fallback to mock sources when needed    |
                     +-------------------+-------------------+
                                         |
                                         v
                   +---------------------+---------------------+
                   | Event Backbone and Stream Processing      |
                   |-------------------------------------------|
                   | Kafka topics / schema registry            |
                   | Flink jobs / windowing / anomaly filters  |
                   | outbox / retry / DLQ                      |
                   +---------------------+---------------------+
                                         |
                                         v
        +----------------+   +----------+-----------+   +----------------+
        | Redis Cache    |   | Feature / State Layer |   | PostgreSQL     |
        | live DRI state |<->| shipment snapshots    |<->| system of truth |
        +----------------+   | feature assembly      |   | routes / audit  |
                               +----------+-----------+   +----------------+
                                         |
                                         v
                +------------------------+------------------------+
                | Risk Intelligence and Explainability Layer      |
                |--------------------------------------------------|
                | XGBoost classifier                               |
                | Isolation Forest anomaly detector                |
                | LSTM temporal expert (asynchronous / optional)  |
                | SHAP explanation generator                       |
                | DRI normalization and thresholding               |
                +------------------------+------------------------+
                                         |
                                         v
                +------------------------+------------------------+
                | Route Intelligence and Policy Layer             |
                |--------------------------------------------------|
                | NetworkX candidate path generation              |
                | PuLP constraint solver                           |
                | tariff scoring / cold-chain / sanctions / SLA   |
                | geospatial route scoring                         |
                +------------------------+------------------------+
                                         |
                                         v
                +------------------------+------------------------+
                | LangGraph Autonomous Agent                      |
                |--------------------------------------------------|
                | assess -> decide -> reroute -> notify -> log    |
                | override handling / approval workflow           |
                | audit trail and replay                           |
                +------------------------+------------------------+
                                         |
                +------------------------+------------------------+
                | Grounded Copilot and Scenario Engine            |
                |--------------------------------------------------|
                | Claude API                                      |
                | proactive brief on red alerts                    |
                | voice Q&A / what-if simulation                   |
                | SHAP-grounded explanations                      |
                +------------------------+------------------------+
                                         |
                                         v
                  +----------------------+----------------------+
                  | Realtime API and UI Projection Layer         |
                  |----------------------------------------------|
                  | REST / WebSocket / event feed                |
                  | React dashboard / map / alerts / war game    |
                  | operator override / customer notifications   |
                  +----------------------+----------------------+
                                         |
                                         v
           +-----------------------------+-----------------------------+
           | Proof and Learning Loops                                 |
           |----------------------------------------------------------|
           | Ever Given backtesting                                   |
           | Monte Carlo Disturber vs Healer war game                 |
           | model registry / experiment tracking / observability     |
           +----------------------------------------------------------+
```

## 5. Module-Level Design

### 5.1 Runtime services

| Service | Responsibility | Scale mode | Key dependencies |
|---|---|---|---|
| API Gateway / BFF | Public REST API, auth enforcement, request shaping, dashboard aggregation | Horizontally scaled and stateless | FastAPI, OIDC, Redis, Postgres |
| Ingestion Service | AIS, weather, customs, tariff, and news adapters | Per-source scaling | Kafka, source SDKs, mock adapters |
| Stream Processor | Windowing, normalization, signal fusion, anomaly prefiltering | Partitioned by shipment or region | Kafka, Flink |
| Feature Service | Build shipment feature vectors and maintain latest state | Stateless compute plus Redis cache | Postgres, Redis |
| DRI Scoring Service | XGBoost, Isolation Forest, optional LSTM, SHAP | Stateless inference workers | MLflow model artifacts, feature service |
| Graph Service | Build port graph, candidate routes, route metadata | CPU-light, scales by query rate | NetworkX, geospatial store |
| Constraint Solver Service | Enforce cargo, SLA, and sanctions constraints | Stateless workers | PuLP, graph service, policy data |
| Agent Service | LangGraph orchestration, threshold logic, autonomous actions | Scheduled workers | DRI scoring, solver, audit log |
| Copilot Service | Grounded explanations, proactive briefs, voice and what-if | Stateless except conversation cache | Claude API, SHAP, route logs |
| Simulation Service | Ever Given replay and war game scenario engine | On-demand workers | Event replay data, agent and solver |
| WebSocket Broker | Push live updates to clients | Horizontally scaled with sticky sessions or pub/sub | Redis pub/sub or Kafka fanout |

### 5.2 Offline and platform services

| Service | Responsibility | Notes |
|---|---|---|
| Model Training Pipeline | Train, evaluate, and register models | Use MLflow for experiment tracking and promotion gates |
| Backfill and Replay Pipeline | Historical reprocessing and backtesting | Re-run historical AIS or disruption windows |
| Identity Provider | Authentication and role claims | OIDC-compatible provider such as Cognito or Keycloak |
| Observability Stack | Metrics, logs, traces, alerting | Prometheus, Grafana, OpenTelemetry, Sentry |
| Object Storage | Model artifacts, replay files, raw feeds | S3 or S3-compatible storage |
| IaC and Deployment | Environment provisioning and rollout | Terraform, Helm, EKS |

### 5.3 Frontend modules

| Module | Responsibility |
|---|---|
| Map | Real-time shipment and vessel visualization |
| ShipmentCard | DRI, SHAP top factor, shipment state |
| AlertPanel | Color-coded disruption triage |
| RouteComparison | Top 3 constraint-valid routes |
| ShapPanel | Explainability bars and trend deltas |
| Copilot | Chat, voice capture, proactive brief cards |
| AgentLog | Decision history and audit visibility |
| WarGame | Disturber vs Healer live simulation |
| BacktestTimeline | Ever Given replay and scenario scrubber |
| WhatIfPanel | Scenario entry and impact summary |

## 6. Runtime Data Flow

### 6.1 Normal monitoring loop

1. External sources emit events or the mock generator seeds them.
2. Ingestion adapters normalize the payloads into canonical events.
3. Kafka or the in-process event bus distributes those events.
4. Feature assembly builds the current shipment feature vector.
5. Risk scoring returns DRI and SHAP factors.
6. The agent evaluates the DRI against policy thresholds.
7. If the shipment is critical, the graph service generates candidates.
8. The solver validates hard constraints and ranks the feasible routes.
9. The agent executes the approved route and records the decision.
10. The copilot explains the action and the UI receives a realtime update.

### 6.2 Red-alert autonomous reroute

```text
signal -> normalize -> score -> DRI >= red threshold?
  -> no: monitor and cache
  -> yes: compute candidates -> solve constraints -> select route
      -> update shipment state -> notify customer / ops
      -> append audit log -> broadcast websocket event
```

### 6.3 Human override flow

1. Ops submits an override request for a shipment.
2. The request creates an audit record and a temporary policy flag.
3. The agent respects the override for the configured window.
4. The override itself is visible in the audit stream and dashboard.

### 6.4 What-if simulation flow

1. Operator enters or speaks a scenario.
2. Copilot parses the scenario intent.
3. The graph layer temporarily mutates the route topology.
4. The scorer recomputes impacted DRI values.
5. The solver returns the projected impact and alternate routes.
6. The UI shows network cost, delay, and reroute options.

### 6.5 Ever Given backtest flow

1. Historical AIS data is replayed through the same feature pipeline.
2. The scoring service emits a historical DRI timeline.
3. The agent is run in replay mode, not production mode.
4. Route decisions are compared with the expected historical outcome.
5. The resulting report is stored for evidence and judge-facing proof.

### 6.6 War game flow

1. The Disturber emits simulated events.
2. The Healer consumes the events through the same agent interface.
3. The solver and reroute logic respond under the same policies as production.
4. The simulation tracks ROI defended, actions taken, and response latency.

## 7. API Design

### 7.1 REST endpoints

All public endpoints should be versioned, for example under `/api/v1`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness and version check |
| GET | `/ready` | Readiness check for dependencies |
| GET | `/api/v1/shipments` | List current shipment state |
| GET | `/api/v1/shipments/{id}` | Get one shipment and its route |
| POST | `/api/v1/disruptions/simulate` | Trigger a controlled disruption for testing |
| POST | `/api/v1/reroutes/{shipment_id}` | Compute or execute a reroute |
| GET | `/api/v1/agent/status` | Agent health and current tick status |
| POST | `/api/v1/agent/override/{shipment_id}` | Temporarily freeze agent actions |
| POST | `/api/v1/copilot/query` | Ask the grounded copilot a question |
| POST | `/api/v1/what-if` | Run scenario planning |
| POST | `/api/v1/wargame/start` | Start a simulation session |
| GET | `/api/v1/wargame/{session_id}` | Inspect simulation state |
| GET | `/metrics` | Prometheus metrics |

### 7.2 WebSocket channels

| Channel | Payloads |
|---|---|
| `/ws/live` | DRI updates, route changes, shipment position, alert state |
| `/ws/agent` | Decision tick, route approval, override events, audit summary |
| `/ws/copilot` | Proactive briefs, answer tokens, what-if results |
| `/ws/wargame` | Disturber events, Healer responses, ROI counter |

### 7.3 Event contracts

Use canonical event names that are stable across runtime and replay modes.

| Event | Meaning |
|---|---|
| `shipment.signal.received` | Raw source event ingested |
| `shipment.features.built` | Feature vector assembled |
| `shipment.dri.updated` | DRI and SHAP output generated |
| `shipment.route.proposed` | Candidate routes computed |
| `shipment.route.selected` | Final route chosen |
| `shipment.action.executed` | Reroute or notification applied |
| `shipment.override.requested` | Human override filed |
| `copilot.brief.generated` | Proactive explanation created |
| `scenario.whatif.completed` | What-if summary returned |
| `wargame.event.fired` | Disturber emitted a simulated event |

## 8. Data and Storage Design

### 8.1 Storage layers

| Layer | Recommended store | Why |
|---|---|---|
| Operational truth | PostgreSQL | Strong consistency for shipments, routes, actions, overrides |
| Geospatial querying | PostGIS extension in PostgreSQL | Efficient port and route geometry queries |
| Live state cache | Redis | Low-latency DRI and dashboard state |
| Event backbone | Kafka | Durable decoupled processing at scale |
| Stream compute | Flink | Windowing, joins, enrichment, anomaly detection |
| Model registry | MLflow | Versioned model lifecycle and promotion |
| Artifact storage | S3 or compatible object store | Model files, replay data, logs, exported reports |

### 8.2 Core entities

Keep the documented entities, but harden them for production.

| Entity | Purpose | Recommendation |
|---|---|---|
| shipments | Current shipment state | Add tenant_id, version, and geospatial columns |
| disruption_events | Detected disruptions | Partition by time and tenant |
| routes | Candidate and selected routes | Store path geometry and score breakdown |
| agent_actions | Audit trail for autonomous decisions | Append-only, immutable, heavily indexed |
| wargame_sessions | Simulation metadata | Store ROI defended and scenario labels |

### 8.3 Recommended schema improvements

- Use `geography(Point, 4326)` for shipment and port coordinates.
- Use `LineString` or route polyline encoding for route geometry.
- Add `tenant_id` to every business table if multi-tenancy is required.
- Add `model_version`, `feature_version`, and `decision_version` to audit records.
- Add `idempotency_key` to command endpoints.
- Add `source_event_id` and `source_timestamp` to every event-backed record.
- Partition event tables monthly or by tenant if throughput grows.
- Index common dashboard filters: `shipment_id`, `status`, `dri_score`, `updated_at`.
- Use GIN indexes on JSONB fields such as SHAP factors and route constraint metadata.

## 9. External Integrations

### 9.1 Operational data sources

- AIS vessel tracking, preferably `aisstream.io` for live demo and production validation.
- Weather APIs for storm, wind, and wave severity.
- Port congestion feeds and port authority notices.
- Customs clearance and SLA status feeds.
- Geopolitical risk and sanctions data.
- Tariff data, whether rule-based tables or a connected tariff feed.
- News/headline ingestion for disruption detection.

### 9.2 Platform integrations

- Claude API for grounded explanations, proactive briefs, and scenario parsing.
- MLflow for model tracking and registry.
- Kafka and Flink for streaming and enrichment.
- Redis for live dashboard state.
- PostgreSQL and PostGIS for operational truth.
- S3-compatible storage for artifacts and replay files.
- Prometheus, Grafana, and OpenTelemetry for observability.
- Sentry for exception tracking.

### 9.3 Notification integrations

- Email and webhook delivery for customers.
- Slack, Teams, or similar ops channels for internal escalation.
- Optional SMS or push notifications for critical reroutes.

## 10. Security, Trust, and Governance

### 10.1 Authentication and authorization

- Use OIDC for user authentication.
- Enforce role-based access control with roles such as `ops_analyst`, `logistics_manager`, `auditor`, and `admin`.
- Separate read-only dashboard access from route override and reroute permissions.
- Protect all machine-to-machine calls with service identities and signed tokens.

### 10.2 Data protection

- Encrypt all transport with TLS.
- Encrypt databases and object storage at rest.
- Keep secrets in a managed secret store, not in `.env` for production.
- Mask sensitive payload fields in logs and audit exports.

### 10.3 Copilot safety

- Copilot responses must be grounded in SHAP output, route solver output, and shipment state.
- The copilot must never invent a reason that is not present in the observed data.
- Prompt instructions should explicitly forbid ungrounded speculation.
- If the LLM service fails, fall back to a deterministic explanation template.

### 10.4 Audit and compliance

- Treat `agent_actions` as an immutable audit log.
- Record who approved or overrode each critical action.
- Store enough data to replay the decision later.
- Keep retention policies explicit for operational, analytical, and simulation data.

## 11. Scalability and Performance

### 11.1 Scaling model

- Scale ingestion by source and region.
- Scale scoring and copilot workers horizontally because they are stateless.
- Partition Kafka topics by shipment or tenant key.
- Use Redis to absorb frequent dashboard reads.
- Keep websocket fanout isolated from core decisioning workers.

### 11.2 Performance targets

Recommended SLOs for production:

| Metric | Target |
|---|---|
| DRI inference latency | under 100 ms per shipment |
| Red alert to route proposal | under 30 s |
| Dashboard propagation delay | under 1 s |
| Copilot brief generation | under 3 s |
| WebSocket reconnect recovery | under 5 s |
| End-to-end signal to audit log | under 2 min in steady state |

### 11.3 Optimization tactics

- Warm-load models at service startup.
- Cache the latest feature vector and DRI per shipment.
- Precompute candidate routes for high-risk corridors.
- Limit graph expansion with route horizon and constraint-aware pruning.
- Use async database and HTTP clients.
- Batch low-priority news and tariff updates into the scoring window.
- Prefer read models and materialized views for dashboard screens.
- Keep the LLM out of the critical path for actual reroute execution.

## 12. Reliability and Fault Tolerance

### 12.1 Failure handling

- Use retries with exponential backoff for transient upstream failures.
- Use a dead-letter queue for malformed or unrecoverable events.
- Make all command endpoints idempotent.
- Use circuit breakers for external APIs such as weather or AIS.
- If a source is unavailable, continue with cached values and mark the source as degraded.
- If copilot generation fails, fall back to a deterministic summary.
- If route solving fails, escalate instead of guessing.

### 12.2 Data durability

- Keep Postgres as the system of record.
- Use point-in-time backups and tested restore procedures.
- Store raw source events for replay and forensic review.
- Replicate object storage artifacts across regions when the deployment warrants it.

### 12.3 Deployment resilience

- Run health, readiness, and liveness checks on every service.
- Use rolling updates or blue/green for production deploys.
- Keep a rollback path for model and code deployments.
- Separate demo mode from production mode with configuration, not branches.

## 13. Observability and Operations

### 13.1 What to observe

- Event lag by topic and source.
- DRI distribution by lane, region, and cargo type.
- Route solver time and constraint rejection counts.
- Agent tick duration and override frequency.
- Copilot latency and fallback rate.
- Dashboard websocket connection health.
- Model drift, score calibration, and source quality.

### 13.2 Operational dashboards

- Supply chain command view: live shipments, red alerts, and reroutes.
- Agent view: last tick, queued actions, overrides, and failures.
- Simulation view: war game state and ROI defended.
- Model view: training runs, live accuracy, and feature drift.

### 13.3 Incident response

- Alert when the agent falls behind schedule.
- Alert when a source degrades or stops emitting events.
- Alert when route solve latency breaches the SLO.
- Alert when copilot grounding fails or falls back repeatedly.

## 14. Technology Stack Recommendation

| Layer | Recommendation | Rationale |
|---|---|---|
| Backend API | FastAPI + Pydantic + async Python | Matches the docs, supports websockets, and is fast to build |
| Agent orchestration | LangGraph | Explicit state machine for autonomous flows |
| Risk models | XGBoost + Isolation Forest + optional LSTM | Balanced accuracy, anomaly detection, and temporal signal capture |
| Explainability | SHAP | Mandatory trust layer for every DRI score |
| Routing | NetworkX + PuLP | Fast candidate generation plus hard constraints |
| Graph persistence | PostgreSQL + PostGIS now, Neo4j-compatible schema later | Practical MVP plus clean production migration path |
| Streaming | Kafka + Flink | Durable and scalable event processing |
| Cache | Redis | Low-latency live state |
| Frontend | React + TypeScript + Vite | Matches the docs and is maintainable |
| Map | Leaflet for MVP, Mapbox GL JS for production geo layers | Fast delivery now, richer visualization later |
| LLM copilot | Claude API | Already in the docs and suited to grounded response generation |
| ML ops | MLflow | Versioning, comparison, and promotion of models |
| IaC | Terraform + Helm on EKS | Reproducible production deployment |
| Observability | OpenTelemetry + Prometheus + Grafana + Sentry | Coverage for traces, metrics, dashboards, and exceptions |
| Identity | OIDC provider | Standard auth, easy enterprise integration |

## 15. Build and Deployment Topology

### 15.1 Environment tiers

- Local demo: docker-compose, mock sources, seeded shipments, single-node Postgres and Redis.
- Integration/staging: real APIs where available, test Kafka, test ML registry, staging dashboards.
- Production: EKS, managed Postgres, Redis, Kafka, object storage, TLS, centralized observability.

### 15.2 CI/CD gates

1. Lint and format.
2. Unit tests and contract tests.
3. Model smoke tests.
4. Integration tests for API and websocket behavior.
5. Container build and vulnerability scan.
6. Deploy to staging.
7. Synthetic checks and canary verification.
8. Promote to production with rollback enabled.

### 15.3 Runtime safety switches

- `KAFKA_BOOTSTRAP_SERVERS` empty -> mock mode.
- Missing external API key -> fallback source adapter.
- LLM timeout -> deterministic explanation fallback.
- Route solver failure -> escalate, do not auto-guess.
- Agent override -> shipment-level or tenant-level freeze window.

## 16. Recommended Implementation Order

If this blueprint is used as a build guide, the correct order is:

1. Establish the schema, auth, and health endpoints.
2. Implement mock ingestion and the live shipment read model.
3. Add DRI scoring with SHAP and the Redis cache.
4. Add route generation and PuLP constraint enforcement.
5. Add the LangGraph agent and the audit log.
6. Add the grounded copilot, proactive briefs, and voice input.
7. Add Ever Given backtesting and the war game.
8. Replace mock sources with real integrations source by source.
9. Add Kafka, Flink, and production deployment hardening.

## 17. Final Architectural Verdict

The best version of Precursa is not a single model or a single dashboard.
It is a policy-driven control loop with three inseparable layers:

- Perception: ingest and score the world in near real time.
- Decision: validate every action against explicit constraints.
- Explanation: make every action auditable and understandable.

The v2 docs provide the correct system spine.
The v3 docs supply the credibility upgrades that make the spine believable in 2026.
The production design should preserve both:

- agent-first autonomy,
- SHAP-based explainability,
- constraint-aware routing,
- real-world data sources,
- proactive and voice-enabled copilots,
- scenario planning,
- backtesting,
- and adversarial simulation.

That combination is the strongest foundation for a production-grade Precursa platform.