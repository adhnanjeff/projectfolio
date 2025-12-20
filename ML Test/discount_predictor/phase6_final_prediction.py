import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

def load_processed_data():
    """Load the preprocessed data"""
    train_df = pd.read_csv('train_final.csv')
    test_df = pd.read_csv('test_final.csv')
    
    print("=== LOADING PROCESSED DATA ===")
    print(f"Train shape: {train_df.shape}")
    print(f"Test shape: {test_df.shape}")
    
    return train_df, test_df

def prepare_final_training_data(train_df):
    """Prepare training data - handle missing targets"""
    print("\n=== PREPARING TRAINING DATA ===")
    
    # Remove rows with missing or anomalous target values
    original_size = len(train_df)
    train_clean = train_df.dropna(subset=['Discount_percentage'])
    train_clean = train_clean[train_clean['Discount_percentage'] != -99]
    
    print(f"Original training size: {original_size}")
    print(f"Clean training size: {len(train_clean)}")
    print(f"Removed: {original_size - len(train_clean)} rows")
    
    # Separate features and target
    target_col = 'Discount_percentage'
    feature_cols = [col for col in train_clean.columns if col != target_col]
    
    X_train = train_clean[feature_cols]
    y_train = train_clean[target_col]
    
    print(f"Features: {len(feature_cols)}")
    print(f"Target range: {y_train.min():.1f} to {y_train.max():.1f}")
    
    return X_train, y_train, feature_cols

def prepare_test_data(test_df, feature_cols):
    """Prepare test data with same preprocessing"""
    print("\n=== PREPARING TEST DATA ===")
    
    # Ensure same features as training
    X_test = test_df[feature_cols]
    
    print(f"Test features: {X_test.shape[1]}")
    print(f"Feature alignment: {'✓' if list(X_test.columns) == feature_cols else '✗'}")
    
    # Check for any missing values
    missing_count = X_test.isnull().sum().sum()
    print(f"Missing values in test: {missing_count}")
    
    return X_test

def train_final_model(X_train, y_train):
    """Train the best model on full training data"""
    print("\n=== TRAINING FINAL MODEL ===")
    
    # Use best parameters from Phase 5
    final_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        min_samples_leaf=4,
        min_samples_split=2,
        random_state=42,
        n_jobs=-1
    )
    
    print("Model parameters:")
    print(f"  n_estimators: {final_model.n_estimators}")
    print(f"  max_depth: {final_model.max_depth}")
    print(f"  min_samples_leaf: {final_model.min_samples_leaf}")
    
    # Train on full data
    final_model.fit(X_train, y_train)
    
    # Training performance
    train_pred = final_model.predict(X_train)
    train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
    train_r2 = r2_score(y_train, train_pred)
    
    print(f"\nTraining Performance:")
    print(f"  RMSE: {train_rmse:.3f}")
    print(f"  R²: {train_r2:.3f}")
    
    return final_model

def generate_test_predictions(model, X_test):
    """Generate predictions for test data"""
    print("\n=== GENERATING TEST PREDICTIONS ===")
    
    # Predict
    test_predictions = model.predict(X_test)
    
    print(f"Predictions generated: {len(test_predictions)}")
    print(f"Prediction range: {test_predictions.min():.1f} to {test_predictions.max():.1f}")
    print(f"Mean prediction: {test_predictions.mean():.1f}")
    
    # Sanity checks
    if test_predictions.min() < 0:
        print("⚠️ Warning: Negative predictions found")
    if test_predictions.max() > 100:
        print("⚠️ Warning: Predictions > 100% found")
    
    return test_predictions

def create_submission_file(test_predictions):
    """Create final submission file"""
    print("\n=== CREATING SUBMISSION FILE ===")
    
    # Load original test file to get Customer_IDs
    original_test = pd.read_csv('../test.csv')
    
    # Create submission dataframe
    submission = pd.DataFrame({
        'Customer_ID': original_test['Customer_ID'],
        'Discount_percentage': test_predictions
    })
    
    print(f"Submission shape: {submission.shape}")
    print(f"Customer_ID count: {len(submission['Customer_ID'].unique())}")
    
    # Verify no missing values
    missing_ids = submission['Customer_ID'].isnull().sum()
    missing_preds = submission['Discount_percentage'].isnull().sum()
    
    print(f"Missing Customer_IDs: {missing_ids}")
    print(f"Missing predictions: {missing_preds}")
    
    # Save submission
    submission.to_csv('final_submission.csv', index=False)
    print("✓ Saved: final_submission.csv")
    
    # Display sample
    print(f"\nSample predictions:")
    print(submission.head())
    
    return submission

def final_model_summary(model, X_train, y_train, test_predictions):
    """Print final model summary"""
    print("\n" + "="*50)
    print("FINAL MODEL SUMMARY")
    print("="*50)
    
    print(f"Model: Random Forest Regressor (Tuned)")
    print(f"Training samples: {len(X_train)}")
    print(f"Features: {X_train.shape[1]}")
    print(f"Test predictions: {len(test_predictions)}")
    
    # Feature importance (top 5)
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\nTop 5 Important Features:")
    for i, (_, row) in enumerate(feature_importance.head(5).iterrows(), 1):
        print(f"  {i}. {row['feature']}: {row['importance']:.3f}")
    
    print(f"\nPrediction Statistics:")
    print(f"  Min: {test_predictions.min():.1f}%")
    print(f"  Max: {test_predictions.max():.1f}%")
    print(f"  Mean: {test_predictions.mean():.1f}%")
    print(f"  Std: {test_predictions.std():.1f}%")

if __name__ == "__main__":
    # Load processed data
    train_df, test_df = load_processed_data()
    
    # Prepare training data
    X_train, y_train, feature_cols = prepare_final_training_data(train_df)
    
    # Prepare test data
    X_test = prepare_test_data(test_df, feature_cols)
    
    # Train final model
    final_model = train_final_model(X_train, y_train)
    
    # Generate predictions
    test_predictions = generate_test_predictions(final_model, X_test)
    
    # Create submission file
    submission = create_submission_file(test_predictions)
    
    # Final summary
    final_model_summary(final_model, X_train, y_train, test_predictions)
    
    print("\n=== PHASE 6 COMPLETE ===")
    print("Final model trained and predictions generated!")
    print("Ready for submission: final_submission.csv")