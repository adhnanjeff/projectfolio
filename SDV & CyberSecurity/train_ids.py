import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import joblib
import ast
import numpy as np
from config import *
def extract_enhanced_features(df):
    """Extract enhanced features with temporal and statistical analysis"""
    features_list = []
    
    # Sort by timestamp
    df = df.sort_values('timestamp_epoch' if 'timestamp_epoch' in df.columns else 'timestamp')
    
    for idx, row in df.iterrows():
        # Basic features
        msg_id = row.get('msg_id', row.get('id', 0))
        
        # Decoded values
        speed = row.get('speed', 0) or 0
        rpm = row.get('rpm', 0) or 0
        engine_temp = row.get('engine_temp', 0) or 0
        
        # Temporal features
        interarrival = row.get('interarrival_ms', 0) or 0
        msg_rate = row.get('msg_rate_1s', 0) or 0
        
        # Statistical features (if available)
        speed_mean = row.get('speed_mean_5s', speed) or speed
        speed_std = row.get('speed_std_5s', 0) or 0
        rpm_mean = row.get('rpm_mean_5s', rpm) or rpm
        rpm_std = row.get('rpm_std_5s', 0) or 0
        delta_speed = row.get('delta_speed', 0) or 0
        delta_rpm = row.get('delta_rpm', 0) or 0
        
        # Derived features
        speed_anomaly = 1 if speed > 200 else 0
        rpm_anomaly = 1 if rpm > 8000 else 0
        temp_anomaly = 1 if engine_temp > 120 else 0
        rate_anomaly = 1 if msg_rate > 50 else 0
        
        features = [
            msg_id, speed, rpm, engine_temp, interarrival, msg_rate,
            speed_mean, speed_std, rpm_mean, rpm_std, delta_speed, delta_rpm,
            speed_anomaly, rpm_anomaly, temp_anomaly, rate_anomaly
        ]
        
        features_list.append(features)
    
    return np.array(features_list)

def train_enhanced_models():
    """Train multiple ML models with enhanced features"""
    try:
        print("📊 Loading training data...")
        df = pd.read_csv(TRAINING_DATA_FILE)
        print(f"Loaded {len(df)} samples")
        
        # Extract enhanced features
        print("🔧 Extracting enhanced features...")
        X = extract_enhanced_features(df)
        y = df.get('label', pd.Series([0] * len(df))).values
        
        print(f"Features shape: {X.shape}")
        print(f"Normal samples: {sum(y == 0)}, Attack samples: {sum(y == 1)}")
        
        # Time-based split for realistic evaluation
        tscv = TimeSeriesSplit(n_splits=3)
        
        models = {}
        results = {}
        
        # 1. Isolation Forest (Unsupervised)
        print("\n🧠 Training Isolation Forest...")
        iso_model = IsolationForest(
            contamination=CONTAMINATION_RATE,
            random_state=RANDOM_STATE,
            n_estimators=200
        )
        iso_model.fit(X[y == 0])  # Train only on normal data
        models['isolation_forest'] = iso_model
        
        # 2. XGBoost (Supervised)
        if sum(y) > 0:  # If we have attack labels
            print("🚀 Training XGBoost...")
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
            )
            
            xgb_model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=RANDOM_STATE,
                eval_metric='logloss'
            )
            xgb_model.fit(X_train, y_train)
            models['xgboost'] = xgb_model
            
            # Evaluate XGBoost
            y_pred = xgb_model.predict(X_test)
            y_prob = xgb_model.predict_proba(X_test)[:, 1]
            
            print("\n=== XGBoost Performance ===")
            print(classification_report(y_test, y_pred, target_names=['Normal', 'Attack']))
            print(f"ROC-AUC: {roc_auc_score(y_test, y_prob):.3f}")
            
            results['xgboost'] = {
                'accuracy': (y_pred == y_test).mean(),
                'roc_auc': roc_auc_score(y_test, y_prob)
            }
        
        # 3. Random Forest (Supervised)
        if sum(y) > 0:
            print("🌲 Training Random Forest...")
            rf_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=RANDOM_STATE
            )
            rf_model.fit(X_train, y_train)
            models['random_forest'] = rf_model
            
            # Feature importance
            feature_names = [
                'msg_id', 'speed', 'rpm', 'engine_temp', 'interarrival', 'msg_rate',
                'speed_mean', 'speed_std', 'rpm_mean', 'rpm_std', 'delta_speed', 'delta_rpm',
                'speed_anomaly', 'rpm_anomaly', 'temp_anomaly', 'rate_anomaly'
            ]
            
            importances = rf_model.feature_importances_
            print("\n📊 Top Feature Importances:")
            for i, imp in sorted(enumerate(importances), key=lambda x: x[1], reverse=True)[:5]:
                print(f"{feature_names[i]}: {imp:.3f}")
        
        # Save best model (use XGBoost if available, else Isolation Forest)
        best_model = models.get('xgboost', models['isolation_forest'])
        joblib.dump(best_model, MODEL_FILE)
        
        # Save model metadata
        metadata = {
            'model_type': 'xgboost' if 'xgboost' in models else 'isolation_forest',
            'features': 16,
            'training_samples': len(X),
            'results': results
        }
        joblib.dump(metadata, MODEL_FILE.replace('.pkl', '_metadata.pkl'))
        
        print(f"\n✅ Best model saved as {MODEL_FILE}")
        return best_model, metadata
        
    except Exception as e:
        print(f"❌ Error training models: {e}")
        raise

