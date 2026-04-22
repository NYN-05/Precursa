from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import AgentAction, CopilotInteraction, RouteRecord, ShipmentSnapshot

SYSTEM_PROMPT = """
You are Precursa's AI copilot for supply chain operations.
STRICT RULE: Only reference factors explicitly listed in the SHAP values or LP constraints
provided. Never infer, assume, or add context not present in the data.
Keep explanations to 2-3 sentences. Be specific and factual.
""".strip()


@dataclass(frozen=True)
class CopilotAnswer:
    answer: str
    grounded_on: list[str]
    shap_factors_used: list[dict[str, Any]]
    route_constraints_used: list[str]


def _factor_name(factor: dict[str, Any]) -> str:
    return str(factor.get("feature") or factor.get("name") or "").strip()


def _factor_value(factor: dict[str, Any]) -> float:
    value = factor.get("shap_value", factor.get("value", 0.0))
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _latest_selected_route(db: Session, shipment_key: str) -> RouteRecord | None:
    return db.scalar(
        select(RouteRecord)
        .where(RouteRecord.shipment_key == shipment_key, RouteRecord.selected.is_(True))
        .order_by(desc(RouteRecord.created_at), desc(RouteRecord.id))
    )


def _latest_action(db: Session, shipment_key: str) -> AgentAction | None:
    return db.scalar(
        select(AgentAction)
        .where(AgentAction.shipment_key == shipment_key)
        .order_by(desc(AgentAction.executed_at), desc(AgentAction.id))
    )


def explain_agent_state(state: dict[str, Any]) -> CopilotAnswer:
    shap_factors = list(state.get("shap_factors") or [])[:3]
    selected_route = state.get("selected_route") or {}
    constraints = list(selected_route.get("constraints_applied") or [])
    grounded_on = [_factor_name(factor) for factor in shap_factors if _factor_name(factor)]
    grounded_on.extend(constraints)

    route_path = selected_route.get("path") or []
    action_taken = str(state.get("action_taken") or "monitor")
    shipment_key = str(state.get("shipment_id") or state.get("shipment_key") or "unknown shipment")
    dri_score = int(state.get("dri_score") or state.get("dri") or 0)

    factor_clauses = []
    for factor in shap_factors:
        name = _factor_name(factor)
        if not name:
            continue
        direction = str(factor.get("direction") or "increase")
        factor_clauses.append(f"{name} ({direction}, {_factor_value(factor):+.3f})")

    if route_path and action_taken == "reroute":
        first_sentence = (
            f"Shipment {shipment_key} was rerouted at DRI {dri_score}/100 because "
            f"the computed factors were {', '.join(factor_clauses) or 'available risk factors'}."
        )
        second_sentence = (
            f"The selected path {' -> '.join(route_path)} satisfies the LP checks "
            f"{', '.join(constraints) or 'none'}."
        )
    elif action_taken == "escalate":
        first_sentence = (
            f"Shipment {shipment_key} was escalated at DRI {dri_score}/100 because "
            f"no candidate route satisfied the provided LP constraints."
        )
        second_sentence = (
            f"The grounded factors were {', '.join(factor_clauses) or 'not available'}."
        )
    else:
        first_sentence = (
            f"Shipment {shipment_key} is in {action_taken} mode at DRI {dri_score}/100."
        )
        second_sentence = (
            f"The grounded factors are {', '.join(factor_clauses) or 'not available'}."
        )

    return CopilotAnswer(
        answer=f"{first_sentence} {second_sentence}",
        grounded_on=grounded_on,
        shap_factors_used=shap_factors,
        route_constraints_used=constraints,
    )


def answer_question(
    db: Session,
    shipment_key: str,
    question: str,
    persist: bool = True,
) -> CopilotAnswer:
    snapshot = db.scalar(
        select(ShipmentSnapshot).where(ShipmentSnapshot.shipment_key == shipment_key)
    )
    action = _latest_action(db, shipment_key)
    route = _latest_selected_route(db, shipment_key)

    shap_factors: list[dict[str, Any]] = []
    dri_score = 0
    action_taken = "monitor"
    if action is not None:
        state_snapshot = action.state_snapshot if isinstance(action.state_snapshot, dict) else {}
        shap_factors = list(state_snapshot.get("shap_factors") or [])
        dri_score = action.dri_at_action
        action_taken = action.action_type

    if not shap_factors and snapshot is not None:
        feature_vector = (
            snapshot.feature_vector if isinstance(snapshot.feature_vector, dict) else {}
        )
        shap_factors = list(feature_vector.get("shap_factors") or [])
        dri_score = snapshot.provisional_dri

    selected_route = {}
    if route is not None:
        selected_route = {
            "path": route.path,
            "constraints_applied": route.constraints_applied,
        }

    answer = explain_agent_state(
        {
            "shipment_id": shipment_key,
            "dri_score": dri_score,
            "action_taken": action_taken,
            "shap_factors": shap_factors,
            "selected_route": selected_route,
            "question": question,
        }
    )

    if persist:
        record = CopilotInteraction(
            shipment_key=shipment_key,
            question=question,
            answer=answer.answer,
            grounded_on=answer.grounded_on,
            shap_factors_used=answer.shap_factors_used,
            route_constraints_used=answer.route_constraints_used,
        )
        db.add(record)
        db.flush()

    return answer
