# Precursa Context

## 0. Workspace State
This workspace is documentation-first. There is no executable backend/frontend source code in the repo yet; the present files define the product, architecture, roadmap, demo story, and supporting visuals.

Canonical docs and assets:
- `Docs/precursa_documentation.md`
- `Docs/precursa_documentation.txt`
- `Docs/ROADMAP.md`
- `Docs/solution.md`
- `Docs/precursa_architecture_light.svg`
- `Docs/precursa_architecture_light.png`
- `Docs/market_research.png`
- `Docs/precursa_documentation.pdf`

Interpretation:
- `precursa_documentation.md` is the master narrative and investor/demo blueprint.
- `ROADMAP.md` is the implementation contract for the future codebase.
- `solution.md` is the plain-English product explanation.
- The architecture SVG/PNG are the visual system map.
- `market_research.png` is supporting evidence/screenshot material, not runtime logic.
- The PDF is the packaged export of the same documentation bundle.

## 1. Project Overview
### Purpose
Precursa is an AI-powered self-healing supply chain intelligence platform that detects shipment disruptions early, scores risk per shipment, reroutes shipments autonomously, and explains the decision to operators.

### Problem It Solves
Modern supply chains are reactive:
- disruptions are detected too late,
- monitoring is fragmented across many signals,
- manual rerouting is slow,
- one local issue can cascade into network-wide failures,
- current visibility tools inform users but do not act.

The docs repeatedly anchor on these quantified pain points:
- about $184B annual loss from supply chain disruptions,
- 4-6 hour average detection time,
- 73% manual monitoring,
- 2-3 day manual recovery delays,
- 85% of disruptions have detectable precursor signals in existing data.

### Key Capabilities
- Ingests 10+ live data streams: weather, port feeds, IoT/GPS, geo-risk, customs, and other shipping signals.
- Computes a 0-100 Disruption Risk Index (DRI) per shipment.
- Triggers autonomous rerouting when risk is high.
- Rebooks carriers, updates warehouse slots, and notifies customers.
- Explains decisions through a Claude-powered AI Copilot.
- Shows a live dashboard with shipment markers, route changes, and alert states.

### Target Users / Systems
Primary users:
- freight forwarders,
- 3PLs,
- global manufacturers,
- e-commerce logistics teams,
- pharma and cold-chain operators,
- supply chain operators and demo judges.

Primary system integrations:
- weather APIs,
- port/AIS feeds,
- customs systems,
- carrier GPS/IoT sensors,
- risk-index providers,
- analytics and model-serving infrastructure.

## 2. High-Level Architecture
### Architecture Snapshot
The project has two explicit architectural layers:
1. Hackathon MVP: minimal-infra demo path that works locally.
2. Full vision: production-grade streaming and automation stack.

```text
[Weather / Port / IoT / GPS / Geo-risk / Customs]
                |
                v
 [Ingestion + Stream layer]
   MVP: mock generator + polling
   Vision: Kafka + Flink
                |
                v
 [Risk Scoring]
   LSTM + Isolation Forest + XGBoost
   -> DRI 0-100
                |
                v
 [State + Persistence]
   Redis cache + Postgres event/route logs
                |
                v
 [Routing / Decisions]
   MVP: NetworkX + direct Claude prompt
   Vision: NetworkX / Neo4j + LangGraph
                |
                v
 [WebSocket live updates]
                |
                v
 [React dashboard]
   MVP: Leaflet
   Vision: Mapbox GL JS
```

