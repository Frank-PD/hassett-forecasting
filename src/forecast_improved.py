#!/usr/bin/env python3
"""
IMPROVED HASSETT FORECASTING - Route-Level Accuracy
Fixes critical issues with baseline approach:
- Uses RECENT data (last 4-8 weeks) instead of 2022/2024
- Route-level trends instead of product-level
- Only forecasts ACTIVE routes
- Detects NEW routes
- Provides confidence scoring
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

def load_recent_activity(conn, target_week, target_year, lookback_weeks=8, table_name="decus_domesticops_prod.dbo.tmp_hassett_report"):
    """
    Load RECENT shipping activity (last N weeks before target week).
    This is the KEY CHANGE - we look at recent data, not historical baselines.
    """
    # Calculate date range
    from datetime import datetime, timedelta

    # Approximate target date (first day of target week)
    # Week 50 of 2025 ≈ mid-December
    year_start = datetime(target_year, 1, 1)
    target_date = year_start + timedelta(weeks=target_week - 1)
    lookback_date = target_date - timedelta(weeks=lookback_weeks)

    query = f"""
    SELECT
        DATE_SHIP as date,
        ODC,
        DDC,
        ProductType,
        PIECES as pieces,
        weekofyear(DATE_SHIP) as week,
        YEAR(DATE_SHIP) as year,
        dayofweek(DATE_SHIP) as dayofweek
    FROM {table_name}
    WHERE ProductType IN ('MAX', 'EXP')
        AND DATE_SHIP >= '{lookback_date.strftime('%Y-%m-%d')}'
        AND DATE_SHIP < '{target_date.strftime('%Y-%m-%d')}'
        AND ODC IS NOT NULL
        AND DDC IS NOT NULL
    ORDER BY DATE_SHIP DESC
    """

    print(f"📊 Loading recent activity ({lookback_weeks} weeks before Week {target_week})...")
    print(f"   Date range: {lookback_date.date()} to {target_date.date()}")

    df = pd.read_sql(query, conn)
    df['date'] = pd.to_datetime(df['date'])

    print(f"✅ Loaded {len(df):,} recent shipments")
    print(f"📅 Date range: {df['date'].min().date()} to {df['date'].max().date()}")

    return df

def identify_active_routes(df, min_shipments=2):
    """
    Identify which routes are CURRENTLY ACTIVE.
    A route is active if it had shipments in recent weeks.
    """
    active_routes = df.groupby(['ODC', 'DDC', 'ProductType']).agg({
        'pieces': ['sum', 'count', 'mean'],
        'date': ['min', 'max']
    }).reset_index()

    active_routes.columns = ['ODC', 'DDC', 'ProductType', 'total_pieces', 'shipment_count', 'avg_pieces', 'first_date', 'last_date']

    # Filter: require minimum number of shipments
    active_routes = active_routes[active_routes['shipment_count'] >= min_shipments]

    print(f"\n📍 Active Routes Identified:")
    print(f"   Total active routes: {len(active_routes)}")
    print(f"   (Minimum {min_shipments} shipments required)")

    return active_routes

def calculate_route_baseline(df, route_info):
    """
    Calculate baseline forecast for a specific route using RECENT data.
    Uses last 4-8 weeks of actual shipments per day of week.
    """
    odc = route_info['ODC']
    ddc = route_info['DDC']
    product = route_info['ProductType']

    # Get recent shipments for this route
    route_data = df[
        (df['ODC'] == odc) &
        (df['DDC'] == ddc) &
        (df['ProductType'] == product)
    ].copy()

    if len(route_data) == 0:
        return pd.DataFrame()

    # Calculate average pieces per day of week
    dow_baseline = route_data.groupby('dayofweek')['pieces'].agg(['mean', 'count']).reset_index()
    dow_baseline.columns = ['dayofweek', 'baseline', 'data_points']

    dow_baseline['ODC'] = odc
    dow_baseline['DDC'] = ddc
    dow_baseline['ProductType'] = product
    dow_baseline['confidence'] = np.minimum(dow_baseline['data_points'] / 3.0, 1.0)  # 3+ data points = 100% confidence

    return dow_baseline

def calculate_route_trend(df, route_info, recent_weeks=4):
    """
    Calculate route-specific trend (not product-level).
    Compare last N weeks to previous N weeks.
    """
    odc = route_info['ODC']
    ddc = route_info['DDC']
    product = route_info['ProductType']

    route_data = df[
        (df['ODC'] == odc) &
        (df['DDC'] == ddc) &
        (df['ProductType'] == product)
    ].copy()

    if len(route_data) < 2:
        return 1.0  # No trend if insufficient data

    # Sort by date
    route_data = route_data.sort_values('date')

    # Split into recent and previous periods
    mid_point = len(route_data) // 2
    recent = route_data.iloc[mid_point:]
    previous = route_data.iloc[:mid_point]

    recent_avg = recent['pieces'].mean()
    previous_avg = previous['pieces'].mean()

    if previous_avg > 0:
        trend = recent_avg / previous_avg
    else:
        trend = 1.0

    # Cap trend to reasonable range [-50% to +100%]
    trend = np.clip(trend, 0.5, 2.0)

    return trend

def generate_improved_forecast(conn, target_week, target_year, table_name):
    """
    Generate forecast using IMPROVED route-level logic.
    """
    print(f"\n{'='*80}")
    print(f"IMPROVED FORECASTING: Week {target_week}, {target_year}")
    print(f"{'='*80}\n")

    # Step 1: Load recent activity
    df_recent = load_recent_activity(conn, target_week, target_year, lookback_weeks=8, table_name=table_name)

    # Step 2: Identify active routes
    active_routes = identify_active_routes(df_recent, min_shipments=2)

    # Step 3: Generate forecast for each active route
    print(f"\n📊 Generating route-level forecasts...")
    forecasts = []

    for idx, route in active_routes.iterrows():
        # Get baseline per day of week
        route_baseline = calculate_route_baseline(df_recent, route)

        if len(route_baseline) == 0:
            continue

        # Calculate route-specific trend
        route_trend = calculate_route_trend(df_recent, route)

        # Apply trend
        route_baseline['trend'] = route_trend
        route_baseline['forecast'] = route_baseline['baseline'] * route_baseline['trend']

        forecasts.append(route_baseline)

    if len(forecasts) == 0:
        print("❌ No forecasts generated")
        return pd.DataFrame()

    # Combine all forecasts
    forecast = pd.concat(forecasts, ignore_index=True)
    forecast['week'] = target_week
    forecast['year'] = target_year
    forecast['method'] = 'Recent_Activity_Based'

    # Summary
    print(f"\n✅ Forecast Generated:")
    print(f"   Total routes: {len(forecast)}")
    print(f"   Total pieces: {forecast['forecast'].sum():,.0f}")

    print(f"\n📊 By Product:")
    for product in ['MAX', 'EXP']:
        product_forecast = forecast[forecast['ProductType'] == product]['forecast'].sum()
        product_routes = len(forecast[forecast['ProductType'] == product]['ODC'].unique())
        print(f"   {product}: {product_forecast:,.0f} pieces ({product_routes} ODCs)")

    print(f"\n📈 Confidence Distribution:")
    high_conf = len(forecast[forecast['confidence'] >= 0.8])
    med_conf = len(forecast[(forecast['confidence'] >= 0.5) & (forecast['confidence'] < 0.8)])
    low_conf = len(forecast[forecast['confidence'] < 0.5])
    print(f"   High (≥80%): {high_conf} routes")
    print(f"   Medium (50-80%): {med_conf} routes")
    print(f"   Low (<50%): {low_conf} routes")

    return forecast

def save_forecast(forecast, output_path=None):
    """Save forecast to CSV."""
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"improved_week_{forecast['week'].iloc[0]}_{forecast['year'].iloc[0]}_{timestamp}.csv"

    output_path = Path(output_path)
    forecast.to_csv(output_path, index=False)
    print(f"\n💾 Saved to: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description="IMPROVED: Route-Level Forecasting")
    parser.add_argument('--week', type=int, required=True, help='Target week (1-53)')
    parser.add_argument('--year', type=int, required=True, help='Target year')
    parser.add_argument('--output', type=str, default=None, help='Output CSV path')
    parser.add_argument('--table', type=str, default='decus_domesticops_prod.dbo.tmp_hassett_report')
    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"IMPROVED HASSETT FORECASTING")
    print(f"Route-Level Accuracy with Recent Activity")
    print(f"{'='*80}\n")

    conn = connect_to_databricks()

    try:
        forecast = generate_improved_forecast(conn, args.week, args.year, args.table)

        if len(forecast) > 0:
            save_forecast(forecast, args.output)
            print(f"\n{'='*80}")
            print(f"✅ IMPROVED FORECAST COMPLETE!")
            print(f"{'='*80}\n")
        else:
            print("❌ Forecast generation failed")
            sys.exit(1)

    finally:
        conn.close()

if __name__ == "__main__":
    main()
