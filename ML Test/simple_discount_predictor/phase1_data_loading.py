import pandas as pd
import numpy as np

def load_data():
    """Load and basic inspection of train and test data"""
    print("=== LOADING DATA ===")
    
    # Load datasets
    train_df = pd.read_csv('../train (1).csv')
    test_df = pd.read_csv('../test.csv')
    
    print(f"Train shape: {train_df.shape}")
    print(f"Test shape: {test_df.shape}")
    print(f"Target range: {train_df['Discount_percentage'].min():.1f} to {train_df['Discount_percentage'].max():.1f}")
    print(f"Missing values in target: {train_df['Discount_percentage'].isnull().sum()}")
    
    return train_df, test_df

if __name__ == "__main__":
    train_df, test_df = load_data()
    print("✓ Data loaded successfully")