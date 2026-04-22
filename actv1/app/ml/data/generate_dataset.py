import pandas as pd
import numpy as np
import os

def generate_synthetic_data(num_rows=5000):
    np.random.seed(42)
    
    # Generate random features (0-1)
    data = {
        'port_congestion': np.random.uniform(0, 1, num_rows),
        'weather': np.random.uniform(0, 1, num_rows),
        'carrier_reliability': np.random.uniform(0, 1, num_rows),
        'customs_delay': np.random.uniform(0, 1, num_rows),
        'geo_risk': np.random.uniform(0, 1, num_rows),
        'trend_congestion': np.random.uniform(0, 1, num_rows),
        'trend_delay': np.random.uniform(0, 1, num_rows),
        'route_variability': np.random.uniform(0, 1, num_rows)
    }
    
    df = pd.DataFrame(data)
    
    # 1. Context Score (XGB-like ground truth)
    # Blend of congestion, weather, geo_risk, and customs_delay
    df['context_score'] = (
        0.3 * df['port_congestion'] + 
        0.2 * df['weather'] + 
        0.25 * df['geo_risk'] + 
        0.25 * df['customs_delay']
    )
    
    # 2. Temporal Score (Trend-based)
    # Blend of carrier_reliability (inverse), trend_congestion, trend_delay
    df['temporal_score'] = (
        0.4 * (1 - df['carrier_reliability']) + 
        0.3 * df['trend_congestion'] + 
        0.3 * df['trend_delay']
    )
    
    # 3. Anomaly Score (Isolation Forest-like)
    # High route_variability or extreme spikes in others
    df['anomaly_score'] = df['route_variability'] * 0.7 + np.random.uniform(0, 0.3, num_rows)
    
    # Final DRI label (0-100)
    # Formula: 0.5 * context + 0.3 * temporal + 0.2 * anomaly
    df['final_dri'] = (
        0.5 * df['context_score'] + 
        0.3 * df['temporal_score'] + 
        0.2 * df['anomaly_score']
    ) * 100
    
    # Clip final DRI to 0-100
    df['final_dri'] = df['final_dri'].clip(0, 100).astype(int)
    
    # Save to CSV
    output_path = os.path.join(os.path.dirname(__file__), 'dri_dataset.csv')
    df.to_csv(output_path, index=False)
    print(f"Dataset generated at {output_path}")

if __name__ == "__main__":
    generate_synthetic_data()
