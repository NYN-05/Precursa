from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, TypedDict

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import AgentAction, AgentOverride, RouteRecord, ShipmentSnapshot
from app.db.session import SessionLocal
from app.services.copilot import explain_agent_state
from app.services.feature_state import cache_shipment_snapshot, list_shipment_snapshots
from app.services.notifications import send_notification
from app.services.observability import latency_timer, metrics
from app.services.risk_scoring import RiskFactor, risk_scoring_service
from app.services.route_intelligence import (
    RoutePlanResult,
    persist_route_plan,
    route_intelligence_service,
)
from app.websocket.broadcaster import broadcaster

logger = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    shipment_id: str
    dri_score: int
    dri_level: str
    shap_factors: list[dict[str, Any]]
    disruption_type: str | None
    candidate_routes: list[dict[str, Any]]
    lp_valid_routes: list[dict[str, Any]]
    selected_route: dict[str, Any] | None
    action_taken: str
    roi_defended_usd: float
    copilot_explanation: str | None
    ops_override_active: bool
    approval_status: str
    route_selected_id: int | None
    rejected_routes: list[dict[str, Any]]
    replay_data: dict[str, Any]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _dri_level(dri: int) -> str:
    if dri >= settings.dri_threshold_red:
        return "red"
    if dri >= settings.dri_threshold_orange:
        return "orange"
    if dri >= settings.dri_threshold_yellow:
        return "yellow"
    return "green"


def _factor_to_dict(factor: RiskFactor) -> dict[str, Any]:
    return {
        "feature": factor.feature,
        "shap_value": factor.shap_value,
        "direction": factor.direction,
    }


def _route_to_dict(route: RouteRecord | dict[str, Any]) -> dict[str, Any]:
    if isinstance(route, dict):
        return route
    return {
        "id": route.id,
        "path": route.path,
        "waypoints": route.waypoints,
        "cost_usd": route.cost_usd,
        "eta_hours": route.eta_hours,
        "risk_score": route.risk_score,
        "carbon_kg": route.carbon_kg,
        "lp_score": route.lp_score,
        "constraints_applied": route.constraints_applied,
        "selected": route.selected,
    }


def _plan_route_dicts(plan: RoutePlanResult) -> list[dict[str, Any]]:
    return [
        {
            "path": option.path,
            "waypoints": option.waypoints,
            "cost_usd": option.cost_usd,
            "eta_hours": option.eta_hours,
            "risk_score": option.risk_score,
            "carbon_kg": option.carbon_kg,
            "tariff_delta_usd": option.tariff_delta_usd,
            "policy_penalty_usd": option.policy_penalty_usd,
            "composite_score": option.composite_score,
            "lp_score": option.lp_score,
            "constraints_applied": option.constraints_applied,
            "selected": option.path == plan.selected_path,
        }
        for option in plan.top_routes
    ]


def _rejected_route_dicts(plan: RoutePlanResult) -> list[dict[str, Any]]:
    return [{"path": route.path, "reasons": route.reasons} for route in plan.rejected_routes]


def _active_override(db: Session, shipment_key: str) -> AgentOverride | None:
    override = db.scalar(
        select(AgentOverride).where(
            AgentOverride.shipment_key == shipment_key,
            AgentOverride.active.is_(True),
        )
    )
    if override is None:
        return None
    if override.expires_at and _as_aware(override.expires_at) <= _now():
        override.active = False
        db.add(override)
        db.flush()
        return None
    return override


def set_agent_override(
    db: Session,
    shipment_key: str,
    reason: str,
    requested_by: str,
    expires_minutes: int | None = None,
) -> AgentOverride:
    override = db.scalar(select(AgentOverride).where(AgentOverride.shipment_key == shipment_key))
    expires_at = _now() + timedelta(minutes=expires_minutes) if expires_minutes else None
    if override is None:
        override = AgentOverride(
            shipment_key=shipment_key,
            reason=reason,
            requested_by=requested_by,
            expires_at=expires_at,
            active=True,
        )
    else:
        override.reason = reason
        override.requested_by = requested_by
        override.expires_at = expires_at
        override.active = True
    db.add(override)
    db.flush()
    broadcaster.publish(
        "agent_override_set",
        {
            "shipment_key": shipment_key,
            "reason": reason,
            "requested_by": requested_by,
            "expires_at": expires_at.isoformat() if expires_at else None,
        },
    )
    return override


