import pickle
import os
import logging

logger = logging.getLogger(__name__)

def load_model(filename):
    model_path = os.path.join(os.path.dirname(__file__), 'models', filename)
    if not os.path.exists(model_path):
        logger.warning(f"Model file {filename} not found at {model_path}")
        return None
    
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        return model
    except Exception as e:
        logger.error(f"Error loading model {filename}: {e}")
        return None

def load_xgb_model():
    return load_model('xgb_model.pkl')

def load_iso_model():
    return load_model('iso_forest.pkl')
