from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_roles
from app.db.models import CopilotInteraction, WhatIfSimulation
from app.db.session import get_db
from app.services.copilot import answer_question
from app.services.simulation import run_what_if_simulation

router = APIRouter(prefix="/copilot", tags=["copilot"])


class CopilotRequest(BaseModel):
    shipment_key: str
    question: str


class CopilotResponse(BaseModel):
    answer: str
    grounded_on: list[str]
    shap_factors_used: list[dict[str, Any]]
    route_constraints_used: list[str]


class WhatIfRequest(BaseModel):
    shipment_key: str
    scenario: dict[str, Any]


class WhatIfResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shipment_key: str
    scenario: dict[str, Any]
    projected_dri: int
    projected_routes: list[dict[str, Any]]
    explanation: str
    created_at: datetime


class CopilotInteractionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shipment_key: str
    question: str
    answer: str
    grounded_on: list[str]
    shap_factors_used: list[dict[str, Any]]
    route_constraints_used: list[str]
    created_at: datetime


@router.post("", response_model=CopilotResponse)
def ask_copilot_endpoint(
    request: CopilotRequest,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager", "auditor")),
) -> CopilotResponse:
    answer = answer_question(
        db,
        shipment_key=request.shipment_key,
        question=request.question,
        persist=True,
    )
    db.commit()
    return CopilotResponse(
        answer=answer.answer,
        grounded_on=answer.grounded_on,
        shap_factors_used=answer.shap_factors_used,
        route_constraints_used=answer.route_constraints_used,
    )


@router.post("/what-if", response_model=WhatIfResponse)
def what_if_endpoint(
    request: WhatIfRequest,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager")),
) -> WhatIfResponse:
    try:
        record = run_what_if_simulation(db, shipment_key=request.shipment_key, scenario=request.scenario)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    db.commit()
    db.refresh(record)
    return WhatIfResponse.model_validate(record)
