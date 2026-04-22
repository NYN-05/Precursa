  
**PRECURSA**

*Self-Healing Supply Chain Intelligence*

**Complete Project Documentation & Blueprint**

Team Return0  |  Smart Supply Chains Track

*April 2026*

| $184B Annual Losses | \< 2 min Detection Time | 85% Detectable Signals | $23.6B Market by 2028 |
| :---: | :---: | :---: | :---: |

# **1\. Executive Summary**

Precursa is an AI-powered self-healing supply chain intelligence platform that detects, predicts, and autonomously resolves disruptions before they cascade into network-wide failures. In a world where $184 billion is lost annually to supply chain disruptions — and 73% of companies still rely on manual monitoring — Precursa delivers predictive intelligence with a detection time under 2 minutes, compared to the industry average of 4–6 hours.

The platform ingests 10+ live data streams (weather APIs, port feeds, IoT sensors, carrier GPS, geopolitical risk indices, and customs APIs), runs a 3-model AI ensemble to generate a per-shipment Disruption Risk Index (DRI), and uses a graph-based rerouting engine to autonomously select optimal alternate routes — all without human intervention.

| Detect Sub-2-minute disruption detection via continuous AI monitoring | Predict Hours-ahead forecasting using LSTM temporal models on live data | Heal Autonomous rerouting, carrier rebooking & customer notification |
| :---: | :---: | :---: |

Built for the Smart Supply Chains hackathon track, the 50-hour executable MVP demonstrates the full detect-predict-heal loop through a live dashboard, real-time DRI scoring, interactive rerouting simulation, and an AI Copilot powered by the Claude API.

# **2\. Problem Statement**

## **2.1  The Core Problem**

Modern supply chains are fundamentally reactive. Disruptions — whether caused by extreme weather, port congestion, geopolitical events, or customs delays — are typically detected only after timelines have already been missed. By the time a logistics manager is alerted, the disruption has already cascaded into delayed inventory, missed SLAs, and mounting losses.

## **2.2  Scale of the Problem**

| Metric | Current Reality | Impact | Root Cause |
| ----- | ----- | ----- | ----- |
| Detection Time | 4–6 hours average | Cascading delays | Manual monitoring |
| Monitoring Method | 73% manual | $184B annual loss | No unified data layer |
| Disruption Visibility | Localized only | Network-wide failure | Siloed systems |
| Recovery | Manual rerouting | 2–3 day delays | No automation layer |

## **2.3  Three Core Pain Points**

### **Pain Point 1: Reactive, Not Predictive**

Critical disruptions — weather events, port delays, carrier bottlenecks — are detected only AFTER timelines are already missed. No current system correlates early-warning signals across data streams to provide advance notice.

### **Pain Point 2: Unmanageable Scale**

Global networks process millions of concurrent shipments. Manual teams can only monitor a fraction. No existing tool connects weather data, IoT sensors, carrier GPS, geopolitical risk, and customs status into a unified real-time intelligence layer.

### **Pain Point 3: Cascading Failures**

A single localized bottleneck — one congested port, one delayed carrier — silently snowballs into network-wide delays worth millions in losses. Without automated propagation analysis, companies cannot see the cascade coming.

## **2.4  The Opportunity**

85% of supply chain disruptions have detectable precursor signals in data that already exists — weather APIs, AIS vessel tracking, port authority feeds, news sentiment APIs. The problem is not data availability; it is the absence of an intelligent layer that aggregates, correlates, and acts on this data in real time.

# **3\. Solution Overview**

## **3.1  What Precursa Does**

Precursa is the intelligence layer that sits between raw supply chain data and autonomous action. It ingests 10+ live data streams, runs a three-model AI ensemble to score disruption risk per shipment, uses a graph-based rerouting engine to compute optimal alternate routes, and executes autonomous remediation — rebooking carriers, updating warehouse slots, and notifying customers — before the disruption reaches critical impact.