### Full Vision vs MVP Mapping
| Layer | Full Vision | 50-Hour MVP Replacement | Why |
|---|---|---|---|
| Event bus | Apache Kafka + Confluent Cloud | FastAPI mock data generator | Kafka setup cost and time |
| Stream processing | Apache Flink | Python polling loop | Same demo effect, no infra |
| ML ensemble | LSTM + Isolation Forest + XGBoost | Single XGBoost model or rule-based fallback | Fast to train and demo |
| Graph engine | Neo4j + NetworkX | NetworkX only | Lower setup friction |
| Automation agent | LangGraph orchestration | Direct Claude structured prompt | Same autonomous feel |
| ML Ops | AWS SageMaker + MLflow | Local FastAPI model endpoint | Demo simplicity |
| Frontend map | Mapbox GL JS | Leaflet + OpenStreetMap | No API key friction |
| Infra | Docker + Kubernetes + Terraform | Run locally | Hackathon practicality |

### Component Interaction
- REST endpoints are used for commands and snapshots.
- WebSocket is the source of truth for live frontend state.
- Redis is the low-latency runtime cache for DRI and shipment state.
- PostgreSQL stores durable records: shipments, disruptions, routes, and agent actions.
- The graph engine consumes the current disruption map and route graph, then returns ranked alternatives.
- The Copilot consumes shipment context plus the reroute decision and returns a human explanation.

### End-to-End Data Flow
1. Data arrives from live sources or mock generators.
2. The backend normalizes features and computes DRI.
3. DRI and shipment state are cached and logged.
4. If DRI crosses the action threshold, routes are computed.
5. Best route is selected and written back to state.
6. WebSocket pushes updates to the frontend.
7. Copilot generates a plain-English explanation.
8. Operator/customer notifications are emitted.

### Feedback Loops Visible in the Diagram
The SVG architecture diagram also shows two important feedback paths:
- MLOps retraining loop: outcomes and labels feed back into model improvement.
- Ops override loop: human intervention can supersede autonomous action.

## 3. File & Module Breakdown
### 3.1 Current Files in the Workspace
| File | Role | Key Responsibility | Notes |
|---|---|---|---|
| `Docs/precursa_documentation.md` | Master brief | Full product story, problem framing, technical architecture, demo blueprint, market analysis, business model, roadmap, risks, and pitch changes | Most complete narrative source |
| `Docs/precursa_documentation.txt` | Text export | Plain-text version of the same content for easier extraction/search | Useful for text-only pipelines |
| `Docs/ROADMAP.md` | Implementation plan | Canonical build order, folder structure, env vars, phase-by-phase MVP to production roadmap, schema shapes, API contracts | Most actionable engineering source |
| `Docs/solution.md` | Simplified explanation | Five-step non-technical summary of how Precursa works | Best for stakeholder/pitch language |
| `Docs/precursa_architecture_light.svg` | Canonical diagram | Vector architecture diagram with interactive nodes, color legend, data/agent feedback loops | Best visual source of system shape |
| `Docs/precursa_architecture_light.png` | Diagram raster export | Static image export of the same architecture | Slide-friendly copy |
| `Docs/market_research.png` | Supporting evidence image | Screenshot-style supporting material for market-research/analysis narrative | Not part of runtime system |
| `Docs/precursa_documentation.pdf` | Packaged export | PDF bundle of the documentation set | Shareable submission artifact |

### 3.2 Planned Source Modules From the Roadmap
These modules are not present yet, but they define the intended codebase shape.

