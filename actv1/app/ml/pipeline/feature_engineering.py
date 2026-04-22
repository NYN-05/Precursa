from typing import Any

FEATURE_ORDER = [
    'port_congestion', 'weather', 'carrier_reliability', 'customs_delay',
    'geo_risk', 'trend_congestion', 'trend_delay', 'route_variability'
]

def build_feature_vector(snapshot_data: dict[str, Any], external_data: dict[str, Any]) -> list[float]:
    """
    Transforms raw shipment data and external signals into a normalized numeric vector.
    """
    fv = snapshot_data.get('feature_vector', {})
    ext = external_data or {}
    
    # Mapping and normalization
    data = {
        'port_congestion': float(ext.get('port_congestion', 0.3)),
        'weather': float(ext.get('weather_severity', ext.get('weather', 0.2))),
        'carrier_reliability': float(ext.get('carrier_reliability', 0.85)),
        'customs_delay': float(ext.get('customs_delay', 0.15)),
        'geo_risk': float(ext.get('geo_risk', 0.1)),
        'trend_congestion': float(ext.get('trend_congestion', 0.25)),
        'trend_delay': float(ext.get('trend_delay', 0.2)),
        'route_variability': float(ext.get('route_variability', 0.12))
    }
    
    return [max(0.0, min(1.0, data[k])) for k in FEATURE_ORDER]
