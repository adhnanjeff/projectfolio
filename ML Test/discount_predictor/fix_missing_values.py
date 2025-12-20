import pandas as pd
import numpy as np

def fix_remaining_missing_values():
    # Load processed data
    train_df = pd.read_csv('train_processed.csv')
    test_df = pd.read_csv('test_processed.csv')
    
    print("=== FIXING REMAINING MISSING VALUES ===")
    
    # Handle missing date features with median
    date_features = ['days_since_last_order', 'last_order_month', 'last_order_weekday']
    
    for feat in date_features:
        if train_df[feat].isnull().sum() > 0:
            median_val = train_df[feat].median()
            train_df[feat].fillna(median_val, inplace=True)
            test_df[feat].fillna(median_val, inplace=True)
            print(f"  ✓ {feat}: filled with median")
    
    # Handle missing target (we'll deal with this in modeling)
    target_missing = train_df['Discount_percentage'].isnull().sum()
    print(f"  ! Discount_percentage: {target_missing} missing (will handle in modeling)")
    
    # Final check
    print(f"\n=== FINAL MISSING VALUES ===")
    train_missing = train_df.isnull().sum()
    test_missing = test_df.isnull().sum()
    
    print("Train:", train_missing[train_missing > 0])
    print("Test:", test_missing[test_missing > 0])
    
    # Save final processed data
    train_df.to_csv('train_final.csv', index=False)
    test_df.to_csv('test_final.csv', index=False)
    
    print(f"\n=== FINAL DATA SHAPES ===")
    print(f"Train: {train_df.shape}")
    print(f"Test: {test_df.shape}")
    
    print("\n=== SAVED FINAL DATA ===")
    print("  ✓ train_final.csv")
    print("  ✓ test_final.csv")

if __name__ == "__main__":
    fix_remaining_missing_values()