## **3.2  Four Core Pillars**

| \# | Pillar | What It Does | Key Technology |
| ----- | ----- | ----- | ----- |
| 01 | Omni-Source Data Fabric | Ingests weather, port feeds, IoT sensors, carrier GPS, geopolitical risk, and customs APIs into a unified stream | Apache Kafka, Confluent Cloud |
| 02 | AI Disruption Detection | Three-model ensemble generates a Disruption Risk Index (DRI) per shipment, updated every 2 minutes | PyTorch LSTM \+ XGBoost \+ Isolation Forest |
| 03 | Graph-Based Rerouting Engine | Live supply chain graph computes optimal alternate routes ranked by cost, ETA, risk, and carbon footprint | Neo4j \+ NetworkX \+ Modified Dijkstra |
| 04 | Self-Healing Automation | Autonomously books alternate carriers, updates warehouse slots, and notifies customers with revised ETAs | LangGraph \+ Claude API by Anthropic |

## **3.3  The Disruption Risk Index (DRI)**

The DRI is Precursa's core output — a 0–100 risk score per shipment, updated every 2 minutes. It is the ensemble product of three model outputs:

* LSTM temporal score: Probability of disruption in the next 6 hours based on historical sequences

* Isolation Forest anomaly score: Deviation from normal shipment behavior patterns

* XGBoost classification score: Risk category based on current contextual features

| DRI 0–30 | Green — Normal operations, no action required |
| :---- | :---- |
| **DRI 31–60** | Yellow — Monitor closely, prepare contingency routes |
| **DRI 61–80** | Orange — High risk, recommend operator review |
| **DRI 81–100** | Red — Critical, autonomous rerouting triggered |

## **3.4  AI Copilot**

Every disruption event and rerouting decision is explained in plain language by an AI Copilot powered by the Claude API. Operators can ask questions like 'Why was this route chosen?' or 'What is the cost-carbon tradeoff on SHP-004?' and receive a contextual, data-grounded answer in real time. This transforms Precursa from a black box into a transparent, collaborative intelligence partner.

# **4\. Technical Architecture**

## **4.1  Full Vision Architecture (18-Month)**

The complete Precursa architecture as designed for production deployment:

| Data Streaming | Apache Kafka \+ Confluent Cloud — real-time pub/sub for 10+ live data streams |
| :---- | :---- |
| **Stream Processing** | Apache Flink — sub-second stateful stream processing with event windowing |
| **ML Models** | PyTorch LSTM \+ XGBoost \+ Isolation Forest — 3-model ensemble with MLflow tracking |
| **ML Ops** | AWS SageMaker — model monitoring, continuous retraining, feedback loop |
| **Graph Engine** | Neo4j \+ NetworkX — live supply chain graph with modified Dijkstra algorithm |
| **LLM Copilot** | Claude API by Anthropic — natural language explanation and Q\&A interface |
| **Automation Agent** | LangGraph — agentic orchestration for autonomous rerouting actions |
| **Backend / API** | FastAPI \+ WebSockets — real-time data push to frontend |
| **Frontend** | React \+ Mapbox GL JS — real-time shipment map, DRI heatmap, alerts |
| **Infrastructure** | Docker \+ Kubernetes (EKS) \+ Terraform — cloud-native deployment |

## **4.2  50-Hour MVP Architecture (Hackathon Build)**

The following is the executable architecture scoped for the hackathon demo. Every full-vision component has a pragmatic replacement that delivers the same demo experience without the setup overhead:

