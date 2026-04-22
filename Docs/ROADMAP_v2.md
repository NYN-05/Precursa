# Precursa v2.0 — Development Roadmap
> **For AI Coding Assistants (Copilot / Cursor / Claude Code):**
> This is the canonical build guide for Precursa v2.0. Read every section before writing
> any code. Follow phases in strict order. Each phase ends with a testable acceptance
> criterion — do not start the next phase until the current one passes.
>
> **Critical architectural rule:** The LangGraph autonomous agent is the core of this
> system. Everything else — the dashboard, the copilot, the graph engine — is an output
> channel for the agent. Never write code that makes the agent optional or button-triggered.

---

## What Is Precursa v2.0

Precursa v2.0 is a closed-loop autonomous supply chain intelligence platform.

**Core loop (runs every 2 minutes, no human input required):**
```
Ingest live data
    → Score disruption risk per shipment (DRI 0–100, ML ensemble + SHAP)
        → If DRI > 75: LP solver computes constraint-valid reroutes
            → Agent selects and executes best route autonomously
                → Grounded copilot explains the decision (SHAP-backed)
                    → War game stress-tests the system in parallel
```

**What is new in v2.0 vs v1.0:**

| v1.0 (alert system) | v2.0 (closed-loop agent) |
|---|---|
| LangGraph agent was Phase 5 afterthought | LangGraph agent is Phase 1 backbone |
| Dijkstra-only routing | LP solver enforces hard cargo constraints |
| No model explainability | SHAP values on every DRI prediction |
| Copilot could hallucinate route reasons | Copilot strictly grounded in algorithm output |
| Kaggle dataset validation only | Ever Given backtesting proves real-world accuracy |
| Manual simulation button | Monte Carlo adversarial war game |

---

## Canonical Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Language | Python 3.11 | Backend only |
| API framework | FastAPI + Uvicorn | Async, WebSocket support built-in |
| Agent orchestration | LangGraph 0.2+ | Core of the system — never optional |
| Constraint solver | PuLP | Linear programming for hard cargo constraints |
| Graph engine | NetworkX (MVP) | Neo4j-compatible schema from day one |
| Graph DB (production) | Neo4j | Driver swap only — schema already compatible |
| ML — temporal | PyTorch LSTM | Sequence prediction on shipment history |
| ML — classification | XGBoost | Risk classification from feature snapshot |
| ML — anomaly | scikit-learn Isolation Forest | Detects statistical deviations |
| ML explainability | SHAP | Required on every DRI prediction — not optional |
| ML tracking | MLflow | Experiment tracking + model registry |
| LLM copilot | Anthropic Claude API (claude-sonnet-4-20250514) | Grounded prompts only |
| Event streaming | Apache Kafka + Confluent Cloud | Phase 8 — mock mode for MVP |
| Stream processing | Apache Flink (PyFlink) | Phase 8 — mock mode for MVP |
| Database | PostgreSQL (async via asyncpg) | Shipments, events, routes, agent audit log |
| Cache | Redis | Live DRI scores, WebSocket state |
| Frontend | React 18 + TypeScript + Vite | |
| Map | Leaflet.js (MVP) → Mapbox GL JS (production) | Free tier for hackathon |
| Containerisation | Docker + Docker Compose | Local dev |
| Orchestration | Kubernetes (EKS) + Helm | Production only |
| Infrastructure as code | Terraform | Production only |
| CI/CD | GitHub Actions | From Phase 0 |
| Monitoring | Prometheus + Grafana | Phase 9 |
| Error tracking | Sentry | Phase 9 |

---

## Repository Structure

Create this exact structure before writing any code:

```
precursa/
├── .github/
│   └── workflows/
│       ├── ci.yml                        # Run tests on every push
│       └── deploy.yml                    # Deploy to EKS on merge to main
├── backend/
│   ├── app/
│   │   ├── main.py                       # FastAPI app entry point
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── shipments.py              # GET /api/shipments, GET /api/shipments/{id}
│   │   │   ├── disruptions.py            # POST /api/trigger-disruption (test tool)
│   │   │   ├── reroute.py                # POST /api/reroute/{id}
│   │   │   ├── copilot.py                # POST /api/copilot
│   │   │   ├── agent.py                  # GET /api/agent/status, POST /api/agent/override/{id}
│   │   │   └── wargame.py                # POST /api/wargame/start, GET /api/wargame/status
│   │   ├── core/
│   │   │   ├── config.py                 # All env vars via pydantic-settings
│   │   │   ├── database.py               # PostgreSQL async engine + session
│   │   │   └── redis_client.py           # Redis connection + helpers
│   │   ├── models/
│   │   │   ├── shipment.py               # SQLAlchemy + Pydantic shipment models
│   │   │   ├── disruption.py             # Disruption event models
│   │   │   ├── route.py                  # Route + leg models
│   │   │   └── agent_action.py           # Agent audit log model
│   │   ├── services/
│   │   │   ├── agent_service.py          # LangGraph agent definition + runner
│   │   │   ├── dri_scorer.py             # ML ensemble → DRI + SHAP values
│   │   │   ├── lp_solver.py              # PuLP constraint-valid route selection
│   │   │   ├── graph_engine.py           # NetworkX port graph + path generation
│   │   │   ├── copilot_service.py        # Claude API grounded prompts
│   │   │   ├── data_generator.py         # Mock shipment seeder
│   │   │   ├── backtesting.py            # Ever Given AIS replay engine
│   │   │   └── wargame.py                # Monte Carlo Disturber agent
│   │   └── websocket/
│   │       └── broadcaster.py            # WebSocket connection manager + live feed
│   ├── ml/
│   │   ├── data/
│   │   │   ├── raw/                      # Place Kaggle CSV here
│   │   │   ├── processed/                # Cleaned features
│   │   │   └── ais_ever_given/           # AIS telemetry for backtesting
│   │   ├── data_prep.py                  # Feature engineering pipeline
│   │   ├── train_xgboost.py              # XGBoost training + MLflow logging
│   │   ├── train_lstm.py                 # PyTorch LSTM training
│   │   ├── train_isolation_forest.py     # Anomaly detector training
│   │   ├── ensemble.py                   # Fuses 3 model scores → DRI int
│   │   ├── shap_explainer.py             # SHAP wrapper — returns top 5 factors
│   │   └── models/                       # Saved model artifacts (.pkl, .pt)
│   ├── tests/
│   │   ├── test_agent.py
│   │   ├── test_dri_scorer.py
│   │   ├── test_lp_solver.py
│   │   ├── test_graph_engine.py
│   │   ├── test_copilot.py
│   │   ├── test_api.py
│   │   └── test_wargame.py
│   ├── alembic/                          # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── Map.tsx                   # Leaflet map + shipment markers
│   │   │   ├── ShipmentCard.tsx          # DRI badge, SHAP top factor, status
│   │   │   ├── AlertPanel.tsx            # Red/orange alert list
│   │   │   ├── RouteComparison.tsx       # LP solver top 3 routes sidebar
│   │   │   ├── ShapPanel.tsx             # SHAP breakdown bar chart
│   │   │   ├── Copilot.tsx               # Claude chat panel
│   │   │   ├── AgentLog.tsx              # Live agent decision feed
│   │   │   ├── WarGame.tsx               # Disturber vs Healer live panel
│   │   │   └── BacktestTimeline.tsx      # Ever Given AIS replay timeline
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts           # Live DRI + agent updates
│   │   │   └── useShipments.ts           # Shipment state management
│   │   ├── types/
│   │   │   └── index.ts                  # All shared TypeScript types
│   │   └── api/
│   │       └── client.ts                 # Axios instance + all API calls
│   ├── package.json
│   └── Dockerfile
├── infra/
│   ├── docker-compose.yml                # Full local stack
│   ├── docker-compose.dev.yml            # Dev with hot reload
│   ├── k8s/                              # Kubernetes manifests (Phase 9)
│   │   ├── backend-deployment.yaml
│   │   ├── frontend-deployment.yaml
│   │   ├── postgres-statefulset.yaml
│   │   ├── redis-deployment.yaml
│   │   └── ingress.yaml
│   └── terraform/                        # AWS infrastructure (Phase 9)
│       ├── main.tf
│       ├── eks.tf
│       ├── rds.tf
│       └── variables.tf
├── .env.example                          # All required env vars documented
├── ROADMAP.md                            # This file
└── README.md
```

