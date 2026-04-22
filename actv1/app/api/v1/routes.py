from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_roles
from app.db.session import get_db
from app.services.feature_state import get_shipment_snapshot
from app.services.route_intelligence import (
    RejectedRoute,
    RouteOption,
    RoutePlanResult,
    persist_route_plan,
    route_intelligence_service,
)

router = APIRouter(prefix="/routes", tags=["routes"])


class RouteOptionResponse(BaseModel):
    path: list[str]
    waypoints: list[dict[str, float | str]]
    cost_usd: float
    eta_hours: float
    risk_score: float
    carbon_kg: float
    tariff_delta_usd: float
    policy_penalty_usd: float
    composite_score: float
    lp_score: float
    constraints_applied: list[str]
    selected_best: bool


class RejectedRouteResponse(BaseModel):
    path: list[str]
    reasons: list[str]


class RoutePlanResponse(BaseModel):
    shipment_key: str
    source_port: str
    destination_port: str
    solver_status: str
    message: str
    top_routes: list[RouteOptionResponse]
    rejected_routes: list[RejectedRouteResponse]


def _to_option_response(
    option: RouteOption,
    selected_path: list[str] | None,
) -> RouteOptionResponse:
    return RouteOptionResponse(
        path=option.path,
        waypoints=option.waypoints,
        cost_usd=option.cost_usd,
        eta_hours=option.eta_hours,
        risk_score=option.risk_score,
        carbon_kg=option.carbon_kg,
        tariff_delta_usd=option.tariff_delta_usd,
        policy_penalty_usd=option.policy_penalty_usd,
        composite_score=option.composite_score,
        lp_score=option.lp_score,
        constraints_applied=option.constraints_applied,
        selected_best=(selected_path == option.path),
    )


def _to_rejected_response(route: RejectedRoute) -> RejectedRouteResponse:
    return RejectedRouteResponse(path=route.path, reasons=route.reasons)


def _to_plan_response(plan: RoutePlanResult) -> RoutePlanResponse:
    return RoutePlanResponse(
        shipment_key=plan.shipment_key,
        source_port=plan.source_port,
        destination_port=plan.destination_port,
        solver_status=plan.solver_status,
        message=plan.message,
        top_routes=[_to_option_response(option, plan.selected_path) for option in plan.top_routes],
        rejected_routes=[_to_rejected_response(route) for route in plan.rejected_routes],
    )


@router.post("/reroute/{shipment_key}", response_model=RoutePlanResponse)
def reroute_shipment_endpoint(
    shipment_key: str,
    max_paths: int = Query(default=12, ge=1, le=30),
    top_k: int = Query(default=3, ge=1, le=10),
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager")),
) -> RoutePlanResponse:
    snapshot = get_shipment_snapshot(db, shipment_key=shipment_key)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment snapshot not found for key '{shipment_key}'",
        )

    try:
        plan = route_intelligence_service.reroute_shipment(
            snapshot=snapshot,
            max_paths=max_paths,
            top_k=top_k,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    persist_route_plan(db, plan)
    db.commit()

    return _to_plan_response(plan)
