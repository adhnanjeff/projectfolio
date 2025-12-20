import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def perform_eda():
    """Simple EDA focused on key insights for Random Forest"""
    print("=== EXPLORATORY DATA ANALYSIS ===")
    
    # Load processed data
    train_df = pd.read_csv('train_processed.csv')
    
    # Basic statistics
    print(f"Dataset shape: {train_df.shape}")
    print(f"Target statistics:")
    print(train_df['Discount_percentage'].describe())
    
    # Missing values check
    missing = train_df.isnull().sum()
    if missing.any():
        print(f"Missing values: {missing[missing > 0]}")
    else:
        print("✓ No missing values")
    
    # Target distribution
    plt.figure(figsize=(10, 4))
    
    plt.subplot(1, 2, 1)
    plt.hist(train_df['Discount_percentage'], bins=30, alpha=0.7)
    plt.title('Target Distribution')
    plt.xlabel('Discount Percentage')
    
    plt.subplot(1, 2, 2)
    plt.boxplot(train_df['Discount_percentage'])
    plt.title('Target Boxplot')
    plt.ylabel('Discount Percentage')
    
    plt.tight_layout()
    plt.savefig('target_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Feature correlations with target
    numeric_cols = train_df.select_dtypes(include=[np.number]).columns
    correlations = train_df[numeric_cols].corr()['Discount_percentage'].abs().sort_values(ascending=False)
    
    print(f"\nTop 10 correlations with target:")
    for feature, corr in correlations.head(11).items():  # 11 to exclude target itself
        if feature != 'Discount_percentage':
            print(f"  {feature}: {corr:.3f}")
    
    # Save EDA summary
    eda_summary = {
        'dataset_shape': train_df.shape,
        'target_mean': train_df['Discount_percentage'].mean(),
        'target_std': train_df['Discount_percentage'].std(),
        'top_correlations': correlations.head(6).to_dict()
    }
    
    pd.Series(eda_summary).to_csv('eda_summary.csv')
    
    print("✓ EDA complete - target_distribution.png saved")
    return eda_summary

if __name__ == "__main__":
    summary = perform_eda()