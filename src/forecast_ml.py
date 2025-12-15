#!/usr/bin/env python3
"""
MACHINE LEARNING FORECASTING MODEL
True ML approach with memory, learning, and dynamic adjustment.

Components:
  1. Feature Engineering - Extract route-level patterns
  2. Binary Classification - Will route ship? (XGBoost)
  3. Volume Regression - How much? (XGBoost)
  4. Error Tracking - Memory of performance per route
  5. Adaptive Learning - Adjust based on recent errors
  6. Continuous Improvement - Re-train on actuals

This solves the granular route-level accuracy problem.
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from databricks import sql
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, mean_absolute_error, accuracy_score
import pickle

DATABRICKS_CONFIG = {
    "server_hostname": "adb-434028626745069.9.azuredatabricks.net",
    "http_path": "/sql/1.0/warehouses/23a9897d305fb7e2",
    "auth_type": "databricks-oauth"
}

class RouteMemory:
    """
    Memory system to track performance per route.
    Stores historical errors and adjusts future predictions.
    """
    def __init__(self, memory_file='route_memory.json'):
        self.memory_file = Path(memory_file)
        self.memory = self.load_memory()

    def load_memory(self):
        """Load existing memory or create new."""
        if self.memory_file.exists():
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        return {}

    def save_memory(self):
        """Persist memory to disk."""
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f, indent=2)

    def get_route_key(self, odc, ddc, product, dow):
        """Generate unique route key."""
        return f"{odc}|{ddc}|{product}|{dow}"

    def record_prediction(self, odc, ddc, product, dow, predicted, actual, week, year):
        """Record a prediction and actual for learning."""
        route_key = self.get_route_key(odc, ddc, product, dow)

        if route_key not in self.memory:
            self.memory[route_key] = {
                'predictions': [],
                'total_predictions': 0,
                'total_error': 0,
                'avg_error': 0,
                'last_updated': None
            }

        error = abs(predicted - actual)

        self.memory[route_key]['predictions'].append({
            'week': week,
            'year': year,
            'predicted': predicted,
            'actual': actual,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })

        # Keep only last 12 predictions for memory efficiency
        self.memory[route_key]['predictions'] = self.memory[route_key]['predictions'][-12:]

        # Update statistics
        self.memory[route_key]['total_predictions'] += 1
        self.memory[route_key]['total_error'] += error
        self.memory[route_key]['avg_error'] = (
            self.memory[route_key]['total_error'] /
            self.memory[route_key]['total_predictions']
        )
        self.memory[route_key]['last_updated'] = datetime.now().isoformat()

        self.save_memory()

    def get_route_error_rate(self, odc, ddc, product, dow):
        """Get historical error rate for a route."""
        route_key = self.get_route_key(odc, ddc, product, dow)

        if route_key in self.memory:
            return self.memory[route_key]['avg_error']
        return None

    def get_adjustment_factor(self, odc, ddc, product, dow):
        """
        Calculate adjustment factor based on historical errors.
        If model consistently over/under predicts, adjust.
        """
        route_key = self.get_route_key(odc, ddc, product, dow)

        if route_key not in self.memory:
            return 1.0

        recent = self.memory[route_key]['predictions'][-5:]  # Last 5 predictions

        if len(recent) < 3:
            return 1.0

        # Calculate average over/under prediction
        avg_predicted = np.mean([p['predicted'] for p in recent])
        avg_actual = np.mean([p['actual'] for p in recent])

        if avg_predicted == 0:
            return 1.0

        # Adjustment factor: if we over-predict, factor < 1; under-predict, factor > 1
        adjustment = avg_actual / avg_predicted

        # Cap adjustment to reasonable range
        adjustment = np.clip(adjustment, 0.5, 1.5)

        return adjustment

class FeatureEngineer:
    """
    Feature engineering for route-level ML models.
    Extracts meaningful patterns from historical data.
    """
    @staticmethod
    def extract_features(df, target_odc, target_ddc, target_product, target_dow, target_week, target_year):
        """
        Extract features for a specific route-day combination.

        Features:
        - Shipping frequency (last 4, 8, 12 weeks)
        - Days since last shipment
        - Volume trends
        - Day-of-week patterns
        - Week-of-year seasonality
        - Route stability (variance)
        """
        route_data = df[
            (df['ODC'] == target_odc) &
            (df['DDC'] == target_ddc) &
            (df['ProductType'] == target_product) &
            (df['dayofweek'] == target_dow)
        ].copy()

        features = {
            'ODC': target_odc,
            'DDC': target_ddc,
            'ProductType': target_product,
            'dayofweek': target_dow,
            'week': target_week,
            'year': target_year
        }

        if len(route_data) == 0:
            # New route with no history
            features.update({
                'shipped_last_4w': 0,
                'shipped_last_8w': 0,
                'shipped_last_12w': 0,
                'days_since_last': 999,
                'avg_volume_4w': 0,
                'avg_volume_8w': 0,
                'volume_trend': 0,
                'volume_std': 0,
                'seasonality_score': 0,
                'is_new_route': 1
            })
            return features

        route_data = route_data.sort_values('date', ascending=False)

        # Shipping frequency
        cutoff_4w = route_data['date'].max() - timedelta(weeks=4)
        cutoff_8w = route_data['date'].max() - timedelta(weeks=8)
        cutoff_12w = route_data['date'].max() - timedelta(weeks=12)

        features['shipped_last_4w'] = len(route_data[route_data['date'] >= cutoff_4w])
        features['shipped_last_8w'] = len(route_data[route_data['date'] >= cutoff_8w])
        features['shipped_last_12w'] = len(route_data[route_data['date'] >= cutoff_12w])

        # Days since last shipment
        days_since = (datetime.now() - route_data.iloc[0]['date']).days
        features['days_since_last'] = min(days_since, 999)

        # Volume averages
        recent_4w = route_data[route_data['date'] >= cutoff_4w]
        recent_8w = route_data[route_data['date'] >= cutoff_8w]

        features['avg_volume_4w'] = recent_4w['pieces'].mean() if len(recent_4w) > 0 else 0
        features['avg_volume_8w'] = recent_8w['pieces'].mean() if len(recent_8w) > 0 else 0

        # Volume trend (is it growing or declining?)
        if len(route_data) >= 4:
            mid = len(route_data) // 2
            recent_avg = route_data.iloc[:mid]['pieces'].mean()
            older_avg = route_data.iloc[mid:]['pieces'].mean()
            features['volume_trend'] = (recent_avg - older_avg) / (older_avg + 1)
        else:
            features['volume_trend'] = 0

        # Volume stability (standard deviation)
        features['volume_std'] = route_data['pieces'].std() if len(route_data) > 1 else 0

        # Seasonality (has this route shipped in this week before?)
        same_week_data = route_data[route_data['week'] == target_week]
        features['seasonality_score'] = len(same_week_data)

        # Is this a new route?
        features['is_new_route'] = 0

        return features

def connect_to_databricks():
    """Establish connection to Azure Databricks."""
    try:
        conn = sql.connect(**DATABRICKS_CONFIG)
        print("✅ Connected to Azure Databricks")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)

def load_training_data(conn, table_name, weeks_back=16):
    """
    Load historical data for training.
    We need enough history to learn patterns.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=weeks_back)

    query = f"""
    SELECT
        DATE_SHIP as date,
        ODC, DDC, ProductType,
        PIECES as pieces,
        weekofyear(DATE_SHIP) as week,
        YEAR(DATE_SHIP) as year,
        dayofweek(DATE_SHIP) as dayofweek
    FROM {table_name}
    WHERE DATE_SHIP >= '{start_date.strftime('%Y-%m-%d')}'
        AND ProductType IN ('MAX', 'EXP')
        AND ODC IS NOT NULL
        AND DDC IS NOT NULL
    ORDER BY DATE_SHIP
    """

    print(f"\n📊 Loading training data ({weeks_back} weeks)...")
    print(f"   Date range: {start_date.date()} to {end_date.date()}")

    df = pd.read_sql(query, conn)
    df['date'] = pd.to_datetime(df['date'])

    print(f"   ✅ Loaded {len(df):,} shipments")

    return df