| Planned Path | Responsibility | Key Functions / Types | Dependencies |
|---|---|---|---|
| `backend/app/main.py` | FastAPI entrypoint | app startup, health endpoint, router registration, background tasks | FastAPI, lifespan startup, websocket, services |
| `backend/app/api/shipments.py` | Shipment read API | GET shipment list/detail | models, Redis, database |
| `backend/app/api/disruptions.py` | Disruption trigger API | POST trigger-disruption | services, event log, websocket |
| `backend/app/api/reroute.py` | Reroute API | POST reroute by shipment id, return top 3 routes | graph engine, route persistence, websocket |
| `backend/app/api/copilot.py` | Copilot API | POST question->answer, stream response when needed | Claude client, shipment context, events |
| `backend/app/core/config.py` | Configuration | env parsing, settings, feature flags | python-dotenv / Pydantic settings |
| `backend/app/core/database.py` | Persistence wiring | async SQLAlchemy engine/session, Redis client | PostgreSQL, Redis |
| `backend/app/models/*.py` | Data schemas | Shipment, Disruption, Route models | Pydantic, SQLAlchemy |
| `backend/app/services/data_generator.py` | Mock data source | seed shipments, periodic DRI nudges | port coordinate map, websocket |
| `backend/app/services/dri_scorer.py` | DRI computation | score_shipment, model loading, Redis cache update | XGBoost, LSTM, Isolation Forest, ML ensemble |
| `backend/app/services/graph_engine.py` | Route ranking | build graph, rank candidate routes, composite scoring | NetworkX |
| `backend/app/services/copilot_service.py` | Explanation engine | explain_disruption, Claude prompt assembly | Anthropic SDK |
| `backend/app/websocket/live_feed.py` | Live broadcast | push updated shipment state to clients | backend state, websocket manager |
| `backend/ml/train_xgboost.py` | XGBoost trainer | fit classifier, log metrics/artifacts | XGBoost, MLflow |
| `backend/ml/train_lstm.py` | LSTM trainer | sequence model for temporal disruption prediction | PyTorch |
| `backend/ml/isolation_forest.py` | Anomaly detector | fit anomaly model, derive anomaly score | scikit-learn |
| `backend/ml/ensemble.py` | Score fusion | combine model outputs into DRI | deterministic weighting |
| `backend/ml/data/README.md` | Dataset notes | Kaggle/source instructions | documentation only |
| `frontend/src/App.tsx` | Dashboard shell | compose map, cards, copilot, panels | React |
| `frontend/src/components/Map.tsx` | Shipment map | Leaflet map, markers, polylines, popups | Leaflet, OSM |
| `frontend/src/components/ShipmentCard.tsx` | Shipment summary card | DRI badge, route/status display | React props |
| `frontend/src/components/DisruptionPanel.tsx` | User action UI | select shipment/disruption, trigger API call | API client |
| `frontend/src/components/RouteComparison.tsx` | Route options UI | show top 3 paths and deltas | reroute API |
| `frontend/src/components/Copilot.tsx` | Chat/explanation panel | explanation history, follow-up Q&A | Claude response, websocket |
| `frontend/src/hooks/useWebSocket.ts` | Live data hook | connect/update state from websocket | WS URL |
| `frontend/src/hooks/useShipments.ts` | Shipment state hook | store and derive shipment state | websocket + API |
| `frontend/src/types/index.ts` | Shared TS types | shipment, route, disruption contracts | frontend API shapes |
| `frontend/src/api/client.ts` | HTTP client | fetch snapshots and trigger actions | axios |
| `infra/docker-compose.yml` | Local environment | backend, frontend, postgres, redis | Docker Compose |
| `infra/docker-compose.dev.yml` | Dev environment | hot-reload setup | Docker Compose |
| `infra/k8s/*` | Production manifests | deployments, ingress, stateful services | Kubernetes |
| `.github/workflows/ci.yml` | CI pipeline | tests, build, deploy gates | GitHub Actions |

## 4. Core Logic & Algorithms
### 4.1 DRI Scoring
The DRI is the central product abstraction. It is always an integer in the range 0-100.

Roadmap scoring logic:
- XGBoost estimates current disruption probability.
- LSTM estimates temporal disruption risk from recent shipment history.
- Isolation Forest estimates anomaly likelihood from feature outliers.
- The three outputs are fused into a single DRI.

Weighted fusion used in the roadmap:
```text
DRI = clamp(int((0.4 * xgb_prob + 0.4 * lstm_prob + 0.2 * iso_score) * 100), 0, 100)
```

Fallback rule bands used before ML is ready:
- 0-30   -> green   -> on_track
- 31-60  -> yellow  -> at_risk
- 61-80  -> orange  -> at_risk
- 81-100 -> red     -> disrupted

