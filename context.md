# Precursa Context

This file is the single-read overview of the Precursa workspace. It condenses every file currently present in the folder into one coherent project narrative so a human or an AI agent can understand the system without opening the source files one by one.

## How to Read This Workspace

- `Docs/` is the current source of truth.
- `doc_old/` is legacy material and is superseded by `Docs/`.
- `Instructions.md` is the workspace operating manual and sets the behavior rules for future edits.
- The workspace currently contains documentation, diagrams, and research artifacts only. There is no application source code in the folder yet.

## One-Sentence Summary

Precursa is a self-healing supply chain intelligence platform that ingests live disruption signals, scores shipment risk with an AI ensemble, explains the risk with SHAP, reroutes cargo through constraint-aware optimization, and presents the result through an autonomous agent and operator dashboard.

## Core Product Idea

The project is built around a closed-loop control system for supply chains:

1. Ingest signals from weather, port feeds, IoT/GPS, geo-risk, and customs systems.
2. Stream and normalize those signals through Kafka and Flink.
3. Convert them into a Disruption Risk Index (DRI) from 0 to 100.
4. Use SHAP to explain why the risk is high.
5. Trigger an autonomous LangGraph agent when risk is critical.
6. Generate candidate routes with graph search.
7. Apply hard constraints with PuLP so infeasible routes are rejected.
8. Execute reroutes, rebook carriers, update warehouse slots, and notify customers.
9. Show everything on a dashboard and copilot panel.
10. Validate the system with Ever Given backtesting and a multi-agent war game.

## Workspace File Index

| File | Role | What it contains |
|---|---|---|
| `Instructions.md` | Workspace operating manual | Global rules for how future work should be done, including docs-first behavior, validation, clean structure, testing, audit, and phase order. |
| `Docs/precursa_v2_documentation.txt` | Primary architecture narrative | The v2.0 system story, problem framing, accepted architect critiques, upgrades from v1, SHAP, LP solver, war game, backtesting, and the updated abstract. |
| `Docs/ROADMAP_v2.md` | Canonical build guide | The implementation plan, tech stack, repo structure, environment variables, database schema, canonical port list, phase plan, tests, demo acts, and hard architectural rules. |
| `Docs/solution.md` | Plain-English summary | A very simple five-step explanation of what Precursa does for non-technical readers. |
| `Docs/precursa_architecture_light.svg` | Interactive architecture diagram | The full top-down architecture in vector form, with clickable nodes and labels for sources, Kafka, Flink, AI ensemble, DRI, graph rerouting, agent, actions, and dashboard. |
| `Docs/precursa_architecture_light.png` | Raster architecture diagram | A rendered image of the same architecture shown in the SVG. |
| `Docs/market_research.png` | Research screenshot | A screenshot of market/problem research with citations, losses, TAM/SAM/SOM discussion, and trend notes. |
| `Docs/precursa_v2_documentation.pdf` | Formatted document mirror | Binary PDF rendering of the v2 documentation. It mirrors the text document content. |
| `doc_old/precursa_documentation.md` | Legacy v1 documentation | Earlier version of the project story, with a simpler alert-system framing and less mature autonomous behavior. |
| `doc_old/ROADMAP.md` | Legacy v1 roadmap | Earlier implementation plan with manual simulation and a lighter architecture. |
| `doc_old/precursa_documentation.pdf` | Legacy PDF mirror | Binary PDF rendering of the legacy v1 documentation. |

## What the Current Docs Say

### 1) The Problem

Precursa is solving a reactive supply-chain disruption problem. The current industry baseline described in the docs is that companies detect problems too late, often rely on manual monitoring, and absorb cascading delays, missed SLAs, expediting costs, and customer trust loss before anyone intervenes.

The docs repeatedly emphasize:

- average detection times in the 4 to 6 hour range in the old world,
- heavy manual monitoring reliance,
- annual losses in the hundreds of billions of dollars,
- and recovery times that can stretch into days when disruptions cascade.

### 2) The Product Thesis

Precursa is not meant to be a passive alerting dashboard. It is an autonomous system that can:

- detect disruption early,
- predict near-future risk,
- explain the reason for the risk,
- decide on a route,
- execute the reroute,
- notify stakeholders,
- and prove resilience in simulation.

