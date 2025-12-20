import pandas as pd
import numpy as np

def load_and_inspect_data():
    """Phase 1: Load and inspect the data"""
    
    # Load datasets
    train_df = pd.read_csv('../train (1).csv')
    test_df = pd.read_csv('../test.csv')
    
    print("=== DATA SHAPES ===")
    print(f"train.csv → {train_df.shape[0]} rows × {train_df.shape[1]} columns")
    print(f"test.csv → {test_df.shape[0]} rows × {test_df.shape[1]} columns")
    
    print("\n=== TRAIN COLUMNS ===")
    print(train_df.columns.tolist())
    
    print("\n=== TEST COLUMNS ===")
    print(test_df.columns.tolist())
    
    # Check target column (should be 'Discount_percentage')
    target_in_train = 'Discount_percentage' in train_df.columns
    target_in_test = 'Discount_percentage' in test_df.columns
    print(f"\n=== TARGET COLUMN CHECK ===")
    print(f"Target 'Discount_percentage' in train: {target_in_train}")
    print(f"Target 'Discount_percentage' in test: {target_in_test}")
    
    # Basic statistics
    print(f"\n=== BASIC STATISTICS ===")
    if target_in_train:
        print(f"Target variable statistics:")
        print(train_df['Discount_percentage'].describe())
    
    # Missing values analysis
    print(f"\n=== MISSING VALUES ANALYSIS ===")
    print("Train dataset missing values:")
    train_missing = train_df.isnull().sum()
    print(train_missing[train_missing > 0])
    
    print("\nTest dataset missing values:")
    test_missing = test_df.isnull().sum()
    print(test_missing[test_missing > 0])
    
    # Check Customer_ID
    print(f"\n=== CUSTOMER_ID CHECK ===")
    print(f"Customer_ID in train: {'Customer_ID' in train_df.columns}")
    print(f"Customer_ID in test: {'Customer_ID' in test_df.columns}")
    
    return train_df, test_df

def identify_feature_types(train_df):
    """Identify and categorize feature types"""
    
    # Define feature categories based on the actual dataset
    numerical_features = [
        'No_of_orders_placed',
        'Maximum_bill', 
        'Minimum_bill',
        'No_of_issues_raised',
        'Customer_rating',
        'Average_food_rating',
        'Average_happiness_rating',
        'Coupon_consumption_status',
        'Coupons_offered'
    ]
    
    categorical_features = [
        'Category_of_customers',
        'Premium_membership'
    ]
    
    date_features = [
        'Last_order_placed_date'
    ]
    
    # Identify actual features present in the dataset
    actual_numerical = [feat for feat in numerical_features if feat in train_df.columns]
    actual_categorical = [feat for feat in categorical_features if feat in train_df.columns]
    actual_date = [feat for feat in date_features if feat in train_df.columns]
    
    print("\n=== FEATURE TYPES ===")
    print("🔢 Numerical Features:")
    for feat in actual_numerical:
        print(f"  ✓ {feat}")
        # Show basic stats for numerical features
        if feat in train_df.columns:
            non_null_count = train_df[feat].count()
            print(f"    Non-null values: {non_null_count}/{len(train_df)}")
    
    print("\n🔤 Categorical Features:")
    for feat in actual_categorical:
        print(f"  ✓ {feat}")
        if feat in train_df.columns:
            unique_vals = train_df[feat].unique()
            print(f"    Unique values ({len(unique_vals)}): {unique_vals}")
    
    print("\n📅 Date Features:")
    for feat in actual_date:
        print(f"  ✓ {feat}")
        if feat in train_df.columns:
            print(f"    Sample values: {train_df[feat].dropna().head(3).tolist()}")
            print(f"    Non-null values: {train_df[feat].count()}/{len(train_df)}")
    
    return actual_numerical, actual_categorical, actual_date

if __name__ == "__main__":
    # Execute Phase 1
    train_df, test_df = load_and_inspect_data()
    numerical_features, categorical_features, date_features = identify_feature_types(train_df)
    
    print("\n=== PHASE 1 COMPLETE ===")
    print("Data loaded and feature types identified successfully!")