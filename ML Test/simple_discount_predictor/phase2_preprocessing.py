import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

def preprocess_data():
    """Simple preprocessing for Random Forest model"""
    print("=== PREPROCESSING DATA ===")
    
    # Load data
    train_df = pd.read_csv('../train (1).csv')
    test_df = pd.read_csv('../test.csv')
    
    # Remove rows with missing target
    train_clean = train_df.dropna(subset=['Discount_percentage']).copy()
    print(f"Removed {len(train_df) - len(train_clean)} rows with missing target")
    
    # Combine for consistent preprocessing
    combined_df = pd.concat([train_clean.drop('Discount_percentage', axis=1), test_df], ignore_index=True)
    
    # Handle categorical variables with Label Encoding
    categorical_cols = combined_df.select_dtypes(include=['object']).columns
    print(f"Encoding {len(categorical_cols)} categorical columns")
    
    for col in categorical_cols:
        le = LabelEncoder()
        combined_df[col] = le.fit_transform(combined_df[col].astype(str))
    
    # Fill missing values with median for numeric, mode for categorical
    for col in combined_df.columns:
        if combined_df[col].isnull().any():
            if combined_df[col].dtype in ['int64', 'float64']:
                combined_df[col].fillna(combined_df[col].median(), inplace=True)
            else:
                combined_df[col].fillna(combined_df[col].mode()[0], inplace=True)
    
    # Split back
    train_processed = combined_df.iloc[:len(train_clean)].copy()
    test_processed = combined_df.iloc[len(train_clean):].copy()
    
    # Add target back to train
    train_processed['Discount_percentage'] = train_clean['Discount_percentage'].values
    
    # Save processed data
    train_processed.to_csv('train_processed.csv', index=False)
    test_processed.to_csv('test_processed.csv', index=False)
    
    print(f"Train processed: {train_processed.shape}")
    print(f"Test processed: {test_processed.shape}")
    print("✓ Data preprocessing complete")
    
    return train_processed, test_processed

if __name__ == "__main__":
    train_processed, test_processed = preprocess_data()