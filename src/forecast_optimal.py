#!/usr/bin/env python3
"""
OPTIMAL FORECASTING MODEL - ML Classification + Simple Volume

Combines the best of both approaches:
  1. ML Classifier identifies which routes will ship (68% coverage)
  2. Simple recent averaging for volume prediction (robust accuracy)
  3. Memory-based adjustments for continuous learning

This addresses the key finding: ML is great at route selection,
but simple averaging beats regression for volume prediction.
"""

import argparse
import sys
import pickle
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from databricks import sql

DATABRICKS_CONFIG = {
    "server_hostname": "adb-434028626745069.9.azuredatabricks.net",
    "http_path": "/sql/1.0/warehouses/23a9897d305fb7e2",
    "auth_type": "databricks-oauth"
}

def connect_to_databricks():
    """Establish connection to Azure Databricks."""
    try:
        conn = sql.connect(**DATABRICKS_CONFIG)
        print("✅ Connected to Azure Databricks")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)

def load_recent_data(conn, target_week, target_year, table_name, lookback_weeks=12):
    """Load recent shipment data for analysis."""
    year_start = datetime(target_year, 1, 1)
    target_date = year_start + timedelta(weeks=target_week - 1)
    lookback_date = target_date - timedelta(weeks=lookback_weeks)

    query = f"""
    SELECT
        DATE_SHIP as date,
        ODC, DDC, ProductType,
        PIECES as pieces,
        weekofyear(DATE_SHIP) as week,
        YEAR(DATE_SHIP) as year,
        dayofweek(DATE_SHIP) as dayofweek
    FROM {table_name}
    WHERE DATE_SHIP >= '{lookback_date.strftime('%Y-%m-%d')}'
        AND DATE_SHIP < '{target_date.strftime('%Y-%m-%d')}'
        AND ProductType IN ('MAX', 'EXP')
        AND ODC IS NOT NULL
        AND DDC IS NOT NULL
    ORDER BY DATE_SHIP DESC
    """

    print(f"📊 Loading {lookback_weeks} weeks of recent data...")
    print(f"   Date range: {lookback_date.date()} to {target_date.date()}")

    df = pd.read_sql(query, conn)
    df['date'] = pd.to_datetime(df['date'])

    print(f"✅ Loaded {len(df):,} shipments")

    return df

def extract_features(df, odc, ddc, product, dow, cutoff_date):
    """
    Extract ML features for a single route.

    Same feature engineering as the ML model for consistency.
    """
    route_data = df[
        (df['ODC'] == odc) &
        (df['DDC'] == ddc) &
        (df['ProductType'] == product) &
        (df['dayofweek'] == dow) &
        (df['date'] < cutoff_date)
    ].sort_values('date', ascending=False)

    # Calculate features
    shipped_last_4w = len(route_data[route_data['date'] >= (cutoff_date - timedelta(weeks=4))])
    shipped_last_8w = len(route_data[route_data['date'] >= (cutoff_date - timedelta(weeks=8))])
    shipped_last_12w = len(route_data)

    if len(route_data) > 0:
        days_since_last = (cutoff_date - route_data.iloc[0]['date']).days

        recent_4w = route_data[route_data['date'] >= (cutoff_date - timedelta(weeks=4))]
        recent_8w = route_data[route_data['date'] >= (cutoff_date - timedelta(weeks=8))]

        avg_volume_4w = recent_4w['pieces'].mean() if len(recent_4w) > 0 else 0
        avg_volume_8w = recent_8w['pieces'].mean() if len(recent_8w) > 0 else 0
        volume_std = route_data['pieces'].std() if len(route_data) > 1 else 0

        # Volume trend: recent vs older
        mid_point = len(route_data) // 2
        if mid_point > 0:
            recent_avg = route_data.iloc[:mid_point]['pieces'].mean()
            older_avg = route_data.iloc[mid_point:]['pieces'].mean()
            volume_trend = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
        else:
            volume_trend = 0
    else:
        days_since_last = 999
        avg_volume_4w = 0
        avg_volume_8w = 0
        volume_std = 0
        volume_trend = 0

    week = cutoff_date.isocalendar()[1]
    seasonality_score = len(route_data[route_data['week'] == week])
    is_new_route = 1 if shipped_last_12w == 0 else 0

    return {
        'shipped_last_4w': shipped_last_4w,
        'shipped_last_8w': shipped_last_8w,
        'shipped_last_12w': shipped_last_12w,
        'days_since_last': days_since_last,
        'avg_volume_4w': avg_volume_4w,
        'avg_volume_8w': avg_volume_8w,
        'volume_trend': volume_trend,
        'volume_std': volume_std,
        'seasonality_score': seasonality_score,
        'is_new_route': is_new_route,
        'dayofweek': dow,
        'week': week
    }

