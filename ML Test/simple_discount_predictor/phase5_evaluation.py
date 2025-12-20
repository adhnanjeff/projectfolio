import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import cross_val_score, validation_curve
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt

def evaluate_model():
    """Evaluate Random Forest model performance"""
    print("=== MODEL EVALUATION ===")
    
    # Load model and data
    model = joblib.load('random_forest_model.pkl')
    train_df = pd.read_csv('train_processed.csv')
    
    X = train_df.drop('Discount_percentage', axis=1)
    y = train_df['Discount_percentage']
    
    # Cross-validation scores
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_squared_error')
    cv_rmse = np.sqrt(-cv_scores)
    
    print(f"Cross-validation RMSE: {cv_rmse.mean():.3f} ± {cv_rmse.std():.3f}")
    
    # Training performance
    model.fit(X, y)
    train_pred = model.predict(X)
    train_rmse = np.sqrt(mean_squared_error(y, train_pred))
    train_r2 = r2_score(y, train_pred)
    
    print(f"Training RMSE: {train_rmse:.3f}")
    print(f"Training R²: {train_r2:.3f}")
    
    # Residual analysis
    residuals = y - train_pred
    
    plt.figure(figsize=(12, 4))
    
    # Residuals vs Predicted
    plt.subplot(1, 3, 1)
    plt.scatter(train_pred, residuals, alpha=0.5)
    plt.axhline(y=0, color='r', linestyle='--')
    plt.xlabel('Predicted')
    plt.ylabel('Residuals')
    plt.title('Residuals vs Predicted')
    
    # Residuals histogram
    plt.subplot(1, 3, 2)
    plt.hist(residuals, bins=30, alpha=0.7)
    plt.xlabel('Residuals')
    plt.ylabel('Frequency')
    plt.title('Residual Distribution')
    
    # Actual vs Predicted
    plt.subplot(1, 3, 3)
    plt.scatter(y, train_pred, alpha=0.5)
    plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--')
    plt.xlabel('Actual')
    plt.ylabel('Predicted')
    plt.title('Actual vs Predicted')
    
    plt.tight_layout()
    plt.savefig('model_evaluation.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Performance summary
    performance = {
        'cv_rmse_mean': cv_rmse.mean(),
        'cv_rmse_std': cv_rmse.std(),
        'train_rmse': train_rmse,
        'train_r2': train_r2,
        'residual_mean': residuals.mean(),
        'residual_std': residuals.std()
    }
    
    pd.Series(performance).to_csv('model_performance.csv')
    
    print("✓ Model evaluation complete - model_evaluation.png saved")
    return performance

if __name__ == "__main__":
    performance = evaluate_model()