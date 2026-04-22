# Precursa — Full Development Roadmap
> **For AI Coding Assistants (Copilot / Cursor / Claude Code):**
> This file is the single source of truth for building Precursa from scratch to production.
> Read this entire file before writing any code. Follow the phases in order.
> Never skip a phase. Each phase produces working, testable software before the next begins.

---

## Project Overview

**Name:** Precursa  
**Tagline:** Self-Healing Supply Chain Intelligence  
**Domain:** AI/ML  
**Core Loop:** Ingest live data → Score disruption risk per shipment (DRI 0–100) → Reroute autonomously → Notify stakeholders  

---

## Tech Stack (Canonical)

| Layer | Technology |
|---|---|
| Backend API | Python 3.11 + FastAPI + WebSockets |
| Stream processing | Apache Kafka (Confluent Cloud) → Apache Flink |
| ML models | PyTorch (LSTM) + XGBoost + scikit-learn (Isolation Forest) |
| ML Ops | MLflow experiment tracking + model registry |
| Graph engine | NetworkX (MVP) → Neo4j (production) |
| AI Copilot | Anthropic Claude API (claude-sonnet-4-20250514) |
| Automation agent | LangGraph |
| Database | PostgreSQL (shipments, events, routes) + Redis (live DRI cache) |
| Frontend | React 18 + TypeScript + Vite + Leaflet.js (MVP) → Mapbox GL JS (production) |
| Infra (production) | Docker + Docker Compose (local) → Kubernetes EKS + Terraform (production) |
| CI/CD | GitHub Actions |

---

## Repository Structure

Set up this folder structure before writing any code:

```
precursa/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── api/
│   │   │   ├── shipments.py         # GET /api/shipments
│   │   │   ├── disruptions.py       # POST /api/trigger-disruption
│   │   │   ├── reroute.py           # POST /api/reroute/{id}
│   │   │   └── copilot.py           # POST /api/copilot
│   │   ├── core/
│   │   │   ├── config.py            # env vars, settings
│   │   │   └── database.py          # PostgreSQL + Redis connections
│   │   ├── models/
│   │   │   ├── shipment.py          # Pydantic + SQLAlchemy models
│   │   │   ├── disruption.py
│   │   │   └── route.py
│   │   ├── services/
│   │   │   ├── dri_scorer.py        # ML ensemble → DRI score
│   │   │   ├── graph_engine.py      # NetworkX rerouting
│   │   │   ├── data_generator.py    # mock data seeder
│   │   │   └── copilot_service.py   # Claude API integration
│   │   └── websocket/
│   │       └── live_feed.py         # WebSocket broadcaster
│   ├── ml/
│   │   ├── train_xgboost.py         # XGBoost training script
│   │   ├── train_lstm.py            # PyTorch LSTM training
│   │   ├── isolation_forest.py      # Anomaly detection
│   │   ├── ensemble.py              # Fuses 3 model scores → DRI
│   │   └── data/
│   │       └── README.md            # Instructions for Kaggle dataset download
│   ├── tests/
│   │   ├── test_dri_scorer.py
│   │   ├── test_graph_engine.py
│   │   └── test_api.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── Map.tsx              # Leaflet shipment map
│   │   │   ├── ShipmentCard.tsx     # DRI badge + shipment info
│   │   │   ├── DisruptionPanel.tsx  # Alert + reroute trigger UI
│   │   │   ├── RouteComparison.tsx  # 3 alternate routes sidebar
│   │   │   └── Copilot.tsx          # Claude chat panel
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts      # Live DRI updates
│   │   │   └── useShipments.ts      # Shipment state
│   │   ├── types/
│   │   │   └── index.ts             # Shared TypeScript types
│   │   └── api/
│   │       └── client.ts            # Axios API client
│   ├── package.json
│   └── Dockerfile
├── infra/
│   ├── docker-compose.yml           # Local full-stack setup
│   ├── docker-compose.dev.yml       # Dev with hot reload
│   └── k8s/                         # Kubernetes manifests (Phase 4)
├── .github/
│   └── workflows/
│       └── ci.yml                   # GitHub Actions CI
├── .env.example                     # All required env vars documented
├── ROADMAP.md                       # This file
└── README.md
```

---

## Environment Variables

Create `.env` in root before starting. Document every variable in `.env.example`:

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

---

