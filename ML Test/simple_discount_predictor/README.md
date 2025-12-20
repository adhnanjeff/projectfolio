# Simple Discount Predictor

A streamlined machine learning pipeline using only Random Forest for discount percentage prediction.

## Overview

This simplified version focuses on a single, well-optimized Random Forest model instead of testing multiple algorithms. The approach is cleaner, faster, and more focused.

## Pipeline Structure

### Phase 1: Data Loading (`phase1_data_loading.py`)
- Load train and test datasets
- Basic data inspection
- Check target variable distribution

### Phase 2: Preprocessing (`phase2_preprocessing.py`)
- Handle missing values in target
- Label encode categorical variables
- Fill missing values with median/mode
- Save processed datasets

### Phase 3: EDA (`phase3_eda.py`)
- Target distribution analysis
- Feature correlations with target
- Basic statistical summaries
- Generate visualization plots

### Phase 4: Model Training (`phase4_model_training.py`)
- Train Random Forest with hyperparameter optimization
- Use RandomizedSearchCV for efficient tuning
- Save best model and feature importance
- Cross-validation for robust performance estimation

### Phase 5: Evaluation (`phase5_evaluation.py`)
- Cross-validation performance metrics
- Residual analysis and diagnostics
- Model performance visualization
- Generate evaluation reports

### Phase 6: Prediction (`phase6_prediction.py`)
- Load trained model
- Generate predictions on test set
- Create submission file

## Key Simplifications

1. **Single Model**: Only Random Forest (proven performer for tabular data)
2. **Focused Tuning**: Optimized parameter search for RF only
3. **Clean Phases**: Each phase has one clear responsibility
4. **Minimal Dependencies**: Only essential libraries
5. **Fast Execution**: No complex ensemble methods

## Usage

### Run Complete Pipeline
```bash
python run_pipeline.py
```

### Run Individual Phases
```bash
python phase1_data_loading.py
python phase2_preprocessing.py
python phase3_model_training.py
python phase4_prediction.py
```

## Output Files

- `train_processed.csv` - Preprocessed training data
- `test_processed.csv` - Preprocessed test data
- `target_distribution.png` - Target variable visualization
- `eda_summary.csv` - EDA summary statistics
- `random_forest_model.pkl` - Trained model
- `feature_importance.csv` - Feature importance rankings
- `model_evaluation.png` - Model performance plots
- `model_performance.csv` - Performance metrics
- `submission.csv` - Final predictions

## Why Random Forest?

- Handles mixed data types well
- Built-in feature importance
- Robust to outliers
- Good baseline performance
- Fast training and prediction
- Minimal preprocessing required

## Performance

The model uses cross-validation RMSE for performance estimation and includes hyperparameter optimization for best results while maintaining simplicity.