### 4.2 Route Ranking / Rerouting
The graph engine models ports as a directed graph with weighted edges.

Composite edge weight from the roadmap:
```text
score = 0.4 * cost/5000 + 0.35 * eta_hours/300 + 0.15 * risk + 0.1 * carbon/600
```

Route selection process:
1. Build a directed graph of ports and edge attributes.
2. Compute shortest simple paths from origin to destination.
3. Rank paths by composite score.
4. Return the top 3 options.
5. Write the selected route back to shipment state.
6. Broadcast updated waypoints to the UI.

### 4.3 Autonomous Decision Loop
The docs describe a threshold-driven self-healing loop.

```text
if dri_score > 75:
    routes = compute_routes(origin, destination, disruption_map)
    selected = select_route(routes, cargo_policy)
    execute_reroute(selected)
    notify_stakeholders(selected)
    explain_decision(shipment, disruption, selected)
else:
    continue monitoring
```

Selection policy can be cargo-aware:
- pharma/cold chain -> minimize ETA delta,
- general freight -> balance cost, risk, and carbon,
- demo scenarios -> prefer visibly different reroutes for clarity.

### 4.4 Streaming and Update Loop
Two operational modes exist:
- MVP mode: mock generator nudges shipments every 30 seconds or 2 minutes.
- Production mode: Kafka/Flink pipeline feeds enrichment data to the scorer.

The frontend should not poll for live state. It should subscribe to WebSocket updates.

### 4.5 Copilot Explanation Flow
The Claude copilot is used to turn a machine decision into an operator-friendly explanation.
- Input: shipment context, disruption type, route choice, cost delta, ETA delta, carbon delta.
- Output: 2-3 plain-English sentences explaining why the selected route was chosen.
- Failure mode: return a canned fallback explanation instead of breaking the demo.

## 5. Data Structures & Schema
### 5.1 Shipment Model
The roadmap defines the core shipment record as:

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Shipment id, e.g. `SHP-004` |
| `origin_port` | string | Origin port name |
| `destination_port` | string | Destination port name |
| `cargo_type` | string | Cargo category |
| `carrier` | string | Carrier name |
| `current_lat` | float | Current latitude |
| `current_lon` | float | Current longitude |
| `dri_score` | int | Risk score, 0-100 |
| `dri_level` | string | `green`, `yellow`, `orange`, `red` |
| `status` | string | `on_track`, `at_risk`, `disrupted`, `rerouted` |
| `eta` | datetime | Estimated arrival |
| `route` | list[dict] | Waypoints as `{lat, lon}` |

### 5.2 Supporting Data Objects
#### Disruption event record
Implied fields from the roadmap and docs:
- event id,
- shipment id,
- disruption type,
- old DRI,
- new DRI,
- timestamp,
- selected route id,
- notes/cause,
- operator/agent origin.

#### Route response object
`POST /api/reroute/{shipment_id}` returns:
- `routes`: array of 3 routes.

Each route includes:
- `path`,
- `cost`,
- `eta_hours`,
- `risk`,
- `carbon`,
- `composite_score`,
- optionally `cost_delta`, `eta_delta_hours`, `carbon_delta_kg`.

#### Agent action record
The autonomous agent logs to `agent_actions` with:
- shipment id,
- DRI at decision time,
- action taken,
- selected route,
- timestamp,
- explanation,
- notification status.

### 5.3 API Contracts
| Endpoint | Shape | Purpose |
|---|---|---|
| `GET /api/shipments` | response list of shipments | current snapshot for UI |
| `GET /api/shipments/{id}` | response single shipment | detail panel |
| `POST /api/trigger-disruption` | body: `{ shipment_id, disruption_type }` | force a disruption event |
| `POST /api/reroute/{shipment_id}` | response: `{ routes: [...] }` | compute and select routes |
| `POST /api/copilot` | body: `{ shipment_id, question }` | ask natural language question |
| `WS /ws/live` | stream of shipment state updates | live frontend state |