## Phase 0 — Project Bootstrap
**Goal:** Working repo, running services, hello world on every layer.  
**Time estimate:** 2–3 hours  
**Done when:** `docker-compose up` brings up all services with no errors.

### Steps

1. **Initialise the repo**
   ```bash
   git init precursa
   cd precursa
   ```

2. **Backend bootstrap**
   ```bash
   cd backend
   python -m venv venv && source venv/bin/activate
   pip install fastapi uvicorn sqlalchemy asyncpg redis pydantic python-dotenv
   pip freeze > requirements.txt
   ```
   - Create `app/main.py` with a single `GET /health` endpoint returning `{"status": "ok"}`
   - Verify: `uvicorn app.main:app --reload` responds at `http://localhost:8000/health`

3. **Database setup**
   - Start PostgreSQL and Redis via `docker-compose.yml`
   - Create `precursa` database
   - Write `app/core/database.py` with SQLAlchemy async engine
   - Run Alembic migration scaffold: `alembic init alembic`

4. **Frontend bootstrap**
   ```bash
   cd frontend
   npm create vite@latest . -- --template react-ts
   npm install axios leaflet @types/leaflet react-leaflet
   ```
   - Verify: `npm run dev` shows Vite default page at `http://localhost:5173`

5. **Docker Compose**
   - Write `docker-compose.yml` with services: `backend`, `frontend`, `postgres`, `redis`
   - All services start with `docker-compose up`

6. **GitHub Actions CI**
   - `.github/workflows/ci.yml`: install deps, run `pytest`, run `npm test` on every push

---

## Phase 1 — Data Models and Mock Data
**Goal:** Realistic shipment data flowing through the system. No ML yet.  
**Time estimate:** 4–6 hours  
**Done when:** `GET /api/shipments` returns 5 live shipments with coordinates and DRI scores. WebSocket pushes updates every 30 seconds.

### Steps

1. **Define core data models** in `app/models/`

   **Shipment model** — required fields:
   ```python
   id: str                    # e.g. "SHP-001"
   origin_port: str           # e.g. "Mumbai"
   destination_port: str      # e.g. "Rotterdam"
   cargo_type: str            # e.g. "Electronics"
   carrier: str               # e.g. "Maersk"
   current_lat: float
   current_lon: float
   dri_score: int             # 0-100
   dri_level: str             # "green" | "yellow" | "orange" | "red"
   status: str                # "on_track" | "at_risk" | "disrupted" | "rerouted"
   eta: datetime
   route: list[dict]          # list of {lat, lon} waypoints
   ```

2. **Seed 5 realistic shipments** in `services/data_generator.py`

   Use these real-world routes:
   - SHP-001: Mumbai → Rotterdam (via Suez Canal)
   - SHP-002: Shanghai → Los Angeles (Trans-Pacific)
   - SHP-003: Chennai → Hamburg (via Colombo)
   - SHP-004: Nhava Sheva → Felixstowe (via Jebel Ali)
   - SHP-005: Hong Kong → Busan → Los Angeles

   Real port coordinates to use:
   ```python
   PORTS = {
       "Mumbai":      (18.9220, 72.8347),
       "Rotterdam":   (51.9225, 4.4792),
       "Shanghai":    (31.2304, 121.4737),
       "Los Angeles": (33.7291, -118.2620),
       "Chennai":     (13.0827, 80.2707),
       "Hamburg":     (53.5753, 9.9920),
       "Colombo":     (6.9271, 79.8612),
       "Nhava Sheva": (18.9500, 72.9500),
       "Felixstowe":  (51.9614, 1.3514),
       "Jebel Ali":   (24.9857, 55.0272),
       "Hong Kong":   (22.3193, 114.1694),
       "Busan":       (35.1796, 129.0756),
       "Singapore":   (1.3521, 103.8198),
       "Antwerp":     (51.2194, 4.4025),
       "Durban":      (-29.8587, 31.0218),
   }
   ```

3. **Implement DRI business rules** (before ML is ready, use rule-based scoring):
   ```
   DRI 0–30   → green   → status: on_track
   DRI 31–60  → yellow  → status: at_risk
   DRI 61–80  → orange  → status: at_risk
   DRI 81–100 → red     → status: disrupted
   ```

4. **Build REST endpoints**
   - `GET /api/shipments` → list all shipments
   - `GET /api/shipments/{id}` → single shipment detail
   - Store in Redis with 60-second TTL for fast reads

