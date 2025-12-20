import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, RandomizedSearchCV, train_test_split
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostRegressor
import warnings
warnings.filterwarnings('ignore')

def load_and_prepare_data():
    train_df = pd.read_csv('train_final.csv')
    test_df = pd.read_csv('test_final.csv')
    
    # Remove rows with missing target and anomalous values
    train_clean = train_df.dropna(subset=['Discount_percentage'])
    train_clean = train_clean[train_clean['Discount_percentage'] != -99]  # Remove anomalous values
    
    # Prepare features and target
    target_col = 'Discount_percentage'
    feature_cols = [col for col in train_clean.columns if col != target_col]
    
    X = train_clean[feature_cols]
    y = train_clean[target_col]
    X_test = test_df[feature_cols]
    
    print(f"Training data: {X.shape}")
    print(f"Test data: {X_test.shape}")
    print(f"Target range: {y.min():.1f} to {y.max():.1f}")
    
    return X, y, X_test, feature_cols

def baseline_models(X, y):
    print("\n=== BASELINE MODELS ===")
    
    models = {
        'Linear Regression': LinearRegression(),
        'Ridge': Ridge(alpha=1.0),
        'Lasso': Lasso(alpha=1.0)
    }
    
    baseline_scores = {}
    
    for name, model in models.items():
        # 5-fold CV RMSE
        cv_scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_squared_error')
        rmse_scores = np.sqrt(-cv_scores)
        
        baseline_scores[name] = {
            'RMSE_mean': rmse_scores.mean(),
            'RMSE_std': rmse_scores.std()
        }
        
        print(f"{name:<18} RMSE: {rmse_scores.mean():.3f} ± {rmse_scores.std():.3f}")
    
    return baseline_scores

def tree_based_models(X, y):
    print("\n=== TREE-BASED MODELS ===")
    
    # Define models with basic parameters
    models = {
        'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        'XGBoost': xgb.XGBRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        'LightGBM': lgb.LGBMRegressor(n_estimators=100, random_state=42, n_jobs=-1, verbose=-1),
        'CatBoost': CatBoostRegressor(iterations=100, random_state=42, verbose=False)
    }
    
    tree_scores = {}
    
    for name, model in models.items():
        # 5-fold CV RMSE
        cv_scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_squared_error')
        rmse_scores = np.sqrt(-cv_scores)
        
        tree_scores[name] = {
            'RMSE_mean': rmse_scores.mean(),
            'RMSE_std': rmse_scores.std(),
            'model': model
        }
        
        print(f"{name:<12} RMSE: {rmse_scores.mean():.3f} ± {rmse_scores.std():.3f}")
    
    return tree_scores