### 5.4 Cache / Storage Conventions
- Redis key style: `dri:{shipment_id}` for fast DRI lookup.
- Shipment snapshots may use a short TTL (roadmap mentions 60 seconds for fast reads).
- PostgreSQL is the durable audit layer for shipments, disruptions, routes, and agent actions.

## 6. Execution Flow
### 6.1 Startup Lifecycle
1. Load environment variables from `.env`.
2. Start PostgreSQL and Redis.
3. Initialize backend app and async database wiring.
4. Load ML models or fallback scoring logic.
5. Seed 5 shipments if running in demo/mock mode.
6. Start WebSocket broadcaster.
7. Start frontend and subscribe it to live updates.

### 6.2 Live Demo Lifecycle
1. Open dashboard and show 5 seeded shipments.
2. Trigger a disruption on a selected shipment, commonly `SHP-004`.
3. DRI spikes to a high-risk value such as 87.
4. Status changes to disrupted and an alert appears.
5. Graph engine computes 3 alternate routes.
6. Best route is selected and the map visibly changes.
7. Copilot explains the reroute in plain English.
8. Operator can ask a follow-up question such as why Colombo was chosen over Jebel Ali.

### 6.3 Production Streaming Lifecycle
1. External signals are ingested from weather, AIS, port, and customs sources.
2. Kafka transports the streams.
3. Flink enriches and windows the data.
4. DRI scorer computes shipment risk.
5. Redis/Postgres store fast and durable state.
6. Rerouting and automation logic act on high-risk shipments.
7. WebSocket updates the dashboard and Copilot panel.
8. Audit logs preserve the full decision trail.

## 7. External Integrations
| Integration | Purpose | Phase |
|---|---|---|
| Weather APIs / OpenWeatherMap | disruption signal source | MVP + production |
| Port feeds / AIS / MarineTraffic | vessel and port congestion inputs | MVP + production |
| Customs APIs | clearance and delay signals | MVP + production |
| Geo-risk indexes | geopolitical risk features | MVP + production |
| Kafka / Confluent Cloud | event bus for live streams | production |
| Flink / PyFlink | stream enrichment and windowing | production |
| FastAPI | backend API server | MVP + production |
| WebSockets | live UI state transport | MVP + production |
| PostgreSQL | durable record store | MVP + production |
| Redis | low-latency cache | MVP + production |
| XGBoost | risk classification | MVP + production |
| PyTorch LSTM | temporal prediction | production vision |
| Isolation Forest | anomaly detection | production vision |
| MLflow | model tracking and registry | production vision |
| Claude API (Anthropic) | explanation and natural-language Q&A | MVP + production |
| LangGraph | autonomous decision workflow | production vision |
| React 18 + TypeScript + Vite | frontend app shell | MVP + production |
| Leaflet + OpenStreetMap | demo map rendering | MVP |
| Mapbox GL JS | production map rendering | production vision |
| Docker / Docker Compose | local execution and packaging | MVP + production |
 | Kubernetes / EKS / Terraform | cloud deployment | production |
| GitHub Actions | CI/CD pipeline | production |
| Prometheus / Grafana / Sentry | observability | production hardening |

## 8. Configuration & Environment
### 8.1 Environment Variables
The roadmap defines these canonical env vars:

```env
# Backend
DATABASE_URL=postgresql://user:pass@localhost:5432/precursa
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key

# Anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key

# Kafka (leave blank for MVP mock mode)
KAFKA_BOOTSTRAP_SERVERS=
CONFLUENT_API_KEY=
CONFLUENT_API_SECRET=

# ML
MLFLOW_TRACKING_URI=./mlruns
MODEL_PATH=./ml/models/

# Frontend
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/live
```

### 8.2 Build / Run Instructions From the Roadmap
These are roadmap instructions, not yet backed by source files in the workspace.