def build_training_dataset(df, target_week, target_year):
    """
    Build training dataset with features and labels.

    For each potential route-day in recent weeks:
    - Extract features
    - Label: did it ship? (1/0)
    - If shipped, what volume?
    """
    print(f"\n🔨 Building training dataset...")

    # Get all unique route-day combinations from recent data
    route_days = df.groupby(['ODC', 'DDC', 'ProductType', 'dayofweek']).size().reset_index(name='count')

    # Use data before target week for training
    year_start = datetime(target_year, 1, 1)
    target_date = year_start + timedelta(weeks=target_week - 1)

    train_data = df[df['date'] < target_date - timedelta(weeks=2)]  # Leave 2-week gap

    # Build features for each route-day
    training_samples = []

    for idx, row in route_days.iterrows():
        # Extract features
        features = FeatureEngineer.extract_features(
            train_data,
            row['ODC'], row['DDC'], row['ProductType'], row['dayofweek'],
            target_week, target_year
        )

        # Get actual outcome (did this route ship in the validation period?)
        validation_data = df[
            (df['date'] >= target_date - timedelta(weeks=2)) &
            (df['date'] < target_date) &
            (df['ODC'] == row['ODC']) &
            (df['DDC'] == row['DDC']) &
            (df['ProductType'] == row['ProductType']) &
            (df['dayofweek'] == row['dayofweek'])
        ]

        if len(validation_data) > 0:
            features['shipped'] = 1
            features['volume'] = validation_data['pieces'].mean()
        else:
            features['shipped'] = 0
            features['volume'] = 0

        training_samples.append(features)

        if (idx + 1) % 100 == 0:
            print(f"      Processed {idx + 1}/{len(route_days)} routes...")

    df_train = pd.DataFrame(training_samples)

    print(f"   ✅ Built {len(df_train)} training samples")
    print(f"   Positive samples (shipped): {df_train['shipped'].sum()}")
    print(f"   Negative samples (didn't ship): {len(df_train) - df_train['shipped'].sum()}")

    return df_train

