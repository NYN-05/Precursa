from .feature_engineering import FEATURE_ORDER

def explain_dri(features: list[float]) -> list[str]:
    """
    Identifies top 3 contributing factors to the risk.
    """
    # Weight factors based on their impact in the synthetic formula
    # port_congestion (0), weather (1), geo_risk (4), customs_delay (3) -> high context weight
    # carrier_reliability (2), trend_congestion (5), trend_delay (6) -> temporal weight
    # route_variability (7) -> anomaly weight
    
    impacts = []
    for i, val in enumerate(features):
        name = FEATURE_ORDER[i]
        # Heuristic weight
        weight = 1.0
        if name in ['port_congestion', 'weather', 'geo_risk']: weight = 1.5
        if name == 'route_variability': weight = 1.2
        
        impacts.append((name, val * weight))
    
    # Sort by impact
    impacts.sort(key=lambda x: x[1], reverse=True)
    
    return [x[0] for x in impacts[:3]]