def hyperparameter_tuning(X, y, best_models):
    print("\n=== HYPERPARAMETER TUNING ===")
    
    # Focus on top 2 models for tuning
    top_models = sorted(best_models.items(), key=lambda x: x[1]['RMSE_mean'])[:2]
    
    tuned_models = {}
    
    for name, model_info in top_models:
        print(f"\nTuning {name}...")
        
        if 'XGBoost' in name:
            param_dist = {
                'n_estimators': [100, 200, 300],
                'max_depth': [3, 4, 5, 6],
                'learning_rate': [0.01, 0.1, 0.2],
                'subsample': [0.8, 0.9, 1.0],
                'colsample_bytree': [0.8, 0.9, 1.0]
            }
            model = xgb.XGBRegressor(random_state=42, n_jobs=-1)
            
        elif 'CatBoost' in name:
            param_dist = {
                'iterations': [100, 200, 300],
                'depth': [4, 5, 6, 7],
                'learning_rate': [0.01, 0.1, 0.2],
                'l2_leaf_reg': [1, 3, 5, 7]
            }
            model = CatBoostRegressor(random_state=42, verbose=False)
            
        elif 'LightGBM' in name:
            param_dist = {
                'n_estimators': [100, 200, 300],
                'max_depth': [3, 4, 5, 6],
                'learning_rate': [0.01, 0.1, 0.2],
                'subsample': [0.8, 0.9, 1.0],
                'colsample_bytree': [0.8, 0.9, 1.0]
            }
            model = lgb.LGBMRegressor(random_state=42, n_jobs=-1, verbose=-1)
            
        else:  # Random Forest
            param_dist = {
                'n_estimators': [100, 200, 300],
                'max_depth': [5, 10, 15, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
            model = RandomForestRegressor(random_state=42, n_jobs=-1)
        
        # Randomized search with 5-fold CV
        random_search = RandomizedSearchCV(
            model, param_dist, n_iter=20, cv=5, 
            scoring='neg_mean_squared_error', random_state=42, n_jobs=-1
        )
        
        random_search.fit(X, y)
        
        # Get best RMSE
        best_rmse = np.sqrt(-random_search.best_score_)
        
        tuned_models[name] = {
            'model': random_search.best_estimator_,
            'RMSE': best_rmse,
            'params': random_search.best_params_
        }
        
        print(f"  Best RMSE: {best_rmse:.3f}")
        print(f"  Best params: {random_search.best_params_}")
    
    return tuned_models

def final_model_selection(baseline_scores, tree_scores, tuned_models):
    print("\n=== FINAL MODEL COMPARISON ===")
    
    # Compare all models
    all_results = []
    
    # Baseline models
    for name, scores in baseline_scores.items():
        all_results.append((f"Baseline_{name}", scores['RMSE_mean']))
    
    # Tree models (original)
    for name, scores in tree_scores.items():
        all_results.append((f"Original_{name}", scores['RMSE_mean']))
    
    # Tuned models
    for name, scores in tuned_models.items():
        all_results.append((f"Tuned_{name}", scores['RMSE']))
    
    # Sort by RMSE
    all_results.sort(key=lambda x: x[1])
    
    print("Model Performance Ranking:")
    for i, (name, rmse) in enumerate(all_results, 1):
        print(f"{i:2d}. {name:<25} RMSE: {rmse:.3f}")
    
    # Select best model
    best_model_name = all_results[0][0]
    if 'Tuned_' in best_model_name:
        model_key = best_model_name.replace('Tuned_', '')
        best_model = tuned_models[model_key]['model']
        best_rmse = tuned_models[model_key]['RMSE']
    else:
        model_key = best_model_name.replace('Original_', '')
        best_model = tree_scores[model_key]['model']
        best_rmse = tree_scores[model_key]['RMSE_mean']
    
    print(f"\n🏆 BEST MODEL: {best_model_name}")
    print(f"   RMSE: {best_rmse:.3f}")
    
    return best_model, best_model_name, best_rmse

def generate_predictions(best_model, X, y, X_test):
    print("\n=== GENERATING PREDICTIONS ===")
    
    # Train on full dataset
    best_model.fit(X, y)
    
    # Generate predictions
    test_predictions = best_model.predict(X_test)
    
    # Train predictions for validation
    train_predictions = best_model.predict(X)
    train_rmse = np.sqrt(mean_squared_error(y, train_predictions))
    train_r2 = r2_score(y, train_predictions)
    
    print(f"Training RMSE: {train_rmse:.3f}")
    print(f"Training R²: {train_r2:.3f}")
    print(f"Test predictions range: {test_predictions.min():.1f} to {test_predictions.max():.1f}")
    
    return test_predictions

if __name__ == "__main__":
    # Load and prepare data
    X, y, X_test, feature_cols = load_and_prepare_data()
    
    # Step 1: Baseline models
    baseline_scores = baseline_models(X, y)
    
    # Step 2: Tree-based models
    tree_scores = tree_based_models(X, y)
    
    # Step 3: Hyperparameter tuning (top 2 models)
    tuned_models = hyperparameter_tuning(X, y, tree_scores)
    
    # Step 4: Final model selection
    best_model, best_model_name, best_rmse = final_model_selection(
        baseline_scores, tree_scores, tuned_models
    )
    
    # Step 5: Generate final predictions
    test_predictions = generate_predictions(best_model, X, y, X_test)
    
    # Save predictions
    submission = pd.DataFrame({
        'Customer_ID': pd.read_csv('../test.csv')['Customer_ID'],
        'Discount_percentage': test_predictions
    })
    submission.to_csv('submission.csv', index=False)
    
    print(f"\n=== PHASE 4 COMPLETE ===")
    print(f"Best model: {best_model_name}")
    print(f"CV RMSE: {best_rmse:.3f}")
    print("Predictions saved to submission.csv")