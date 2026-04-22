import pandas as pd
from sklearn.ensemble import IsolationForest
import pickle
import os

def train_iso():
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'dri_dataset.csv')
    if not os.path.exists(data_path):
        print("Dataset not found. Run generate_dataset.py first.")
        return

    df = pd.read_csv(data_path)
    
    # All features for anomaly detection
    features = [
        'port_congestion', 'weather', 'carrier_reliability', 'customs_delay',
        'geo_risk', 'trend_congestion', 'trend_delay', 'route_variability'
    ]
    X = df[features]
    
    model = IsolationForest(
        n_estimators=100,
        contamination='auto',
        random_state=42
    )
    
    model.fit(X)
    
    model_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, 'iso_forest.pkl')
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"Isolation Forest model saved at {model_path}")

if __name__ == "__main__":
    train_iso()