Backend bootstrap:
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn sqlalchemy asyncpg redis pydantic python-dotenv
pip freeze > requirements.txt
uvicorn app.main:app --reload
```

Frontend bootstrap:
```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install axios leaflet @types/leaflet react-leaflet
npm run dev
```

Local stack:
- Use `docker-compose up` for backend, frontend, postgres, and redis.
- Run Alembic migration scaffolding for schema changes.
- Run `pytest` for backend tests and `npm test` for frontend tests.
- Run `mlflow ui` for model tracking when ML training exists.

### 8.3 Demo Prerequisites
- Backend running on `localhost:8000`.
- Frontend visible with 5 seeded shipments.
- Claude API key configured.
- Browser zoom around 90% for presentation.
- Disruption scenarios pre-seeded.
- Fallback/mock mode available if any external service is down.

### 8.4 Port and Runtime Notes
- The roadmap bootstrap uses Vite's default `5173`.
- The demo checklist expects the frontend to be on `3000`.
- Treat that as an implementation detail to normalize during setup.

## 9. Key Insights & Design Decisions
- The docs deliberately separate MVP and 18-month vision; do not collapse them into one implementation plan.
- Precursa differentiates on action, not just visibility. The platform must reroute, not merely alert.
- The DRI is the product's central abstraction and should remain a plain integer, not a probability object.
- WebSocket should be the frontend's live state source; REST is for commands and initial snapshots.
- Mock mode is mandatory so the demo cannot fail because an external API is unavailable.
- NetworkX and Leaflet are pragmatic MVP choices that avoid infrastructure and billing friction.
- Neo4j, Mapbox, Kafka, Flink, LangGraph, SageMaker, and Terraform are production-vision components, not required for the hackathon demo.
- Some market and impact numbers are projections or benchmark-based; they should be presented honestly as estimates unless separately validated.
- Human override is a first-class concept, not a failure state.

## 10. Limitations & Risks
### Technical Risks
- No executable source code exists yet in the workspace, so the docs describe an intended system rather than a running repo.
- ML quality depends on training data quality and feature engineering.
- Graph routes can become infeasible if the edge set is incomplete.
- Claude latency or API failure can affect the explanation layer.
- WebSocket instability can freeze the live dashboard if no fallback exists.
- Kafka/Flink/managed cloud services add operational complexity in production.

### Product / Demo Risks
- Some claims in the docs are simulation-based or projected rather than validated by production pilots.
- If the demo story overstates maturity, judges may challenge the numbers.
- The system depends on a clean distinction between demo mode and production vision.

### Scale Risks
- Millions of shipments and many concurrent connections would require partitioning, backpressure handling, and stronger infra.
- State synchronization between Redis, Postgres, and WebSocket broadcasts can drift if not carefully managed.

## 11. Extension Points
- Implement the roadmap folder structure under `backend/`, `frontend/`, `infra/`, and `ml/`.
- Replace mock generation with Kafka/Flink ingestion.
- Replace NetworkX-only routing with Neo4j-backed graph services.
- Expand the ML ensemble and track runs in MLflow.
- Add JWT auth, observability, and production deployment manifests.
- Add more disruption types, more route heuristics, and more cargo-specific policies.
- Add customer notification channels beyond the current conceptual webhook/email layer.
- Add test coverage for DRI scoring, route ranking, API endpoints, and live WebSocket behavior.
- Add a real data ingestion contract for weather, AIS, and customs providers.

## 12. Canonical Facts To Remember
- Product name: Precursa.
- Tagline: Self-Healing Supply Chain Intelligence.
- Core loop: ingest signals -> score DRI -> reroute -> notify -> explain.
- DRI range: 0-100 integer.
- Live update cadence: every 2 minutes in the docs, 30-second nudges in the mock loop.
- Hackathon demo seed: 5 shipments.
- Route search output: top 3 candidate routes.
- Demo goal: show a live disruption, an automatic reroute, and a Copilot explanation.
- 50-hour mode is explicitly simpler than the 18-month production roadmap.
