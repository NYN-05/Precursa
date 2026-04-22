from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_roles
from app.db.models import AgentAction, NotificationRecord, RouteRecord, ShipmentSnapshot
from app.db.session import get_db
from app.websocket.broadcaster import broadcaster

router = APIRouter(tags=["realtime"])


class DashboardSummary(BaseModel):
    shipments: list[dict[str, Any]]
    recent_agent_actions: list[dict[str, Any]]
    recent_notifications: list[dict[str, Any]]
    recent_routes: list[dict[str, Any]]
    websocket_connections: int


def _snapshot_row(snapshot: ShipmentSnapshot) -> dict[str, Any]:
    return {
        "shipment_key": snapshot.shipment_key,
        "provisional_dri": snapshot.provisional_dri,
        "event_count": snapshot.event_count,
        "last_source": snapshot.last_source,
        "last_event_type": snapshot.last_event_type,
        "feature_vector": snapshot.feature_vector,
        "updated_at": snapshot.updated_at.isoformat(),
    }


@router.websocket("/ws/live")
async def live_socket(websocket: WebSocket) -> None:
    await broadcaster.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.disconnect(websocket)


@router.get("/realtime/dashboard", response_model=DashboardSummary)
def dashboard_summary_endpoint(
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager", "auditor")),
) -> DashboardSummary:
    snapshots = list(
        db.scalars(
            select(ShipmentSnapshot)
            .order_by(desc(ShipmentSnapshot.updated_at), desc(ShipmentSnapshot.id))
            .limit(50)
        ).all()
    )
    actions = list(
        db.scalars(
            select(AgentAction)
            .order_by(desc(AgentAction.executed_at), desc(AgentAction.id))
            .limit(20)
        ).all()
    )
    notifications = list(
        db.scalars(
            select(NotificationRecord)
            .order_by(desc(NotificationRecord.created_at), desc(NotificationRecord.id))
            .limit(20)
        ).all()
    )
    routes = list(
        db.scalars(
            select(RouteRecord)
            .order_by(desc(RouteRecord.created_at), desc(RouteRecord.id))
            .limit(20)
        ).all()
    )

    return DashboardSummary(
        shipments=[_snapshot_row(snapshot) for snapshot in snapshots],
        recent_agent_actions=[
            {
                "id": action.id,
                "shipment_key": action.shipment_key,
                "action_type": action.action_type,
                "dri_at_action": action.dri_at_action,
                "shap_top_factor": action.shap_top_factor,
                "roi_defended_usd": action.roi_defended_usd,
                "executed_at": action.executed_at.isoformat(),
            }
            for action in actions
        ],
        recent_notifications=[
            {
                "id": notification.id,
                "shipment_key": notification.shipment_key,
                "channel": notification.channel,
                "recipient": notification.recipient,
                "status": notification.status,
                "created_at": notification.created_at.isoformat(),
            }
            for notification in notifications
        ],
        recent_routes=[
            {
                "id": route.id,
                "shipment_key": route.shipment_key,
                "path": route.path,
                "selected": route.selected,
                "lp_score": route.lp_score,
                "created_at": route.created_at.isoformat(),
            }
            for route in routes
        ],
        websocket_connections=broadcaster.connection_count,
    )
