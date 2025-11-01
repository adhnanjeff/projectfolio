import pandas as pd
import numpy as np
from config import *

class SimulinkDataConverter:
    @staticmethod
    def can_to_simulink_format(can_data):
        """Convert CAN data to Simulink-compatible format"""
        return {
            'time': can_data.get('timestamp', 0),
            'id': int(can_data['id']),
            'data': list(can_data['data'])[:8],
            'dlc': len(can_data['data'])
        }
    
    @staticmethod
    def simulink_to_can_format(sim_data):
        """Convert Simulink data to CAN format"""
        return {
            'timestamp': sim_data.get('time', 0),
            'id': sim_data['id'],
            'data': sim_data['data']
        }
    
    @staticmethod
    def export_model_for_simulink(model_file=MODEL_FILE):
        """Export trained model parameters for Simulink"""
        import joblib
        
        model = joblib.load(model_file)
        
        # Extract model parameters
        params = {
            'contamination': model.contamination,
            'n_estimators': model.n_estimators,
            'max_samples': model.max_samples,
            'threshold': model.offset_
        }
        
        # Save as MATLAB-readable format
        import scipy.io
        scipy.io.savemat('ids_model_params.mat', params)
        print("✅ Model parameters exported to ids_model_params.mat")
        
        return params