def train_models(df_train):
    """
    Train ML models:
    1. Classification: Will route ship?
    2. Regression: If yes, how much?
    """
    print(f"\n🤖 Training ML models...")

    # Separate features and labels
    feature_cols = [
        'shipped_last_4w', 'shipped_last_8w', 'shipped_last_12w',
        'days_since_last', 'avg_volume_4w', 'avg_volume_8w',
        'volume_trend', 'volume_std', 'seasonality_score',
        'is_new_route', 'dayofweek', 'week'
    ]

    X = df_train[feature_cols]
    y_class = df_train['shipped']
    y_reg = df_train['volume']

    # Train-test split
    X_train, X_test, y_class_train, y_class_test = train_test_split(
        X, y_class, test_size=0.2, random_state=42
    )

    # Classification Model
    print(f"\n   Training Classification Model (Will it ship?)...")
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=10,
        random_state=42
    )
    clf.fit(X_train, y_class_train)

    y_pred_class = clf.predict(X_test)
    accuracy = accuracy_score(y_class_test, y_pred_class)

    print(f"   ✅ Classification Accuracy: {accuracy*100:.1f}%")

    # Regression Model (only for routes that shipped)
    print(f"\n   Training Regression Model (How much?)...")
    shipped_mask = df_train['shipped'] == 1
    X_reg = df_train[shipped_mask][feature_cols]
    y_reg_train = df_train[shipped_mask]['volume']

    reg = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        random_state=42
    )
    reg.fit(X_reg, y_reg_train)

    # Evaluate on test set
    test_shipped_mask = y_class_test == 1
    if test_shipped_mask.sum() > 0:
        X_test_reg = X_test[test_shipped_mask]
        y_test_reg = df_train.iloc[X_test.index[test_shipped_mask]]['volume']
        y_pred_reg = reg.predict(X_test_reg)

        mae = mean_absolute_error(y_test_reg, y_pred_reg)
        print(f"   ✅ Regression MAE: {mae:.1f} pieces")

    # Feature importance
    print(f"\n   📊 Top 5 Important Features:")
    importances = pd.DataFrame({
        'feature': feature_cols,
        'importance': clf.feature_importances_
    }).sort_values('importance', ascending=False)

    for idx, row in importances.head(5).iterrows():
        print(f"      {row['feature']:<25} {row['importance']:.3f}")

    return clf, reg, feature_cols