5. **WebSocket live feed** in `websocket/live_feed.py`
   - Every 30 seconds, randomly nudge each shipment's DRI by ±3 points
   - Broadcast updated shipment list to all connected clients
   - Endpoint: `ws://localhost:8000/ws/live`

6. **Frontend: basic shipment list**
   - `useWebSocket.ts` connects to `/ws/live`, updates state on message
   - `ShipmentCard.tsx` renders id, route, DRI badge (color-coded), status
   - Verify cards update in real time without page refresh

---

## Phase 2 — Interactive Map and Disruption Simulation
**Goal:** Visual map with live shipment markers, clickable disruption trigger, route update on screen.  
**Time estimate:** 6–8 hours  
**Done when:** Clicking "Simulate disruption" on SHP-004 causes its marker to turn red and its route to visibly change on the map.

### Steps

1. **Map component** — `components/Map.tsx`
   - Initialise Leaflet map centered at (20, 60) zoom 3
   - Use OpenStreetMap tiles (free, no API key)
   - Render each shipment as a circle marker, color = DRI level
     - green: `#22c55e`, yellow: `#eab308`, orange: `#f97316`, red: `#ef4444`
   - Draw route as a Leaflet polyline using the shipment's `route` waypoints
   - Click a marker → opens popup with shipment details + DRI score

2. **Disruption simulation endpoint**
   ```
   POST /api/trigger-disruption
   body: { shipment_id: "SHP-004", disruption_type: "port_congestion" | "weather" | "customs" }
   ```
   - Sets target shipment DRI to 87
   - Sets status to "disrupted"
   - Logs disruption event to PostgreSQL `disruption_events` table
   - Pushes update to all WebSocket clients immediately

3. **DisruptionPanel component**
   - Dropdown: select shipment
   - Dropdown: select disruption type
   - Button: "Simulate disruption"
   - Calls `POST /api/trigger-disruption`
   - Shows toast notification: `"⚠ Disruption detected on SHP-004. DRI: 87"`

4. **Graph rerouting engine** — `services/graph_engine.py`

   Build a NetworkX directed graph with ports as nodes:
   ```python
   import networkx as nx

   G = nx.DiGraph()
   # Add edges with weight attributes
   G.add_edge("Mumbai", "Colombo",     cost=800,   eta_hours=48,  risk=0.1, carbon=120)
   G.add_edge("Colombo", "Rotterdam",  cost=3200,  eta_hours=240, risk=0.15, carbon=480)
   G.add_edge("Mumbai", "Jebel Ali",   cost=600,   eta_hours=36,  risk=0.2, carbon=90)
   G.add_edge("Jebel Ali", "Rotterdam",cost=2800,  eta_hours=192, risk=0.25, carbon=420)
   # ... add all 15 ports with realistic edges
   ```

   Composite weight function:
   ```python
   def composite_weight(cost, eta_hours, risk, carbon, w_cost=0.4, w_eta=0.35, w_risk=0.15, w_carbon=0.1):
       return (w_cost * cost/5000) + (w_eta * eta_hours/300) + (w_risk * risk) + (w_carbon * carbon/600)
   ```

   Return top 3 paths using `nx.shortest_simple_paths()` ranked by composite weight.

5. **Reroute endpoint**
   ```
   POST /api/reroute/{shipment_id}
   response: { routes: [ {path, cost, eta_hours, risk, carbon, composite_score}, x3 ] }
   ```
   - Updates shipment status to "rerouted"
   - Stores selected route in PostgreSQL
   - Broadcasts new route waypoints via WebSocket

6. **RouteComparison sidebar component**
   - Shows 3 route options as cards
   - Each card: path string, cost delta, ETA delta, risk score, carbon delta
   - "Select this route" button → calls reroute endpoint → map updates

---

## Phase 3 — ML Ensemble and Real DRI Scoring
**Goal:** Replace rule-based DRI with actual trained ML models.  
**Time estimate:** 8–12 hours  
**Done when:** XGBoost, LSTM, and Isolation Forest all produce scores; ensemble fuses them into a real DRI.

### Steps