---

## Environment Variables

Create `.env` in project root. Never commit it. Every variable must exist in `.env.example` with a description.

```env
# ── DATABASE ──────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://precursa:precursa@localhost:5432/precursa
REDIS_URL=redis://localhost:6379/0

# ── SECURITY ──────────────────────────────────────────────
SECRET_KEY=change-this-to-a-random-64-char-string
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480

# ── ANTHROPIC ─────────────────────────────────────────────
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# ── ML ────────────────────────────────────────────────────
MODEL_DIR=./ml/models
MLFLOW_TRACKING_URI=./mlruns
DRI_THRESHOLD_YELLOW=31
DRI_THRESHOLD_ORANGE=61
DRI_THRESHOLD_RED=81
AGENT_TICK_SECONDS=120

# ── KAFKA (leave blank to use mock mode) ──────────────────
KAFKA_BOOTSTRAP_SERVERS=
CONFLUENT_API_KEY=
CONFLUENT_API_SECRET=
KAFKA_TOPIC_WEATHER=weather-events
KAFKA_TOPIC_PORT=port-congestion
KAFKA_TOPIC_POSITIONS=shipment-positions
KAFKA_TOPIC_DRI=dri-updates

# ── EXTERNAL APIS (leave blank to use mock mode) ──────────
OPENWEATHER_API_KEY=
MARINETRAFFIC_API_KEY=

# ── FRONTEND ──────────────────────────────────────────────
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/live

# ── WAR GAME ──────────────────────────────────────────────
WARGAME_TICK_SECONDS=10
WARGAME_DISTURBER_INTENSITY=0.7
```

**Rules:**
- All config loaded via `pydantic-settings` in `app/core/config.py`
- If `KAFKA_BOOTSTRAP_SERVERS` is empty, fall back to mock data generator silently
- If any external API key is missing, fall back to mock data for that source
- The app must start and run fully without any external API keys (demo safety)

---

## Database Schema

Run Alembic migrations for every schema change. Never alter the database manually.

```sql
-- shipments
CREATE TABLE shipments (
    id VARCHAR(20) PRIMARY KEY,           -- e.g. "SHP-001"
    origin_port VARCHAR(50) NOT NULL,
    destination_port VARCHAR(50) NOT NULL,
    cargo_type VARCHAR(50) NOT NULL,      -- "Electronics" | "Pharma" | "FMCG" | "Automotive"
    carrier VARCHAR(100) NOT NULL,
    weight_kg FLOAT NOT NULL,
    temp_requirement_celsius FLOAT,       -- NULL if not temperature-controlled
    current_lat FLOAT NOT NULL,
    current_lon FLOAT NOT NULL,
    current_route JSONB NOT NULL,         -- [{lat, lon}, ...] waypoints
    dri_score INTEGER NOT NULL DEFAULT 0,
    dri_level VARCHAR(10) NOT NULL DEFAULT 'green',
    shap_factors JSONB,                   -- [{feature, value, direction}, ...]
    status VARCHAR(20) NOT NULL DEFAULT 'on_track',
    eta TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- disruption_events
CREATE TABLE disruption_events (
    id SERIAL PRIMARY KEY,
    shipment_id VARCHAR(20) REFERENCES shipments(id),
    disruption_type VARCHAR(50) NOT NULL, -- "port_congestion" | "weather" | "customs" | "carrier_failure"
    severity FLOAT NOT NULL,              -- 0.0 to 1.0
    affected_port VARCHAR(50),
    dri_at_detection INTEGER NOT NULL,
    detected_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);

-- routes
CREATE TABLE routes (
    id SERIAL PRIMARY KEY,
    shipment_id VARCHAR(20) REFERENCES shipments(id),
    path JSONB NOT NULL,                  -- ["Mumbai", "Colombo", "Rotterdam"]
    waypoints JSONB NOT NULL,             -- [{lat, lon}, ...]
    cost_usd FLOAT NOT NULL,
    eta_hours FLOAT NOT NULL,
    risk_score FLOAT NOT NULL,
    carbon_kg FLOAT NOT NULL,
    lp_score FLOAT NOT NULL,              -- composite LP objective value
    constraints_applied JSONB,           -- list of hard constraints enforced
    selected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- agent_actions (audit log — every autonomous decision recorded)
CREATE TABLE agent_actions (
    id SERIAL PRIMARY KEY,
    shipment_id VARCHAR(20) REFERENCES shipments(id),
    action_type VARCHAR(50) NOT NULL,     -- "reroute" | "monitor" | "escalate" | "override_blocked"
    dri_at_action INTEGER NOT NULL,
    route_selected_id INTEGER REFERENCES routes(id),
    shap_top_factor VARCHAR(100),
    lp_constraints_count INTEGER,
    roi_defended_usd FLOAT,
    executed_at TIMESTAMP DEFAULT NOW(),
    overridden_by_ops BOOLEAN DEFAULT FALSE
);

-- wargame_sessions
CREATE TABLE wargame_sessions (
    id SERIAL PRIMARY KEY,
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    disturber_events_fired INTEGER DEFAULT 0,
    healer_actions_taken INTEGER DEFAULT 0,
    total_roi_defended_usd FLOAT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'running'  -- "running" | "complete" | "stopped"
);
```

---

## Port Graph Data

Use these exact ports and coordinates throughout the application.
Do not invent port data — use this canonical list.