def generate_ml_forecast(conn, clf, reg, feature_cols, memory, target_week, target_year, table_name):
    """
    Generate forecast using trained ML models + memory/learning.
    """
    print(f"\n{'='*80}")
    print(f"ML FORECASTING WITH MEMORY: Week {target_week}, {target_year}")
    print(f"{'='*80}\n")

    # Load recent data for feature extraction
    df_recent = load_training_data(conn, table_name, weeks_back=12)

    # Get all potential route-days from recent activity
    route_days = df_recent.groupby(['ODC', 'DDC', 'ProductType', 'dayofweek']).size().reset_index(name='count')
    route_days = route_days[route_days['count'] >= 2]  # Require min 2 shipments

    print(f"📊 Generating predictions for {len(route_days)} routes...")

    forecasts = []

    for idx, row in route_days.iterrows():
        # Extract features
        features = FeatureEngineer.extract_features(
            df_recent,
            row['ODC'], row['DDC'], row['ProductType'], row['dayofweek'],
            target_week, target_year
        )

        # Prepare features for prediction
        X_pred = pd.DataFrame([features])[feature_cols]

        # Step 1: Classification - Will it ship?
        ship_prob = clf.predict_proba(X_pred)[0][1]  # Probability of shipping
        will_ship = ship_prob > 0.5

        if not will_ship:
            continue

        # Step 2: Regression - How much?
        predicted_volume = reg.predict(X_pred)[0]

        # Step 3: Apply memory/learning adjustment
        adjustment = memory.get_adjustment_factor(
            row['ODC'], row['DDC'], row['ProductType'], row['dayofweek']
        )

        adjusted_volume = predicted_volume * adjustment

        # Get historical error rate for confidence
        historical_error = memory.get_route_error_rate(
            row['ODC'], row['DDC'], row['ProductType'], row['dayofweek']
        )

        if historical_error is not None:
            confidence = max(0.1, 1.0 - (historical_error / (adjusted_volume + 1)))
        else:
            confidence = ship_prob

        forecasts.append({
            'ODC': row['ODC'],
            'DDC': row['DDC'],
            'ProductType': row['ProductType'],
            'dayofweek': row['dayofweek'],
            'ship_probability': ship_prob,
            'predicted_volume_raw': predicted_volume,
            'adjustment_factor': adjustment,
            'forecast': adjusted_volume,
            'confidence': confidence,
            'historical_error': historical_error if historical_error else 0,
            'week': target_week,
            'year': target_year,
            'model': 'ML_with_Memory'
        })

        if (idx + 1) % 100 == 0:
            print(f"   Processed {idx + 1}/{len(route_days)} routes...")

    df_forecast = pd.DataFrame(forecasts)

    print(f"\n✅ ML Forecast Generated:")
    print(f"   Routes: {len(df_forecast)}")
    print(f"   Total Pieces: {df_forecast['forecast'].sum():,.0f}")

    print(f"\n📦 By Product:")
    for product in ['MAX', 'EXP']:
        vol = df_forecast[df_forecast['ProductType'] == product]['forecast'].sum()
        routes = len(df_forecast[df_forecast['ProductType'] == product])
        print(f"   {product}: {vol:>12,.0f} pieces ({routes:>6} routes)")

    print(f"\n📈 Confidence Distribution:")
    high = len(df_forecast[df_forecast['confidence'] >= 0.7])
    med = len(df_forecast[(df_forecast['confidence'] >= 0.4) & (df_forecast['confidence'] < 0.7)])
    low = len(df_forecast[df_forecast['confidence'] < 0.4])
    print(f"   High (≥70%): {high:>6} routes")
    print(f"   Medium (40-70%): {med:>6} routes")
    print(f"   Low (<40%): {low:>6} routes")

    return df_forecast

def save_models(clf, reg, feature_cols, output_dir='models'):
    """Save trained models for reuse."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    with open(output_path / 'classifier.pkl', 'wb') as f:
        pickle.dump(clf, f)

    with open(output_path / 'regressor.pkl', 'wb') as f:
        pickle.dump(reg, f)

    with open(output_path / 'feature_cols.json', 'w') as f:
        json.dump(feature_cols, f)

    print(f"\n💾 Models saved to: {output_path}/")

def save_forecast(forecast, output_path=None):
    """Save forecast to CSV."""
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"ml_forecast_week_{forecast['week'].iloc[0]}_{forecast['year'].iloc[0]}_{timestamp}.csv"

    output_path = Path(output_path)
    forecast.to_csv(output_path, index=False)
    print(f"\n💾 Forecast saved to: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description="ML Forecasting with Memory & Learning")
    parser.add_argument('--week', type=int, required=True, help='Target week (1-53)')
    parser.add_argument('--year', type=int, required=True, help='Target year')
    parser.add_argument('--train', action='store_true', help='Train new models (default: use existing)')
    parser.add_argument('--output', type=str, default=None, help='Output CSV path')
    parser.add_argument('--table', type=str, default='decus_domesticops_prod.dbo.tmp_hassett_report')
    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"MACHINE LEARNING FORECASTING MODEL")
    print(f"With Memory, Learning & Dynamic Adjustment")
    print(f"{'='*80}\n")

    conn = connect_to_databricks()
    memory = RouteMemory()

    try:
        # Train or load models
        if args.train or not Path('models/classifier.pkl').exists():
            print("🔄 Training new models...")
            df_historical = load_training_data(conn, args.table, weeks_back=16)
            df_train = build_training_dataset(df_historical, args.week, args.year)
            clf, reg, feature_cols = train_models(df_train)
            save_models(clf, reg, feature_cols)
        else:
            print("📂 Loading existing models...")
            with open('models/classifier.pkl', 'rb') as f:
                clf = pickle.load(f)
            with open('models/regressor.pkl', 'rb') as f:
                reg = pickle.load(f)
            with open('models/feature_cols.json', 'r') as f:
                feature_cols = json.load(f)
            print("   ✅ Models loaded")

        # Generate forecast
        forecast = generate_ml_forecast(conn, clf, reg, feature_cols, memory,
                                       args.week, args.year, args.table)

        if len(forecast) > 0:
            save_forecast(forecast, args.output)
            print(f"\n{'='*80}")
            print(f"✅ ML FORECAST COMPLETE!")
            print(f"{'='*80}\n")
        else:
            print("❌ Forecast generation failed")
            sys.exit(1)

    finally:
        conn.close()

if __name__ == "__main__":
    main()