def clear_agent_override(db: Session, shipment_key: str, requested_by: str) -> AgentOverride | None:
    override = db.scalar(select(AgentOverride).where(AgentOverride.shipment_key == shipment_key))
    if override is None:
        return None
    override.active = False
    override.requested_by = requested_by
    db.add(override)
    db.flush()
    broadcaster.publish(
        "agent_override_cleared",
        {"shipment_key": shipment_key, "requested_by": requested_by},
    )
    return override


def assess_risk(state: AgentState) -> AgentState:
    if state.get("ops_override_active"):
        state["action_taken"] = "override_blocked"
        state["approval_status"] = "blocked_by_override"
        return state

    dri_score = int(state["dri_score"])
    if dri_score >= settings.agent_reroute_threshold:
        state["action_taken"] = "reroute"
    elif dri_score >= settings.dri_threshold_orange:
        state["action_taken"] = "monitor"
    else:
        state["action_taken"] = "pass"
    state["approval_status"] = "auto_approved"
    return state


def compute_candidate_routes(
    state: AgentState,
    snapshot: ShipmentSnapshot,
) -> tuple[AgentState, RoutePlanResult | None]:
    if state.get("action_taken") not in {"reroute", "monitor"}:
        state["candidate_routes"] = []
        state["lp_valid_routes"] = []
        state["rejected_routes"] = []
        return state, None

    try:
        plan = route_intelligence_service.reroute_shipment(snapshot=snapshot, max_paths=12, top_k=3)
    except ValueError as exc:
        state["action_taken"] = "escalate"
        state["candidate_routes"] = []
        state["lp_valid_routes"] = []
        state["rejected_routes"] = [{"path": [], "reasons": [str(exc)]}]
        return state, None

    state["candidate_routes"] = _plan_route_dicts(plan) + _rejected_route_dicts(plan)
    state["lp_valid_routes"] = _plan_route_dicts(plan)
    state["rejected_routes"] = _rejected_route_dicts(plan)
    if state.get("action_taken") == "reroute" and not plan.top_routes:
        state["action_taken"] = "escalate"
    return state, plan


def select_route(state: AgentState, plan: RoutePlanResult | None) -> AgentState:
    if state.get("action_taken") != "reroute" or plan is None or not plan.top_routes:
        state["selected_route"] = None
        state["route_selected_id"] = None
        return state

    selected = next(
        (route for route in _plan_route_dicts(plan) if route["path"] == plan.selected_path),
        _plan_route_dicts(plan)[0],
    )
    state["selected_route"] = selected
    return state


def execute_reroute(
    db: Session,
    state: AgentState,
    snapshot: ShipmentSnapshot,
    plan: RoutePlanResult | None,
) -> AgentState:
    if plan is not None and plan.top_routes:
        records = persist_route_plan(db, plan)
        selected_record = next((record for record in records if record.selected), records[0])
        state["route_selected_id"] = selected_record.id
        if state.get("action_taken") == "reroute":
            state["selected_route"] = _route_to_dict(selected_record)
            feature_vector = (
                snapshot.feature_vector if isinstance(snapshot.feature_vector, dict) else {}
            )
            feature_vector["current_route"] = selected_record.path
            feature_vector["current_waypoints"] = selected_record.waypoints
            feature_vector["status"] = "rerouted"
            feature_vector["route_updated_at"] = _now().isoformat()
            snapshot.feature_vector = feature_vector
            snapshot.provisional_dri = int(state["dri_score"])
            db.add(snapshot)
            db.flush()
            cache_shipment_snapshot(snapshot)
    return state


def notify_stakeholders(db: Session, state: AgentState) -> AgentState:
    action_taken = str(state.get("action_taken"))
    if action_taken in {"reroute", "monitor", "escalate", "override_blocked"}:
        send_notification(
            db,
            shipment_key=str(state["shipment_id"]),
            channel="ops_dashboard",
            payload={
                "action_taken": action_taken,
                "dri_score": state["dri_score"],
                "selected_route": state.get("selected_route"),
                "approval_status": state.get("approval_status"),
            },
        )
    return state