That is the central design shift across the docs: from visibility-only to action-taking automation.

### 3) The DRI Model

The Disruption Risk Index is the core score in the system.

- Range: 0 to 100.
- Updated every 2 minutes in the main narrative.
- Produced by an ensemble of three models.
- Must always be returned as an integer.
- Must always be accompanied by SHAP explanations in v2.

The thresholds described in the docs are:

| DRI range | Meaning | Expected system response |
|---|---|---|
| 0 to 30 | Green | Normal monitoring, no action. |
| 31 to 60 | Yellow | Monitor and pre-compute contingencies. |
| 61 to 80 | Orange | High risk, prepare or stage reroutes. |
| 81 to 100 | Red | Critical, autonomous reroute. |

### 4) The AI Ensemble

The current architecture uses three model types:

- PyTorch LSTM for temporal prediction.
- Isolation Forest for anomaly detection.
- XGBoost for risk classification.

The ensemble is treated as the decision engine that drives the DRI. In v2, SHAP is layered on top of the ensemble so every alert has a human-readable reason.

### 5) Explainability and Trust

The docs make explainability a hard requirement, not a cosmetic feature. SHAP values are used to explain which features pushed the risk up or down. The copilot must only talk about factors that actually appear in the SHAP output or the LP constraint log. It is explicitly not allowed to invent reasons.

This is one of the most important trust mechanisms in the project.

### 6) Routing and Constraints

Precursa does not rely on shortest-path routing alone. The docs distinguish between:

- candidate path generation via NetworkX, and
- final route selection via PuLP linear programming.

The LP solver exists to enforce hard constraints such as:

- cold-chain requirements,
- sanctioned port exclusions,
- weight limits,
- and SLA deadlines.

This is the main difference between a route suggestion tool and a route execution system.

### 7) The Autonomous Agent

The LangGraph agent is the core loop in v2. The docs say this repeatedly:

- the agent is not optional,
- the agent is not button-triggered in production behavior,
- the dashboard and copilot are output surfaces for the agent,
- and every autonomous action must be logged.

The agent flow is roughly:

ingest -> score -> assess risk -> compute candidate routes -> apply LP constraints -> select route -> execute reroute -> notify -> explain -> log.

### 8) Validation Story

The docs include two major proof mechanisms:

- Ever Given backtesting for historical validation.
- A Monte Carlo multi-agent war game for live resilience demonstration.

The Ever Given story is used to show that Precursa could flag a disruption before the grounding event. The war game is used to show the agent defending ROI against simulated chaos in real time.

## File-by-File Details

### Instructions.md

This file is the workspace operating policy. It is not project product content, but it strongly affects how future edits should be made.

Key rules it contains:

- Use `Docs/` as the source of truth.
- Do not rely on `doc_old` for current decisions.
- Work in phases: Analysis -> Structuring -> Refactoring -> Documentation -> Quality -> Testing -> Optimization -> Deployment -> Audit.
- Generate `CONTEXT.md` as part of analysis.
- Generate `README.md` and `QUALITY_REPORT.md` later in the lifecycle.
- Keep the code clean, validated, modular, and maintainable.

The file also requires folder structure conventions, testing discipline, config hygiene, logging, security hardening, CI/CD, observability, and a final audit.

### Docs/precursa_v2_documentation.txt

This is the main architecture and strategy document for Precursa v2.0.

Important ideas in this file:

- v1.0 was an alert system with the agent too far back in the stack.
- v2.0 moves the agent to the core.
- The accepted critiques are:
  - self-healing was not really closed-loop,
  - DRI was a black box,
  - routing was too simple,
  - the copilot could hallucinate,
  - validation was too weak.
- v2.0 fixes those with SHAP, LP constraints, grounded prompts, and Ever Given backtesting.
- The war game is introduced as the killer feature.
- The docs present v2.0 as a closed-loop autonomous supply chain intelligence platform.

The document also includes:

- a v1 vs v2 flow comparison,
- a SHAP example table,
- a route constraint discussion,
- a Neo4j-compatible graph schema,
- the war game design,
- the updated tech stack,
- and a concise hackathon abstract.

### Docs/ROADMAP_v2.md

This is the canonical implementation guide.

It defines:

- the project overview,
- the canonical tech stack,
- the repo structure,
- environment variables,
- the database schema,
- the canonical port graph,
- the roadmap phases,
- demo scenarios,
- testing strategy,
- and immutable architectural rules.

It is the most operationally useful document in the workspace.

Key points:

- Backend: Python 3.11, FastAPI, WebSockets, async PostgreSQL, Redis.
- Streaming: Kafka and Flink in production; mock mode allowed for MVP.
- ML: LSTM, XGBoost, Isolation Forest, SHAP, MLflow.
- Routing: NetworkX for candidate paths, PuLP for final selection.
- Copilot: Claude, but strictly grounded.
- Frontend: React 18, TypeScript, Vite, Leaflet in MVP, Mapbox in production vision.
- Infra: Docker locally, Kubernetes EKS and Terraform for production.

The roadmap also defines 12 major phases in the later sections of the file:

1. Bootstrap.
2. LangGraph agent core.
3. Data models and mock feed.
4. ML ensemble and SHAP.
5. LP constraint solver.
6. Grounded copilot.
7. Interactive dashboard and map.
8. Ever Given backtesting.
9. Multi-agent war game.
10. Kafka and Flink production streaming.
11. Authentication and security.
12. Production hardening.

The file ends with testing gates and architectural rules that must never be broken.

### Docs/solution.md

This file is the simplest possible explanation of the product.

It frames Precursa as:

- a smoke detector,
- a fire extinguisher,
- and an insurance agent for supply chains.

Its five steps are:

1. Watch everything continuously.
2. Score every shipment with DRI.
3. Predict trouble before it happens.
4. Fix it automatically.
5. Explain every decision.

This file is useful when the project needs to be explained to a non-technical audience.

### Docs/precursa_architecture_light.svg

This is a structured, interactive architecture diagram in vector form.

It visually encodes the system as:

input data sources -> Kafka event bus -> Flink stream processing -> AI ensemble -> DRI -> graph rerouting engine -> LangGraph autonomous agent -> action nodes -> ops dashboard and AI copilot.

The diagram explicitly shows the data/action layers, streaming layers, ML layers, DRI layer, AI agent layer, and dashboard layer. It also includes a legend and feedback loops.

### Docs/precursa_architecture_light.png

This is the same architecture as the SVG, rendered as a raster image.

It shows the same conceptual pipeline and is best thought of as the visual companion to the architecture text.

### Docs/market_research.png

This screenshot captures market research and problem framing notes.

From the visible content, it appears to summarize:

- the reactive nature of supply-chain disruption management,
- manual monitoring as a core weakness,
- detection and recovery delays,
- market-loss verification sources,
- TAM/SAM/SOM reasoning,
- and trend notes such as rising disruption frequency and growing AI adoption.

The screenshot also references source labels such as Resilinc, the World Bank, MarketsandMarkets, and Grand View Research.

### Docs/precursa_v2_documentation.pdf

This PDF appears to be the formatted binary copy of the v2 documentation text.

It should be treated as a presentation-friendly mirror of `Docs/precursa_v2_documentation.txt`, not a separate source of product logic.

### doc_old/precursa_documentation.md

This is the older documentation set for Precursa.

The legacy version describes a simpler v1.0 project:

- the system is still about supply-chain disruption management,
- but the autonomous agent is not the core,
- the reroute flow is more manual,
- and the project is less mature on explainability and validation.

The old document still contains the same broad idea, but it does not have the stronger v2 features such as SHAP grounding, LP constraint enforcement, or the war game emphasis.

### doc_old/ROADMAP.md

This is the older build plan for the v1-era project.

Its structure is simpler than ROADMAP_v2.md and centers on:

- bootstrap,
- data models and mock data,
- interactive map and disruption simulation,
- ML ensemble,
- Claude copilot,
- and a manual or button-triggered LangGraph-style agent layer.

It is useful as historical context, but it has been superseded by the v2 roadmap.

### doc_old/precursa_documentation.pdf

This is the formatted PDF mirror of the legacy documentation.

Like the other PDF artifact, it is a presentation version of the older text document.

## Canonical Data and Model Details

### DRI and Explainability

The v2 docs require these properties:

- DRI is an integer in the 0 to 100 range.
- DRI is produced every 2 minutes in the main loop.
- Every DRI score must have SHAP factors attached.
- The top SHAP factors are surfaced in the dashboard, copilot, and audit log.

### Canonical Shipment Data

The roadmap defines a seed set of five shipments used for the MVP and demo flow:

- SHP-001: Mumbai -> Rotterdam.
- SHP-002: Shanghai -> Los Angeles.
- SHP-003: Chennai -> Hamburg.
- SHP-004: Nhava Sheva -> Felixstowe.
- SHP-005: Hong Kong -> Antwerp or, in the v1 roadmap, Hong Kong -> Busan -> Los Angeles.

Across the docs, the point is consistent: the demo needs realistic long-haul international routes with enough variation to show rerouting.

### Canonical Port Graph

The v2 roadmap defines a canonical port list with coordinates and cold-chain / congestion metadata. The exact list is important because it anchors the route graph and the cold-chain constraint logic.

Ports referenced in the v2 roadmap include:

| Port | Country | Cold chain | Congestion baseline |
|---|---|---:|---:|
| Mumbai | India | Yes | 0.30 |
| Nhava Sheva | India | Yes | 0.35 |
| Chennai | India | No | 0.25 |
| Colombo | Sri Lanka | Yes | 0.20 |
| Singapore | Singapore | Yes | 0.40 |
| Port Klang | Malaysia | Yes | 0.30 |
| Jebel Ali | UAE | Yes | 0.25 |
| Suez | Egypt | No | 0.50 |
| Rotterdam | Netherlands | Yes | 0.30 |
| Hamburg | Germany | Yes | 0.25 |
| Felixstowe | UK | Yes | 0.35 |
| Antwerp | Belgium | Yes | 0.30 |
| Shanghai | China | Yes | 0.45 |
| Hong Kong | HK | Yes | 0.40 |
| Busan | South Korea | Yes | 0.30 |
| Los Angeles | USA | Yes | 0.40 |
| Durban | South Africa | No | 0.20 |
| Cape Town | South Africa | No | 0.15 |

The docs also include exact coordinates in the roadmap text for route visualization and graph routing.

### Database Entities

The v2 roadmap defines these core tables:

- shipments
- disruption_events
- routes
- agent_actions
- wargame_sessions

The database layer is meant to support auditability, replay, and simulation history.

### Pricing and Business Model

The project is positioned as SaaS with tiers such as:

- Starter: around $2,000 / month.
- Growth: around $8,000 / month.
- Enterprise: custom pricing.

The business story is that the product is valuable to freight forwarders, 3PLs, e-commerce, and regulated cold-chain industries because it takes action, not just visibility.

## Visual and Narrative Alignment Across Files

The files are consistent with each other in three different ways:

1. The text docs define the architecture and product story.
2. The SVG and PNG diagram show the same architecture visually.
3. The solution doc compresses the same idea into a non-technical explanation.

That means the workspace is not a collection of unrelated notes; it is a coordinated product narrative with one central system design.

## What Is Missing From the Workspace

The folder does not yet contain implementation code.

There is no backend source tree, frontend source tree, test suite, package manifest, or deployment config in the current workspace. The docs are planning and architecture artifacts, not a runnable app.

That matters because the current task is documentation and context extraction, not code repair.

## Practical Reading Order

If a human or AI agent wants to understand the project fast, the best order is:

1. `Instructions.md` for process rules.
2. `Docs/solution.md` for the simplest product explanation.
3. `Docs/precursa_v2_documentation.txt` for the upgraded architecture narrative.
4. `Docs/ROADMAP_v2.md` for the build plan and concrete implementation rules.
5. `Docs/precursa_architecture_light.svg` for the architecture visual.
6. `Docs/market_research.png` for the market framing.
7. `doc_old/` only if historical comparison is needed.

## Final Summary

Precursa is a documentation-first design for an autonomous supply-chain disruption platform. The v2 docs define a much stronger system than the legacy docs: the agent is central, DRI is explainable, route selection is constraint-aware, validation is historical and adversarial, and the product is meant to be deployable, testable, and auditable.

If this workspace is implemented later, the docs imply the first real source code should be a FastAPI backend, a React dashboard, a model scoring pipeline, a route solver, and an agent loop with strict audit logging.