def classify_attack_type(row):
    """Classify attack type based on message characteristics"""
    try:
        msg_id = row['id']
        data = ast.literal_eval(row['data']) if isinstance(row['data'], str) else row['data']
        label = row.get('label', 0)
        
        if label == 0:  # Normal traffic
            return 'NORMAL'
        
        # Simple heuristic classification
        if msg_id == CAN_IDS['SPEED'] and len(data) > 0:
            if data[0] > 200:  # Unrealistic speed
                return 'SPOOFING'
        elif msg_id == CAN_IDS['RPM'] and len(data) >= 2:
            rpm = int.from_bytes(data[:2], byteorder='big')
            if rpm > 8000:  # Unrealistic RPM
                return 'SPOOFING'
        
        # Check for fuzzing patterns
        if all(b == 0xFF for b in data):  # All max values
            return 'FUZZING'
        
        # Default to DOS for other attacks
        return 'DOS'
        
    except:
        return 'NORMAL'

def generate_enhanced_synthetic_data():
    """Generate enhanced synthetic data with rich features"""
    print("🔧 Generating enhanced synthetic training data...")
    
    import random
    import time
    from datetime import datetime, timedelta
    
    data = []
    base_time = time.time()
    
    # Generate normal traffic with realistic patterns
    for i in range(2000):
        timestamp = base_time + i * 0.1  # 100ms intervals
        
        # Normal speed with realistic variation
        base_speed = 60 + 30 * np.sin(i * 0.01)  # Varying speed pattern
        speed = max(0, min(120, base_speed + random.gauss(0, 5)))
        
        # Correlated RPM
        rpm = 800 + speed * 25 + random.gauss(0, 100)
        rpm = max(800, min(6000, rpm))
        
        # Engine temperature
        engine_temp = 85 + random.gauss(0, 5)
        
        data.append({
            'timestamp_epoch': timestamp,
            'timestamp_iso': datetime.fromtimestamp(timestamp).isoformat(),
            'msg_id': CAN_IDS['SPEED'],
            'speed': speed,
            'rpm': None,
            'engine_temp': None,
            'interarrival_ms': 100,
            'msg_rate_1s': 10,
            'label': 0
        })
        
        data.append({
            'timestamp_epoch': timestamp + 0.05,
            'timestamp_iso': datetime.fromtimestamp(timestamp + 0.05).isoformat(),
            'msg_id': CAN_IDS['RPM'],
            'speed': None,
            'rpm': rpm,
            'engine_temp': None,
            'interarrival_ms': 100,
            'msg_rate_1s': 10,
            'label': 0
        })
    
    # Generate attack scenarios
    attack_start = len(data)
    
    # Spoofing attacks
    for i in range(100):
        timestamp = base_time + attack_start * 0.1 + i * 0.1
        fake_speed = random.randint(250, 350)  # Unrealistic speed
        
        data.append({
            'timestamp_epoch': timestamp,
            'timestamp_iso': datetime.fromtimestamp(timestamp).isoformat(),
            'msg_id': CAN_IDS['SPEED'],
            'speed': fake_speed,
            'rpm': None,
            'engine_temp': None,
            'interarrival_ms': 50,  # Faster rate
            'msg_rate_1s': 20,
            'label': 1
        })
    
    # DoS attacks - high frequency
    for i in range(200):
        timestamp = base_time + (attack_start + 100) * 0.1 + i * 0.01  # 10ms intervals
        
        data.append({
            'timestamp_epoch': timestamp,
            'timestamp_iso': datetime.fromtimestamp(timestamp).isoformat(),
            'msg_id': CAN_IDS['BRAKE'],
            'speed': None,
            'rpm': None,
            'engine_temp': None,
            'interarrival_ms': 10,  # Very fast
            'msg_rate_1s': 100,  # High rate
            'label': 1
        })
    
    # Save enhanced synthetic data
    df = pd.DataFrame(data)
    df.to_csv(TRAINING_DATA_FILE, index=False)
    print(f"✅ Generated {len(data)} enhanced samples saved to {TRAINING_DATA_FILE}")
    
    return df

