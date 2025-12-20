import pandas as pd
import numpy as np
import joblib

def generate_predictions():
    """Generate final predictions using trained Random Forest model"""
    print("=== GENERATING PREDICTIONS ===")
    
    # Load trained model
    model = joblib.load('random_forest_model.pkl')
    print("✓ Model loaded")
    
    # Load test data
    test_df = pd.read_csv('test_processed.csv')
    print(f"Test data shape: {test_df.shape}")
    
    # Generate predictions
    predictions = model.predict(test_df)
    
    print(f"Predictions range: {predictions.min():.1f} to {predictions.max():.1f}")
    print(f"Predictions mean: {predictions.mean():.1f}")
    
    # Load original test data for Customer_ID
    original_test = pd.read_csv('../test.csv')
    
    # Create submission file
    submission = pd.DataFrame({
        'Customer_ID': original_test['Customer_ID'],
        'Discount_percentage': predictions
    })
    
    # Save submission
    submission.to_csv('submission.csv', index=False)
    
    print("✓ Predictions saved to submission.csv")
    print(f"Submission shape: {submission.shape}")
    
    return submission

if __name__ == "__main__":
    submission = generate_predictions()