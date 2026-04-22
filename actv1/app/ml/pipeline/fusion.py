def fuse_dri(context_score: float, temporal_score: float, anomaly_score: float) -> int:
    """
    DRI = 0.5 * context + 0.3 * temporal + 0.2 * anomaly
    Returns integer 0-100.
    """
    # Ensure inputs are valid
    c = context_score if context_score is not None else 0.3
    t = temporal_score if temporal_score is not None else 0.2
    a = anomaly_score if anomaly_score is not None else 0.1
    
    dri = (0.5 * c + 0.3 * t + 0.2 * a) * 100
    return int(round(max(0, min(100, dri))))