def train_ids_model():
    """Train simple IDS model"""
    try:
        print("📊 Loading training data...")
        df = pd.read_csv(TRAINING_DATA_FILE)
        
        features = []
        labels = []
        
        for _, row in df.iterrows():
            try:
                if 'data' in row and isinstance(row['data'], str):
                    data_bytes = ast.literal_eval(row['data'])
                else:
                    data_bytes = [0] * 8
                data_bytes = (data_bytes + [0]*8)[:8]
                
                msg_id = row.get('msg_id', row.get('id', 0))
                fv = [msg_id] + data_bytes
                features.append(fv)
                labels.append(row.get('label', 0))
            except:
                continue
        
        X = pd.DataFrame(features)
        y = np.array(labels)
        
        print(f"Features shape: {X.shape}")
        
        model = IsolationForest(
            contamination=CONTAMINATION_RATE,
            random_state=RANDOM_STATE,
            n_estimators=100
        )
        
        model.fit(X)
        joblib.dump(model, MODEL_FILE)
        
        print(f"✅ Model saved as {MODEL_FILE}")
        return model
        
    except Exception as e:
        print(f"❌ Error training model: {e}")
        raise

def generate_synthetic_data():
    """Generate simple synthetic data"""
    print("🔧 Generating synthetic training data...")
    
    import random
    from datetime import datetime
    
    data = []
    
    for _ in range(1000):
        speed = random.randint(0, 120)
        data.append({
            'timestamp': datetime.now().isoformat(),
            'id': CAN_IDS['SPEED'],
            'data': [speed],
            'label': 0
        })
        
        rpm = random.randint(800, 4000)
        rpm_bytes = list(rpm.to_bytes(2, byteorder='big'))
        data.append({
            'timestamp': datetime.now().isoformat(),
            'id': CAN_IDS['RPM'],
            'data': rpm_bytes,
            'label': 0
        })
    
    for _ in range(200):
        fake_speed = random.randint(200, 300)
        data.append({
            'timestamp': datetime.now().isoformat(),
            'id': CAN_IDS['SPEED'],
            'data': [fake_speed],
            'label': 1
        })
    
    df = pd.DataFrame(data)
    df.to_csv(TRAINING_DATA_FILE, index=False)
    print(f"✅ Generated {len(data)} samples")
    return df

async def main():
    """Main async training function"""
    try:
        try:
            df = pd.read_csv(TRAINING_DATA_FILE)
            if len(df) < 100:
                raise FileNotFoundError("Insufficient training data")
        except FileNotFoundError:
            print("⚠️ No training data found. Generating synthetic data...")
            df = generate_synthetic_data()
        
        model = train_ids_model()
        
        print("\n🎉 IDS training completed!")
        print(f"Model saved to: {MODEL_FILE}")
        print("\n🚀 Ready to run:")
        print("1. python ids.py (monitoring)")
        print("2. streamlit run dashboard.py (dashboard)")
        print("3. python attack_engine.py (attack simulation)")
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

