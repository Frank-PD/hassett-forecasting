#!/usr/bin/env python3
"""
ENSEMBLE FORECASTING - Multi-Method with Dynamic Selection
For each route, calculate forecasts using MULTIPLE methods:
  1. Historical baseline (Week N from 2022/2024)
  2. Recent 4-week average
  3. Prior week (Week N-1)
  4. Same week last year
  5. Recent trend-adjusted

Then SELECT the method with lowest historical error for that route.
This allows different routes to use different methods!
"""

import argparse
import sys
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

def load_all_data(conn, target_week, target_year, table_name):
    """Load ALL data needed for ensemble methods."""

    year_start = datetime(target_year, 1, 1)
    target_date = year_start + timedelta(weeks=target_week - 1)

    # Load last 12 weeks for comprehensive analysis
    lookback_date = target_date - timedelta(weeks=12)

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
        AND ProductType IN ('MAX', 'EXP')
        AND ODC IS NOT NULL
        AND DDC IS NOT NULL
    ORDER BY DATE_SHIP DESC
    """

    print(f"📊 Loading data for ensemble methods...")
    print(f"   Date range: {lookback_date.date()} to {target_date.date()}")

    df = pd.read_sql(query, conn)
    df['date'] = pd.to_datetime(df['date'])

    print(f"✅ Loaded {len(df):,} shipments")

    return df

def method_1_historical_baseline(df, route_key, target_week):
    """Method 1: Historical baseline (Week N from 2022/2024)"""
    odc, ddc, product, dow = route_key
    baseline_year = 2022 if product == 'MAX' else 2024

    data = df[
        (df['ODC'] == odc) &
        (df['DDC'] == ddc) &
        (df['ProductType'] == product) &
        (df['dayofweek'] == dow) &
        (df['week'] == target_week) &
        (df['year'] == baseline_year)
    ]

    if len(data) > 0:
        return data['pieces'].mean(), len(data)
    return None, 0

def method_2_recent_average(df, route_key, weeks=4):
    """Method 2: Recent N-week average"""
    odc, ddc, product, dow = route_key

    data = df[
        (df['ODC'] == odc) &
        (df['DDC'] == ddc) &
        (df['ProductType'] == product) &
        (df['dayofweek'] == dow)
    ].nlargest(weeks * 2, 'date')  # Get last N weeks

    if len(data) > 0:
        return data['pieces'].mean(), len(data)
    return None, 0

def method_3_prior_week(df, route_key, target_week):
    """Method 3: Prior week (Week N-1)"""
    odc, ddc, product, dow = route_key
    prior_week = target_week - 1

    data = df[
        (df['ODC'] == odc) &
        (df['DDC'] == ddc) &
        (df['ProductType'] == product) &
        (df['dayofweek'] == dow) &
        (df['week'] == prior_week)
    ]

    if len(data) > 0:
        return data['pieces'].mean(), len(data)
    return None, 0

def method_4_same_week_last_year(df, route_key, target_week, target_year):
    """Method 4: Same week from last year"""
    odc, ddc, product, dow = route_key
    last_year = target_year - 1

    data = df[
        (df['ODC'] == odc) &
        (df['DDC'] == ddc) &
        (df['ProductType'] == product) &
        (df['dayofweek'] == dow) &
        (df['week'] == target_week) &
        (df['year'] == last_year)
    ]

    if len(data) > 0:
        return data['pieces'].mean(), len(data)
    return None, 0

def method_5_trend_adjusted(df, route_key):
    """Method 5: Recent trend applied to baseline"""
    odc, ddc, product, dow = route_key

    route_data = df[
        (df['ODC'] == odc) &
        (df['DDC'] == ddc) &
        (df['ProductType'] == product) &
        (df['dayofweek'] == dow)
    ].sort_values('date')

    if len(route_data) < 4:
        return None, 0

    # Split into recent and previous
    mid = len(route_data) // 2
    recent = route_data.iloc[mid:]
    previous = route_data.iloc[:mid]

    if len(recent) > 0 and len(previous) > 0:
        recent_avg = recent['pieces'].mean()
        previous_avg = previous['pieces'].mean()
        trend = recent_avg / previous_avg if previous_avg > 0 else 1.0

        # Apply trend to baseline
        baseline = previous_avg * trend
        return baseline, len(route_data)

    return None, 0

def calculate_historical_accuracy(df, route_key, method_func, validation_weeks=4, **kwargs):
    """
    Calculate how accurate this method would have been historically.
    Look at last N weeks and see what error the method would have had.
    """
    odc, ddc, product, dow = route_key

    # Get actual data from validation period
    validation_data = df[
        (df['ODC'] == odc) &
        (df['DDC'] == ddc) &
        (df['ProductType'] == product) &
        (df['dayofweek'] == dow)
    ].nlargest(validation_weeks, 'date')

    if len(validation_data) == 0:
        return np.inf, 0  # No data = infinite error

    errors = []
    for _, row in validation_data.iterrows():
        # Get data excluding this week
        df_exclude = df[df['date'] < row['date']]

        # Calculate forecast using this method
        forecast, _ = method_func(df_exclude, route_key, **kwargs)

        if forecast is not None:
            actual = row['pieces']
            error = abs(forecast - actual)
            errors.append(error)

    if len(errors) > 0:
        mae = np.mean(errors)  # Mean Absolute Error
        return mae, len(errors)

    return np.inf, 0

def generate_ensemble_forecast(conn, target_week, target_year, table_name):
    """
    Generate forecast using ENSEMBLE approach.
    For each route, try all methods and pick the best one.
    """
    print(f"\n{'='*80}")
    print(f"ENSEMBLE FORECASTING: Week {target_week}, {target_year}")
    print(f"Dynamic Method Selection per Route")
    print(f"{'='*80}\n")

    # Load all data
    df = load_all_data(conn, target_week, target_year, table_name)

    # Get all unique route-day combinations from recent data
    recent_cutoff = df['date'].max() - timedelta(weeks=8)
    recent_routes = df[df['date'] >= recent_cutoff].groupby(
        ['ODC', 'DDC', 'ProductType', 'dayofweek']
    ).size().reset_index(name='count')

    print(f"\n🔍 Evaluating {len(recent_routes)} active routes...")
    print(f"   Testing 5 forecasting methods per route...")

    forecasts = []
    method_counts = {
        'Historical Baseline': 0,
        'Recent Average': 0,
        'Prior Week': 0,
        'Same Week Last Year': 0,
        'Trend Adjusted': 0
    }

    for idx, row in recent_routes.iterrows():
        route_key = (row['ODC'], row['DDC'], row['ProductType'], row['dayofweek'])

        # Calculate forecast using ALL methods
        methods = [
            ('Historical Baseline', method_1_historical_baseline, {'target_week': target_week}),
            ('Recent Average', method_2_recent_average, {'weeks': 4}),
            ('Prior Week', method_3_prior_week, {'target_week': target_week}),
            ('Same Week Last Year', method_4_same_week_last_year, {'target_week': target_week, 'target_year': target_year}),
            ('Trend Adjusted', method_5_trend_adjusted, {})
        ]

        best_method = None
        best_forecast = None
        best_error = np.inf

        for method_name, method_func, kwargs in methods:
            # Get forecast
            forecast, data_points = method_func(df, route_key, **kwargs)

            if forecast is None or data_points < 1:
                continue

            # Calculate historical accuracy (how well did this method work in past?)
            # For simplicity, use recent average as proxy for accuracy
            # In production, you'd do full backtesting
            mae, validation_points = calculate_historical_accuracy(
                df, route_key, method_func, validation_weeks=2, **kwargs
            )

            if mae < best_error and forecast > 0:
                best_error = mae
                best_forecast = forecast
                best_method = method_name

        # Save best forecast
        if best_forecast is not None:
            forecasts.append({
                'ODC': row['ODC'],
                'DDC': row['DDC'],
                'ProductType': row['ProductType'],
                'dayofweek': row['dayofweek'],
                'forecast': best_forecast,
                'method': best_method,
                'historical_mae': best_error,
                'confidence': min(1.0, 5.0 / (best_error + 1.0)),  # Lower error = higher confidence
                'week': target_week,
                'year': target_year
            })

            method_counts[best_method] += 1

        # Progress indicator
        if (idx + 1) % 100 == 0:
            print(f"   Processed {idx + 1}/{len(recent_routes)} routes...")

    forecast_df = pd.DataFrame(forecasts)

    # Summary
    print(f"\n✅ Ensemble Forecast Generated:")
    print(f"   Total routes: {len(forecast_df)}")
    print(f"   Total pieces: {forecast_df['forecast'].sum():,.0f}")

    print(f"\n📊 Method Selection Distribution:")
    for method, count in sorted(method_counts.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(forecast_df) * 100 if len(forecast_df) > 0 else 0
        print(f"   {method:<25} {count:>6} routes ({pct:>5.1f}%)")

    print(f"\n📦 By Product:")
    for product in ['MAX', 'EXP']:
        product_forecast = forecast_df[forecast_df['ProductType'] == product]['forecast'].sum()
        product_routes = len(forecast_df[forecast_df['ProductType'] == product])
        print(f"   {product}: {product_forecast:,.0f} pieces ({product_routes} routes)")

    return forecast_df

def save_forecast(forecast, output_path=None):
    """Save forecast to CSV."""
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"ensemble_week_{forecast['week'].iloc[0]}_{forecast['year'].iloc[0]}_{timestamp}.csv"

    output_path = Path(output_path)
    forecast.to_csv(output_path, index=False)
    print(f"\n💾 Saved to: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description="ENSEMBLE: Multi-Method Dynamic Selection")
    parser.add_argument('--week', type=int, required=True, help='Target week (1-53)')
    parser.add_argument('--year', type=int, required=True, help='Target year')
    parser.add_argument('--output', type=str, default=None, help='Output CSV path')
    parser.add_argument('--table', type=str, default='decus_domesticops_prod.dbo.tmp_hassett_report')
    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"ENSEMBLE HASSETT FORECASTING")
    print(f"Multi-Method with Dynamic Route-Level Selection")
    print(f"{'='*80}\n")

    conn = connect_to_databricks()

    try:
        forecast = generate_ensemble_forecast(conn, args.week, args.year, args.table)

        if len(forecast) > 0:
            save_forecast(forecast, args.output)
            print(f"\n{'='*80}")
            print(f"✅ ENSEMBLE FORECAST COMPLETE!")
            print(f"{'='*80}\n")
        else:
            print("❌ Forecast generation failed")
            sys.exit(1)

    finally:
        conn.close()

if __name__ == "__main__":
    main()
