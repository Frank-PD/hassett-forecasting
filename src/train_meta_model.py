#!/usr/bin/env python3
"""
META-LEARNING MODEL
Train an ML model that predicts which forecasting model to use for each route.

This meta-model learns patterns about when each forecasting method works best,
allowing it to:
1. Make predictions for new routes not in the routing table
2. Adapt to changing route characteristics
3. Provide fast inference (no need to run all 18 models)
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score
import joblib
from pathlib import Path

def extract_route_features(df, historical_data):
    """
    Extract features from route characteristics and historical data.

    Features:
    - Volume statistics (mean, median, std, cv)
    - Trend (increasing, decreasing, stable)
    - Seasonality (week-to-week variance)
    - Frequency (how often route ships)
    - Volatility (coefficient of variation)
    - Day of week
    - Product type
    - Route characteristics (ODC, DDC encoded)
    """

    print("🔍 Extracting route features...")

    features_list = []

    for idx, row in df.iterrows():
        route_key = row['route_key']

        # Get historical data for this route
        route_hist = historical_data[
            (historical_data['ODC'] == row['ODC']) &
            (historical_data['DDC'] == row['DDC']) &
            (historical_data['ProductType'] == row['ProductType']) &
            (historical_data['dayofweek'] == row['dayofweek'])
        ]

        if len(route_hist) == 0:
            continue

        pieces = route_hist['pieces'].values

        # Volume statistics
        mean_vol = np.mean(pieces)
        median_vol = np.median(pieces)
        std_vol = np.std(pieces)
        cv_vol = (std_vol / mean_vol) if mean_vol > 0 else 0
        max_vol = np.max(pieces)
        min_vol = np.min(pieces)

        # Trend (simple linear regression slope)
        if len(pieces) >= 2:
            x = np.arange(len(pieces))
            trend = np.polyfit(x, pieces, 1)[0]  # slope
        else:
            trend = 0

        # Frequency (how many non-zero weeks)
        frequency = np.sum(pieces > 0) / len(pieces) if len(pieces) > 0 else 0

        # Seasonality (week-to-week variance)
        if len(pieces) >= 2:
            week_to_week_changes = np.diff(pieces)
            seasonality = np.std(week_to_week_changes)
        else:
            seasonality = 0

        # Zero weeks percentage
        zero_pct = np.sum(pieces == 0) / len(pieces) if len(pieces) > 0 else 1

        # Recent vs historical (last 4 weeks vs earlier)
        if len(pieces) >= 8:
            recent_avg = np.mean(pieces[-4:])
            historical_avg = np.mean(pieces[:-4])
            recent_vs_hist = (recent_avg / historical_avg) if historical_avg > 0 else 1
        else:
            recent_vs_hist = 1

        features = {
            'route_key': route_key,
            'mean_volume': mean_vol,
            'median_volume': median_vol,
            'std_volume': std_vol,
            'cv_volume': cv_vol,
            'max_volume': max_vol,
            'min_volume': min_vol,
            'trend': trend,
            'frequency': frequency,
            'seasonality': seasonality,
            'zero_pct': zero_pct,
            'recent_vs_hist': recent_vs_hist,
            'dayofweek': row['dayofweek'],
            'ProductType': row['ProductType'],
            'optimal_model': row.get('Winner_Model', row.get('Optimal_Model', None))
        }

        features_list.append(features)

    features_df = pd.DataFrame(features_list)
    print(f"✅ Extracted features for {len(features_df):,} routes")

    return features_df

def prepare_training_data(features_df):
    """Prepare features and target for training."""

    print("\n📊 Preparing training data...")

    # Encode categorical variables
    features_df_encoded = features_df.copy()

    # One-hot encode ProductType
    product_dummies = pd.get_dummies(features_df['ProductType'], prefix='product')
    features_df_encoded = pd.concat([features_df_encoded, product_dummies], axis=1)

    # Select feature columns
    feature_cols = [
        'mean_volume', 'median_volume', 'std_volume', 'cv_volume',
        'max_volume', 'min_volume', 'trend', 'frequency',
        'seasonality', 'zero_pct', 'recent_vs_hist', 'dayofweek'
    ] + list(product_dummies.columns)

    X = features_df_encoded[feature_cols].fillna(0)
    y = features_df_encoded['optimal_model']

    print(f"   Features: {X.shape[1]} columns")
    print(f"   Samples: {len(X):,}")
    print(f"   Classes (models): {y.nunique()}")

    return X, y, feature_cols

def train_meta_model(X, y):
    """Train the meta-learning model."""

    print("\n🤖 Training Meta-Learning Model...")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"   Training set: {len(X_train):,} routes")
    print(f"   Test set: {len(X_test):,} routes")

    # Train RandomForest classifier
    meta_model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )

    meta_model.fit(X_train, y_train)

    # Evaluate
    train_score = meta_model.score(X_train, y_train)
    test_score = meta_model.score(X_test, y_test)

    print(f"\n✅ Model Trained!")
    print(f"   Training Accuracy: {train_score*100:.1f}%")
    print(f"   Test Accuracy: {test_score*100:.1f}%")

    # Cross-validation
    cv_scores = cross_val_score(meta_model, X, y, cv=5)
    print(f"   Cross-Val Accuracy: {cv_scores.mean()*100:.1f}% (+/- {cv_scores.std()*2*100:.1f}%)")

    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': meta_model.feature_importances_
    }).sort_values('importance', ascending=False)

    print(f"\n📊 Top 10 Most Important Features:")
    for idx, row in feature_importance.head(10).iterrows():
        print(f"   {row['feature']:<25} {row['importance']:.4f}")

    # Test set predictions
    y_pred = meta_model.predict(X_test)

    print(f"\n📋 Test Set Performance by Model:")
    print("-" * 80)

    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    model_performance = []
    for model_name, metrics in report.items():
        if model_name not in ['accuracy', 'macro avg', 'weighted avg']:
            model_performance.append({
                'Model': model_name,
                'Precision': metrics['precision'],
                'Recall': metrics['recall'],
                'F1-Score': metrics['f1-score'],
                'Support': int(metrics['support'])
            })

    perf_df = pd.DataFrame(model_performance).sort_values('F1-Score', ascending=False)

    for idx, row in perf_df.head(15).iterrows():
        print(f"{row['Model']:<40} P:{row['Precision']:.2f} R:{row['Recall']:.2f} F1:{row['F1-Score']:.2f} ({row['Support']} routes)")

    return meta_model, feature_importance, test_score

def save_meta_model(meta_model, feature_cols, model_path='models/meta_model.pkl', feature_path='models/feature_columns.pkl'):
    """Save the trained meta-model."""

    Path(model_path).parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(meta_model, model_path)
    joblib.dump(feature_cols, feature_path)

    print(f"\n💾 Meta-model saved:")
    print(f"   Model: {model_path}")
    print(f"   Features: {feature_path}")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Train Meta-Learning Model")
    parser.add_argument('--comparison', type=str, required=True, help='Path to comprehensive comparison CSV')
    parser.add_argument('--historical', type=str, required=True, help='Path to historical data CSV')
    parser.add_argument('--model-output', type=str, default='models/meta_model.pkl', help='Output path for model')
    parser.add_argument('--features-output', type=str, default='models/feature_columns.pkl', help='Output path for feature columns')
    args = parser.parse_args()

    print("=" * 80)
    print("META-LEARNING MODEL TRAINING")
    print("=" * 80)

    # Load data
    print("\n📂 Loading data...")
    comparison_df = pd.read_csv(args.comparison)
    historical_df = pd.read_csv(args.historical)

    print(f"   Comparison data: {len(comparison_df):,} routes")
    print(f"   Historical data: {len(historical_df):,} records")

    # Extract features
    features_df = extract_route_features(comparison_df, historical_df)

    # Prepare training data
    X, y, feature_cols = prepare_training_data(features_df)

    # Train model
    meta_model, feature_importance, test_score = train_meta_model(X, y)

    # Save model
    save_meta_model(meta_model, feature_cols, args.model_output, args.features_output)

    print("\n" + "=" * 80)
    print("✅ META-MODEL TRAINING COMPLETE")
    print("=" * 80)
    print(f"\nTest Accuracy: {test_score*100:.1f}%")
    print(f"\nThis model can now predict which forecasting model to use for any route")
    print(f"based on its characteristics (volume, volatility, trend, seasonality, etc.)")
    print(f"\nUse 'predict_with_meta_model.py' to make predictions for new routes.")

if __name__ == "__main__":
    main()
