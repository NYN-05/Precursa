import pandas as pd
import xgboost as xgb
import pickle
import os

def train_xgb():
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'dri_dataset.csv')
    if not os.path.exists(data_path):
        print("Dataset not found. Run generate_dataset.py first.")
        return

    df = pd.read_csv(data_path)
    
    # Context features
    features = ['port_congestion', 'weather', 'geo_risk', 'customs_delay']
    X = df[features]
    y = df['context_score']
    
    model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42
    )
    
    model.fit(X, y)
    
    model_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, 'xgb_model.pkl')
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"XGB model saved at {model_path}")

if __name__ == "__main__":
    train_xgb()
