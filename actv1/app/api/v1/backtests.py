from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_roles
from app.db.session import get_db
from app.services.backtesting import list_backtest_results, run_ever_given_backtest

router = APIRouter(prefix="/backtests", tags=["backtests"])


class BacktestResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scenario: str
    flag_time: datetime | None
    grounding_time: datetime
    industry_response_time: datetime
    precursa_lead_minutes: float | None
    timeline: list[dict[str, Any]]
    created_at: datetime


@router.post("/ever-given", response_model=BacktestResultResponse)
def run_ever_given_endpoint(
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager")),
) -> BacktestResultResponse:
    result = run_ever_given_backtest(db)
    db.commit()
    db.refresh(result)
    return BacktestResultResponse.model_validate(result)


@router.get("", response_model=list[BacktestResultResponse])
def list_backtests_endpoint(
    scenario: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager", "auditor")),
) -> list[BacktestResultResponse]:
    results = list_backtest_results(db, scenario=scenario, limit=limit)
    return [BacktestResultResponse.model_validate(result) for result in results]