1. **Get training data**
   - Download from Kaggle: "Supply Chain Shipment Pricing Data" (SCMS dataset, public domain)
   - Place CSV in `ml/data/raw/`
   - Write `ml/data_prep.py` to clean and feature-engineer:
     - Features: route_distance, cargo_weight, carrier_reliability_score, port_congestion_index, weather_severity, days_since_departure, customs_flag
     - Target: `disruption_occurred` (binary) + `disruption_severity` (0–100)

2. **Train XGBoost classifier** — `ml/train_xgboost.py`
   ```python
   import xgboost as xgb
   import mlflow

   with mlflow.start_run():
       model = xgb.XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.05)
       model.fit(X_train, y_train)
       mlflow.log_metric("accuracy", accuracy_score(y_test, model.predict(X_test)))
       mlflow.xgboost.log_model(model, "xgboost_model")
   ```
   - Target metric: accuracy > 0.78 on test set
   - Save model to `ml/models/xgboost_dri.pkl`

3. **Train LSTM** — `ml/train_lstm.py`
   ```python
   import torch
   import torch.nn as nn

   class DRIPredictor(nn.Module):
       def __init__(self, input_size=7, hidden_size=64, num_layers=2):
           super().__init__()
           self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
           self.fc = nn.Linear(hidden_size, 1)

       def forward(self, x):
           out, _ = self.lstm(x)
           return torch.sigmoid(self.fc(out[:, -1, :]))
   ```
   - Input: sequence of last 10 time-steps of shipment features
   - Output: disruption probability (0–1)
   - Save model to `ml/models/lstm_dri.pt`

4. **Isolation Forest** — `ml/isolation_forest.py`
   ```python
   from sklearn.ensemble import IsolationForest

   iso = IsolationForest(contamination=0.1, random_state=42)
   iso.fit(X_train)
   # anomaly_score: -1 (anomaly) or 1 (normal) → convert to 0-100 range
   ```

5. **Ensemble fusion** — `ml/ensemble.py`
   ```python
   def compute_dri(xgb_prob: float, lstm_prob: float, iso_score: float) -> int:
       # Weighted fusion
       fused = (0.4 * xgb_prob) + (0.4 * lstm_prob) + (0.2 * iso_score)
       return min(100, max(0, int(fused * 100)))
   ```

6. **Wire ensemble into backend** — `services/dri_scorer.py`
   - Load all three models at startup (FastAPI lifespan event)
   - `score_shipment(shipment_features) -> int` called every 2 minutes per shipment
   - Cache result in Redis with key `dri:{shipment_id}`
   - Replace the random nudge in the WebSocket loop with real ensemble scores

7. **MLflow experiment tracking**
   - Track every training run: params, metrics, model artifacts
   - `mlflow ui` at `http://localhost:5000` for local model comparison

---

## Phase 4 — Claude API Copilot
**Goal:** Natural language Q&A on every disruption and rerouting decision.  
**Time estimate:** 3–4 hours  
**Done when:** Copilot explains a rerouting decision in plain English and answers follow-up questions.

### Steps

1. **Copilot service** — `services/copilot_service.py`
   ```python
   import anthropic

   client = anthropic.Anthropic()

   def explain_disruption(shipment: dict, disruption: dict, selected_route: dict) -> str:
       prompt = f"""
       You are Precursa's AI copilot for supply chain operations.
       
       Shipment: {shipment['id']} from {shipment['origin_port']} to {shipment['destination_port']}
       Disruption: {disruption['type']} detected. DRI score: {disruption['dri_score']}/100
       Action taken: Rerouted via {' → '.join(selected_route['path'])}
       Cost delta: ${selected_route['cost_delta']}
       ETA delta: +{selected_route['eta_delta_hours']} hours
       Carbon delta: {selected_route['carbon_delta_kg']}kg
       
       Explain this decision in 2-3 sentences in plain English for a logistics operator.
       Be specific about why this route was chosen over alternatives.
       """
       message = client.messages.create(
           model="claude-sonnet-4-20250514",
           max_tokens=300,
           messages=[{"role": "user", "content": prompt}]
       )
       return message.content[0].text
   ```

2. **Copilot endpoint**
   ```
   POST /api/copilot
   body: { shipment_id: str, question: str }
   response: { answer: str }
   ```
   - Loads shipment context + recent disruption events from PostgreSQL
   - Sends structured context + user question to Claude API
   - Streams response back if question is open-ended