def get_copilot_explanation(state: AgentState) -> AgentState:
    if state.get("action_taken") in {"reroute", "escalate"}:
        answer = explain_agent_state(state)
        state["copilot_explanation"] = answer.answer
    else:
        state["copilot_explanation"] = None
    return state


def log_action(db: Session, state: AgentState) -> AgentAction:
    shap_factors = state.get("shap_factors") or []
    top_factor = shap_factors[0]["feature"] if shap_factors else None
    selected_route = state.get("selected_route") or {}
    constraints = selected_route.get("constraints_applied") or []
    action = AgentAction(
        shipment_key=str(state["shipment_id"]),
        action_type=str(state.get("action_taken", "pass")),
        dri_at_action=int(state.get("dri_score", 0)),
        route_selected_id=state.get("route_selected_id"),
        shap_top_factor=top_factor,
        lp_constraints_count=len(constraints),
        roi_defended_usd=float(state.get("roi_defended_usd", 0.0)),
        approval_status=str(state.get("approval_status", "auto_approved")),
        overridden_by_ops=bool(state.get("ops_override_active", False)),
        replay_data=state.get("replay_data") or {},
        state_snapshot=dict(state),
    )
    db.add(action)
    db.flush()
    metrics.increment("agent_actions_total")
    metrics.increment(f"agent_actions_{action.action_type}_total")
    broadcaster.publish(
        "agent_action",
        {
            "id": action.id,
            "shipment_key": action.shipment_key,
            "action_type": action.action_type,
            "dri_at_action": action.dri_at_action,
            "route_selected_id": action.route_selected_id,
            "roi_defended_usd": action.roi_defended_usd,
            "executed_at": action.executed_at.isoformat(),
        },
    )
    return action


def run_agent_for_shipment(
    db: Session,
    shipment_key: str,
    roi_context_usd: float = 0.0,
    replay_data: dict[str, Any] | None = None,
) -> AgentState:
    with latency_timer("agent_run"):
        snapshot = db.scalar(
            select(ShipmentSnapshot).where(ShipmentSnapshot.shipment_key == shipment_key)
        )
        if snapshot is None:
            raise ValueError(f"Shipment snapshot not found for key '{shipment_key}'")

        score = risk_scoring_service.score_snapshot(snapshot, top_k=5)
        override = _active_override(db, shipment_key)
        shap_factors = [_factor_to_dict(factor) for factor in score.top_factors]
        state: AgentState = {
            "shipment_id": shipment_key,
            "dri_score": score.dri,
            "dri_level": _dri_level(score.dri),
            "shap_factors": shap_factors,
            "disruption_type": snapshot.last_event_type,
            "candidate_routes": [],
            "lp_valid_routes": [],
            "selected_route": None,
            "action_taken": "pass",
            "roi_defended_usd": round(roi_context_usd * 0.72, 2) if roi_context_usd else 0.0,
            "copilot_explanation": None,
            "ops_override_active": override is not None,
            "approval_status": "pending",
            "route_selected_id": None,
            "rejected_routes": [],
            "replay_data": replay_data or {},
        }

        state = assess_risk(state)
        plan: RoutePlanResult | None = None
        state, plan = compute_candidate_routes(state, snapshot)
        state = select_route(state, plan)
        state = execute_reroute(db, state, snapshot, plan)
        state = notify_stakeholders(db, state)
        state = get_copilot_explanation(state)
        log_action(db, state)
        return state


def run_agent_tick(db: Session, limit: int = 100) -> list[AgentState]:
    states: list[AgentState] = []
    for snapshot in list_shipment_snapshots(db, limit=limit):
        states.append(run_agent_for_shipment(db, snapshot.shipment_key))
    return states


def list_agent_actions(
    db: Session,
    shipment_key: str | None = None,
    limit: int = 50,
) -> list[AgentAction]:
    query = select(AgentAction)
    if shipment_key:
        query = query.where(AgentAction.shipment_key == shipment_key)
    query = query.order_by(desc(AgentAction.executed_at), desc(AgentAction.id)).limit(limit)
    return list(db.scalars(query).all())


async def agent_tick_loop() -> None:
    await asyncio.sleep(settings.agent_tick_seconds)
    while True:
        try:
            with SessionLocal() as db:
                run_agent_tick(db)
                db.commit()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover
            logger.warning("Agent tick failed: %s", exc)
        await asyncio.sleep(settings.agent_tick_seconds)
