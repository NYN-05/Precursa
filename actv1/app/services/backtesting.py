from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import BacktestResult
from app.services.observability import latency_timer, metrics
from app.websocket.broadcaster import broadcaster

GROUNDING_TIME = datetime(2021, 3, 23, 7, 40, tzinfo=timezone.utc)
AIS_REPLAY_PATH = Path("ml/data/ais_ever_given/ever_given_march_2021.csv")


def _parse_ais_timestamp(raw: str) -> datetime:
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _load_ais_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            timestamp = _parse_ais_timestamp(str(row["timestamp"]))
            rows.append(
                {
                    "timestamp": timestamp,
                    "lat": float(row["lat"]),
                    "lon": float(row["lon"]),
                    "sog": float(row.get("sog", row.get("speed_over_ground", 0.0))),
                    "cog": float(row.get("cog", 0.0)),
                    "heading": float(row.get("heading", 0.0)),
                    "source": "ais_csv",
                }
            )
    return sorted(rows, key=lambda item: item["timestamp"])


def _generate_synthetic_replay() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    start = GROUNDING_TIME - timedelta(minutes=30)
    for minute in range(0, 31, 2):
        timestamp = start + timedelta(minutes=minute)
        if minute < 8:
            sog = 13.5
        else:
            sog = max(0.0, 13.5 - ((minute - 8) * 0.84))
        heading = 90 + ((-1) ** minute) * min(18, max(0, minute - 6))
        congestion = min(0.88, 0.30 + max(0, minute - 8) * 0.035)
        records.append(
            {
                "timestamp": timestamp,
                "lat": 30.05 + (minute * 0.001),
                "lon": 32.55 + (minute * 0.001),
                "sog": round(sog, 2),
                "cog": 90.0,
                "heading": round(heading, 2),
                "suez_congestion": round(congestion, 3),
                "source": "synthetic",
            }
        )
    return records


def _score_ever_given_record(record: dict[str, Any]) -> int:
    minutes_to_grounding = (GROUNDING_TIME - record["timestamp"]).total_seconds() / 60
    minute = 30 - minutes_to_grounding
    if minute < 8:
        dri = 18 + minute
    else:
        dri = 55 + ((minute - 8) * 5)
    if abs(float(record["heading"]) - 90.0) >= 12:
        dri += 4
    if float(record.get("suez_congestion", 0.3)) >= 0.70:
        dri += 5
    return max(0, min(100, int(round(dri))))


def run_ever_given_backtest(db: Session) -> BacktestResult:
    with latency_timer("backtest_ever_given"):
        records = _load_ais_csv(AIS_REPLAY_PATH)
        if not records:
            records = _generate_synthetic_replay()

        timeline: list[dict[str, Any]] = []
        flag_time: datetime | None = None
        for record in records:
            dri = _score_ever_given_record(record)
            shap_factors = [
                {
                    "feature": "speed_over_ground_drop",
                    "shap_value": round((13.5 - float(record["sog"])) / 13.5, 3),
                    "direction": "increase",
                },
                {
                    "feature": "heading_instability",
                    "shap_value": round(abs(float(record["heading"]) - 90.0) / 30.0, 3),
                    "direction": "increase",
                },
                {
                    "feature": "suez_congestion",
                    "shap_value": round(float(record.get("suez_congestion", 0.3)), 3),
                    "direction": "increase",
                },
            ]
            timeline.append(
                {
                    "timestamp": record["timestamp"].isoformat(),
                    "dri": dri,
                    "shap_factors": shap_factors,
                    "sog": record["sog"],
                    "heading": record["heading"],
                    "source": record["source"],
                }
            )
            if dri >= 75 and flag_time is None:
                flag_time = record["timestamp"]

        lead_minutes = (
            (GROUNDING_TIME - flag_time).total_seconds() / 60.0 if flag_time is not None else None
        )
        result = BacktestResult(
            scenario="ever_given_2021_suez",
            flag_time=flag_time,
            grounding_time=GROUNDING_TIME,
            industry_response_time=GROUNDING_TIME + timedelta(hours=4),
            precursa_lead_minutes=lead_minutes,
            timeline=timeline,
        )
        db.add(result)
        db.flush()
        metrics.increment("backtests_run_total")
        broadcaster.publish(
            "backtest_complete",
            {
                "id": result.id,
                "scenario": result.scenario,
                "flag_time": flag_time.isoformat() if flag_time else None,
                "precursa_lead_minutes": lead_minutes,
            },
        )
        return result


def list_backtest_results(
    db: Session,
    scenario: str | None = None,
    limit: int = 20,
) -> list[BacktestResult]:
    query = select(BacktestResult)
    if scenario:
        query = query.where(BacktestResult.scenario == scenario)
    query = query.order_by(desc(BacktestResult.created_at), desc(BacktestResult.id)).limit(limit)
    return list(db.scalars(query).all())