3. **Copilot component** — `components/Copilot.tsx`
   - Fixed panel on right side of dashboard
   - Auto-populates with explanation after every disruption
   - Text input for follow-up questions
   - Shows typing indicator while waiting for Claude response
   - Message history scrollable

4. **Auto-trigger on disruption**
   - After every `POST /api/reroute/{id}` completes, automatically call copilot service
   - Push explanation to WebSocket so Copilot panel updates without user action

---

## Phase 5 — LangGraph Autonomous Agent
**Goal:** Replace manual "Simulate disruption" button with a fully autonomous agent loop.  
**Time estimate:** 6–8 hours  
**Done when:** Agent detects high DRI, selects best route, triggers reroute, notifies customer — all without any button click.

### Steps

1. **Install LangGraph**
   ```bash
   pip install langgraph langchain-anthropic
   ```

2. **Define agent state**
   ```python
   from typing import TypedDict, Annotated
   from langgraph.graph import StateGraph

   class AgentState(TypedDict):
       shipment_id: str
       dri_score: int
       disruption_type: str
       candidate_routes: list
       selected_route: dict
       action_taken: str
       notification_sent: bool
   ```

3. **Define agent nodes** (each node = one function):
   - `assess_risk` → reads DRI from Redis, decides if action needed (DRI > 75)
   - `compute_routes` → calls graph engine, gets top 3 routes
   - `select_route` → applies business rules (e.g. pharma cargo = minimize ETA delta)
   - `execute_reroute` → calls reroute endpoint, updates PostgreSQL
   - `notify_stakeholders` → sends webhook to logistics partner + email to customer
   - `explain_decision` → calls Claude API copilot, stores explanation

4. **Build the graph**
   ```python
   workflow = StateGraph(AgentState)
   workflow.add_node("assess_risk", assess_risk)
   workflow.add_node("compute_routes", compute_routes)
   workflow.add_node("select_route", select_route)
   workflow.add_node("execute_reroute", execute_reroute)
   workflow.add_node("notify", notify_stakeholders)
   workflow.add_node("explain", explain_decision)

   workflow.add_conditional_edges("assess_risk", lambda s: "act" if s["dri_score"] > 75 else "monitor")
   workflow.add_edge("compute_routes", "select_route")
   workflow.add_edge("select_route", "execute_reroute")
   workflow.add_edge("execute_reroute", "notify")
   workflow.add_edge("notify", "explain")
   ```

5. **Agent loop**
   - Run agent every 2 minutes as a FastAPI background task
   - One agent invocation per shipment with DRI > 75
   - Log every agent decision to PostgreSQL `agent_actions` table
   - Ops override: `POST /api/agent/override/{shipment_id}` freezes agent for that shipment

---

## Phase 6 — Kafka + Flink (Production Streaming)
**Goal:** Replace mock data generator with real streaming infrastructure.  
**Time estimate:** 8–10 hours  
**Done when:** Live weather and AIS data flows through Kafka → Flink → DRI scorer → WebSocket.

### Steps

1. **Set up Confluent Cloud (free tier)**
   - Create cluster, get API keys, store in `.env`
   - Create topics: `weather-events`, `port-congestion`, `shipment-positions`, `dri-updates`

2. **Kafka producer** — `services/kafka_producer.py`
   - Polls OpenWeatherMap API every 5 minutes for port city weather
   - Polls MarineTraffic API (or mock AIS data) for vessel positions
   - Publishes to relevant Kafka topics

3. **Flink job** — `backend/flink/dri_pipeline.py`
   - Uses PyFlink (Python Flink API)
   - Consumes from all input topics
   - 5-minute tumbling window aggregation per shipment
   - Joins weather + AIS + customs signals
   - Outputs enriched shipment features to `dri-updates` topic

4. **Update DRI scorer** to consume from `dri-updates` topic instead of polling timer

5. **Keep mock mode** — if `KAFKA_BOOTSTRAP_SERVERS` is empty in `.env`, fall back to mock data generator. This preserves local dev experience.

---

## Phase 7 — Production Hardening
**Goal:** Secure, observable, deployable to cloud.  
**Time estimate:** 10–14 hours  
**Done when:** App runs on AWS EKS, passes security checklist, has monitoring dashboard.

### Steps

1. **Authentication**
   - Add JWT auth to all API endpoints using `python-jose`
   - Ops manager login: email + password → JWT token
   - Protect all `/api/*` routes with `Depends(get_current_user)`
   - Frontend: store JWT in httpOnly cookie (not localStorage)