| Component | Full Vision | 50-Hour MVP Replacement | Why |
| ----- | ----- | ----- | ----- |
| Event Bus | Apache Kafka \+ Confluent Cloud | FastAPI mock data generator | Kafka setup alone takes 6–8 hrs |
| Stream Processing | Apache Flink | Python background polling loop (2-min interval) | Same effect, zero infra |
| ML Ensemble | LSTM \+ Isolation Forest \+ XGBoost | Single XGBoost model on Kaggle logistics dataset | Trains in minutes, still impressive |
| Graph Engine | Neo4j \+ NetworkX | NetworkX only (pure Python) | Neo4j setup is unnecessary for demo |
| Automation Agent | LangGraph orchestration | Direct Claude API structured prompt | Same autonomous feel, fraction of work |
| ML Ops | AWS SageMaker | Local model served via FastAPI endpoint | No cloud setup needed for demo |
| Frontend Maps | React \+ Mapbox GL JS | React \+ Leaflet.js (free, no API key friction) | Mapbox billing setup wastes time |
| Infrastructure | Docker \+ Kubernetes \+ Terraform | Run locally on laptop | Nobody checks infra during demo |

## **4.3  System Flow (MVP)**

The following describes the end-to-end data and control flow in the MVP:

1. Mock data generator produces 5 shipments with real-world port coordinates, cargo type, and DRI scores every 30 seconds

2. FastAPI backend receives data, runs XGBoost model to update DRI per shipment

3. WebSocket pushes updated shipment state to React frontend in real time

4. Frontend renders shipment markers on Leaflet map with color-coded DRI badges

5. Operator clicks 'Simulate Disruption' — backend triggers DRI spike for selected shipment

6. NetworkX graph engine computes 3 alternate routes ranked by cost, ETA, risk, and carbon score

7. Auto-rerouting fires: route updates on map, carrier reallocation logged

8. Claude API Copilot generates natural language explanation of the decision

9. Customer notification panel shows revised ETA and reroute rationale

## **4.4  API Endpoint Design**

| GET /api/shipments | Returns all active shipments with current DRI scores, coordinates, and status |
| :---- | :---- |
| **POST /api/trigger-disruption** | Simulates a disruption event on a specified shipment (type: port/weather/customs) |
| **POST /api/reroute/{id}** | Triggers NetworkX graph rerouting, returns top 3 alternate routes |
| **GET /api/routes/{id}** | Returns route graph for a shipment with node metadata |
| **POST /api/copilot** | Sends disruption context to Claude API, returns natural language explanation |
| **WS /ws/live** | WebSocket endpoint streaming real-time shipment state updates |

# **5\. Demo Blueprint**

The demo is the single most important element of the hackathon presentation. This section defines exactly what judges will see, in what order, and what talking points to deliver at each moment. Target runtime: 2.5 to 3 minutes.

## **5.1  Pre-Demo Setup Checklist**

* Backend running on localhost:8000 with 5 seeded shipments

* Frontend running on localhost:3000 — map loaded, all shipments visible

* Claude API key loaded in environment, Copilot panel visible

* Browser zoomed to 90% — full dashboard visible without scrolling

* Disable all browser notifications and OS alerts

* Have the 3 disruption scenarios pre-selected in the simulate panel

## **5.2  Demo Script — Step by Step**

| Step | Action | What Judges See | Talking Point |
| ----- | ----- | ----- | ----- |
| 1 | Open Dashboard | Global map with 5 live shipment markers. Green/yellow DRI score badges on each. | 'This is Precursa's Ops Dashboard. 5 shipments active across 3 trade lanes. All green right now — DRI scores below 30.' |
| 2 | Trigger Disruption | Click 'Simulate: Port Congestion — Singapore'. SHP-004's DRI spikes from 23 to 87\. Marker turns red. | 'We just simulated a port congestion signal hitting Singapore. Watch SHP-004's DRI spike in real time — that's the AI ensemble firing.' |
| 3 | Alert Fires | Toast notification: '⚠ Disruption detected on SHP-004. Risk Index: 87\. Cause: Port congestion.' | 'Under 2 minutes from signal to alert. Industry average is 4 to 6 hours. We've already caught it.' |
| 4 | Rerouting Triggers | Route on map visibly shifts. Sidebar shows 3 alternate routes with cost, ETA, risk, and carbon scores. | 'Graph engine is running modified Dijkstra across 18 port nodes. Three routes ranked by our composite score. Best route auto-selected.' |
| 5 | Copilot Explains | Claude Copilot panel: 'Rerouted SHP-004 via Colombo. ETA impact: \+6 hours. Cost delta: \-$1,200. Carbon reduced 8%.' | 'Every autonomous decision is explained. Operators stay in control — they can override or ask follow-up questions.' |
| 6 | Ask Copilot Live | Type 'Why was Colombo chosen over Jebel Ali?' — Copilot explains cost and congestion tradeoff. | 'Watch this.' \[Ask question live.\] This is the moment that makes Precursa feel like a real product, not a prototype.' |

