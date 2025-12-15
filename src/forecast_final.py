#!/usr/bin/env python3
"""
FINAL FORECASTING MODEL - Hybrid-Ensemble Approach
Combines:
  1. HYBRID route selection (baseline + recent validation)
  2. ENSEMBLE method selection (try multiple methods, pick best per route)
  3. NEW route detection (routes in recent but not baseline)

This is the ultimate model for granular route-level accuracy.
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

def load_baseline_routes(conn, target_week, table_name):
    """
    STEP 1: Get baseline routes (which routes ship in Week N historically?)
    Uses HYBRID approach - Week 50 from 2022 (MAX) / 2024 (EXP)
    """
    baseline_year_max = 2022
    baseline_year_exp = 2024

    query = f"""
    SELECT
        ODC, DDC, ProductType, dayofweek(DATE_SHIP) as dayofweek,
        AVG(PIECES) as baseline_pieces,
        COUNT(*) as baseline_count
    FROM {table_name}
    WHERE weekofyear(DATE_SHIP) = {target_week}
        AND ((ProductType = 'MAX' AND YEAR(DATE_SHIP) = {baseline_year_max})
             OR (ProductType = 'EXP' AND YEAR(DATE_SHIP) = {baseline_year_exp}))
        AND ProductType IN ('MAX', 'EXP')
        AND ODC IS NOT NULL
        AND DDC IS NOT NULL
    GROUP BY ODC, DDC, ProductType, dayofweek(DATE_SHIP)
    """

    print(f"\n📊 STEP 1: Loading baseline routes (Week {target_week})...")
    print(f"   MAX from {baseline_year_max}, EXP from {baseline_year_exp}")

    df = pd.read_sql(query, conn)
    print(f"   ✅ {len(df)} route-day combinations in baseline")

    return df

def load_recent_data(conn, target_week, target_year, lookback_weeks, table_name):
    """
    Load recent data for validation and forecasting.
    """
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

    print(f"\n📊 STEP 2: Loading recent data ({lookback_weeks} weeks)...")
    print(f"   Date range: {lookback_date.date()} to {target_date.date()}")

    df = pd.read_sql(query, conn)
    df['date'] = pd.to_datetime(df['date'])

    print(f"   ✅ {len(df):,} shipments loaded")

    return df

def validate_active_routes(baseline_routes, recent_data, min_shipments=1):
    """
    STEP 2: Validate which baseline routes are still ACTIVE.
    Filter out dead routes.
    """
    print(f"\n🔍 STEP 3: Validating active routes...")

    # Get recent activity per route-day
    recent_activity = recent_data.groupby(['ODC', 'DDC', 'ProductType', 'dayofweek']).agg({
        'pieces': ['sum', 'count', 'mean']
    }).reset_index()

    recent_activity.columns = ['ODC', 'DDC', 'ProductType', 'dayofweek', 'recent_total', 'recent_count', 'recent_avg']

    # Merge with baseline
    active_routes = baseline_routes.merge(
        recent_activity,
        on=['ODC', 'DDC', 'ProductType', 'dayofweek'],
        how='inner'  # Only keep routes in BOTH baseline AND recent
    )

    # Filter by minimum shipments
    active_routes = active_routes[active_routes['recent_count'] >= min_shipments]

    print(f"   Baseline routes: {len(baseline_routes)}")
    print(f"   Still active: {len(active_routes)}")
    print(f"   Filtered out (dead): {len(baseline_routes) - len(active_routes)}")

    return active_routes

def forecast_method_recent_avg(route_data, weeks=4):
    """Method 1: Recent N-week average"""
    recent = route_data.nlargest(weeks * 7, 'date')  # Last N weeks
    if len(recent) > 0:
        return recent['pieces'].mean(), len(recent)
    return None, 0

def forecast_method_prior_week(route_data, target_week):
    """Method 2: Prior week (Week N-1)"""
    prior_week = target_week - 1
    data = route_data[route_data['week'] == prior_week]
    if len(data) > 0:
        return data['pieces'].mean(), len(data)
    return None, 0

def forecast_method_trend_adjusted(route_data):
    """Method 3: Trend-adjusted (recent trend applied)"""
    if len(route_data) < 4:
        return None, 0

    sorted_data = route_data.sort_values('date')
    mid = len(sorted_data) // 2

    recent = sorted_data.iloc[mid:]
    previous = sorted_data.iloc[:mid]

    if len(recent) > 0 and len(previous) > 0:
        recent_avg = recent['pieces'].mean()
        previous_avg = previous['pieces'].mean()

        if previous_avg > 0:
            trend = recent_avg / previous_avg
            trend = np.clip(trend, 0.5, 2.0)  # Cap extreme trends
            forecast = recent_avg * trend
            return forecast, len(route_data)

    return None, 0

def forecast_method_same_week_last_year(route_data, target_week, target_year):
    """Method 4: Same week from last year"""
    last_year = target_year - 1
    data = route_data[(route_data['week'] == target_week) & (route_data['year'] == last_year)]
    if len(data) > 0:
        return data['pieces'].mean(), len(data)
    return None, 0

def evaluate_method_accuracy(route_data, method_func, validation_weeks=2, **kwargs):
    """
    Backtest a method to see how accurate it would have been.
    Returns Mean Absolute Error.
    """
    if len(route_data) < validation_weeks:
        return np.inf

    # Get most recent data for validation
    validation_data = route_data.nlargest(validation_weeks, 'date')

    errors = []
    for _, actual_row in validation_data.iterrows():
        # Get data before this date
        historical_data = route_data[route_data['date'] < actual_row['date']]

        if len(historical_data) == 0:
            continue

        # Try to forecast using this method
        forecast, _ = method_func(historical_data, **kwargs)

        if forecast is not None and forecast > 0:
            actual = actual_row['pieces']
            error = abs(forecast - actual)
            errors.append(error)

    if len(errors) > 0:
        return np.mean(errors)

    return np.inf

def apply_ensemble_to_routes(active_routes, recent_data, target_week, target_year):
    """
    STEP 3: For each active route, try multiple forecasting methods.
    Select the method with lowest historical error.
    """
    print(f"\n🎯 STEP 4: Applying ensemble method selection...")
    print(f"   Testing 4 methods per route...")

    forecasts = []
    method_counts = {
        'Recent Average': 0,
        'Prior Week': 0,
        'Trend Adjusted': 0,
        'Same Week Last Year': 0
    }

    total_routes = len(active_routes)

    for idx, route_row in active_routes.iterrows():
        # Get all data for this specific route-day
        route_data = recent_data[
            (recent_data['ODC'] == route_row['ODC']) &
            (recent_data['DDC'] == route_row['DDC']) &
            (recent_data['ProductType'] == route_row['ProductType']) &
            (recent_data['dayofweek'] == route_row['dayofweek'])
        ]

        if len(route_data) == 0:
            # Fallback to baseline if no recent data
            forecasts.append({
                'ODC': route_row['ODC'],
                'DDC': route_row['DDC'],
                'ProductType': route_row['ProductType'],
                'dayofweek': route_row['dayofweek'],
                'forecast': route_row['recent_avg'],  # From validation step
                'method': 'Recent Average (fallback)',
                'confidence': 0.5,
                'baseline_pieces': route_row['baseline_pieces'],
                'recent_avg': route_row['recent_avg']
            })
            continue

        # Try all methods
        methods = [
            ('Recent Average', forecast_method_recent_avg, {'weeks': 4}),
            ('Prior Week', forecast_method_prior_week, {'target_week': target_week}),
            ('Trend Adjusted', forecast_method_trend_adjusted, {}),
            ('Same Week Last Year', forecast_method_same_week_last_year,
             {'target_week': target_week, 'target_year': target_year})
        ]

        best_method = None
        best_forecast = None
        best_error = np.inf

        for method_name, method_func, kwargs in methods:
            # Get forecast
            forecast, data_points = method_func(route_data, **kwargs)

            if forecast is None or data_points == 0 or forecast <= 0:
                continue

            # Evaluate historical accuracy
            mae = evaluate_method_accuracy(route_data, method_func, validation_weeks=2, **kwargs)

            if mae < best_error:
                best_error = mae
                best_forecast = forecast
                best_method = method_name

        # If no method worked, use recent average as fallback
        if best_forecast is None:
            best_forecast = route_row['recent_avg']
            best_method = 'Recent Average (fallback)'
            best_error = 0

        # Save forecast
        forecasts.append({
            'ODC': route_row['ODC'],
            'DDC': route_row['DDC'],
            'ProductType': route_row['ProductType'],
            'dayofweek': route_row['dayofweek'],
            'forecast': best_forecast,
            'method': best_method,
            'historical_mae': best_error,
            'confidence': min(1.0, 10.0 / (best_error + 1.0)),
            'baseline_pieces': route_row['baseline_pieces'],
            'recent_avg': route_row['recent_avg']
        })

        if best_method in method_counts:
            method_counts[best_method] += 1

        # Progress
        if (idx + 1) % 100 == 0:
            print(f"      Processed {idx + 1}/{total_routes} routes...")

    print(f"   ✅ Ensemble complete for {len(forecasts)} routes")

    return pd.DataFrame(forecasts), method_counts

def detect_new_routes(baseline_routes, recent_data, target_week, min_shipments=2):
    """
    STEP 4: Detect NEW routes that exist in recent data but NOT in baseline.
    These are emerging routes we need to capture.
    """
    print(f"\n🆕 STEP 5: Detecting new routes...")

    # Get all recent route-days
    recent_routes = recent_data.groupby(['ODC', 'DDC', 'ProductType', 'dayofweek']).agg({
        'pieces': ['mean', 'count']
    }).reset_index()

    recent_routes.columns = ['ODC', 'DDC', 'ProductType', 'dayofweek', 'recent_avg', 'recent_count']

    # Filter by minimum shipments
    recent_routes = recent_routes[recent_routes['recent_count'] >= min_shipments]

    # Find routes NOT in baseline
    baseline_keys = set(
        baseline_routes[['ODC', 'DDC', 'ProductType', 'dayofweek']].apply(tuple, axis=1)
    )

    recent_keys = recent_routes[['ODC', 'DDC', 'ProductType', 'dayofweek']].apply(tuple, axis=1)

    new_route_mask = ~recent_keys.isin(baseline_keys)
    new_routes = recent_routes[new_route_mask].copy()

    if len(new_routes) > 0:
        new_routes['forecast'] = new_routes['recent_avg']
        new_routes['method'] = 'New Route (Recent Avg)'
        new_routes['confidence'] = 0.6  # Lower confidence for new routes
        new_routes['historical_mae'] = 0
        new_routes['baseline_pieces'] = 0

        print(f"   ✅ Found {len(new_routes)} new routes")
        print(f"   New route volume: {new_routes['forecast'].sum():,.0f} pieces")
    else:
        print(f"   No new routes detected")

    return new_routes

def generate_final_forecast(conn, target_week, target_year, table_name):
    """
    Generate the ULTIMATE forecast using Hybrid-Ensemble approach.
    """
    print(f"\n{'='*80}")
    print(f"HYBRID-ENSEMBLE FORECASTING: Week {target_week}, {target_year}")
    print(f"{'='*80}")

    # Step 1: Get baseline routes
    baseline_routes = load_baseline_routes(conn, target_week, table_name)

    # Step 2: Load recent data
    recent_data = load_recent_data(conn, target_week, target_year, lookback_weeks=8, table_name=table_name)

    # Step 3: Validate active routes
    active_routes = validate_active_routes(baseline_routes, recent_data, min_shipments=1)

    # Step 4: Apply ensemble to active routes
    forecast_df, method_counts = apply_ensemble_to_routes(active_routes, recent_data, target_week, target_year)

    # Step 5: Detect and add new routes
    new_routes = detect_new_routes(baseline_routes, recent_data, target_week, min_shipments=2)

    # Combine forecasts
    if len(new_routes) > 0:
        final_forecast = pd.concat([forecast_df, new_routes], ignore_index=True)
    else:
        final_forecast = forecast_df

    # Add metadata
    final_forecast['week'] = target_week
    final_forecast['year'] = target_year

    # Summary
    print(f"\n{'='*80}")
    print(f"FORECAST SUMMARY")
    print(f"{'='*80}")

    print(f"\n📊 Total Forecast:")
    print(f"   Routes: {len(final_forecast):,}")
    print(f"   Pieces: {final_forecast['forecast'].sum():,.0f}")

    print(f"\n📦 By Product Type:")
    for product in ['MAX', 'EXP']:
        product_vol = final_forecast[final_forecast['ProductType'] == product]['forecast'].sum()
        product_routes = len(final_forecast[final_forecast['ProductType'] == product])
        print(f"   {product}: {product_vol:>12,.0f} pieces ({product_routes:>6} routes)")

    print(f"\n🎯 Method Selection:")
    for method, count in sorted(method_counts.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(forecast_df) * 100 if len(forecast_df) > 0 else 0
        print(f"   {method:<25} {count:>6} routes ({pct:>5.1f}%)")

    if len(new_routes) > 0:
        print(f"   {'New Routes':<25} {len(new_routes):>6} routes ({len(new_routes)/len(final_forecast)*100:>5.1f}%)")

    print(f"\n📈 Confidence Distribution:")
    high_conf = len(final_forecast[final_forecast['confidence'] >= 0.8])
    med_conf = len(final_forecast[(final_forecast['confidence'] >= 0.5) & (final_forecast['confidence'] < 0.8)])
    low_conf = len(final_forecast[final_forecast['confidence'] < 0.5])
    print(f"   High (≥80%): {high_conf:>6} routes")
    print(f"   Medium (50-80%): {med_conf:>6} routes")
    print(f"   Low (<50%): {low_conf:>6} routes")

    return final_forecast

def save_forecast(forecast, output_path=None):
    """Save forecast to CSV."""
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"final_week_{forecast['week'].iloc[0]}_{forecast['year'].iloc[0]}_{timestamp}.csv"

    output_path = Path(output_path)
    forecast.to_csv(output_path, index=False)
    print(f"\n💾 Saved to: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description="FINAL: Hybrid-Ensemble Forecasting")
    parser.add_argument('--week', type=int, required=True, help='Target week (1-53)')
    parser.add_argument('--year', type=int, required=True, help='Target year')
    parser.add_argument('--output', type=str, default=None, help='Output CSV path')
    parser.add_argument('--table', type=str, default='decus_domesticops_prod.dbo.tmp_hassett_report')
    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"FINAL HASSETT FORECASTING MODEL")
    print(f"Hybrid-Ensemble with Dynamic Method Selection")
    print(f"{'='*80}\n")

    conn = connect_to_databricks()

    try:
        forecast = generate_final_forecast(conn, args.week, args.year, args.table)

        if len(forecast) > 0:
            save_forecast(forecast, args.output)
            print(f"\n{'='*80}")
            print(f"✅ FINAL FORECAST COMPLETE!")
            print(f"{'='*80}\n")
        else:
            print("❌ Forecast generation failed")
            sys.exit(1)

    finally:
        conn.close()

if __name__ == "__main__":
    main()
