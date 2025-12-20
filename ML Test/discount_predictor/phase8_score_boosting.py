import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error
import xgboost as xgb
import lightgbm as lgb
import warnings
warnings.filterwarnings('ignore')

def load_data():
    train_df = pd.read_csv('train_final.csv')
    test_df = pd.read_csv('test_final.csv')
    
    train_clean = train_df.dropna(subset=['Discount_percentage'])
    train_clean = train_clean[train_clean['Discount_percentage'] != -99]
    
    target_col = 'Discount_percentage'
    feature_cols = [col for col in train_clean.columns if col != target_col]
    
    X = train_clean[feature_cols]
    y = train_clean[target_col]
    X_test = test_df[feature_cols]
    
    return X, y, X_test, feature_cols

def remove_weak_features(X, y, X_test, feature_cols):
    print("=== REMOVING WEAK FEATURES ===")
    
    # Train RF to get feature importance
    rf = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    
    # Get feature importance
    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': rf.feature_importances_
    }).sort_values('importance', ascending=False)
    
    # Keep top features (importance > 0.01)
    strong_features = importance_df[importance_df['importance'] > 0.01]['feature'].tolist()
    
    print(f"Original features: {len(feature_cols)}")
    print(f"Strong features: {len(strong_features)}")
    print(f"Removed: {len(feature_cols) - len(strong_features)} weak features")
    
    X_selected = X[strong_features]
    X_test_selected = X_test[strong_features]
    
    return X_selected, X_test_selected, strong_features

def log_target_experiment(X, y, X_test):
    print("\n=== LOG-TARGET TRANSFORMATION ===")
    
    # Add small constant to avoid log(0)
    y_log = np.log1p(y)
    
    # Test with Random Forest
    rf_log = RandomForestRegressor(n_estimators=100, max_depth=10, 
                                   min_samples_leaf=4, random_state=42, n_jobs=-1)
    
    # Cross-validation on log-transformed target
    cv_scores_log = cross_val_score(rf_log, X, y_log, cv=5, scoring='neg_mean_squared_error')
    cv_rmse_log = np.sqrt(-cv_scores_log)
    
    # Train and predict
    rf_log.fit(X, y_log)
    log_pred = rf_log.predict(X_test)
    
    # Inverse transform
    final_pred = np.expm1(log_pred)
    
    print(f"Log-target CV RMSE: {cv_rmse_log.mean():.3f} ± {cv_rmse_log.std():.3f}")
    print(f"Predictions range: {final_pred.min():.1f} to {final_pred.max():.1f}")
    
    return final_pred, cv_rmse_log.mean()

def create_ensemble_models(X, y, X_test):
    print("\n=== CREATING ENSEMBLE MODELS ===")
    
    # Define top 3 models
    models = {
        'RandomForest': RandomForestRegressor(
            n_estimators=100, max_depth=10, min_samples_leaf=4, 
            random_state=42, n_jobs=-1
        ),
        'XGBoost': xgb.XGBRegressor(
            n_estimators=100, max_depth=5, learning_rate=0.1,
            random_state=42, n_jobs=-1
        ),
        'LightGBM': lgb.LGBMRegressor(
            n_estimators=100, max_depth=5, learning_rate=0.1,
            random_state=42, n_jobs=-1, verbose=-1
        )
    }
    
    predictions = {}
    cv_scores = {}
    
    for name, model in models.items():
        print(f"Training {name}...")
        
        # Cross-validation
        cv_score = cross_val_score(model, X, y, cv=5, scoring='neg_mean_squared_error')
        cv_rmse = np.sqrt(-cv_score)
        cv_scores[name] = cv_rmse.mean()
        
        # Train and predict
        model.fit(X, y)
        pred = model.predict(X_test)
        predictions[name] = pred
        
        print(f"  CV RMSE: {cv_rmse.mean():.3f}")
    
    return predictions, cv_scores

def create_ensemble_prediction(predictions, cv_scores):
    print("\n=== CREATING ENSEMBLE PREDICTION ===")
    
    # Weight by inverse of CV RMSE (better models get higher weight)
    weights = {}
    total_inv_rmse = 0
    
    for name, rmse in cv_scores.items():
        inv_rmse = 1.0 / rmse
        weights[name] = inv_rmse
        total_inv_rmse += inv_rmse
    
    # Normalize weights
    for name in weights:
        weights[name] /= total_inv_rmse
    
    print("Model weights:")
    for name, weight in weights.items():
        print(f"  {name}: {weight:.3f}")
    
    # Create weighted ensemble
    ensemble_pred = np.zeros(len(list(predictions.values())[0]))
    
    for name, pred in predictions.items():
        ensemble_pred += weights[name] * pred
    
    return ensemble_pred