## **5.3  Three Demo Scenarios (Prepared)**

Have three disruption scenarios seeded and ready to trigger during the demo:

* Scenario A — Port Congestion (Singapore): DRI spike on Mumbai-Rotterdam lane. Best reroute via Colombo.

* Scenario B — Weather Event (Bay of Bengal): DRI spike on Chennai-Hamburg lane. Best reroute via Colombo overland segment.

* Scenario C — Customs Delay (Suez): DRI spike on Nhava Sheva-Felixstowe lane. Best reroute via Cape of Good Hope with \+18hr ETA delta.

## **5.4  Anticipated Judge Questions & Answers**

| How does DRI work? | Three models: XGBoost classifies current risk features, LSTM predicts 6-hour temporal trend, Isolation Forest detects anomalies. Ensemble fuses scores into a 0-100 index. |
| :---- | :---- |
| **Is this real data?** | In the MVP, data is seeded using real port coordinates and realistic disruption patterns. Full version ingests live APIs — weather, AIS vessel tracking, port authority feeds. |
| **What makes this different from existing tools?** | FourKites and project44 provide visibility. Precursa provides action. We don't just alert — we reroute autonomously before the operator even sees the notification. |
| **How do you make money?** | SaaS subscription: Starter $2K/month (500 shipments), Growth $8K/month (5,000 shipments), Enterprise custom. First target: mid-size freight forwarders. |
| **Are the impact numbers real?** | Projected based on simulation. $47K per early-detected disruption is based on industry benchmark cost models. Pilot validation is Phase 1 objective. |

# **6\. 50-Hour Build Plan**

This section provides the hour-by-hour execution plan for the hackathon. The plan is structured for a backend-strong team starting from zero. Critical path items are marked.

## **6.1  Team Task Allocation**

| Role | Primary Tasks | Hours | Owner |
| ----- | ----- | ----- | ----- |
| Backend Lead | FastAPI server, data models, WebSocket, disruption simulation endpoint | Hours 0-30 | Team Member 1 |
| ML Engineer | XGBoost model training, DRI scoring logic, data generation scripts | Hours 0-20 | Team Member 2 |
| Graph Engineer | NetworkX port graph, rerouting algorithm, route ranking logic | Hours 8-28 | Team Member 1/2 |
| Frontend Dev | React dashboard, Leaflet map, DRI cards, disruption UI | Hours 20-42 | Team Member 3 |
| Integration | Claude API Copilot, end-to-end testing, demo seeding | Hours 38-48 | All |

## **6.2  Hour-by-Hour Schedule**