def calculate_simple_volume(df, odc, ddc, product, dow, cutoff_date, weeks=4):
    """
    Calculate volume using SIMPLE AVERAGING (not ML regression).

    This is what the hybrid model does - and it works!
    """
    route_data = df[
        (df['ODC'] == odc) &
        (df['DDC'] == ddc) &
        (df['ProductType'] == product) &
        (df['dayofweek'] == dow) &
        (df['date'] < cutoff_date)
    ].sort_values('date', ascending=False)

    # Get last N weeks
    recent = route_data.head(weeks)

    if len(recent) > 0:
        return recent['pieces'].mean(), len(recent)

    # Fallback: try without day-of-week filter
    route_data_any_day = df[
        (df['ODC'] == odc) &
        (df['DDC'] == ddc) &
        (df['ProductType'] == product) &
        (df['date'] < cutoff_date)
    ].sort_values('date', ascending=False).head(weeks)

    if len(route_data_any_day) > 0:
        # Scale down by days/week
        return route_data_any_day['pieces'].mean() * 0.3, len(route_data_any_day)

    return 0, 0

def load_memory(memory_file='route_memory.json'):
    """Load route memory for adjustment factors."""
    import json
    memory_path = Path(memory_file)
    if memory_path.exists():
        with open(memory_path, 'r') as f:
            return json.load(f)
    return {}

def get_adjustment_factor(memory, odc, ddc, product, dow):
    """Get adjustment factor from memory."""
    route_key = f"{odc}|{ddc}|{product}|{dow}"

    if route_key not in memory:
        return 1.0

    predictions = memory[route_key].get('predictions', [])
    if len(predictions) < 3:  # Need at least 3 predictions
        return 1.0

    # Use last 5 predictions
    recent = predictions[-5:]
    total_predicted = sum(p['predicted'] for p in recent)
    total_actual = sum(p['actual'] for p in recent)

    if total_predicted > 0:
        adjustment = total_actual / total_predicted
        # Cap adjustment between 0.5 and 1.5
        return max(0.5, min(1.5, adjustment))

    return 1.0

