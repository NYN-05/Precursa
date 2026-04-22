from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ShipmentSnapshot, WhatIfSimulation
from app.services.risk_scoring import risk_scoring_service
from app.services.route_intelligence import route_intelligence_service


@dataclass
class ScenarioSnapshot:
    shipment_key: str
    feature_vector: dict[str, Any]
    event_count: int
    avg_severity: float
    last_severity: float
    provisional_dri: int
    last_source: str
    last_occurred_at: Any


def _scenario_feature_vector(base: dict[str, Any], scenario: dict[str, Any]) -> dict[str, Any]:
    projected = dict(base)
    for key, value in scenario.items():
        if value is not None:
            projected[key] = value

    blocked_ports = scenario.get("blocked_ports")
    if isinstance(blocked_ports, list):
        existing = projected.get("sanctioned_ports", [])
        if not isinstance(existing, list):
            existing = []
        projected["sanctioned_ports"] = sorted({*existing, *blocked_ports})

    delay_delta_hours = scenario.get("delay_delta_hours")
    if delay_delta_hours is not None:
        projected["delay_hours"] = float(projected.get("delay_hours", 0.0) or 0.0) + float(delay_delta_hours)

    return projected


def run_what_if_simulation(
    db: Session,
    shipment_key: str,
    scenario: dict[str, Any],
) -> WhatIfSimulation:
    snapshot = db.scalar(select(ShipmentSnapshot).where(ShipmentSnapshot.shipment_key == shipment_key))
    if snapshot is None:
        raise ValueError(f"Shipment snapshot not found for key '{shipment_key}'")

    base_vector = snapshot.feature_vector if isinstance(snapshot.feature_vector, dict) else {}
    projected_vector = _scenario_feature_vector(base_vector, scenario)
    severity_delta = float(scenario.get("severity_delta", 0.0) or 0.0)
    projected_last_severity = min(1.0, max(0.0, snapshot.last_severity + severity_delta))
    projected_avg = min(1.0, max(0.0, (snapshot.avg_severity + projected_last_severity) / 2.0))
    projected_dri_seed = min(
        100,
        max(0, int(round(max(snapshot.provisional_dri, projected_last_severity * 100)))),
    )

    scenario_snapshot = ScenarioSnapshot(
        shipment_key=shipment_key,
        feature_vector=projected_vector,
        event_count=snapshot.event_count + 1,
        avg_severity=projected_avg,
        last_severity=projected_last_severity,
        provisional_dri=projected_dri_seed,
        last_source=snapshot.last_source,
        last_occurred_at=snapshot.last_occurred_at,
    )
    score = risk_scoring_service.score_snapshot(scenario_snapshot, top_k=5)  # type: ignore[arg-type]

    projected_routes: list[dict[str, Any]] = []
    explanation: str
    try:
        plan = route_intelligence_service.reroute_shipment(scenario_snapshot, max_paths=12, top_k=3)  # type: ignore[arg-type]
        projected_routes = [
            {
                "path": route.path,
                "eta_hours": route.eta_hours,
                "risk_score": route.risk_score,
                "lp_score": route.lp_score,
                "constraints_applied": route.constraints_applied,
                "selected_best": route.path == plan.selected_path,
            }
            for route in plan.top_routes
        ]
        explanation = (
            f"Projected DRI is {score.dri}/100 and {len(projected_routes)} feasible route(s) "
            f"remain after applying the scenario constraints."
        )
    except ValueError as exc:
        explanation = f"Projected DRI is {score.dri}/100, but routing could not run: {exc}"

    record = WhatIfSimulation(
        shipment_key=shipment_key,
        scenario=scenario,
        projected_dri=score.dri,
        projected_routes=projected_routes,
        explanation=explanation,
    )
    db.add(record)
    db.flush()
    return record