| Hours | Phase | Tasks | Priority |
| ----- | ----- | ----- | ----- |
| 0 – 8 | Backend Core | FastAPI project setup, shipment data models (Pydantic), mock data generator (5 shipments, realistic port coords), /api/shipments endpoint, basic WebSocket scaffold | CRITICAL |
| 8 – 20 | ML \+ Graph | Download Kaggle logistics disruption dataset, train XGBoost classifier, DRI scoring function, NetworkX graph with 18 port nodes (real coordinates), modified Dijkstra with cost+ETA+risk weights | CRITICAL |
| 20 – 30 | API Integration | /api/trigger-disruption endpoint, /api/reroute/{id} endpoint, WebSocket real-time push working end-to-end, DRI update loop (30-second polling) | CRITICAL |
| 30 – 38 | Frontend | React app scaffolding, Leaflet map with port markers, shipment marker layer with DRI color coding, disruption simulation panel, route visualization on map | HIGH |
| 38 – 44 | Copilot \+ Polish | Claude API integration in frontend, Copilot chat panel, disruption toast notifications, route comparison sidebar, DRI trend sparklines | HIGH |
| 44 – 48 | Demo Seeding | Seed all 3 demo scenarios with realistic data, end-to-end test all demo steps, fix UI polish issues, rehearse demo script 3 times | HIGH |
| 48 – 50 | Buffer | Bug fixes, final rehearsal, prepare Q\&A answers, backup demo recording in case of live issues | SAFETY |

## **6.3  Data Sources & APIs**

| XGBoost Training Data | Kaggle: 'Supply Chain Shipment Pricing Dataset' or 'Freight Delay Dataset' — free, no API key |
| :---- | :---- |
| **Port Coordinates** | Use real coordinates for 18 major ports: Shanghai, Singapore, Rotterdam, Hamburg, Los Angeles, Mumbai, Nhava Sheva, Colombo, Jebel Ali, Hong Kong, Busan, Felixstowe, Antwerp, Tanjung Pelepas, Port Klang, Chennai, Sydney, Durban |
| **Weather Simulation** | Seed realistic weather disruption events from historical data (no live API needed for MVP) |
| **Claude API** | Anthropic API key — use claude-sonnet-4-20250514 model for Copilot responses |
| **Leaflet.js** | Free, no API key required, OpenStreetMap tiles included |

# **7\. Market Analysis**

## **7.1  Market Size**

| Market | Size | Year | Source |
| ----- | ----- | ----- | ----- |
| Global Supply Chain Disruption Losses | $184 Billion/year | 2024 | Resilinc Industry Report |
| Supply Chain AI Market | $10.1 Billion | 2024 | MarketsandMarkets |
| Supply Chain AI Market (Projected) | $23.6 Billion | 2028 | MarketsandMarkets |
| Supply Chain Visibility Market | $6.8 Billion | 2025 | Grand View Research |

## **7.2  Target Segments**

* Global manufacturers with multi-tier supply chains — highest disruption exposure, highest willingness to pay

* Freight forwarders and 3PL logistics providers — need real-time visibility across thousands of shipments

* E-commerce giants with high SLA sensitivity — every delayed shipment impacts NPS and customer retention

* Pharma and cold-chain operators — zero-tolerance for delays, regulatory compliance requirements add urgency

## **7.3  Competitive Landscape**

| Competitor | What They Do | Limitation | Precursa Advantage |
| ----- | ----- | ----- | ----- |
| FourKites | Real-time shipment tracking and visibility | Visibility only — no autonomous action | Precursa detects AND fixes autonomously |
| project44 | Supply chain visibility platform | Alert-based, requires manual response | Precursa reroutes before operator is alerted |
| Resilinc | Supply chain risk mapping | Strategic risk only, no real-time ops | Precursa operates at shipment level in real time |
| Flexport | Digital freight forwarding | Carrier-specific, not network-wide | Precursa is carrier-agnostic, network-wide |

## **7.4  Projected Impact Metrics**

The following metrics are projected based on industry benchmark cost models and pilot simulation results. These will be validated through live pilot partnerships in Phase 1\.

* $47,000 saved per early-detected transoceanic disruption (based on industry average cost-per-disruption models)

* 40% reduction in expediting costs through automated rerouting vs. manual emergency rebooking

* 3x faster incident response compared to manual operations teams

* 60% fewer customer SLA breaches in pilot simulations

# **8\. Business Model**

## **8.1  Revenue Model — SaaS Subscription**

