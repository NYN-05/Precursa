from typing import Any, TypedDict
import logging

from .feature_engineering import build_feature_vector
from .inference import run_xgb, run_iso, run_temporal_fallback
from .fusion import fuse_dri
from .explain import explain_dri

logger = logging.getLogger(__name__)

class MLPipelineOutput(TypedDict):
    dri: int
    context_score: float
    temporal_score: float
    anomaly_score: float
    top_features: list[str]
    is_fallback: bool

def compute_dri_pipeline(snapshot_data: dict[str, Any], external_data: dict[str, Any]) -> MLPipelineOutput:
    """
    Main entry point for ML-driven DRI computation.
    """
    try:
        # 1. Feature Engineering
        features = build_feature_vector(snapshot_data, external_data)
        
        # 2. Inference
        context = run_xgb(features)
        anomaly = run_iso(features)
        temporal = run_temporal_fallback(features) # Rule-based/fallback
        
        is_fallback = False
        # If models failed, use rule-based fallbacks for everything
        if context is None:
            context = (features[0]*0.3 + features[1]*0.2 + features[4]*0.25 + features[3]*0.25)
            is_fallback = True
        if anomaly is None:
            anomaly = features[7]*0.7 + 0.1
            is_fallback = True
            
        # 3. Fusion
        dri = fuse_dri(context, temporal, anomaly)
        
        # 4. Explainability
        top_features = explain_dri(features)
        
        return {
            "dri": dri,
            "context_score": round(context, 4),
            "temporal_score": round(temporal, 4),
            "anomaly_score": round(anomaly, 4),
            "top_features": top_features,
            "is_fallback": is_fallback
        }
        
    except Exception as e:
        logger.error(f"ML Pipeline failed: {e}")
        # Global fallback
        return {
            "dri": 35, # Safe average
            "context_score": 0.3,
            "temporal_score": 0.3,
            "anomaly_score": 0.2,
            "top_features": ["system_error"],
            "is_fallback": True
        }