```python
PORTS = {
    "Mumbai":       {"lat": 18.9220,  "lon": 72.8347,   "country": "India",       "cold_chain": True,  "congestion_baseline": 0.3},
    "Nhava Sheva":  {"lat": 18.9500,  "lon": 72.9500,   "country": "India",       "cold_chain": True,  "congestion_baseline": 0.35},
    "Chennai":      {"lat": 13.0827,  "lon": 80.2707,   "country": "India",       "cold_chain": False, "congestion_baseline": 0.25},
    "Colombo":      {"lat": 6.9271,   "lon": 79.8612,   "country": "Sri Lanka",   "cold_chain": True,  "congestion_baseline": 0.2},
    "Singapore":    {"lat": 1.3521,   "lon": 103.8198,  "country": "Singapore",   "cold_chain": True,  "congestion_baseline": 0.4},
    "Port Klang":   {"lat": 3.0000,   "lon": 101.4000,  "country": "Malaysia",    "cold_chain": True,  "congestion_baseline": 0.3},
    "Jebel Ali":    {"lat": 24.9857,  "lon": 55.0272,   "country": "UAE",         "cold_chain": True,  "congestion_baseline": 0.25},
    "Suez":         {"lat": 29.9668,  "lon": 32.5498,   "country": "Egypt",       "cold_chain": False, "congestion_baseline": 0.5},
    "Rotterdam":    {"lat": 51.9225,  "lon": 4.4792,    "country": "Netherlands", "cold_chain": True,  "congestion_baseline": 0.3},
    "Hamburg":      {"lat": 53.5753,  "lon": 9.9920,    "country": "Germany",     "cold_chain": True,  "congestion_baseline": 0.25},
    "Felixstowe":   {"lat": 51.9614,  "lon": 1.3514,    "country": "UK",          "cold_chain": True,  "congestion_baseline": 0.35},
    "Antwerp":      {"lat": 51.2194,  "lon": 4.4025,    "country": "Belgium",     "cold_chain": True,  "congestion_baseline": 0.3},
    "Shanghai":     {"lat": 31.2304,  "lon": 121.4737,  "country": "China",       "cold_chain": True,  "congestion_baseline": 0.45},
    "Hong Kong":    {"lat": 22.3193,  "lon": 114.1694,  "country": "HK",          "cold_chain": True,  "congestion_baseline": 0.4},
    "Busan":        {"lat": 35.1796,  "lon": 129.0756,  "country": "South Korea", "cold_chain": True,  "congestion_baseline": 0.3},
    "Los Angeles":  {"lat": 33.7291,  "lon": -118.2620, "country": "USA",         "cold_chain": True,  "congestion_baseline": 0.4},
    "Durban":       {"lat": -29.8587, "lon": 31.0218,   "country": "South Africa","cold_chain": False, "congestion_baseline": 0.2},
    "Cape Town":    {"lat": -33.9249, "lon": 18.4241,   "country": "South Africa","cold_chain": False, "congestion_baseline": 0.15},
}
```

---

## Phase 0 — Project Bootstrap
**Goal:** Every service running, no errors, hello world on every layer.
**Time estimate:** 2–3 hours
**Acceptance criterion:** `docker-compose up` brings up all services. `GET /health` returns `{"status":"ok","version":"2.0.0"}`. Frontend loads at `localhost:5173`.

### Steps

**1. Init repo**
```bash
git init precursa && cd precursa
echo ".env" >> .gitignore
echo "*.pyc" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "node_modules/" >> .gitignore
echo "ml/models/*.pkl" >> .gitignore
echo "ml/models/*.pt" >> .gitignore
echo "ml/data/raw/" >> .gitignore
```

**2. Backend scaffold**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn[standard] sqlalchemy asyncpg alembic redis \
            pydantic-settings python-dotenv httpx pytest pytest-asyncio
```

Create `app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: load ML models, start agent tick
    yield
    # shutdown: stop agent