2. **PostgreSQL migrations**
   - Use Alembic for all schema changes
   - Never alter production schema manually
   - Migration files committed to git

3. **Error handling**
   - All FastAPI endpoints wrapped with try/except
   - Structured error responses: `{ error: str, code: int, detail: str }`
   - Sentry integration for backend error tracking

4. **Observability**
   - Prometheus metrics endpoint at `/metrics`
   - Key metrics: DRI computation latency, WebSocket connection count, agent decisions per hour, reroute success rate
   - Grafana dashboard for ops team

5. **Docker production build**
   ```dockerfile
   # backend/Dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

6. **Kubernetes deployment** — `infra/k8s/`
   - `backend-deployment.yaml` — 2 replicas, resource limits
   - `frontend-deployment.yaml`
   - `postgres-statefulset.yaml`
   - `redis-deployment.yaml`
   - `ingress.yaml` — NGINX ingress with TLS

7. **Terraform** — `infra/terraform/`
   - AWS EKS cluster
   - RDS PostgreSQL (managed)
   - ElastiCache Redis (managed)
   - S3 for ML model artifacts
   - CloudFront for frontend static assets

8. **CI/CD pipeline** — `.github/workflows/`
   - On push to `main`: run tests → build Docker images → push to ECR → deploy to EKS
   - On push to `dev`: run tests only
   - Required: all tests pass before merge to main

---

## Testing Strategy

| Type | Tool | Coverage target |
|---|---|---|
| Unit tests | pytest | All service functions |
| API tests | pytest + httpx | All endpoints |
| ML model tests | pytest | DRI accuracy > 0.78 |
| Frontend tests | Vitest + React Testing Library | All components |
| E2E tests | Playwright | Full demo scenario |
| Load tests | Locust | 100 concurrent WebSocket connections |

Write tests alongside code, not after. Every new function gets a test before the next function is written.

---

## Demo Scenario (Hackathon)

The working app must be able to execute this exact sequence live:

1. Dashboard loads → 5 shipments visible on map, all green/yellow
2. Click "Simulate: Port Congestion — Singapore" on SHP-004
3. SHP-004 DRI spikes from ~25 to 87 in real time on screen
4. Red alert toast appears: `"⚠ Disruption detected on SHP-004. DRI: 87"`
5. Route comparison sidebar appears with 3 alternate routes
6. System auto-selects best route → map route visibly changes
7. Copilot panel auto-populates explanation of the decision
8. Judge types: `"Why was Colombo chosen over Jebel Ali?"` → Copilot answers with cost/risk tradeoff

**Rehearse this sequence minimum 5 times before the presentation.**

---

## Build Priority for Hackathon (50-Hour Mode)

If building for demo only, complete phases in this compressed order:

| Priority | Phase | Hours |
|---|---|---|
| 1 | Phase 0 (bootstrap) | 2h |
| 2 | Phase 1 (mock data + API) | 4h |
| 3 | Phase 2 (map + disruption sim) | 6h |
| 4 | Phase 3 (XGBoost only, skip LSTM) | 4h |
| 5 | Phase 4 (Claude copilot) | 3h |
| 6 | Polish + demo seeding | 5h |
| 7 | Buffer + rehearsal | 2h |

Skip Phase 5 (LangGraph), Phase 6 (Kafka/Flink), and Phase 7 (production infra) entirely for hackathon. Frame them honestly as the 18-month production roadmap.

---

## Key Decisions and Constraints

- **Never hardcode API keys.** All secrets via `.env` and `python-dotenv`. `.env` is in `.gitignore`.
- **Mock mode must always work.** If any external API is down, the app falls back to seeded data. The demo never breaks due to an external dependency.
- **DRI is always an integer 0–100.** Never a float. Never null. Default to 0 if model fails.
- **WebSocket is the source of truth for the frontend.** Do not poll REST for live data.
- **All database queries use async SQLAlchemy.** Never use synchronous DB calls in FastAPI async endpoints.
- **The graph engine is stateless.** It takes origin + destination + current disruption map and returns routes. It does not store state internally.
- **Claude API calls are always wrapped in try/except.** If the API call fails, return a canned fallback explanation. Never let a Claude API failure crash the demo.

---

*Last updated: April 2026 — Team Return0*
