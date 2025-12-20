import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt

def load_data():
    train_df = pd.read_csv('train_final.csv')
    train_clean = train_df.dropna(subset=['Discount_percentage'])
    train_clean = train_clean[train_clean['Discount_percentage'] != -99]
    
    target_col = 'Discount_percentage'
    feature_cols = [col for col in train_clean.columns if col != target_col]
    
    X = train_clean[feature_cols]
    y = train_clean[target_col]
    
    return X, y, feature_cols

def evaluate_best_models(X, y):
    print("=== MODEL EVALUATION ===")
    
    # Define top models from Phase 4
    models = {
        'Random Forest (Tuned)': RandomForestRegressor(
            n_estimators=100, max_depth=10, min_samples_leaf=4, 
            min_samples_split=2, random_state=42, n_jobs=-1
        ),
        'Random Forest (Default)': RandomForestRegressor(
            n_estimators=100, random_state=42, n_jobs=-1
        )
    }
    
    results = {}
    
    for name, model in models.items():
        print(f"\nEvaluating {name}...")
        
        # Cross-validation RMSE
        cv_scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_squared_error')
        cv_rmse = np.sqrt(-cv_scores)
        
        # Train-validation split for stability check
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model.fit(X_train, y_train)
        
        train_pred = model.predict(X_train)
        val_pred = model.predict(X_val)
        
        train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
        val_rmse = np.sqrt(mean_squared_error(y_val, val_pred))
        
        # Calculate overfitting ratio
        overfitting_ratio = val_rmse / train_rmse
        
        results[name] = {
            'CV_RMSE_mean': cv_rmse.mean(),
            'CV_RMSE_std': cv_rmse.std(),
            'Train_RMSE': train_rmse,
            'Val_RMSE': val_rmse,
            'Overfitting_Ratio': overfitting_ratio,
            'model': model
        }
        
        print(f"  CV RMSE: {cv_rmse.mean():.3f} ± {cv_rmse.std():.3f}")
        print(f"  Train RMSE: {train_rmse:.3f}")
        print(f"  Val RMSE: {val_rmse:.3f}")
        print(f"  Overfitting Ratio: {overfitting_ratio:.3f}")
        
        if overfitting_ratio < 1.1:
            print("  ✓ Good generalization")
        elif overfitting_ratio < 1.2:
            print("  ⚠️ Slight overfitting")
        else:
            print("  ❌ Significant overfitting")
    
    return results

def select_final_model(results):
    print("\n=== FINAL MODEL SELECTION ===")
    
    # Rank models by CV RMSE and stability
    model_scores = []
    
    for name, metrics in results.items():
        # Penalty for overfitting
        stability_penalty = max(0, (metrics['Overfitting_Ratio'] - 1.0) * 2)
        adjusted_score = metrics['CV_RMSE_mean'] + stability_penalty
        
        model_scores.append((name, metrics['CV_RMSE_mean'], 
                           metrics['Overfitting_Ratio'], adjusted_score))
    
    # Sort by adjusted score
    model_scores.sort(key=lambda x: x[3])
    
    print("Model Ranking (CV RMSE + Stability):")
    for i, (name, cv_rmse, overfitting, adj_score) in enumerate(model_scores, 1):
        print(f"{i}. {name}")
        print(f"   CV RMSE: {cv_rmse:.3f}")
        print(f"   Overfitting: {overfitting:.3f}")
        print(f"   Adjusted Score: {adj_score:.3f}")
    
    # Select best model
    best_model_name = model_scores[0][0]
    best_model = results[best_model_name]['model']
    
    print(f"\n🏆 SELECTED MODEL: {best_model_name}")
    
    return best_model, best_model_name

def analyze_feature_importance(model, feature_cols):
    print("\n=== FEATURE IMPORTANCE ANALYSIS ===")
    
    # Get feature importances
    importances = model.feature_importances_
    
    # Create feature importance dataframe
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': importances
    }).sort_values('importance', ascending=False)
    
    print("Top 10 Most Important Features:")
    for i, (_, row) in enumerate(feature_importance.head(10).iterrows(), 1):
        print(f"{i:2d}. {row['feature']:<25} {row['importance']:.3f}")
    
    # Sanity check against EDA correlations
    print("\n=== SANITY CHECK ===")
    
    # Expected important features from EDA
    expected_important = [
        'Category_Inactive', 'days_since_last_order', 'Premium_membership',
        'Coupons_offered', 'No_of_orders_placed', 'Category_Active'
    ]
    
    top_5_features = feature_importance.head(5)['feature'].tolist()
    
    matches = 0
    for feat in expected_important:
        if feat in top_5_features:
            matches += 1
            print(f"  ✓ {feat} - Expected and found in top 5")
    
    print(f"\nSanity Check Score: {matches}/{len(expected_important)} expected features in top 5")
    
    if matches >= 4:
        print("  ✅ Excellent - Model learned expected patterns")
    elif matches >= 2:
        print("  ⚠️ Good - Model mostly aligned with EDA")
    else:
        print("  ❌ Poor - Model may have issues")
    
    return feature_importance

def final_model_summary(best_model, best_model_name, results, feature_importance):
    print("\n" + "="*50)
    print("FINAL MODEL SUMMARY")
    print("="*50)
    
    metrics = results[best_model_name]
    
    print(f"Selected Model: {best_model_name}")
    print(f"Cross-Validation RMSE: {metrics['CV_RMSE_mean']:.3f} ± {metrics['CV_RMSE_std']:.3f}")
    print(f"Validation RMSE: {metrics['Val_RMSE']:.3f}")
    print(f"Overfitting Ratio: {metrics['Overfitting_Ratio']:.3f}")
    
    print(f"\nTop 5 Features:")
    for i, (_, row) in enumerate(feature_importance.head(5).iterrows(), 1):
        print(f"  {i}. {row['feature']} ({row['importance']:.3f})")
    
    print(f"\nModel Parameters:")
    print(f"  {best_model.get_params()}")
    
    # Performance assessment
    if metrics['CV_RMSE_mean'] < 8.0:
        performance = "Excellent"
    elif metrics['CV_RMSE_mean'] < 10.0:
        performance = "Good"
    else:
        performance = "Needs Improvement"
    
    print(f"\nPerformance Assessment: {performance}")
    print(f"Ready for Production: {'Yes' if metrics['Overfitting_Ratio'] < 1.2 else 'No'}")

if __name__ == "__main__":
    # Load data
    X, y, feature_cols = load_data()
    
    # Evaluate models
    results = evaluate_best_models(X, y)
    
    # Select final model
    best_model, best_model_name = select_final_model(results)
    
    # Analyze feature importance
    feature_importance = analyze_feature_importance(best_model, feature_cols)
    
    # Final summary
    final_model_summary(best_model, best_model_name, results, feature_importance)
    
    print("\n=== PHASE 5 COMPLETE ===")
    print("Model evaluation complete - ready for deployment!")