app = FastAPI(title="Precursa v2.0", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
```

**3. Docker Compose**

`infra/docker-compose.yml`:
```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [postgres, redis]
    volumes: ["./backend:/app"]
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    env_file: .env
    volumes: ["./frontend:/app", "/app/node_modules"]
    command: npm run dev -- --host

  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: precursa
      POSTGRES_PASSWORD: precursa
      POSTGRES_DB: precursa
    ports: ["5432:5432"]
    volumes: ["postgres_data:/var/lib/postgresql/data"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

volumes:
  postgres_data:
```

**4. Alembic init**
```bash
cd backend && alembic init alembic
# Edit alembic.ini: sqlalchemy.url = env var
# Edit alembic/env.py: import models and use async engine
```

**5. Frontend scaffold**
```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install axios leaflet @types/leaflet react-leaflet recharts
```

**6. GitHub Actions CI** — `.github/workflows/ci.yml`:
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.11"}
      - run: cd backend && pip install -r requirements.txt && pytest
      - uses: actions/setup-node@v4
        with: {node-version: "20"}
      - run: cd frontend && npm ci && npm test
```

---

## Phase 1 — LangGraph Autonomous Agent (Core)
**Goal:** The autonomous agent loop runs every 2 minutes without any human input.
**Time estimate:** 6–8 hours
**Acceptance criterion:** Agent fires on a 2-minute tick. For every shipment with DRI > 75, it logs an `agent_actions` row with `action_type="reroute"`. No button click required. Ops can pause a shipment via `POST /api/agent/override/{id}`.

### Agent State Schema

```python
# backend/app/services/agent_service.py
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    shipment_id: str
    dri_score: int
    dri_level: str
    shap_factors: list[dict]          # [{feature, value, direction}]
    disruption_type: Optional[str]
    candidate_routes: list[dict]      # from graph engine
    lp_valid_routes: list[dict]       # from LP solver (hard constraints applied)
    selected_route: Optional[dict]
    action_taken: str                 # "reroute" | "monitor" | "escalate"
    roi_defended_usd: float
    copilot_explanation: Optional[str]
    ops_override_active: bool
```

### Agent Nodes

Implement each as a pure function returning updated `AgentState`:

```python
def assess_risk(state: AgentState) -> AgentState:
    """Read DRI from Redis. Set action_taken based on threshold."""
    # DRI > 75 → "reroute"
    # DRI 61–75 → "monitor" (pre-compute routes but don't execute)
    # DRI < 61 → "pass" (no action)

def compute_candidate_routes(state: AgentState) -> AgentState:
    """Call graph_engine.get_paths(origin, destination). Returns top 5 paths."""

def apply_lp_constraints(state: AgentState) -> AgentState:
    """Call lp_solver.select(paths, shipment_constraints). Returns 3 valid routes."""
    # Hard constraints: temp_requirement, sanctioned_ports, sla_deadline
    # If no valid route exists → set action_taken = "escalate"

def select_route(state: AgentState) -> AgentState:
    """Pick best route from lp_valid_routes. Apply cargo-type preference weights."""
    # Pharma: minimise ETA delta (w=0.6)
    # E-commerce: minimise cost (w=0.6)
    # Default: balanced (cost 0.4, eta 0.35, risk 0.15, carbon 0.1)

def execute_reroute(state: AgentState) -> AgentState:
    """Write selected_route to PostgreSQL. Update shipment status. Push via WebSocket."""

def notify_stakeholders(state: AgentState) -> AgentState:
    """Log to agent_actions table. Send webhook to logistics partner endpoint."""

def get_copilot_explanation(state: AgentState) -> AgentState:
    """Call copilot_service.explain(state). Returns grounded explanation."""

def log_action(state: AgentState) -> AgentState:
    """Write full AgentState snapshot to agent_actions table."""
```

### Graph Definition

```python
workflow = StateGraph(AgentState)

workflow.add_node("assess_risk",           assess_risk)
workflow.add_node("compute_routes",        compute_candidate_routes)
workflow.add_node("apply_lp",              apply_lp_constraints)
workflow.add_node("select_route",          select_route)
workflow.add_node("execute_reroute",       execute_reroute)
workflow.add_node("notify",                notify_stakeholders)
workflow.add_node("explain",               get_copilot_explanation)
workflow.add_node("log",                   log_action)

workflow.set_entry_point("assess_risk")

def route_after_assess(state: AgentState) -> str:
    if state["ops_override_active"]:   return END
    if state["action_taken"] == "reroute": return "compute_routes"
    return END

workflow.add_conditional_edges("assess_risk", route_after_assess)
workflow.add_edge("compute_routes", "apply_lp")

def route_after_lp(state: AgentState) -> str:
    if state["action_taken"] == "escalate": return "notify"
    return "select_route"

workflow.add_conditional_edges("apply_lp", route_after_lp)
workflow.add_edge("select_route",    "execute_reroute")
workflow.add_edge("execute_reroute", "notify")
workflow.add_edge("notify",          "explain")
workflow.add_edge("explain",         "log")
workflow.add_edge("log",             END)

agent = workflow.compile()
```

### Agent Tick Runner

```python
# Called from FastAPI lifespan startup event
import asyncio

async def run_agent_tick():
    """Run once per AGENT_TICK_SECONDS. Process all high-DRI shipments."""
    while True:
        shipments = await get_all_shipments_from_redis()
        for shipment in shipments:
            if shipment["dri_score"] >= 61:
                initial_state = AgentState(
                    shipment_id=shipment["id"],
                    dri_score=shipment["dri_score"],
                    # ... populate from shipment record
                )
                await asyncio.to_thread(agent.invoke, initial_state)
        await asyncio.sleep(settings.AGENT_TICK_SECONDS)
```

### API Endpoints (Phase 1)

```
GET  /api/agent/status              → running | paused, last tick time, actions taken today
POST /api/agent/override/{ship_id}  → pause agent for this shipment (ops override)
DELETE /api/agent/override/{id}     → re-enable agent for this shipment
GET  /api/agent/log                 → last 50 agent_actions rows
```

---

## Phase 2 — Data Models and Mock Feed
**Goal:** Realistic shipment data flowing through the system. Agent has something to act on.
**Time estimate:** 4–5 hours
**Acceptance criterion:** `GET /api/shipments` returns 5 shipments with coordinates. WebSocket broadcasts updates every 30 seconds. Agent tick at least processes the shipment list without errors.

### Seed Shipments

```python
SEED_SHIPMENTS = [
    {
        "id": "SHP-001",
        "origin_port": "Mumbai",
        "destination_port": "Rotterdam",
        "cargo_type": "Electronics",
        "carrier": "Maersk",
        "weight_kg": 18000,
        "temp_requirement_celsius": None,
        "route": ["Mumbai", "Colombo", "Jebel Ali", "Suez", "Rotterdam"],
    },
    {
        "id": "SHP-002",
        "origin_port": "Shanghai",
        "destination_port": "Los Angeles",
        "cargo_type": "FMCG",
        "carrier": "COSCO",
        "weight_kg": 24000,
        "temp_requirement_celsius": None,
        "route": ["Shanghai", "Hong Kong", "Los Angeles"],
    },
    {
        "id": "SHP-003",
        "origin_port": "Chennai",
        "destination_port": "Hamburg",
        "cargo_type": "Pharma",
        "carrier": "MSC",
        "weight_kg": 8000,
        "temp_requirement_celsius": 4.0,  # Cold chain required
        "route": ["Chennai", "Colombo", "Jebel Ali", "Suez", "Hamburg"],
    },
    {
        "id": "SHP-004",
        "origin_port": "Nhava Sheva",
        "destination_port": "Felixstowe",
        "cargo_type": "Automotive",
        "carrier": "Hapag-Lloyd",
        "weight_kg": 32000,
        "temp_requirement_celsius": None,
        "route": ["Nhava Sheva", "Jebel Ali", "Suez", "Rotterdam", "Felixstowe"],
    },
    {
        "id": "SHP-005",
        "origin_port": "Hong Kong",
        "destination_port": "Antwerp",
        "cargo_type": "Electronics",
        "carrier": "Evergreen",
        "weight_kg": 15000,
        "temp_requirement_celsius": None,
        "route": ["Hong Kong", "Singapore", "Colombo", "Jebel Ali", "Suez", "Antwerp"],
    },
]
```

### WebSocket Live Feed

```python
# backend/app/websocket/broadcaster.py
from fastapi import WebSocket
from typing import set

class ConnectionManager:
    def __init__(self):
        self.active: set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast(self, data: dict):
        dead = set()
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                dead.add(ws)
        self.active -= dead

manager = ConnectionManager()
```

Message types broadcast over WebSocket:
- `{"type": "shipment_update", "shipments": [...]}` — every 30 seconds
- `{"type": "dri_spike", "shipment_id": "SHP-004", "dri": 87}` — immediate on spike
- `{"type": "agent_action", "action": {...}}` — immediate on every agent decision
- `{"type": "wargame_tick", "state": {...}}` — every 10 seconds during war game

---

## Phase 3 — ML Ensemble + SHAP Explainability
**Goal:** Real ML models replace rule-based scoring. Every DRI has SHAP values.
**Time estimate:** 8–10 hours
**Acceptance criterion:** XGBoost accuracy > 0.78 on test set. Every call to `score_shipment()` returns `{"dri": int, "shap_factors": [{feature, value, direction}]}`. SHAP top factor visible in frontend ShapPanel.

### Training Data

Download: **SCMS Delivery History Dataset** (public domain, USAID Supply Chain)
- URL: `https://data.usaid.gov/Global-Health-Supply-Chain/SCMS-Delivery-History/46j6-k9mf`
- Place CSV at `ml/data/raw/scms_delivery.csv`

Feature engineering in `ml/data_prep.py`:
```python
FEATURES = [
    "route_distance_km",          # calculated from port coordinates
    "weight_kg_normalised",       # weight / max_weight in dataset
    "carrier_reliability_score",  # historical on-time rate per carrier
    "port_congestion_index",      # synthetic: baseline + random noise for training
    "weather_severity_score",     # 0.0–1.0 synthetic feature
    "days_since_departure",       # integer
    "customs_flag",               # binary: 1 if customs issue in last 30 days
]

TARGET = "disruption_occurred"    # binary: 1 if delay > 2 days
```

### XGBoost Training

```python
# ml/train_xgboost.py
import xgboost as xgb
import mlflow
import shap
from sklearn.metrics import accuracy_score, roc_auc_score

def train():
    with mlflow.start_run(run_name="xgboost_dri_v2"):
        model = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric="logloss",
        )
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], early_stopping_rounds=20)

        # Log metrics
        acc = accuracy_score(y_test, model.predict(X_test))
        auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
        mlflow.log_metrics({"accuracy": acc, "auc": auc})
        mlflow.log_params(model.get_params())

        # Validate SHAP works on this model
        explainer = shap.TreeExplainer(model)
        sample_shap = explainer.shap_values(X_test[:5])
        assert sample_shap is not None, "SHAP explainer must work on trained model"

        mlflow.xgboost.log_model(model, "xgboost_model")
        model.save_model("ml/models/xgboost_dri.json")
        print(f"Accuracy: {acc:.4f}  AUC: {auc:.4f}")
        assert acc >= 0.78, f"Accuracy {acc:.4f} below required 0.78"
```

### SHAP Explainer

```python
# ml/shap_explainer.py
import shap
import xgboost as xgb
import numpy as np

class DRIExplainer:
    def __init__(self, model_path: str):
        self.model = xgb.XGBClassifier()
        self.model.load_model(model_path)
        self.explainer = shap.TreeExplainer(self.model)
        self.feature_names = [
            "route_distance_km", "weight_kg_normalised", "carrier_reliability_score",
            "port_congestion_index", "weather_severity_score", "days_since_departure", "customs_flag"
        ]

    def explain(self, features: np.ndarray) -> list[dict]:
        """Returns top 5 SHAP factors sorted by absolute value."""
        shap_values = self.explainer.shap_values(features.reshape(1, -1))[0]
        factors = []
        for i, (name, val) in enumerate(zip(self.feature_names, shap_values)):
            factors.append({
                "feature": name,
                "value": round(float(val * 100), 1),   # scale to readable range
                "direction": "increases_risk" if val > 0 else "reduces_risk",
                "feature_value": round(float(features[i]), 3),
            })
        return sorted(factors, key=lambda x: abs(x["value"]), reverse=True)[:5]
```

### Ensemble Fusion

```python
# ml/ensemble.py
def compute_dri(
    xgb_prob: float,
    lstm_prob: float,
    iso_score: float,
    w_xgb: float = 0.40,
    w_lstm: float = 0.40,
    w_iso: float = 0.20,
) -> int:
    """Fuse three model outputs into a single DRI integer 0–100."""
    fused = (w_xgb * xgb_prob) + (w_lstm * lstm_prob) + (w_iso * iso_score)
    return min(100, max(0, int(round(fused * 100))))
```

### Integration in `dri_scorer.py`

- Load all models at FastAPI startup (lifespan event)
- `score_shipment(shipment_id) -> {"dri": int, "shap_factors": list[dict]}`
- Write result to Redis with key `dri:{shipment_id}` (TTL 150 seconds)
- Write SHAP factors to Redis with key `shap:{shipment_id}` (TTL 150 seconds)
- Also persist to `shipments.dri_score` and `shipments.shap_factors` in PostgreSQL

---

## Phase 4 — LP Constraint Solver
**Goal:** PuLP selects routes that satisfy hard cargo constraints. Dijkstra cannot do this.
**Time estimate:** 5–6 hours
**Acceptance criterion:** A pharma shipment (temp_requirement=4.0) never selects a route with a non-cold-chain port. Test: `test_lp_solver.py::test_pharma_cold_chain_enforced` must pass.

### Hard Constraints (Must Never Be Violated)

```python
HARD_CONSTRAINTS = {
    "cold_chain": {
        "applies_when": lambda s: s.temp_requirement_celsius is not None,
        "rule": "all ports in route must have cold_chain == True",
        "violation_action": "eliminate_route",
    },
    "sanctioned_ports": {
        "applies_when": lambda s: True,
        "rule": "route must not contain ports in SANCTIONED_PORTS list",
        "violation_action": "eliminate_route",
    },
    "weight_limit": {
        "applies_when": lambda s: True,
        "rule": "all route legs must support shipment.weight_kg",
        "violation_action": "eliminate_route",
    },
    "sla_deadline": {
        "applies_when": lambda s: s.eta is not None,
        "rule": "route.eta_hours must not exceed hours until sla_deadline",
        "violation_action": "eliminate_route",
    },
}
```

### PuLP Solver Implementation

```python
# backend/app/services/lp_solver.py
import pulp

def select_optimal_route(
    candidate_routes: list[dict],
    shipment: dict,
    weights: dict = None,
) -> list[dict]:
    """
    Apply hard constraints to eliminate invalid routes.
    Use LP to rank remaining routes by weighted objective.
    Returns top 3 valid routes sorted by LP score.
    """
    if weights is None:
        weights = cargo_type_weights(shipment["cargo_type"])
        # Pharma:     {"cost": 0.1, "eta": 0.6, "risk": 0.2, "carbon": 0.1}
        # E-commerce: {"cost": 0.6, "eta": 0.3, "risk": 0.05, "carbon": 0.05}
        # Default:    {"cost": 0.4, "eta": 0.35, "risk": 0.15, "carbon": 0.10}

    # Step 1: eliminate routes violating any hard constraint
    valid_routes = []
    for route in candidate_routes:
        if passes_all_hard_constraints(route, shipment):
            valid_routes.append(route)

    if not valid_routes:
        return []   # triggers "escalate" action in agent

    # Step 2: normalise metrics across valid routes
    # Step 3: solve LP minimisation problem
    prob = pulp.LpProblem("route_selection", pulp.LpMinimize)
    route_vars = [pulp.LpVariable(f"r{i}", 0, 1, cat="Binary") for i in range(len(valid_routes))]

    # Objective: minimise weighted cost
    prob += pulp.lpSum([
        route_vars[i] * (
            weights["cost"]   * valid_routes[i]["cost_normalised"] +
            weights["eta"]    * valid_routes[i]["eta_normalised"] +
            weights["risk"]   * valid_routes[i]["risk_normalised"] +
            weights["carbon"] * valid_routes[i]["carbon_normalised"]
        )
        for i in range(len(valid_routes))
    ])

    # Constraint: select exactly one route (or rank all)
    # For ranking: score each route individually and sort
    for i, route in enumerate(valid_routes):
        route["lp_score"] = (
            weights["cost"]   * route["cost_normalised"] +
            weights["eta"]    * route["eta_normalised"] +
            weights["risk"]   * route["risk_normalised"] +
            weights["carbon"] * route["carbon_normalised"]
        )
        route["constraints_applied"] = get_applied_constraints(route, shipment)

    return sorted(valid_routes, key=lambda r: r["lp_score"])[:3]
```

---

## Phase 5 — Grounded Copilot
**Goal:** Claude API explains every agent decision. Cannot invent reasons not in the data.
**Time estimate:** 3–4 hours
**Acceptance criterion:** `test_copilot.py::test_copilot_cannot_reference_carbon_if_not_in_shap` passes. Copilot auto-fires after every Red alert reroute.

### Grounding Rule

The copilot system prompt must enforce this rule:
> You are explaining a rerouting decision made by an algorithm. You may only reference
> factors that appear in the SHAP values or LP constraint log provided. If carbon was not
> a top SHAP factor, you cannot say "rerouted for carbon reduction." If cost was not a
> constraint, you cannot say "cost was the primary concern." Explain only what the data shows.

### Prompt Template

```python
# backend/app/services/copilot_service.py

SYSTEM_PROMPT = """
You are Precursa's AI copilot for supply chain operations.
You explain rerouting decisions made by an autonomous algorithm.
STRICT RULE: Only reference factors explicitly listed in the SHAP values or LP constraints
provided. Never infer, assume, or add context not present in the data.
Keep explanations to 2-3 sentences. Be specific and factual.
"""

def build_explanation_prompt(state: AgentState) -> str:
    shap_text = "\n".join([
        f"  - {f['feature']}: {f['value']:+.1f} ({f['direction']})"
        for f in state["shap_factors"][:3]
    ])
    constraints_text = ", ".join(state["selected_route"].get("constraints_applied", ["none"]))

    return f"""
Shipment: {state['shipment_id']}
DRI score at rerouting: {state['dri_score']}/100

Top SHAP factors (algorithm computed):
{shap_text}

LP hard constraints enforced: {constraints_text}

Route selected: {" -> ".join(state['selected_route']['path'])}
Cost delta: ${state['selected_route']['cost_delta_usd']:+,.0f}
ETA delta: {state['selected_route']['eta_delta_hours']:+.1f} hours
Carbon delta: {state['selected_route']['carbon_delta_kg']:+.0f} kg

Explain this rerouting decision in 2-3 sentences.
Reference only the SHAP factors and constraints listed above.
"""
```

### API Endpoint

```
POST /api/copilot
body: {
    "shipment_id": "SHP-004",
    "question": "Why was Colombo chosen over Jebel Ali?"
}
response: {
    "answer": str,
    "grounded_on": ["port_congestion_index", "carrier_reliability_score"],
    "shap_factors_used": [...]
}
```

---

## Phase 6 — Interactive Dashboard and Map
**Goal:** Full frontend operational. All 8 demo steps executable in the browser.
**Time estimate:** 6–8 hours
**Acceptance criterion:** The complete hackathon demo scenario (Section: Demo Scenarios) runs end-to-end without any console errors.

### Components to Build

**Map.tsx**
- Leaflet map, center (20, 60), zoom 3, OpenStreetMap tiles
- Circle markers per shipment, color = DRI level
  - green `#22c55e`, yellow `#eab308`, orange `#f97316`, red `#ef4444`
- Polyline per shipment showing current route
- On agent reroute: animate route transition (remove old polyline, add new)
- Click marker → opens popup with id, cargo_type, DRI badge, carrier

**ShapPanel.tsx**
- Horizontal bar chart (Recharts BarChart)
- X-axis: SHAP contribution value (positive = increases risk)
- One bar per top-5 SHAP factor
- Color: red bars for positive SHAP, green for negative
- Visible after any orange/red alert

**WarGame.tsx**
- Left panel: Disturber — event log with timestamp and severity
- Right panel: Healer — agent response log
- Center: score counter — "ROI Defended: $X across Y events"
- Start/Stop buttons
- Updates via WebSocket `wargame_tick` messages

**BacktestTimeline.tsx**
- Horizontal timeline from T-30min to T+4hrs
- DRI line chart showing rise from ~18 to 91
- Vertical markers: "Precursa flagged (T-18min)", "Grounding (T=0)", "Industry response (T+4hrs)"
- Play/Pause replay button

**AgentLog.tsx**
- Live feed of last 20 agent_actions from WebSocket
- Each row: timestamp, shipment_id, action_type, DRI at action, top SHAP factor
- Auto-scrolls to latest

---

## Phase 7 — Ever Given Backtesting
**Goal:** Historical proof that Precursa would have flagged the 2021 Suez blockage before it happened.
**Time estimate:** 4–5 hours
**Acceptance criterion:** Replay shows DRI crossing 75 at least 10 minutes before the official grounding timestamp (2021-03-23 07:40 UTC). Backtesting result stored in PostgreSQL.

### Data Source

AIS telemetry for MV Ever Given, March 23 2021:
- Source: AISHub historical export or MarineTraffic API (free tier, historical data)
- Format: CSV with columns `mmsi, timestamp, lat, lon, sog (speed over ground), cog (course over ground), heading`
- Place at: `ml/data/ais_ever_given/ever_given_march_2021.csv`
- Key window: 07:00–07:45 UTC on 2021-03-23

### Backtesting Pipeline

```python
# backend/app/services/backtesting.py

async def run_ever_given_backtest() -> dict:
    """
    Replay the 22-minute pre-grounding window at 10x speed.
    Feed each AIS record into Isolation Forest + LSTM.
    Record exact timestamp when DRI crosses 75.
    """
    records = load_ais_csv("ml/data/ais_ever_given/ever_given_march_2021.csv")
    grounding_time = datetime(2021, 3, 23, 7, 40, 0)  # UTC

    dri_timeline = []
    flag_time = None

    for record in records:
        features = extract_features_from_ais(record)
        dri_result = dri_scorer.score_shipment_from_features(features)
        dri_timeline.append({
            "timestamp": record["timestamp"].isoformat(),
            "dri": dri_result["dri"],
            "shap_factors": dri_result["shap_factors"],
            "sog": record["sog"],
            "heading": record["heading"],
        })
        if dri_result["dri"] >= 75 and flag_time is None:
            flag_time = record["timestamp"]

    delta_minutes = (grounding_time - flag_time).total_seconds() / 60 if flag_time else None

    result = {
        "flag_time": flag_time.isoformat() if flag_time else None,
        "grounding_time": grounding_time.isoformat(),
        "industry_response_time": (grounding_time + timedelta(hours=4)).isoformat(),
        "precursa_lead_minutes": delta_minutes,
        "timeline": dri_timeline,
    }

    # Store in PostgreSQL for dashboard retrieval
    await save_backtest_result(result)
    return result
```

### If AIS Data Is Unavailable

Generate a statistically accurate synthetic replay:
```python
def generate_synthetic_ever_given_replay():
    """
    Create a 30-minute window with:
    - Normal SOG of 13.5 knots until T-22min
    - SOG drops: 13.5 → 10 → 6 → 2 → 0 over 22 minutes
    - Heading oscillates ±15 degrees (vessel correcting)
    - Congestion index for Suez rises from 0.3 to 0.85
    These parameters match the publicly documented Ever Given event.
    """
```

---

## Phase 8 — Multi-Agent War Game
**Goal:** Monte Carlo Disturber vs LangGraph Healer. Live adversarial demo.
**Time estimate:** 5–6 hours
**Acceptance criterion:** 10-minute war game runs without crashes. At least 8 Disturber events fired. Healer responds to each within 30 seconds. ROI defended counter updates in real time.

### Disturber Agent

```python
# backend/app/services/wargame.py

import numpy as np
from dataclasses import dataclass

DISRUPTION_FREQUENCIES = {
    "port_congestion":  0.40,   # 40% of events
    "weather_event":    0.30,   # 30%
    "carrier_failure":  0.15,   # 15%
    "customs_delay":    0.10,   # 10%
    "geopolitical":     0.05,   # 5%
}

DISRUPTION_COSTS = {
    "port_congestion":  45000,  # avg USD per event
    "weather_event":    62000,
    "carrier_failure":  38000,
    "customs_delay":    28000,
    "geopolitical":     95000,
}

@dataclass
class DisturbanceEvent:
    event_type: str
    affected_port: str
    severity: float          # 0.0 to 1.0
    affected_shipment_ids: list[str]
    potential_loss_usd: float
    timestamp: str

class MonteCarloDisturber:
    def __init__(self, intensity: float = 0.7):
        self.intensity = intensity

    def generate_event(self, active_shipments: list[dict]) -> DisturbanceEvent:
        """Sample event type from frequency distribution. Pick affected shipment(s)."""
        event_type = np.random.choice(
            list(DISRUPTION_FREQUENCIES.keys()),
            p=list(DISRUPTION_FREQUENCIES.values())
        )
        severity = np.random.beta(2, 2) * self.intensity  # beta dist peaks at 0.5
        affected_port = pick_affected_port(event_type, active_shipments)
        affected_ships = [s["id"] for s in active_shipments if affected_port in s["route"]]
        potential_loss = DISRUPTION_COSTS[event_type] * severity * len(affected_ships)

        return DisturbanceEvent(
            event_type=event_type,
            affected_port=affected_port,
            severity=round(severity, 2),
            affected_shipment_ids=affected_ships,
            potential_loss_usd=round(potential_loss),
            timestamp=datetime.utcnow().isoformat(),
        )
```

### War Game Runner

```python
async def run_wargame(session_id: int, duration_seconds: int = 600):
    """Run Disturber vs Healer for duration_seconds. Log all events."""
    disturber = MonteCarloDisturber(intensity=settings.WARGAME_DISTURBER_INTENSITY)
    tick = 0

    while tick * settings.WARGAME_TICK_SECONDS < duration_seconds:
        # Disturber fires event
        event = disturber.generate_event(await get_active_shipments())
        await apply_disruption_to_shipments(event)
        await log_wargame_event(session_id, event, actor="disturber")
        await broadcast_wargame_tick(event, actor="disturber")

        # Healer agent responds (runs immediately, not on 2-min tick)
        for shipment_id in event.affected_shipment_ids:
            healer_result = await run_agent_for_shipment(shipment_id)
            roi_defended = calculate_roi_defended(event, healer_result)
            await update_session_roi(session_id, roi_defended)
            await log_wargame_event(session_id, healer_result, actor="healer")
            await broadcast_wargame_tick(healer_result, actor="healer")

        await asyncio.sleep(settings.WARGAME_TICK_SECONDS)
        tick += 1

    await finalize_wargame_session(session_id)
```

### API Endpoints

```
POST /api/wargame/start               → creates session, returns session_id
GET  /api/wargame/status/{session_id} → current scores, event count, ROI defended
POST /api/wargame/stop/{session_id}   → stop early
GET  /api/wargame/history/{id}        → full event log for a session
```

---

## Phase 9 — Kafka + Flink Production Streaming
**Goal:** Replace mock data generator with real streaming infrastructure.
**Time estimate:** 10–12 hours
**Acceptance criterion:** Live weather data from OpenWeatherMap API flows through Kafka topic `weather-events`. Flink job consumes it and updates shipment DRI in real time. Mock mode still works when `KAFKA_BOOTSTRAP_SERVERS` is empty.

### Kafka Topics

| Topic | Producer | Consumer | Message Schema |
|---|---|---|---|
| `weather-events` | Weather API poller (5-min interval) | Flink job | `{port, temperature, wind_speed, storm_flag, timestamp}` |
| `port-congestion` | Port feed scraper | Flink job | `{port, congestion_index, vessels_waiting, timestamp}` |
| `shipment-positions` | AIS API poller | Flink job | `{mmsi, lat, lon, sog, heading, timestamp}` |
| `dri-updates` | Flink job | DRI scorer service | `{shipment_id, features: {...}, timestamp}` |

### Flink Job

```python
# backend/flink/dri_pipeline.py (PyFlink)
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer

env = StreamExecutionEnvironment.get_execution_environment()
env.set_parallelism(2)

# 5-minute tumbling window: aggregate weather + port + position per shipment
# Output: enriched feature vector to dri-updates topic
```

### Mock Mode Fallback

```python
# In data_generator.py
async def run_mock_feed():
    """Fallback when KAFKA_BOOTSTRAP_SERVERS is not set."""
    while True:
        for shipment in SEED_SHIPMENTS:
            features = generate_mock_features(shipment)
            await dri_scorer.score_and_update(shipment["id"], features)
        await asyncio.sleep(30)
```

---

## Phase 10 — Authentication and Security
**Goal:** Secure all API endpoints. Ops manager login required.
**Time estimate:** 4–5 hours
**Acceptance criterion:** All `/api/*` endpoints return 401 without valid JWT. Login flow works in frontend. JWT stored in httpOnly cookie only (never localStorage).

### Implementation

```python
# JWT auth with python-jose
pip install python-jose[cryptography] passlib[bcrypt]

# Endpoints:
POST /auth/login      → email + password → sets httpOnly cookie with JWT
POST /auth/logout     → clears cookie
GET  /auth/me         → returns current user from JWT

# Protect all routes:
from fastapi import Depends
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User: ...

# Apply to all routers:
router = APIRouter(dependencies=[Depends(get_current_user)])
```

**Frontend:**
- Axios interceptor adds credentials to every request
- 401 response → redirect to `/login`
- Never store token in localStorage or sessionStorage

---

## Phase 11 — Production Hardening
**Goal:** Observable, deployable, resilient.
**Time estimate:** 10–14 hours
**Acceptance criterion:** App deploys to AWS EKS. Grafana dashboard shows DRI latency and agent action rate. Sentry captures backend errors. All Terraform plan applies without errors.

### Observability

```python
# Prometheus metrics — expose at /metrics
from prometheus_client import Counter, Histogram, generate_latest

dri_computation_seconds = Histogram("dri_computation_seconds", "Time to compute DRI")
agent_actions_total = Counter("agent_actions_total", "Total agent actions", ["action_type"])
wargame_roi_defended = Counter("wargame_roi_defended_usd", "Total ROI defended in war games")
websocket_connections = Gauge("websocket_connections_active", "Active WebSocket connections")
```

Key Grafana panels:
- DRI computation latency (p50, p95, p99)
- Agent actions per hour (by type: reroute / monitor / escalate)
- WebSocket active connections
- War game ROI defended (cumulative)
- PostgreSQL query latency
- Redis hit rate for DRI cache

### Kubernetes Manifests

`infra/k8s/backend-deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: precursa-backend
spec:
  replicas: 2
  selector:
    matchLabels: {app: precursa-backend}
  template:
    spec:
      containers:
        - name: backend
          image: <ECR_REPO>/precursa-backend:latest
          resources:
            requests: {cpu: "250m", memory: "512Mi"}
            limits:   {cpu: "1000m", memory: "2Gi"}
          livenessProbe:
            httpGet: {path: /health, port: 8000}
            initialDelaySeconds: 30
          readinessProbe:
            httpGet: {path: /health, port: 8000}
            initialDelaySeconds: 10
          envFrom:
            - secretRef: {name: precursa-secrets}
```

### Terraform (AWS)

```hcl
# infra/terraform/main.tf
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"
  cluster_name    = "precursa-prod"
  cluster_version = "1.29"
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets
}

resource "aws_db_instance" "postgres" {
  identifier        = "precursa-db"
  engine            = "postgres"
  engine_version    = "15"
  instance_class    = "db.t3.medium"
  allocated_storage = 50
  storage_encrypted = true
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id      = "precursa-cache"
  engine          = "redis"
  node_type       = "cache.t3.micro"
  num_cache_nodes = 1
}
```

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
on:
  push:
    branches: [main]
jobs:
  deploy:
    steps:
      - run: cd backend && pytest          # must pass
      - run: cd frontend && npm test       # must pass
      - run: docker build -t backend .
      - run: docker push $ECR_REPO/precursa-backend:$SHA
      - run: helm upgrade precursa ./infra/helm --set image.tag=$SHA
```

---

## Demo Scenarios

The app must execute all three acts flawlessly before the presentation.

### Act 1 — Live Autonomous Reroute (2 minutes)

| Step | What to show | Talking point |
|---|---|---|
| 1 | Dashboard with 5 shipments, all green/yellow | "Live feed. Agent running autonomously." |
| 2 | Trigger port congestion on SHP-004 | "Injecting a Singapore congestion event." |
| 3 | Wait 8 seconds — agent fires without any click | "Nobody clicked anything. The agent decided." |
| 4 | Show SHAP panel: top 3 factors with values | "We know exactly why. Not a black box." |
| 5 | Show LP constraint log: 2 routes eliminated | "Dijkstra can't do this. PuLP enforced pharma temp." |
| 6 | Ask Copilot: "Why Colombo over Jebel Ali?" | "Grounded answer, citing only SHAP data." |

### Act 2 — Ever Given Replay (1 minute)

| Step | What to show | Talking point |
|---|---|---|
| 1 | Switch to Backtest tab | "March 23, 2021. The Ever Given." |
| 2 | Hit Play on the AIS replay | "Watch the DRI rise during the 22-minute window." |
| 3 | DRI crosses 75 at T-18min marker | "Precursa flagged it 18 minutes before the grounding." |
| 4 | Show the gap to "Industry response" marker | "Industry took 4 hours. We took 18 minutes." |

### Act 3 — War Game (1 minute)

| Step | What to show | Talking point |
|---|---|---|
| 1 | Switch to War Game tab, hit Start | "Disturber fires chaos. Healer defends." |
| 2 | Watch events fire and agent respond in real time | "Port congestion. Carrier failure. Weather." |
| 3 | ROI Defended counter ticking up | "$1.2M defended across 8 events in 60 seconds." |
| 4 | Final score | "This is not a dashboard. It's a system that fights." |

**Rehearse all three acts minimum 5 times before the presentation.**

---

## Testing Strategy

| Test type | Tool | Target | Gate |
|---|---|---|---|
| Unit tests | pytest | All service functions | Required before Phase N+1 |
| API tests | pytest + httpx | All endpoints | Required before Phase N+1 |
| ML model tests | pytest | DRI accuracy, SHAP output | Accuracy >= 0.78 |
| LP constraint tests | pytest | Hard constraint enforcement | pharma cold-chain test must pass |
| Agent tests | pytest | Decision logic, audit log | Agent must not act when override active |
| Copilot grounding tests | pytest | LLM cannot hallucinate | Test: carbon not mentioned if not in SHAP |
| Frontend component tests | Vitest + RTL | All components | Required before Phase 6 complete |
| E2E tests | Playwright | Full demo scenario | All 3 acts must run without error |
| Load tests | Locust | 100 concurrent WS connections | < 200ms p95 broadcast latency |

Write tests alongside code. Every new function gets a test in the same PR.

---

## Architectural Rules (Never Break These)

1. **Agent is never optional.** If someone removes the agent tick and the app still "works," the architecture is broken.

2. **SHAP is never skipped.** Every DRI score must produce SHAP values. `score_shipment()` must always return `{"dri": int, "shap_factors": [...]}`. Never return DRI without SHAP.

3. **Copilot never infers.** The copilot system prompt must prevent it from referencing any factor not in the SHAP output or LP constraint log. Test this in CI.

4. **LP replaces final selection, not path generation.** NetworkX generates candidate paths. PuLP selects the valid optimal one. Never use Dijkstra as the final decision.

5. **Mock mode must always work.** If `KAFKA_BOOTSTRAP_SERVERS` is empty, the app falls back to mock data generator silently. The demo must run without any external API keys.

6. **DRI is always int 0–100.** Never float. Never null. If the model fails, return 0 and log the error. The frontend must always have a DRI value to display.

7. **All database queries are async.** Never use synchronous SQLAlchemy in FastAPI async endpoints.

8. **Agent decisions are always logged.** Every `agent_actions` row is the audit trail. Never execute a reroute without writing to this table first.

9. **JWT in httpOnly cookie only.** Never localStorage. Never sessionStorage. Never a response body field the frontend stores manually.

10. **No hardcoded secrets.** All secrets via `.env` + `pydantic-settings`. `.env` is in `.gitignore`. If a secret is found in committed code, rotate it immediately.

---

*Precursa v2.0 — Team Return0 — Smart Supply Chains Track — April 2026*
