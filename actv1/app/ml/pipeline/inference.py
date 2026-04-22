import numpy as np
import pandas as pd
from ..loader import load_xgb_model, load_iso_model
from .feature_engineering import FEATURE_ORDER

# Lazy load models
_xgb = load_xgb_model()
_iso = load_iso_model()

def run_xgb(features: list[float]) -> float | None:
    if _xgb is None:
        return None
    
    # XGB was trained on: ['port_congestion', 'weather', 'geo_risk', 'customs_delay']
    # Indices in FEATURE_ORDER: 0, 1, 4, 3
    xgb_features = [features[0], features[1], features[4], features[3]]
    
    try:
        pred = _xgb.predict([xgb_features])[0]
        return float(max(0.0, min(1.0, pred)))
    except:
        return None

def run_iso(features: list[float]) -> float | None:
    if _iso is None:
        return None
    
    try:
        # iso.score_samples returns values where lower is more anomalous
        # Range is typically roughly [-0.4, 0.4] for sklearn
        raw_score = _iso.score_samples([features])[0]
        # Normalize to 0-1 (higher = more anomalous/risky)
        # Assuming -0.5 is high risk, 0.5 is low risk
        norm_score = (0.5 - raw_score) / 1.0
        return float(max(0.0, min(1.0, norm_score)))
    except:
        return None

def run_temporal_fallback(features: list[float]) -> float:
    # Blend of carrier_reliability (idx 2), trend_congestion (idx 5), trend_delay (idx 6)
    # Formula from generate_dataset.py: 0.4 * (1 - carrier) + 0.3 * trend_c + 0.3 * trend_d
    carrier = features[2]
    trend_c = features[5]
    trend_d = features[6]
    
    temporal = 0.4 * (1 - carrier) + 0.3 * trend_c + 0.3 * trend_d
    return float(max(0.0, min(1.0, temporal)))