| Tier | Monthly Price | Shipment Limit | Key Features | Target Customer |
| ----- | ----- | ----- | ----- | ----- |
| Starter | $2,000 / month | Up to 500 | Dashboard, DRI alerts, manual rerouting | Mid-size freight forwarders |
| Growth | $8,000 / month | Up to 5,000 | Autonomous rerouting, Copilot, API access | Regional 3PLs, e-commerce |
| Enterprise | Custom pricing | Unlimited | Custom integrations, SLA, dedicated support | Global manufacturers, pharma |

## **8.2  Unit Economics**

| Target CAC | $12,000 – $18,000 (enterprise outbound sales \+ pilot program) |
| :---- | :---- |
| **Target LTV** | $96,000+ (Growth tier, 12-month avg. contract, 85% retention) |
| **LTV:CAC Ratio** | 5:1 to 8:1 at scale (healthy SaaS benchmark is 3:1+) |
| **Gross Margin** | 78–82% (infrastructure costs scale sublinearly with customers) |
| **Payback Period** | 4–6 months per customer at Growth tier |

## **8.3  Go-To-Market Strategy**

### **Phase 1: Pilot-First Sales (Months 0–6)**

Target 3 mid-size freight forwarders in India and Southeast Asia. Offer a 90-day free pilot in exchange for data sharing and testimonial rights. Convert to paid Growth tier post-pilot. This validates impact metrics and builds credibility for enterprise sales.

### **Phase 2: Inbound \+ Partnerships (Months 6–12)**

Content marketing on supply chain disruption topics, conference presence at LogiSym, TOC Asia, and Supply Chain India. Partner with ERP vendors (SAP, Oracle) as an embedded intelligence module.

### **Phase 3: Enterprise & Global (Months 12–18)**

Direct enterprise sales to pharma, FMCG, and automotive manufacturers. Series A fundraise to fund global expansion into EU and US markets.

# **9\. Product Roadmap**

The roadmap is structured in three phases, progressing from MVP validation to full platform deployment to global scale. Each phase has clear deliverables, success metrics, and funding milestones.

## **9.1  Roadmap Overview**

| PHASE 1 — Validate | PHASE 2 — Build | PHASE 3 — Scale |
| ----- | ----- | ----- |
| ***Months 0 – 3*** MVP live and pilot-validated •  Kafka \+ Flink pipeline live •  DRI scoring for 5 disruption types •  Dashboard with real-time map overlay •  Pilot with 1 logistics partner •  Basic autonomous rerouting | ***Months 3 – 9*** Full platform deployed •  Full ML ensemble on SageMaker •  LangGraph autonomous rerouting agent •  API integrations: carriers, customs •  Carbon-aware routing module •  5+ pilot customers, $50K MRR target | ***Months 9 – 18*** Global expansion •  Digital Twin simulation engine •  Industry modules (Pharma, FMCG, Auto) •  Federated learning across partner networks •  Series A fundraise •  EU \+ US market entry |

## **9.2  Success Metrics by Phase**

| Phase | Technical Milestone | Business Milestone | Funding Milestone |
| ----- | ----- | ----- | ----- |
| Phase 1 | MVP live, DRI accuracy \>80% on test set | 1 pilot partner, impact data collected | Pre-seed / hackathon prize \+ grants |
| Phase 2 | Full ensemble deployed, \<2 min detection confirmed in production | 5 paying customers, $50K MRR | Seed round: $500K – $1M |
| Phase 3 | Digital twin live, federated learning operational | 30+ customers, $500K MRR | Series A: $5M–$10M |

# **10\. Risk Analysis**

## **10.1  Technical Risks**

