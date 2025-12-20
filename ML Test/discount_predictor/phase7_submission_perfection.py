import pandas as pd
import numpy as np

def load_submission_data():
    """Load the generated submission file"""
    print("=== LOADING SUBMISSION DATA ===")
    
    submission = pd.read_csv('final_submission.csv')
    print(f"Loaded submission shape: {submission.shape}")
    print(f"Columns: {list(submission.columns)}")
    
    return submission

def format_submission_file(submission):
    """Format submission file to exact requirements"""
    print("\n=== FORMATTING SUBMISSION FILE ===")
    
    # Ensure exact column names
    required_columns = ['Customer_ID', 'Discount_percentage']
    
    if list(submission.columns) != required_columns:
        print(f"Renaming columns to: {required_columns}")
        submission.columns = required_columns
    
    # Keep only required columns (remove any extra)
    submission = submission[required_columns]
    
    # Round predictions to reasonable precision
    submission['Discount_percentage'] = submission['Discount_percentage'].round(2)
    
    print(f"✓ Formatted columns: {list(submission.columns)}")
    print(f"✓ Shape: {submission.shape}")
    
    return submission

def perform_sanity_checks(submission):
    """Comprehensive sanity checks"""
    print("\n=== FINAL SANITY CHECKS ===")
    
    checks_passed = 0
    total_checks = 7
    
    # Check 1: No NaNs
    nan_count = submission.isnull().sum().sum()
    if nan_count == 0:
        print("✔ No NaNs found")
        checks_passed += 1
    else:
        print(f"✗ Found {nan_count} NaN values")
    
    # Check 2: Correct column names
    expected_columns = ['Customer_ID', 'Discount_percentage']
    if list(submission.columns) == expected_columns:
        print("✔ Correct column names")
        checks_passed += 1
    else:
        print(f"✗ Wrong columns: {list(submission.columns)}")
    
    # Check 3: Correct row count
    expected_rows = 13319
    if len(submission) == expected_rows:
        print(f"✔ Correct row count: {len(submission)}")
        checks_passed += 1
    else:
        print(f"✗ Wrong row count: {len(submission)} (expected {expected_rows})")
    
    # Check 4: No duplicate Customer_IDs
    duplicates = submission['Customer_ID'].duplicated().sum()
    if duplicates == 0:
        print("✔ No duplicate Customer_IDs")
        checks_passed += 1
    else:
        print(f"✗ Found {duplicates} duplicate Customer_IDs")
    
    # Check 5: Reasonable prediction range
    min_pred = submission['Discount_percentage'].min()
    max_pred = submission['Discount_percentage'].max()
    if 0 <= min_pred and max_pred <= 100:
        print(f"✔ Reasonable prediction range: {min_pred:.1f}% to {max_pred:.1f}%")
        checks_passed += 1
    else:
        print(f"✗ Unreasonable predictions: {min_pred:.1f}% to {max_pred:.1f}%")
    
    # Check 6: No missing Customer_IDs
    missing_ids = submission['Customer_ID'].isnull().sum()
    if missing_ids == 0:
        print("✔ No missing Customer_IDs")
        checks_passed += 1
    else:
        print(f"✗ Found {missing_ids} missing Customer_IDs")
    
    # Check 7: Proper data types
    id_type_ok = submission['Customer_ID'].dtype == 'object'
    pred_type_ok = pd.api.types.is_numeric_dtype(submission['Discount_percentage'])
    
    if id_type_ok and pred_type_ok:
        print("✔ Correct data types")
        checks_passed += 1
    else:
        print(f"✗ Wrong data types: ID={submission['Customer_ID'].dtype}, Pred={submission['Discount_percentage'].dtype}")
    
    # Summary
    print(f"\nSANITY CHECK SUMMARY: {checks_passed}/{total_checks} passed")
    
    if checks_passed == total_checks:
        print("🎉 ALL CHECKS PASSED - SUBMISSION READY!")
        return True
    else:
        print("⚠️ Some checks failed - review submission")
        return False

def create_perfect_submission(submission):
    """Create the final perfect submission file"""
    print("\n=== CREATING PERFECT SUBMISSION ===")
    
    # Save with exact specifications
    submission.to_csv('perfect_submission.csv', index=False)
    
    print("✓ Saved: perfect_submission.csv")
    
    # Verify file format
    print("\nFile verification:")
    with open('perfect_submission.csv', 'r') as f:
        first_line = f.readline().strip()
        print(f"Header: {first_line}")
        
        # Count lines
        f.seek(0)
        line_count = sum(1 for line in f) - 1  # Subtract header
        print(f"Data rows: {line_count}")
    
    # Display sample
    print(f"\nSample submission:")
    print(submission.head())
    
    return submission

def final_submission_summary(submission):
    """Print final submission summary"""
    print("\n" + "="*50)
    print("FINAL SUBMISSION SUMMARY")
    print("="*50)
    
    print(f"File: perfect_submission.csv")
    print(f"Format: CSV (no index)")
    print(f"Columns: {', '.join(submission.columns)}")
    print(f"Rows: {len(submission):,}")
    
    print(f"\nPrediction Statistics:")
    stats = submission['Discount_percentage'].describe()
    print(f"  Mean: {stats['mean']:.2f}%")
    print(f"  Std: {stats['std']:.2f}%")
    print(f"  Min: {stats['min']:.2f}%")
    print(f"  Max: {stats['max']:.2f}%")
    
    print(f"\nCustomer_ID Sample:")
    print(f"  First: {submission['Customer_ID'].iloc[0]}")
    print(f"  Last: {submission['Customer_ID'].iloc[-1]}")
    
    print(f"\n🎯 SUBMISSION STATUS: READY FOR COMPETITION!")

if __name__ == "__main__":
    # Load submission data
    submission = load_submission_data()
    
    # Format to exact requirements
    submission = format_submission_file(submission)
    
    # Perform comprehensive sanity checks
    all_checks_passed = perform_sanity_checks(submission)
    
    if all_checks_passed:
        # Create perfect submission file
        final_submission = create_perfect_submission(submission)
        
        # Final summary
        final_submission_summary(final_submission)
        
        print("\n=== PHASE 7 COMPLETE ===")
        print("Perfect submission file created!")
        print("File: perfect_submission.csv")
    else:
        print("\n=== PHASE 7 FAILED ===")
        print("Please fix the issues before submitting")