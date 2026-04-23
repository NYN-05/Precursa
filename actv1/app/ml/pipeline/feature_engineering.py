from typing import Any

FEATURE_ORDER = [
    'port_congestion', 'weather', 'carrier_reliability', 'customs_delay',
    'geo_risk', 'trend_congestion', 'trend_delay', 'route_variability'
]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _status_risk(status: Any) -> float:
    normalized = str(status or "").strip().lower()
    mapping = {
        "blocked": 1.0,
        "critical": 0.95,
        "delayed": 0.8,
        "inspection": 0.55,
        "in_transit": 0.25,
        "cleared": 0.12,
        "on_time": 0.08,
    }
    return mapping.get(normalized, 0.2)

def build_feature_vector(snapshot_data: dict[str, Any], external_data: dict[str, Any]) -> list[float]:
    """
    Transforms raw shipment data and external signals into a normalized numeric vector.
    """
    fv = snapshot_data.get('feature_vector', {})
    ext = external_data or {}

    if not isinstance(fv, dict):
        fv = {}

    status_risk = _status_risk(fv.get('status'))
    delay_norm = _clamp01(_safe_float(fv.get('delay_hours'), 0.0) / 72.0)
    impact_norm = _clamp01(
        _safe_float(
            fv.get('impact_score'),
            _safe_float(fv.get('avg_severity'), snapshot_data.get('avg_severity', 0.0)),
        )
    )
    severity_norm = _clamp01(_safe_float(fv.get('severity_index'), impact_norm))

    base_port_congestion = _safe_float(ext.get('port_congestion'), 0.3)
    base_weather = _safe_float(ext.get('weather_severity', ext.get('weather')), 0.2)
    base_carrier = _safe_float(ext.get('carrier_reliability'), 0.85)
    base_customs_delay = _safe_float(ext.get('customs_delay'), 0.15)
    base_geo_risk = _safe_float(ext.get('geo_risk'), 0.1)
    base_trend_congestion = _safe_float(ext.get('trend_congestion'), 0.25)
    base_trend_delay = _safe_float(ext.get('trend_delay'), 0.2)
    base_route_variability = _safe_float(ext.get('route_variability'), 0.12)

    customs_delay = max(base_customs_delay, delay_norm, impact_norm * 0.9, status_risk * 0.85)
    geo_risk = max(base_geo_risk, impact_norm, status_risk * 0.8)
    weather = max(base_weather, severity_norm * 0.7)
    port_congestion = max(base_port_congestion, status_risk * 0.75, delay_norm * 0.4)

    if status_risk >= 0.7:
        carrier_reliability = min(base_carrier, 0.55)
    elif delay_norm >= 0.5:
        carrier_reliability = min(base_carrier, 0.7)
    else:
        carrier_reliability = base_carrier

    trend_congestion = max(base_trend_congestion, delay_norm * 0.6)
    trend_delay = max(base_trend_delay, delay_norm * 0.7, status_risk * 0.3)
    route_variability = max(base_route_variability, status_risk * 0.25)
    
    # Mapping and normalization
    data = {
        'port_congestion': port_congestion,
        'weather': weather,
        'carrier_reliability': carrier_reliability,
        'customs_delay': customs_delay,
        'geo_risk': geo_risk,
        'trend_congestion': trend_congestion,
        'trend_delay': trend_delay,
        'route_variability': route_variability,
    }
    
    return [_clamp01(data[k]) for k in FEATURE_ORDER]