| Risk | Level | Impact | Mitigation |
| ----- | ----- | ----- | ----- |
| XGBoost model underperforms on real data | High | DRI scores inaccurate, rerouting suboptimal | Train on diverse dataset; add human override; use rule-based fallback DRI |
| Graph rerouting produces infeasible routes | Med | Demo breaks at critical moment | Pre-validate all 3 demo scenarios end-to-end; hardcode fallback route as safety net |
| Claude API latency too high for live demo | Low | Copilot response feels slow | Pre-cache one response; show loading state; response in 2-4 sec is acceptable |
| WebSocket connection instability | Med | Real-time map updates freeze | Add polling fallback; test on event WiFi network in advance |

## **10.2  Business Risks**

| Risk | Level | Impact | Mitigation |
| ----- | ----- | ----- | ----- |
| FourKites / project44 copies the autonomous action layer | Med | Competitive moat eroded | Move fast on pilot data; proprietary DRI model becomes moat; file provisional patent |
| Enterprise sales cycle too long (12–18 months) | High | Cash burn before revenue | Lead with SMB freight forwarders (3–6 month cycles); pilot-to-paid conversion model |
| Carrier API integration complexity | High | Full automation layer delayed | Phase 1 uses operator-confirmed actions; automation is Phase 2 with real integrations |

# **11\. Pitch Slide Amendments**

The following amendments should be made to the existing Precursa pitch deck before presentation. These changes increase credibility without reducing ambition.

## **11.1  Required Changes**

| Slide | Current Text | Change To | Reason |
| ----- | ----- | ----- | ----- |
| 05 | 'Proven Impact' heading | 'Projected Impact (Simulation-Based)' | Avoids credibility damage if judges probe validation |
| 03 | No framing of MVP vs vision | Add: 'Phase 1 MVP: Live demo. Full vision: 18-month roadmap.' | Judges respect honesty; shows you know the scope |
| New slide | No business model slide | Add: SaaS pricing table (Starter/Growth/Enterprise) | Critical gap — judges will ask about monetization |
| New slide | No competitive analysis | Add: Competitor table vs FourKites, project44, Resilinc | Judges in supply chain track will know these players |

## **11.2  Slides to Keep As-Is**

* Slide 01 — Cover: Strong visual identity, clean tagline

* Slide 02 — Problem Statement: Excellent stat framing, keep all three pain points

* Slide 04 — Tech Stack: Architecture diagram is impressive, keep as the full vision

* Slide 06 — Roadmap: Good three-phase structure, minor update to add success metrics

* Slide 07 — Closing: 'Every minute undetected costs $2,500' is a strong closing hook

# **12\. Closing & Verdict**

## **12.1  Is Precursa Win-Worthy?**

Yes — conditionally. The idea is genuinely strong: real problem, large market, technically sophisticated vision, and a compelling autonomous action layer that competitors lack. The 'self-healing' narrative is sticky and differentiating.

The win condition is executing the demo flawlessly. A judge who sees a live shipment get disrupted, watches the DRI spike, observes autonomous rerouting, and then asks the Copilot a follow-up question — that judge will remember Precursa. The technology story becomes real in that moment.

## **12.2  The Three Things That Will Win It**

| \# | What | How |
| ----- | ----- | ----- |
| 1 | The Live DRI Spike | Trigger the disruption simulation live. Watch a green shipment turn red in real time. This one moment shows the problem and solution simultaneously. |
| 2 | The Autonomous Reroute | The map route visibly changes without anyone clicking a button. Judges will lean forward. Let the silence land before you explain what happened. |
| 3 | The Live Copilot Question | Ask the Copilot a follow-up question during the demo. 'Why Colombo over Jebel Ali?' A real AI answer in front of judges transforms a prototype into a product. |

## **12.3  Final Word**

Every minute a supply chain disruption goes undetected costs $2,500. Precursa finds it in under 120 seconds — and fixes it. Build the demo, nail the three moments, and answer the monetization and competition questions confidently. That is the path to winning.

| Predict Hours before impact | Reroute Graph-optimized instantly | Heal Autonomous & self-correcting |
| :---: | :---: | :---: |

