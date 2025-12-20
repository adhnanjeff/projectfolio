import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

def load_data():
    train_df = pd.read_csv('train_final.csv')
    # Remove rows with missing target for analysis
    train_clean = train_df.dropna(subset=['Discount_percentage'])
    return train_clean

def analyze_target_distribution(train_df):
    print("=== TARGET DISTRIBUTION ANALYSIS ===")
    
    target = train_df['Discount_percentage']
    
    # Basic statistics
    print(f"Count: {len(target)}")
    print(f"Mean: {target.mean():.2f}")
    print(f"Median: {target.median():.2f}")
    print(f"Std: {target.std():.2f}")
    print(f"Min: {target.min():.2f}")
    print(f"Max: {target.max():.2f}")
    
    # Skewness and outliers
    skewness = stats.skew(target)
    print(f"\nSkewness: {skewness:.3f}")
    
    if abs(skewness) > 1:
        print("  ⚠️ Highly skewed distribution")
    elif abs(skewness) > 0.5:
        print("  ⚠️ Moderately skewed distribution")
    else:
        print("  ✓ Approximately normal distribution")
    
    # Outliers using IQR
    Q1 = target.quantile(0.25)
    Q3 = target.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = target[(target < lower_bound) | (target > upper_bound)]
    print(f"\nOutliers: {len(outliers)} ({len(outliers)/len(target)*100:.1f}%)")
    
    # Log transformation check
    if skewness > 1:
        log_target = np.log1p(target)
        log_skewness = stats.skew(log_target)
        print(f"Log1p skewness: {log_skewness:.3f}")
        if abs(log_skewness) < abs(skewness):
            print("  ✓ Log transformation improves distribution")
        else:
            print("  ✗ Log transformation doesn't help")
    
    return target

def analyze_feature_target_correlation(train_df):
    print("\n=== FEATURE-TARGET CORRELATIONS ===")
    
    # Calculate correlations
    target = 'Discount_percentage'
    correlations = train_df.corr()[target].abs().sort_values(ascending=False)
    
    # Remove self-correlation
    correlations = correlations.drop(target)
    
    print("Top correlations with Discount_percentage:")
    for i, (feature, corr) in enumerate(correlations.head(10).items()):
        print(f"{i+1:2d}. {feature:<25} {corr:.3f}")
    
    # Key feature groups analysis
    print("\n=== KEY FEATURE GROUPS ===")
    
    # Orders-related
    order_features = ['No_of_orders_placed', 'bill_range', 'avg_bill', 'Maximum_bill', 'Minimum_bill']
    order_corrs = {f: correlations.get(f, 0) for f in order_features if f in correlations.index}
    print("📦 Orders & Bills:")
    for f, c in sorted(order_corrs.items(), key=lambda x: x[1], reverse=True):
        print(f"   {f:<20} {c:.3f}")
    
    # Recency-related
    recency_features = ['days_since_last_order', 'last_order_month', 'last_order_weekday']
    recency_corrs = {f: correlations.get(f, 0) for f in recency_features if f in correlations.index}
    print("\n📅 Recency:")
    for f, c in sorted(recency_corrs.items(), key=lambda x: x[1], reverse=True):
        print(f"   {f:<20} {c:.3f}")
    
    # Coupon-related
    coupon_features = ['Coupon_consumption_status', 'Coupons_offered', 'coupon_usage_ratio']
    coupon_corrs = {f: correlations.get(f, 0) for f in coupon_features if f in correlations.index}
    print("\n🎟️ Coupons:")
    for f, c in sorted(coupon_corrs.items(), key=lambda x: x[1], reverse=True):
        print(f"   {f:<20} {c:.3f}")
    
    # Membership & satisfaction
    member_features = ['Premium_membership', 'satisfaction_score', 'Customer_rating']
    member_corrs = {f: correlations.get(f, 0) for f in member_features if f in correlations.index}
    print("\n⭐ Membership & Satisfaction:")
    for f, c in sorted(member_corrs.items(), key=lambda x: x[1], reverse=True):
        print(f"   {f:<20} {c:.3f}")
    
    return correlations

def feature_selection_insights(correlations):
    print("\n=== FEATURE SELECTION INSIGHTS ===")
    
    # High correlation features (>0.1)
    high_corr = correlations[correlations > 0.1]
    print(f"Features with correlation > 0.1: {len(high_corr)}")
    
    # Medium correlation features (0.05-0.1)
    medium_corr = correlations[(correlations > 0.05) & (correlations <= 0.1)]
    print(f"Features with correlation 0.05-0.1: {len(medium_corr)}")
    
    # Low correlation features (<0.05)
    low_corr = correlations[correlations <= 0.05]
    print(f"Features with correlation < 0.05: {len(low_corr)}")
    
    print("\n🎯 Recommended for modeling:")
    print("High priority:", list(high_corr.head(5).index))
    print("Medium priority:", list(medium_corr.head(3).index))

if __name__ == "__main__":
    # Load clean data
    train_df = load_data()
    
    # Analyze target distribution
    target = analyze_target_distribution(train_df)
    
    # Analyze feature-target relationships
    correlations = analyze_feature_target_correlation(train_df)
    
    # Feature selection insights
    feature_selection_insights(correlations)
    
    print("\n=== PHASE 3 COMPLETE ===")
    print("EDA analysis complete - ready for modeling!")