def clip_predictions(predictions, min_val=0, max_val=100):
    print(f"\n=== CLIPPING PREDICTIONS ===")
    
    original_min = predictions.min()
    original_max = predictions.max()
    
    clipped_pred = np.clip(predictions, min_val, max_val)
    
    clipped_count = np.sum((predictions < min_val) | (predictions > max_val))
    
    print(f"Original range: {original_min:.1f} to {original_max:.1f}")
    print(f"Clipped range: {clipped_pred.min():.1f} to {clipped_pred.max():.1f}")
    print(f"Clipped values: {clipped_count}")
    
    return clipped_pred

def compare_all_approaches(X, y, X_test, feature_cols):
    print("\n=== COMPARING ALL APPROACHES ===")
    
    results = {}
    
    # 1. Original Random Forest
    rf_original = RandomForestRegressor(n_estimators=100, max_depth=10, 
                                       min_samples_leaf=4, random_state=42, n_jobs=-1)
    cv_original = cross_val_score(rf_original, X, y, cv=5, scoring='neg_mean_squared_error')
    results['Original RF'] = np.sqrt(-cv_original).mean()
    
    # 2. Feature selection
    X_selected, X_test_selected, strong_features = remove_weak_features(X, y, X_test, feature_cols)
    rf_selected = RandomForestRegressor(n_estimators=100, max_depth=10, 
                                       min_samples_leaf=4, random_state=42, n_jobs=-1)
    cv_selected = cross_val_score(rf_selected, X_selected, y, cv=5, scoring='neg_mean_squared_error')
    results['Feature Selected'] = np.sqrt(-cv_selected).mean()
    
    # 3. Log-target
    _, log_rmse = log_target_experiment(X_selected, y, X_test_selected)
    results['Log Target'] = log_rmse
    
    # 4. Ensemble
    predictions, cv_scores = create_ensemble_models(X_selected, y, X_test_selected)
    ensemble_pred = create_ensemble_prediction(predictions, cv_scores)
    
    # Estimate ensemble CV score (weighted average)
    ensemble_cv = sum(weight * rmse for (name, weight), (_, rmse) in 
                     zip([(n, 1.0/cv_scores[n]/sum(1.0/r for r in cv_scores.values())) 
                          for n in cv_scores], cv_scores.items()))
    results['Ensemble'] = ensemble_cv
    
    # Print comparison
    print("\nApproach Comparison:")
    for i, (approach, rmse) in enumerate(sorted(results.items(), key=lambda x: x[1]), 1):
        print(f"{i}. {approach:<20} RMSE: {rmse:.3f}")
    
    return ensemble_pred, X_test_selected

def create_boosted_submission(predictions):
    print("\n=== CREATING BOOSTED SUBMISSION ===")
    
    # Clip predictions to reasonable range
    clipped_pred = clip_predictions(predictions, min_val=0, max_val=60)
    
    # Load original test Customer_IDs
    original_test = pd.read_csv('../test.csv')
    
    # Create submission
    submission = pd.DataFrame({
        'Customer_ID': original_test['Customer_ID'],
        'Discount_percentage': clipped_pred.round(2)
    })
    
    # Save
    submission.to_csv('boosted_submission.csv', index=False)
    
    print(f"✓ Saved: boosted_submission.csv")
    print(f"Prediction stats:")
    print(f"  Mean: {clipped_pred.mean():.2f}%")
    print(f"  Range: {clipped_pred.min():.1f}% to {clipped_pred.max():.1f}%")
    
    return submission

if __name__ == "__main__":
    print("=== PHASE 8: SCORE BOOSTING ===")
    
    # Load data
    X, y, X_test, feature_cols = load_data()
    
    # Compare all approaches and get best predictions
    ensemble_pred, X_test_final = compare_all_approaches(X, y, X_test, feature_cols)
    
    # Create boosted submission
    boosted_submission = create_boosted_submission(ensemble_pred)
    
    print("\n=== PHASE 8 COMPLETE ===")
    print("Score boosting techniques applied!")
    print("Files created:")
    print("  - boosted_submission.csv (ensemble + optimizations)")
    print("  - perfect_submission.csv (original best model)")
    print("\nRecommendation: Test both submissions to see which performs better!")