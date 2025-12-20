import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV, cross_val_score
from sklearn.metrics import mean_squared_error
import joblib

def train_random_forest():
    """Train and optimize Random Forest model"""
    print("=== TRAINING RANDOM FOREST ===")
    
    # Load processed data
    train_df = pd.read_csv('train_processed.csv')
    
    # Prepare features and target
    X = train_df.drop('Discount_percentage', axis=1)
    y = train_df['Discount_percentage']
    
    print(f"Training data: {X.shape}")
    print(f"Target range: {y.min():.1f} to {y.max():.1f}")
    
    # Define parameter grid for optimization
    param_grid = {
        'n_estimators': [100, 200, 300],
        'max_depth': [10, 15, 20, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'max_features': ['sqrt', 'log2', None]
    }
    
    # Initialize Random Forest
    rf = RandomForestRegressor(random_state=42, n_jobs=-1)
    
    # Hyperparameter tuning with RandomizedSearchCV
    print("Optimizing hyperparameters...")
    random_search = RandomizedSearchCV(
        rf, param_grid, n_iter=30, cv=5, 
        scoring='neg_mean_squared_error', 
        random_state=42, n_jobs=-1, verbose=1
    )
    
    random_search.fit(X, y)
    
    # Get best model
    best_rf = random_search.best_estimator_
    best_rmse = np.sqrt(-random_search.best_score_)
    
    print(f"\n🏆 BEST RANDOM FOREST MODEL")
    print(f"Cross-validation RMSE: {best_rmse:.3f}")
    print(f"Best parameters: {random_search.best_params_}")
    
    # Final training on full dataset
    best_rf.fit(X, y)
    
    # Training performance
    train_pred = best_rf.predict(X)
    train_rmse = np.sqrt(mean_squared_error(y, train_pred))
    print(f"Training RMSE: {train_rmse:.3f}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': best_rf.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\nTop 10 Important Features:")
    for i, row in feature_importance.head(10).iterrows():
        print(f"  {row['feature']}: {row['importance']:.3f}")
    
    # Save model and feature importance
    joblib.dump(best_rf, 'random_forest_model.pkl')
    feature_importance.to_csv('feature_importance.csv', index=False)
    
    print("✓ Model training complete")
    return best_rf, best_rmse

if __name__ == "__main__":
    model, rmse = train_random_forest()