def generate_optimal_forecast(conn, target_week, target_year, table_name):
    """
    Generate forecast using OPTIMAL approach:
      1. ML Classifier to identify routes
      2. Simple averaging for volume
      3. Memory-based adjustments
    """
    print(f"\n{'='*80}")
    print(f"OPTIMAL FORECASTING: Week {target_week}, {target_year}")
    print(f"ML Classification + Simple Volume Averaging")
    print(f"{'='*80}\n")

    # Load ML classifier
    model_path = Path('models/classifier.pkl')
    if not model_path.exists():
        print("❌ ML classifier not found. Please run forecast_ml.py --train first")
        sys.exit(1)

    with open(model_path, 'rb') as f:
        classifier = pickle.load(f)
    print("✅ Loaded ML classifier")

    # Load memory
    memory = load_memory()
    print(f"✅ Loaded memory ({len(memory)} routes tracked)")

    # Load data
    df = load_recent_data(conn, target_week, target_year, table_name, lookback_weeks=12)

    # Get all unique route-day combinations from recent 8 weeks
    recent_cutoff = df['date'].max() - timedelta(weeks=8)
    recent_routes = df[df['date'] >= recent_cutoff].groupby(
        ['ODC', 'DDC', 'ProductType', 'dayofweek']
    ).size().reset_index(name='count')

    print(f"\n🔍 Analyzing {len(recent_routes)} potential routes...")
    print(f"   Step 1: ML Classification (will it ship?)")
    print(f"   Step 2: Simple volume averaging")
    print(f"   Step 3: Memory-based adjustment")

    year_start = datetime(target_year, 1, 1)
    target_date = year_start + timedelta(weeks=target_week - 1)

    forecasts = []
    routes_selected = 0
    routes_rejected = 0

    for idx, row in recent_routes.iterrows():
        odc = row['ODC']
        ddc = row['DDC']
        product = row['ProductType']
        dow = row['dayofweek']

        # Extract features
        features = extract_features(df, odc, ddc, product, dow, target_date)
        feature_vector = np.array([[
            features['shipped_last_4w'],
            features['shipped_last_8w'],
            features['shipped_last_12w'],
            features['days_since_last'],
            features['avg_volume_4w'],
            features['avg_volume_8w'],
            features['volume_trend'],
            features['volume_std'],
            features['seasonality_score'],
            features['is_new_route'],
            features['dayofweek'],
            features['week']
        ]])

        # Step 1: ML Classification
        ship_prob = classifier.predict_proba(feature_vector)[0][1]

        # Only forecast if probability > 50%
        if ship_prob > 0.5:
            routes_selected += 1

            # Step 2: Simple volume averaging (NOT regression)
            volume, data_points = calculate_simple_volume(
                df, odc, ddc, product, dow, target_date, weeks=4
            )

            if volume > 0:
                # Step 3: Memory-based adjustment
                adjustment = get_adjustment_factor(memory, odc, ddc, product, dow)
                final_forecast = volume * adjustment

                forecasts.append({
                    'ODC': odc,
                    'DDC': ddc,
                    'ProductType': product,
                    'dayofweek': dow,
                    'ship_probability': ship_prob,
                    'volume_raw': volume,
                    'adjustment_factor': adjustment,
                    'forecast': final_forecast,
                    'confidence': ship_prob,
                    'data_points': data_points,
                    'week': target_week,
                    'year': target_year,
                    'model': 'Optimal_ML_Classification+Simple_Volume'
                })
        else:
            routes_rejected += 1

        # Progress indicator
        if (idx + 1) % 100 == 0:
            print(f"   Processed {idx + 1}/{len(recent_routes)} routes... "
                  f"(Selected: {routes_selected}, Rejected: {routes_rejected})")

    forecast_df = pd.DataFrame(forecasts)

    # Summary
    print(f"\n✅ Optimal Forecast Generated:")
    print(f"   Routes selected: {routes_selected}")
    print(f"   Routes rejected: {routes_rejected}")
    print(f"   Total forecast: {forecast_df['forecast'].sum():,.0f} pieces")

    print(f"\n📦 By Product:")
    for product in ['MAX', 'EXP']:
        product_forecast = forecast_df[forecast_df['ProductType'] == product]['forecast'].sum()
        product_routes = len(forecast_df[forecast_df['ProductType'] == product])
        print(f"   {product}: {product_forecast:,.0f} pieces ({product_routes} routes)")

    print(f"\n📈 Confidence Distribution:")
    high_conf = len(forecast_df[forecast_df['confidence'] >= 0.7])
    med_conf = len(forecast_df[(forecast_df['confidence'] >= 0.4) & (forecast_df['confidence'] < 0.7)])
    low_conf = len(forecast_df[forecast_df['confidence'] < 0.4])
    print(f"   High (≥70%):   {high_conf} routes")
    print(f"   Medium (40-70%): {med_conf} routes")
    print(f"   Low (<40%):    {low_conf} routes")

    return forecast_df

def save_forecast(forecast, output_path=None):
    """Save forecast to CSV."""
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"optimal_forecast_week_{forecast['week'].iloc[0]}_{forecast['year'].iloc[0]}_{timestamp}.csv"

    output_path = Path(output_path)
    forecast.to_csv(output_path, index=False)
    print(f"\n💾 Forecast saved to: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(
        description="OPTIMAL: ML Classification + Simple Volume Averaging"
    )
    parser.add_argument('--week', type=int, required=True, help='Target week (1-53)')
    parser.add_argument('--year', type=int, required=True, help='Target year')
    parser.add_argument('--output', type=str, default=None, help='Output CSV path')
    parser.add_argument('--table', type=str, default='decus_domesticops_prod.dbo.tmp_hassett_report')
    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"OPTIMAL HASSETT FORECASTING")
    print(f"ML Classification + Simple Volume Averaging")
    print(f"{'='*80}\n")

    conn = connect_to_databricks()

    try:
        forecast = generate_optimal_forecast(conn, args.week, args.year, args.table)

        if len(forecast) > 0:
            save_forecast(forecast, args.output)
            print(f"\n{'='*80}")
            print(f"✅ OPTIMAL FORECAST COMPLETE!")
            print(f"{'='*80}\n")
        else:
            print("❌ Forecast generation failed")
            sys.exit(1)

    finally:
        conn.close()

if __name__ == "__main__":
    main()
