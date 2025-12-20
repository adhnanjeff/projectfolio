import pandas as pd
import numpy as np
from datetime import datetime

def load_data():
    train_df = pd.read_csv('../train (1).csv')
    test_df = pd.read_csv('../test.csv')
    return train_df, test_df

def check_missing_values(df, name):
    print(f"\n=== MISSING VALUES IN {name} ===")
    missing = df.isnull().sum()
    print(missing[missing > 0])
    if missing.sum() == 0:
        print("No missing values!")

def handle_missing_values(train_df, test_df):
    print("\n=== HANDLING MISSING VALUES ===")
    
    # Numerical features - fill with median
    numerical_features = ['No_of_orders_placed', 'Maximum_bill', 'Minimum_bill', 
                         'No_of_issues_raised', 'Customer_rating', 'Average_food_rating',
                         'Average_happiness_rating', 'Coupon_consumption_status', 'Coupons_offered']
    
    for feat in numerical_features:
        if train_df[feat].isnull().sum() > 0:
            median_val = train_df[feat].median()
            train_df[feat].fillna(median_val, inplace=True)
            test_df[feat].fillna(median_val, inplace=True)
            print(f"  ✓ {feat}: filled with median")
    
    # Categorical features - fill with mode or "Unknown"
    for feat in ['Category_of_customers', 'Premium_membership']:
        if train_df[feat].isnull().sum() > 0:
            mode_val = train_df[feat].mode()[0] if len(train_df[feat].mode()) > 0 else "Unknown"
            train_df[feat].fillna(mode_val, inplace=True)
            test_df[feat].fillna(mode_val, inplace=True)
            print(f"  ✓ {feat}: filled with mode")
    
    # Clean categorical values (remove '0' anomalies)
    train_df['Category_of_customers'] = train_df['Category_of_customers'].replace('0', 'Unknown')
    test_df['Category_of_customers'] = test_df['Category_of_customers'].replace('0', 'Unknown')
    train_df['Premium_membership'] = train_df['Premium_membership'].replace('0', 'No')
    test_df['Premium_membership'] = test_df['Premium_membership'].replace('0', 'No')
    
    return train_df, test_df

def engineer_features(train_df, test_df):
    print("\n=== FEATURE ENGINEERING ===")
    
    # Date features
    reference_date = pd.to_datetime('2015-12-31')
    
    for df in [train_df, test_df]:
        df['Last_order_placed_date'] = pd.to_datetime(df['Last_order_placed_date'], format='%m/%d/%Y %I:%M %p')
        df['days_since_last_order'] = (reference_date - df['Last_order_placed_date']).dt.days
        df['last_order_month'] = df['Last_order_placed_date'].dt.month
        df['last_order_weekday'] = df['Last_order_placed_date'].dt.weekday
    print("  ✓ Date features: days_since_last_order, last_order_month, last_order_weekday")
    
    # Bill behavior features
    for df in [train_df, test_df]:
        df['bill_range'] = df['Maximum_bill'] - df['Minimum_bill']
        df['avg_bill'] = (df['Maximum_bill'] + df['Minimum_bill']) / 2
    print("  ✓ Bill features: bill_range, avg_bill")
    
    # Coupon efficiency
    for df in [train_df, test_df]:
        df['coupon_usage_ratio'] = df['Coupon_consumption_status'] / (df['Coupons_offered'] + 1)
    print("  ✓ Coupon feature: coupon_usage_ratio")
    
    # Customer satisfaction index
    for df in [train_df, test_df]:
        df['satisfaction_score'] = (df['Customer_rating'] + df['Average_food_rating'] + 
                                   df['Average_happiness_rating']) / 3
    print("  ✓ Satisfaction feature: satisfaction_score")
    
    return train_df, test_df

def encode_categorical(train_df, test_df):
    print("\n=== ENCODING CATEGORICAL VARIABLES ===")
    
    # Premium_membership - Binary encoding
    for df in [train_df, test_df]:
        df['Premium_membership'] = df['Premium_membership'].map({'Yes': 1, 'No': 0})
    print("  ✓ Premium_membership: Binary encoded")
    
    # Category_of_customers - One-Hot Encoding
    train_df = pd.get_dummies(train_df, columns=['Category_of_customers'], prefix='Category')
    test_df = pd.get_dummies(test_df, columns=['Category_of_customers'], prefix='Category')
    
    # Align columns
    train_cols = set(train_df.columns)
    test_cols = set(test_df.columns)
    
    for col in train_cols - test_cols:
        if col.startswith('Category_'):
            test_df[col] = 0
    
    for col in test_cols - train_cols:
        if col.startswith('Category_'):
            train_df[col] = 0
    
    print("  ✓ Category_of_customers: One-Hot encoded")
    
    return train_df, test_df

def remove_non_useful_columns(train_df, test_df):
    print("\n=== REMOVING NON-USEFUL COLUMNS ===")
    
    cols_to_drop = ['Customer_ID', 'Last_order_placed_date']
    
    train_df = train_df.drop(columns=cols_to_drop)
    test_df = test_df.drop(columns=cols_to_drop)
    
    print(f"  ✓ Dropped: {cols_to_drop}")
    
    return train_df, test_df

def save_processed_data(train_df, test_df):
    train_df.to_csv('train_processed.csv', index=False)
    test_df.to_csv('test_processed.csv', index=False)
    print("\n=== SAVED PROCESSED DATA ===")
    print("  ✓ train_processed.csv")
    print("  ✓ test_processed.csv")

if __name__ == "__main__":
    # Load data
    train_df, test_df = load_data()
    
    # Check missing values
    check_missing_values(train_df, "TRAIN")
    check_missing_values(test_df, "TEST")
    
    # Handle missing values
    train_df, test_df = handle_missing_values(train_df, test_df)
    
    # Feature engineering
    train_df, test_df = engineer_features(train_df, test_df)
    
    # Encode categorical variables
    train_df, test_df = encode_categorical(train_df, test_df)
    
    # Remove non-useful columns
    train_df, test_df = remove_non_useful_columns(train_df, test_df)
    
    # Final check
    check_missing_values(train_df, "TRAIN (AFTER)")
    check_missing_values(test_df, "TEST (AFTER)")
    
    print(f"\n=== FINAL SHAPES ===")
    print(f"Train: {train_df.shape}")
    print(f"Test: {test_df.shape}")
    print(f"\nTrain columns: {train_df.columns.tolist()}")
    
    # Save processed data
    save_processed_data(train_df, test_df)
    
    print("\n=== PHASE 2 COMPLETE ===")
